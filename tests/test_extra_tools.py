"""Tests for extra_tools.py — uses cache injection to bypass IP restriction."""
import json
import os

import pytest

os.environ.setdefault("NTIS_API_KEY", "test_key_for_unit_tests")

from mcp_ntis.cache import set_cached
from mcp_ntis.client import (
    CONN_CONTENT_URL,
    ISSUE_RND_URL,
    NTIS_DIC_URL,
    ORG_RND_INFO_URL,
    TARGET_SEARCH_URL,
    NTISClient,
)
from mcp_ntis.config import NTISConfig

ORG_RND_XML = """<?xml version="1.0" encoding="UTF-8"?>
<orgRndInfo>
  <resultCode>00</resultCode>
  <resultMsg>정상처리</resultMsg>
  <orgName>한국전자통신연구원</orgName>
  <orgPageInfo>https://www.ntis.go.kr/rndopen/inst/instIntroInfo.do?instOrgCd=12345</orgPageInfo>
  <rndKorKeyword>인공지능,무선통신,반도체,소프트웨어,보안</rndKorKeyword>
  <rndEngKeyword>AI,wireless,semiconductor,software,security</rndEngKeyword>
  <rndCategory>정보통신,전기전자,기계</rndCategory>
  <numOfList>3</numOfList>
  <rndStatusList>
    <item>
      <year>2023</year>
      <pjtCnt>520</pjtCnt>
      <rndBudget>350000</rndBudget>
      <govBudget>300000</govBudget>
      <paperCnt>1200</paperCnt>
      <patentCnt>850</patentCnt>
      <reportCnt>420</reportCnt>
    </item>
    <item>
      <year>2022</year>
      <pjtCnt>500</pjtCnt>
      <rndBudget>320000</rndBudget>
      <govBudget>280000</govBudget>
      <paperCnt>1100</paperCnt>
      <patentCnt>800</patentCnt>
      <reportCnt>400</reportCnt>
    </item>
  </rndStatusList>
</orgRndInfo>"""

ISSUE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<NewestIssue>
  <selectListCnt>3</selectListCnt>
  <list>
    <topicNo>20240101</topicNo>
    <topicNm>인공지능 안전성 연구동향</topicNm>
    <extrDt>20240315</extrDt>
    <rltdPjtCnt>2450</rltdPjtCnt>
    <url01>https://www.ntis.go.kr/doc/001</url01>
    <url02>https://www.ntis.go.kr/doc/002</url02>
    <rltdKywdList>인공지능,머신러닝,딥러닝,안전,신뢰성</rltdKywdList>
    <imgOfferYn>Y</imgOfferYn>
  </list>
  <list>
    <topicNo>20240102</topicNo>
    <topicNm>탄소중립 그린수소 기술</topicNm>
    <extrDt>20240310</extrDt>
    <rltdPjtCnt>1800</rltdPjtCnt>
    <url01>https://www.ntis.go.kr/doc/003</url01>
    <url02>https://www.ntis.go.kr/doc/004</url02>
    <rltdKywdList>수소,탄소중립,에너지,연료전지</rltdKywdList>
    <imgOfferYn>Y</imgOfferYn>
  </list>
</NewestIssue>"""

DIC_XML = """<?xml version="1.0" encoding="UTF-8"?>
<RESULT>
  <TOTALHITS>15</TOTALHITS>
  <STARTPOSITION>1</STARTPOSITION>
  <HITS>2</HITS>
  <SEARCHTIME>0.05</SEARCHTIME>
  <RESULTSET>
    <HIT>
      <TermSn>10001</TermSn>
      <KorWord>나노소재</KorWord>
      <EngWord>Nanomaterial</EngWord>
      <MainAbrv>NM</MainAbrv>
      <SntStdCls>나노 및 소재</SntStdCls>
      <RelWord>나노입자,나노구조,나노기술</RelWord>
      <TermDctn>크기가 1~100nm 범위에 있는 소재로서 고유한 물리적·화학적 특성을 갖는 물질</TermDctn>
      <TermCls>기술용어</TermCls>
    </HIT>
    <HIT>
      <TermSn>10002</TermSn>
      <KorWord>나노기술</KorWord>
      <EngWord>Nanotechnology</EngWord>
      <MainAbrv>NT</MainAbrv>
      <SntStdCls>나노 및 소재</SntStdCls>
      <RelWord>나노소재,나노공정,나노소자</RelWord>
      <TermDctn>1~100nm 수준의 미세한 영역을 다루는 기술 분야</TermDctn>
      <TermCls>기술용어</TermCls>
    </HIT>
  </RESULTSET>
</RESULT>"""

TARGET_SEARCH_XML = """<?xml version="1.0" encoding="UTF-8"?>
<ntis>
  <status>
    <recode>0000</recode>
    <remsg>성공</remsg>
  </status>
  <contents>
    <dataset>
      <cd>060000</cd>
      <cdNm>정보통신</cdNm>
      <cdNmEng>Information and Communication</cdNmEng>
      <cdExplan>정보통신 분야의 연구개발 활동</cdExplan>
      <upperCd>000000</upperCd>
    </dataset>
    <dataset>
      <cd>060100</cd>
      <cdNm>통신</cdNm>
      <cdNmEng>Communication</cdNmEng>
      <cdExplan>통신 관련 기술 연구</cdExplan>
      <upperCd>060000</upperCd>
    </dataset>
    <dataset>
      <cd>060200</cd>
      <cdNm>정보처리</cdNm>
      <cdNmEng>Information Processing</cdNmEng>
      <cdExplan>정보처리 기술 연구</cdExplan>
      <upperCd>060000</upperCd>
    </dataset>
  </contents>
</ntis>"""

CONN_CONTENT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<RESULT>
  <TOTALHITS>5</TOTALHITS>
  <STARTPOSITION>1</STARTPOSITION>
  <HITS>3</HITS>
  <SEARCHTIME>0.08</SEARCHTIME>
  <RESULTSET>
    <HIT SITID="project">
      <ProjectNumber>1415180001</ProjectNumber>
      <ProjectTitle><Korean>유사 연관 과제 1</Korean></ProjectTitle>
    </HIT>
    <HIT SITID="project">
      <ProjectNumber>1415180002</ProjectNumber>
      <ProjectTitle><Korean>유사 연관 과제 2</Korean></ProjectTitle>
    </HIT>
    <HIT SITID="project">
      <ProjectNumber>1415180003</ProjectNumber>
      <ProjectTitle><Korean>유사 연관 과제 3</Korean></ProjectTitle>
    </HIT>
  </RESULTSET>
</RESULT>"""


def _make_client() -> NTISClient:
    config = NTISConfig(api_key="test_key_for_unit_tests")
    return NTISClient(config)


def _inject_org_cache(org_name: str = "", org_bno: str = "") -> None:
    params = {"apprvKey": "test_key_for_unit_tests"}
    if org_bno:
        params["reqOrgBno"] = org_bno
    if org_name:
        params["reqOrgNm"] = org_name
    set_cached(ORG_RND_INFO_URL, params, ORG_RND_XML)


def _inject_issue_cache(query: str = "") -> None:
    params = {"apprvKey": "test_key_for_unit_tests"}
    if query:
        params["SRWR"] = query
    set_cached(ISSUE_RND_URL, params, ISSUE_XML)


def _inject_dic_cache(query: str, page: int = 1, page_size: int = 10) -> None:
    start = (page - 1) * page_size + 1
    params = {
        "userKey": "test_key_for_unit_tests",
        "query": query,
        "searchField": "BI",
        "sortby": "RANK/DESC",
        "startPosition": start,
        "displayCount": page_size,
    }
    set_cached(NTIS_DIC_URL, params, DIC_XML)


def _inject_target_cache(code_type: str, search_code: str = "") -> None:
    params = {"apprvKey": "test_key_for_unit_tests", "rqstSlctCd": code_type}
    if search_code:
        params["rqstSearchCd"] = search_code
    set_cached(TARGET_SEARCH_URL, params, TARGET_SEARCH_XML)


def _inject_conn_cache(content_type: str, content_id: str) -> None:
    params = {"apprvKey": "test_key_for_unit_tests", "collection": content_type, "id": content_id}
    set_cached(CONN_CONTENT_URL, params, CONN_CONTENT_XML)


# ── get_org_rnd_status ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_org_rnd_status_by_name():
    _inject_org_cache(org_name="한국전자통신연구원")
    client = _make_client()
    result = await client.get_org_rnd_status(org_name="한국전자통신연구원")
    assert result["result_code"] == "00"
    assert result["org_name"] == "한국전자통신연구원"
    assert "인공지능" in result["top_kor_keywords"]
    assert len(result["rnd_status"]) == 2
    assert result["rnd_status"][0]["year"] == "2023"
    assert result["rnd_status"][0]["paper_count"] == "1200"


@pytest.mark.asyncio
async def test_get_org_rnd_status_by_bno():
    _inject_org_cache(org_bno="1248602918")
    client = _make_client()
    result = await client.get_org_rnd_status(org_bno="1248602918")
    assert result["org_name"] == "한국전자통신연구원"
    assert len(result["rnd_status"]) == 2


# ── search_rnd_issues ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_search_rnd_issues_no_query():
    _inject_issue_cache()
    client = _make_client()
    result = await client.search_rnd_issues()
    assert result["total"] == "3"
    assert len(result["items"]) == 2
    assert result["items"][0]["name"] == "인공지능 안전성 연구동향"
    assert result["items"][0]["has_image"] is True
    assert "인공지능" in result["items"][0]["related_keywords"]


@pytest.mark.asyncio
async def test_search_rnd_issues_with_query():
    _inject_issue_cache(query="인공지능")
    client = _make_client()
    result = await client.search_rnd_issues(query="인공지능")
    assert len(result["items"]) == 2
    assert result["items"][1]["name"] == "탄소중립 그린수소 기술"


# ── search_terminology ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_search_terminology_basic():
    _inject_dic_cache("나노")
    client = _make_client()
    result = await client.search_terminology(query="나노")
    assert result["total_hits"] == 15
    assert result["hits"] == 2
    assert len(result["items"]) == 2
    assert result["items"][0]["korean"] == "나노소재"
    assert result["items"][0]["english"] == "Nanomaterial"
    assert result["items"][0]["abbreviation"] == "NM"
    assert "크기가" in result["items"][0]["definition"]


@pytest.mark.asyncio
async def test_search_terminology_fields_present():
    _inject_dic_cache("나노")
    client = _make_client()
    result = await client.search_terminology(query="나노")
    item = result["items"][0]
    for field in ("id", "korean", "english", "abbreviation", "standard_class", "related_words", "definition", "term_class"):
        assert field in item, f"필드 없음: {field}"


# ── get_classification_codes ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_classification_codes_ntis001():
    _inject_target_cache("NTIS001")
    client = _make_client()
    result = await client.get_classification_codes(code_type="NTIS001")
    assert result["result_code"] == "0000"
    assert len(result["items"]) == 3
    assert result["items"][0]["code"] == "060000"
    assert result["items"][0]["name"] == "정보통신"
    assert result["items"][0]["name_eng"] == "Information and Communication"


@pytest.mark.asyncio
async def test_get_classification_codes_with_search_code():
    _inject_target_cache("NTIS001", "060000")
    client = _make_client()
    result = await client.get_classification_codes(code_type="NTIS001", search_code="060000")
    assert len(result["items"]) == 3
    assert all(item["parent_code"] in ("000000", "060000") for item in result["items"])


@pytest.mark.asyncio
async def test_get_classification_codes_ntis002():
    _inject_target_cache("NTIS002")
    client = _make_client()
    result = await client.get_classification_codes(code_type="NTIS002")
    assert result["result_code"] == "0000"
    assert isinstance(result["items"], list)


# ── get_related_content ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_related_content_project():
    _inject_conn_cache("project", "1415140010")
    client = _make_client()
    result = await client.get_related_content(content_type="project", content_id="1415140010")
    assert result["total_hits"] == 5
    assert result["hits"] == 3
    assert len(result["items"]) == 3
    assert result["items"][0]["id"] == "1415180001"
    assert result["content_type"] == "project"


@pytest.mark.asyncio
async def test_get_related_content_title_parsed():
    _inject_conn_cache("project", "1415140010")
    client = _make_client()
    result = await client.get_related_content(content_type="project", content_id="1415140010")
    assert result["items"][0]["title"] == "유사 연관 과제 1"


# ── Tool-layer validation tests ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_org_rnd_status_tool_validation():
    """Both org_name and org_bno missing → error JSON."""
    import importlib
    from mcp_ntis import server
    from mcp_ntis.tools import extra_tools  # noqa: F401
    from mcp_ntis.server import set_client

    config = NTISConfig(api_key="test_key_for_unit_tests")
    set_client(NTISClient(config))

    from mcp_ntis.tools.extra_tools import get_org_rnd_status
    result = await get_org_rnd_status()
    payload = json.loads(result.text)
    assert "error" in payload


@pytest.mark.asyncio
async def test_get_classification_codes_tool_validation():
    """Invalid code_type → error JSON."""
    from mcp_ntis.server import set_client
    from mcp_ntis.tools.extra_tools import get_classification_codes

    config = NTISConfig(api_key="test_key_for_unit_tests")
    set_client(NTISClient(config))

    result = await get_classification_codes(code_type="INVALID")
    payload = json.loads(result.text)
    assert "error" in payload


@pytest.mark.asyncio
async def test_get_related_content_tool_validation():
    """Invalid content_type → error JSON."""
    from mcp_ntis.server import set_client
    from mcp_ntis.tools.extra_tools import get_related_content

    config = NTISConfig(api_key="test_key_for_unit_tests")
    set_client(NTISClient(config))

    result = await get_related_content(content_type="unknown", content_id="123")
    payload = json.loads(result.text)
    assert "error" in payload
