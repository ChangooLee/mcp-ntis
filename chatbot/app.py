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

from chatbot.agent import build_agent, stream_agent_run  # noqa: E402


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

        st.markdown("### 💡 융합 시나리오 (NTIS + ScienceON)")
        examples = [
            "mRNA 백신 상위 3개 기관의 NTIS 정부지원금과 ScienceON 학술 출간량을 비교해서 펀딩 효율을 평가해줘.",
            "전고체 배터리 분야 한국의 강점을 NTIS 과제·ScienceON 논문·특허로 종합 비교해줘. 한국이 더 강한 영역(특허 vs 논문)을 결론지어줘.",
            "NTIS 트렌드 이슈와 ScienceON 동향 보고서를 비교해서 정부·KISTI 큐레이션이 일치하는 분야를 찾아줘.",
            "ETRI AI 최대 예산 과제의 공동연구기관과 핵심 PI를 식별하고, ScienceON 연구자 검색으로 PI의 학술 활동 이력을 추적해줘.",
            "'CRISPR-Cas9 희귀질환 치료' 연구를 NTIS 3종 분류와 ScienceON DDC 분류로 동시에 매핑해서 차이를 비교해줘.",
            "항암 면역치료 vs 치매 신약을 NTIS 정부 예산·ScienceON 논문 수 동시 비교해 1억원당 논문 효율을 계산해줘.",
            "양자 우월성(Quantum Supremacy) 개념의 한국 R&D를 NTIS 통합검색·ScienceON 논문·특허·동향 4-way 교차 검증해줘.",
            "스마트 토일렛 헬스케어 제품을 만들고 싶어. 어떤 기술이 모여야 하고 어떤 기업과 협력할 수 있을지 알려줘.",
        ]
        for ex in examples:
            if st.button(ex[:50] + ("..." if len(ex) > 50 else ""), key=f"ex_{hash(ex)}"):
                st.session_state.pending_question = ex
                st.rerun()

        st.divider()

        if st.button("🗑️ 대화 초기화", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.markdown("---")
        st.caption("국가과학기술지식정보서비스(NTIS) 데이터 활용")


# ---------------------------------------------------------------------------
# 메시지 렌더링
# ---------------------------------------------------------------------------


def render_step(step: dict[str, Any]) -> None:
    """에이전트의 단일 step (생각·도구호출·도구응답)을 시각화."""
    stype = step["type"]
    content = step["content"]

    if stype in ("thinking", "ai_text"):
        if not content.strip():
            return
        with st.chat_message("assistant", avatar="🧠"):
            st.markdown(f"💭 **분석 중...**\n\n{content}")
    elif stype == "tool_call":
        name = content.get("name", "")
        args = content.get("args", {})
        with st.chat_message("assistant", avatar="🛠️"):
            st.markdown(f"**🔧 도구 호출**: `{name}`")
            with st.expander("입력 파라미터", expanded=False):
                st.json(args)
    elif stype == "tool_result":
        name = content.get("name", "")
        text = content.get("content", "")
        with st.chat_message("assistant", avatar="📊"):
            st.markdown(f"**📥 `{name}` 응답**")
            with st.expander("응답 데이터", expanded=False):
                try:
                    parsed = json.loads(text)
                    st.json(parsed)
                except (json.JSONDecodeError, TypeError):
                    st.code(text[:5000])


def render_message(msg: dict[str, Any]) -> None:
    """과거 메시지 (저장된) 렌더링."""
    if msg["role"] == "user":
        with st.chat_message("user", avatar="👤"):
            st.markdown(msg["content"])
    elif msg["role"] == "assistant":
        # 누적된 step들 + 최종 답변
        steps = msg.get("steps", [])
        for step in steps:
            render_step(step)
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
    """질문 처리 중 실시간 단계 표시.

    Streamlit의 sync 환경에서 async 스트림을 처리하기 위해
    동기 wrapper로 step을 모았다가 순차 표시한다.
    """
    placeholder = st.empty()
    progress_status = st.status("🤖 에이전트 분석 시작...", expanded=True)

    steps: list[dict[str, Any]] = []
    final_text = ""

    async def _run() -> None:
        nonlocal final_text
        text_buffer = ""
        async for step in stream_agent_run(agent, question):
            stype = step["type"]
            if stype in ("thinking", "ai_text"):
                text_buffer = step["content"]
                with progress_status:
                    if text_buffer.strip():
                        snippet = text_buffer[:300] + ("..." if len(text_buffer) > 300 else "")
                        st.markdown(f"💭 {snippet}")
            elif stype == "tool_call":
                name = step["content"].get("name", "")
                with progress_status:
                    st.markdown(f"🛠️ **도구 호출**: `{name}`")
            elif stype == "tool_result":
                name = step["content"].get("name", "")
                with progress_status:
                    st.markdown(f"📥 `{name}` 응답 수신")
            steps.append(step)
        final_text = text_buffer

    run_async(_run())

    progress_status.update(label="✅ 분석 완료", state="complete", expanded=False)

    # 마지막 ai_text는 최종 답변, 나머지는 중간 단계
    intermediate = steps[:-1] if (steps and steps[-1]["type"] in ("thinking", "ai_text")) else steps
    for step in intermediate:
        render_step(step)

    if final_text:
        with st.chat_message("assistant", avatar="🔬"):
            st.markdown(final_text)

    return {"steps": intermediate, "final": final_text}


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
        # 사용자 메시지 표시
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user", avatar="👤"):
            st.markdown(question)

        # 에이전트 실행 + 단계별 시각화
        result = render_live(question, agent)

        # 저장
        st.session_state.messages.append({
            "role": "assistant",
            "steps": result["steps"],
            "content": result["final"],
        })


if __name__ == "__main__":
    main()
