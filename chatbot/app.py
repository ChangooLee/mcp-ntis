"""NTIS R&D 분석가 챗봇 — Streamlit + DeepAgent + Claude.

LangChain DeepAgent가 NTIS MCP 도구를 활용해 사용자의 R&D 분석 질문에 답한다.
각 단계(생각·도구 호출·도구 응답·최종 답변)를 실시간으로 시각화한다.

기동:
    streamlit run chatbot/app.py
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
# chatbot 패키지와 mcp_ntis 패키지를 모두 import 가능하게
for p in (PROJECT_ROOT, PROJECT_ROOT / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from chatbot.agent import build_agent, run_agent_collect, enhance_user_prompt  # noqa: E402


# ---------------------------------------------------------------------------
# 페이지 설정
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="NTIS R&D 분석가",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# 세션 상태 초기화
# ---------------------------------------------------------------------------


def init_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "agent" not in st.session_state:
        st.session_state.agent = None
    if "tools" not in st.session_state:
        st.session_state.tools = []
    if "loop" not in st.session_state:
        st.session_state.loop = asyncio.new_event_loop()


def get_loop() -> asyncio.AbstractEventLoop:
    return st.session_state.loop


def run_async(coro: Any) -> Any:
    return get_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# 에이전트 초기화 (앱 시작 시 1회)
# ---------------------------------------------------------------------------


@st.cache_resource(show_spinner="NTIS MCP에 연결하고 DeepAgent를 준비합니다...")
def init_agent() -> tuple[Any, list[Any]]:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    agent, tools = loop.run_until_complete(build_agent())
    st.session_state.loop = loop
    return agent, tools


# ---------------------------------------------------------------------------
# 사이드바
# ---------------------------------------------------------------------------


def render_sidebar(tools: list[Any]) -> None:
    with st.sidebar:
        st.markdown("## 🔬 NTIS R&D 분석가")
        st.caption("LangChain DeepAgent + NTIS MCP + Claude")

        st.divider()

        st.markdown("### 🧰 사용 가능한 도구")
        st.caption(f"총 {len(tools)}개 NTIS 도구")
        for tool in tools:
            name = getattr(tool, "name", str(tool))
            desc = getattr(tool, "description", "")
            with st.expander(f"🛠️ {name}"):
                st.markdown(desc[:500] + ("..." if len(desc) > 500 else ""))

        st.divider()

        st.markdown("### 💡 사업 분석 질문 예시")
        examples = [
            "우리 회사가 mRNA 백신 사업에 진출하려고 해. 한국에서 누가 이 분야를 가장 활발히 하고 있고, 협력 후보 기업·기관을 추천해줘.",
            "전고체 배터리 시장 진입을 검토 중이야. 한국의 R&D 생태계 — 학계·출연연·중소기업 가치사슬을 정리해줘. 우리가 끼어들 수 있는 자리가 어딘지도.",
            "지금 정부가 가장 빠르게 투자를 늘리고 있는 차세대 산업이 뭐야? 우리 회사가 정부 R&D 펀딩을 노릴 만한 분야를 알려줘.",
            "ETRI(한국전자통신연구원)과 AI 분야 협력을 검토 중이야. ETRI의 AI 역량, 진행 중인 대형 과제, 핵심 연구자를 정리해줘.",
            "CRISPR 유전자 편집으로 희귀질환 치료 사업을 시작하려 해. 우리 연구가 어떤 정부 분류 카테고리에 속하고, 한국에서 비슷한 연구를 누가 하는지 알려줘.",
            "고령자 시장 진출 검토 중인데, 치매 신약과 항암 면역치료 중 어느 분야가 정부 펀딩이 더 효율적이야? 5년 추세로 비교.",
            "양자컴퓨터 분야에 우리 회사가 진출할 수 있을까? 한국의 기술 수준, 핵심 연구자·기업, 강한 영역(하드웨어 vs 알고리즘)을 알려줘.",
            "스마트 토일렛 헬스케어 제품을 만들고 싶어. 어떤 기술이 모여야 하고 어떤 기업과 협력할 수 있을지 알려줘.",
            "전자현미경을 활용한 R&D를 시작하려는데, 한국에서 어디와 협업해야 가장 좋은 장비를 쓸 수 있어?",
            "특정 분야 전문가(예: 양자컴퓨팅 분야 'Kim Jun-ki')의 학술 활동을 추적해서 영입 가능성을 검토하고 싶어.",
        ]
        for ex in examples:
            if st.button(ex[:50] + ("..." if len(ex) > 50 else ""), key=f"ex_{hash(ex)}"):
                st.session_state.pending_question = ex
                st.rerun()

        st.divider()

        st.markdown("### ⚙️ 설정")
        st.session_state.setdefault("use_enhancer", True)
        st.session_state.use_enhancer = st.checkbox(
            "🪄 질문 자동 강화 (Prompt Enhancer)",
            value=st.session_state.use_enhancer,
            help="비즈니스 자연어 질문을 분석 도구 활용 계획으로 자동 보강합니다.",
        )

        if st.button("🗑️ 대화 초기화", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.markdown("---")
        st.caption("국가과학기술지식정보서비스(NTIS) 데이터 활용")


# ---------------------------------------------------------------------------
# 메시지 렌더링
# ---------------------------------------------------------------------------


def render_step(step: dict[str, Any]) -> None:
    """(레거시) 사용 안 함. render_live가 expander로 일괄 처리."""
    pass


def render_message(msg: dict[str, Any]) -> None:
    """과거 메시지 (저장된) 렌더링 — expander로 묶기."""
    if msg["role"] == "user":
        with st.chat_message("user", avatar="👤"):
            st.markdown(msg["content"])
    elif msg["role"] == "assistant":
        steps = msg.get("steps", [])
        tool_calls = sum(1 for s in steps if s["type"] == "tool_call")
        tools_used = sorted({s["content"].get("name", "") for s in steps if s["type"] == "tool_call"})
        if steps:
            with st.expander(
                f"🔍 분석 과정 — 도구 {tool_calls}회 ({', '.join(tools_used)})",
                expanded=False,
            ):
                for step in steps:
                    stype = step["type"]
                    content = step["content"]
                    if stype == "ai_text" and content.strip():
                        st.markdown(f"💭 {content[:500]}{'...' if len(content) > 500 else ''}")
                    elif stype == "thinking" and content.strip():
                        st.caption(f"🧠 {content[:300]}")
                    elif stype == "tool_call":
                        st.markdown(f"🔧 **{content.get('name','')}**")
                    elif stype == "tool_result":
                        st.caption(f"📥 {content.get('name','')} — {len(content.get('content',''))}자")
        final = msg.get("content", "")
        if final:
            with st.chat_message("assistant", avatar="🔬"):
                st.markdown(final)


# ---------------------------------------------------------------------------
# 응답 처리
# ---------------------------------------------------------------------------


async def process_question(question: str, agent: Any) -> dict[str, Any]:
    """질문에 대해 에이전트를 실행하고 모든 step을 수집."""
    steps: list[dict[str, Any]] = []
    final_text = ""
    last_thinking = ""

    async for step in stream_agent_run(agent, question):
        steps.append(step)
        if step["type"] == "thinking":
            last_thinking = step["content"]

    # 마지막 thinking이 최종 답변
    final_text = last_thinking

    return {"steps": steps[:-1] if steps else [], "final": final_text}


def render_live(question: str, agent: Any) -> dict[str, Any]:
    """안정 모드: ainvoke로 한 번에 받아 모든 step과 final을 일괄 렌더링.

    스트리밍 모드의 메시지 누락 이슈를 해결하기 위한 처리.
    분석 중에는 spinner만 표시하고, 완료 후 전체 도구 흐름과 최종 답변을 표시.
    """
    progress_status = st.status("🤖 분석 중... 도구를 호출하고 데이터를 수집하고 있어요.", expanded=False)

    result = run_async(run_agent_collect(agent, question))

    # 도구 호출 통계
    tool_calls = sum(1 for s in result["steps"] if s["type"] == "tool_call")
    tool_results = sum(1 for s in result["steps"] if s["type"] == "tool_result")
    tools_used = sorted(
        {s["content"].get("name", "") for s in result["steps"] if s["type"] == "tool_call"}
    )

    progress_status.update(
        label=f"✅ 분석 완료 — 도구 {tool_calls}회 호출 ({len(tools_used)}종)",
        state="complete",
        expanded=False,
    )

    # 도구 흐름을 하나의 expander에 묶어 가독성 확보
    with st.expander(f"🔍 분석 과정 보기 — 도구 {tool_calls}회 / 응답 {tool_results}회 / 사용 도구: {', '.join(tools_used)}", expanded=False):
        for step in result["steps"]:
            stype = step["type"]
            content = step["content"]
            if stype == "ai_text":
                if content.strip():
                    st.markdown(f"💭 **분석 메모** — {content[:500]}{'...' if len(content) > 500 else ''}")
            elif stype == "thinking":
                if content.strip():
                    st.caption(f"🧠 {content[:300]}")
            elif stype == "tool_call":
                name = content.get("name", "")
                args = content.get("args", {})
                st.markdown(f"🔧 **{name}**")
                if args:
                    args_short = {k: (str(v)[:120] + ("..." if len(str(v)) > 120 else "")) for k, v in args.items()}
                    st.code(json.dumps(args_short, ensure_ascii=False, indent=2), language="json")
            elif stype == "tool_result":
                name = content.get("name", "")
                text = content.get("content", "")
                preview = text[:300] + ("..." if len(text) > 300 else "")
                st.markdown(f"📥 **{name}** 응답 ({len(text):,}자)")
                st.caption(preview)

    # 최종 답변
    if result["final"]:
        with st.chat_message("assistant", avatar="🔬"):
            st.markdown(result["final"])
    else:
        st.warning("최종 답변을 생성하지 못했습니다. 질문을 더 구체적으로 작성하거나 다시 시도해주세요.")

    return {"steps": result["steps"], "final": result["final"]}


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------


def main() -> None:
    init_state()

    # 에이전트 초기화
    try:
        agent, tools = init_agent()
    except Exception as exc:
        st.error(f"❌ 에이전트 초기화 실패: {exc}")
        st.info("`.env`에 `ANTHROPIC_API_KEY`가 설정되어 있는지 확인하세요.")
        st.code(str(exc))
        return

    render_sidebar(tools)

    # 헤더
    st.title("🔬 NTIS R&D 분석가")
    st.caption(
        "한국 국가R&D(NTIS) 데이터를 활용한 동향 분석. "
        "LangChain DeepAgent + Claude + NTIS MCP의 16개 도구."
    )

    # 과거 메시지 렌더
    for msg in st.session_state.messages:
        render_message(msg)

    # 사이드바에서 선택한 질문 처리
    pending = st.session_state.pop("pending_question", None) if "pending_question" in st.session_state else None
    question = pending or st.chat_input("궁금한 R&D 동향을 물어보세요...")

    if question:
        # 사용자 메시지 표시 (원본)
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user", avatar="👤"):
            st.markdown(question)

        # Prompt Enhancer 적용
        agent_input = question
        if st.session_state.get("use_enhancer", True):
            with st.status("🪄 질문 강화 중...", expanded=False) as s:
                try:
                    import os as _os
                    enhanced = run_async(enhance_user_prompt(
                        question,
                        model_name=_os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
                        api_key=_os.getenv("ANTHROPIC_API_KEY", ""),
                    ))
                    agent_input = enhanced
                    # 강화된 부분만 표시 (원본 제외)
                    plan_text = enhanced.split("---\n", 1)[-1] if "---" in enhanced else enhanced
                    st.markdown(plan_text)
                    s.update(label="✅ 분석 계획 수립 완료", state="complete", expanded=False)
                except Exception as exc:
                    st.warning(f"질문 강화 실패: {exc} — 원본 질문으로 진행")
                    s.update(label="⚠️ 원본 질문으로 진행", state="complete", expanded=False)

        # 에이전트 실행 + 단계별 시각화
        result = render_live(agent_input, agent)

        # 저장
        st.session_state.messages.append({
            "role": "assistant",
            "steps": result["steps"],
            "content": result["final"],
        })


if __name__ == "__main__":
    main()
