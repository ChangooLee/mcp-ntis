import logging
from typing import Annotated, Optional

from mcp.types import TextContent
from pydantic import Field

from mcp_ntis.server import as_json_text, error_text, get_client, mcp

logger = logging.getLogger("mcp-ntis")

_LENGTH_NOTE = (
    "【텍스트 길이 요건】 "
    "API는 두 단계 검증을 수행함: "
    "(1) 300바이트 미만이면 오류(-1002). 한글 1자=3바이트이므로 최소 한글 100자 이상 필요. "
    "(2) 유효 전문 용어가 32개 이하이면 오류(-2002). 단순 문장 반복은 해당 오류 유발. "
    "실용 기준: 연구목표·연구방법·기대효과를 각각 1~2문장씩 구체적으로 기술한 총 150자(450바이트) 이상 권장. "
    "오류 시 연구 내용을 더 구체적·기술적으로 보완하여 재시도할 것."
)
_DETAIL_NOTE = (
    "상세모드(detailed=True): goal과 abstract 모두 필수, 두 필드 합산 300바이트(한글 약 100자) 이상. "
    "단순모드(detailed=False): text만 입력. "
    + _LENGTH_NOTE
)
_TEXT_HELP = (
    "연구 내용 텍스트. detailed=False일 때 사용. "
    "연구목표·연구방법·기대효과를 포함해 총 150자(450바이트) 이상 구체적으로 기술 권장. "
    "짧거나 전문 용어가 부족하면 API 오류 반환."
)


@mcp.tool(
    name="recommend_std_classification",
    tags={"분류추천", "표준분류", "과기부"},
    description=(
        "국가과학기술표준분류(대/중/소) 코드를 추천합니다. "
        "과기부·교육부·환경부 등 대부분의 R&D 과제에 적용되는 범용 분류 체계. "
        "최대 5개를 정확도(%) 순으로 반환. 결과의 small_code가 과제 등록 시 실제 사용 코드. "
        "단순모드: text 입력(연구목표·방법·효과 포함 150자/450바이트 이상 권장). "
        "상세모드(detailed=True): goal+abstract 합산 300바이트 이상 필수. "
        "텍스트가 짧거나 전문 용어가 부족하면 API 오류 반환 → 내용을 더 구체적으로 보완 후 재시도. "
        "보건복지부→recommend_ht_classification, 산업부→recommend_it_classification 사용."
    ),
)
async def recommend_std_classification(
    text: Annotated[str, Field(description=_TEXT_HELP)] = "",
    detailed: Annotated[bool, Field(description="상세모드 여부. True면 goal+abstract로 추천. False(기본)면 text만 사용")] = False,
    goal: Annotated[str, Field(description="[상세모드 필수] 연구목표 요약. abstract와 합산 300바이트(한글 약 100자) 이상이어야 함")] = "",
    abstract: Annotated[str, Field(description="[상세모드 필수] 연구내용 요약. goal과 합산 300바이트 이상이어야 함")] = "",
    effects: Annotated[str, Field(description="[상세모드 선택] 기대효과 요약")] = "",
    kor_keywords: Annotated[str, Field(description="[상세모드 선택] 국문 핵심어 (쉼표 구분). 예: '나노소재,배터리,에너지저장'")] = "",
    eng_keywords: Annotated[str, Field(description="[상세모드 선택] 영문 핵심어 (쉼표 구분). 예: 'nano material,battery,energy storage'")] = "",
) -> TextContent:
    if not text and not (goal and abstract):
        return as_json_text({"error": "text 또는 goal+abstract를 입력해야 합니다."})
    try:
        client = get_client()
        result = await client.recommend_std_classification(
            text=text,
            detailed=detailed,
            goal=goal,
            abstract=abstract,
            effects=effects,
            kor_keywords=kor_keywords,
            eng_keywords=eng_keywords,
        )
        return as_json_text(result)
    except Exception as e:
        logger.error(f"recommend_std_classification 오류: {e}")
        return error_text(str(e))


@mcp.tool(
    name="recommend_ht_classification",
    tags={"분류추천", "보건의료", "복지부"},
    description=(
        "보건의료기술분류 코드를 추천합니다 (보건복지부·질병관리청·국립암센터 R&D 전용). "
        "세 가지 분류 축을 동시에 추천: "
        "disease_classification(질환분류: KCD 코드, 어떤 질환 대상인지), "
        "research_output_classification(연구행위분류: MOHWR, 어떤 연구 방법인지), "
        "industry_classification(산업기술분류: MOTIE). "
        "최대 5개씩 정확도(%) 순 반환. "
        "텍스트 요건: 150자(450바이트) 이상 구체적 기술 권장. "
        "짧거나 전문 용어 부족 시 오류 반환 → 내용 보완 후 재시도. "
        "단순모드: text 입력. 상세모드(detailed=True): goal+abstract 합산 300바이트 이상 필수."
    ),
)
async def recommend_ht_classification(
    text: Annotated[str, Field(description=_TEXT_HELP)] = "",
    detailed: Annotated[bool, Field(description="상세모드 여부. True면 goal+abstract로 추천. False(기본)면 text만 사용")] = False,
    goal: Annotated[str, Field(description="[상세모드 필수] 연구목표 요약. abstract와 합산 300바이트 이상이어야 함")] = "",
    abstract: Annotated[str, Field(description="[상세모드 필수] 연구내용 요약. goal과 합산 300바이트 이상이어야 함")] = "",
    effects: Annotated[str, Field(description="[상세모드 선택] 기대효과 요약")] = "",
    kor_keywords: Annotated[str, Field(description="[상세모드 선택] 국문 핵심어 (쉼표 구분)")] = "",
    eng_keywords: Annotated[str, Field(description="[상세모드 선택] 영문 핵심어 (쉼표 구분)")] = "",
) -> TextContent:
    if not text and not (goal and abstract):
        return as_json_text({"error": "text 또는 goal+abstract를 입력해야 합니다."})
    try:
        client = get_client()
        result = await client.recommend_ht_classification(
            text=text,
            detailed=detailed,
            goal=goal,
            abstract=abstract,
            effects=effects,
            kor_keywords=kor_keywords,
            eng_keywords=eng_keywords,
        )
        return as_json_text(result)
    except Exception as e:
        logger.error(f"recommend_ht_classification 오류: {e}")
        return error_text(str(e))


@mcp.tool(
    name="recommend_it_classification",
    tags={"분류추천", "산업기술", "산업부"},
    description=(
        "산업기술분류 코드를 추천합니다 (산업통상자원부·중소벤처기업부 R&D 전용). "
        "IT·BT·NT·ET·ST·CT 등 6T 기반 대/중/소 분류 코드와 정확도(%) 반환. 최대 5개 추천. "
        "텍스트 요건: 150자(450바이트) 이상 구체적 기술 권장. "
        "짧거나 전문 용어 부족 시 오류 반환 → 내용 보완 후 재시도. "
        "단순모드: text 입력. 상세모드(detailed=True): goal+abstract 합산 300바이트 이상 필수."
    ),
)
async def recommend_it_classification(
    text: Annotated[str, Field(description=_TEXT_HELP)] = "",
    detailed: Annotated[bool, Field(description="상세모드 여부. True면 goal+abstract로 추천. False(기본)면 text만 사용")] = False,
    goal: Annotated[str, Field(description="[상세모드 필수] 연구목표 요약. abstract와 합산 300바이트 이상이어야 함")] = "",
    abstract: Annotated[str, Field(description="[상세모드 필수] 연구내용 요약. goal과 합산 300바이트 이상이어야 함")] = "",
    effects: Annotated[str, Field(description="[상세모드 선택] 기대효과 요약")] = "",
    kor_keywords: Annotated[str, Field(description="[상세모드 선택] 국문 핵심어 (쉼표 구분)")] = "",
    eng_keywords: Annotated[str, Field(description="[상세모드 선택] 영문 핵심어 (쉼표 구분)")] = "",
) -> TextContent:
    if not text and not (goal and abstract):
        return as_json_text({"error": "text 또는 goal+abstract를 입력해야 합니다."})
    try:
        client = get_client()
        result = await client.recommend_it_classification(
            text=text,
            detailed=detailed,
            goal=goal,
            abstract=abstract,
            effects=effects,
            kor_keywords=kor_keywords,
            eng_keywords=eng_keywords,
        )
        return as_json_text(result)
    except Exception as e:
        logger.error(f"recommend_it_classification 오류: {e}")
        return error_text(str(e))
