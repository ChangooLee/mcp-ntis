import logging
from typing import Annotated, Optional

from mcp.types import TextContent
from pydantic import Field

from mcp_ntis.server import as_json_text, error_text, get_client, mcp

logger = logging.getLogger("mcp-ntis")

_DETAIL_NOTE = (
    "상세모드(detailed=True): goal과 abstract 모두 필수, 두 필드 합산 300바이트(한글 약 100자) 이상. "
    "단순모드(detailed=False): text만 입력, 300바이트 이상. "
    "텍스트가 짧으면 API가 오류를 반환하므로 연구 내용을 충분히 기술할 것."
)
_TEXT_HELP = (
    "연구 내용 텍스트 (300바이트≈한글 100자 이상, 30KB 이하). "
    "detailed=False일 때 사용. 연구목표·방법·기대효과를 포함해 충분히 기술해야 정확한 분류 가능."
)


@mcp.tool(
    name="recommend_std_classification",
    description=(
        "국가과학기술표준분류(대/중/소) 코드를 추천합니다. "
        "과기부·교육부·환경부 등 대부분의 R&D 과제에 적용되는 범용 분류 체계. "
        "최대 5개를 정확도(%) 순으로 반환. 결과의 small_code가 과제 등록 시 실제 사용 코드. "
        "단순모드: text만 입력(300바이트 이상). "
        "상세모드(detailed=True): goal과 abstract 모두 필수이며 합산 300바이트 이상 필요. "
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
    description=(
        "보건의료기술분류 코드를 추천합니다 (보건복지부·질병관리청·국립암센터 R&D 전용). "
        "질환별분류(MOHWD: 어떤 질환을 다루는지)와 "
        "연구행위분류(MOHWR: 어떤 방법으로 연구하는지) 두 축을 동시에 추천. "
        "최대 5개씩 정확도 순 반환. "
        "단순모드: text 300바이트 이상. 상세모드(detailed=True): goal+abstract 합산 300바이트 이상."
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
    description=(
        "산업기술분류 코드를 추천합니다 (산업통상자원부·중소벤처기업부 R&D 전용). "
        "IT·BT·NT·ET·ST·CT 등 6T 기반 대/중/소 분류 코드와 정확도(%) 반환. 최대 5개 추천. "
        "단순모드: text 300바이트 이상. 상세모드(detailed=True): goal+abstract 합산 300바이트 이상."
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
