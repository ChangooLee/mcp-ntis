"""ScienceON XML 응답 → 정제된 JSON dict 변환.

KISTI ScienceON API는 모두 XML(`<MetaData><recordList><record>...`)을 반환한다.
이 모듈은 다음을 수행한다:
  1. XML 파싱 → dict.
  2. client_id·token·session_id 등 인증 메타데이터 제거.
  3. 각 record를 평탄한 dict로 변환 (metaCode → key).
  4. resultSummary에서 TotalCount·statusCode 추출.
  5. 에러(statusCode != 200) 시 errorCode·errorMessage 정제.

목표 응답 스키마:
  {
    "target": "ARTI",
    "status": "ok" | "error",
    "total_count": 12345,
    "page": 1,
    "page_size": 10,
    "items": [ { ...record fields... } ],
    "error": { "code": "E4302", "message": "..." } | None  # 에러 시
  }
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any


_AUTH_FIELDS = {"client_id", "token", "session_id"}

# ScienceON XML metaCode → 명료한 영문 key (mcp-opendart KEY_MAPPING 패턴)
_KEY_MAP: dict[str, str] = {
    # 공통 식별
    "CN": "cn",
    "DBCode": "db_code",
    "rownum": "rownum",
    # 논문 / 보고서 / 일반
    "Title": "title",
    "Title2": "title_alt",
    "Author": "author",
    "Authors": "authors",
    "AuthorNameKor": "author_name_kr",
    "AuthorNameEng": "author_name_en",
    "AuthorInstKor": "author_inst_kr",
    "AuthorInstEng": "author_inst_en",
    "Abstract": "abstract",
    "Keyword": "keywords",
    "Pubyear": "pub_year",
    "Pubdate": "pub_date",
    "RegisterDate": "register_date",
    "JournalId": "journal_id",
    "JournalName": "journal_name",
    "Publisher": "publisher",
    "ISSN": "issn",
    "ISBN": "isbn",
    "VolumeId": "volume_id",
    "VolNo1": "volume_no",
    "VolNo2": "issue_no",
    "Lang": "language",
    "HoldingFlag": "has_holding",
    "ArticleId": "article_id",
    "ContentURL": "content_url",
    "Email": "email",
    # 특허
    "Nation": "nation",
    "NationCode": "nation_code",
    "PatentStatus": "patent_status",
    "IPC": "ipc",
    "Applicants": "applicants",
    "ApplDate": "appl_date",
    "ApplNum": "appl_number",
    "PublDate": "publ_date",
    "PublNum": "publ_number",
    "GrantDate": "grant_date",
    "GrantNum": "grant_number",
    "NoticeDate": "notice_date",
    "NoticeNumber": "notice_number",
    # 기관·연구자 카운트
    "ArticleCnt": "paper_count",
    "PatentCnt": "patent_count",
    "ReportCnt": "report_count",
    "OrganKor": "org_name_kr",
    "OrganEng": "org_name_en",
    "Rno": "raw_id",
    # 과학향기·동향
    "ScentTitle": "title",
    "Content": "content",
    "Class": "category_code",
    "Subclass": "subcategory_code",
    "Volume": "volume",
    "AFCode": "af_code",
    "AFCodeName": "af_code_name",
    # 금주의 뉴스 (SNEWS)
    "ordr": "order",
    "sj": "title",
    "contents": "content",
    "cdNm": "strategic_tech_name",
    "orginUrl": "origin_url",
    "registDt": "register_date",
    # 중첩 그룹
    "CallAPIInfo": "linked_apis",
    "ProviderAPIId": "api_id",
    "ProviderAPIName": "api_name",
    "ParameterValue": "parameter_value",
}

# 숫자형 변환 대상 키 (변환 후 명칭 기준)
_NUMERIC_KEYS = {
    "paper_count", "patent_count", "report_count",
    "pub_year", "volume_no", "issue_no", "rownum",
    "order", "volume",
}


def _strip_html(text: str) -> str:
    """ScienceON이 일부 필드에 <span class="search_word">하이라이트</span>를 끼워넣는데, 토큰 낭비를 막기 위해 제거."""
    if not text:
        return text
    return re.sub(r"<[^>]+>", "", text).strip()


def _to_int(s: Any) -> int | None:
    if s is None:
        return None
    try:
        return int(str(s).strip())
    except (ValueError, TypeError):
        return None


def parse_scienceon_xml(
    xml_text: str,
    target: str,
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    """ScienceON 응답 XML을 정제된 dict로 변환.

    실패 시에도 dict 반환 (status='error' + error.message에 원인).
    """
    if not xml_text or not xml_text.strip():
        return {
            "target": target,
            "status": "error",
            "total_count": 0,
            "items": [],
            "error": {"code": "E_EMPTY", "message": "응답 본문 없음"},
        }

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        return {
            "target": target,
            "status": "error",
            "total_count": 0,
            "items": [],
            "error": {"code": "E_PARSE", "message": f"XML 파싱 실패: {exc}"},
        }

    # resultSummary — 상태·총 건수
    status_code = None
    total_count = 0
    service_type = None
    summary = root.find("resultSummary")
    if summary is not None:
        sc = summary.find("statusCode")
        if sc is not None and sc.text:
            status_code = sc.text.strip()
        tc = summary.find("TotalCount")
        if tc is not None:
            total_count = _to_int(tc.text) or 0
        st = summary.find("serviceDatatype")
        if st is not None and st.text:
            service_type = st.text.strip()

    # errorDetail (statusCode != 200)
    err = root.find("errorDetail")
    if err is not None:
        ec = err.find("errorCode")
        em = err.find("errorMessage")
        sm = err.find("statusMessage")
        return {
            "target": target,
            "status": "error",
            "total_count": 0,
            "items": [],
            "error": {
                "code": (ec.text or "").strip() if ec is not None else "E_UNKNOWN",
                "message": (em.text or sm.text or "").strip() if (em is not None or sm is not None) else "오류",
                "status_message": (sm.text or "").strip() if sm is not None else None,
            },
        }

    # recordList → items
    items: list[dict[str, Any]] = []
    record_list = root.find("recordList")
    if record_list is not None:
        for record in record_list.findall("record"):
            item = _record_to_dict(record)
            if item:
                items.append(item)

    out: dict[str, Any] = {
        "target": target,
        "status": "ok" if (status_code == "200" or status_code is None) else f"warning_{status_code}",
        "total_count": total_count,
        "service_type": service_type,
        "page": page,
        "page_size": page_size,
        "returned": len(items),
        "items": items,
    }

    # 페이지네이션 힌트
    if total_count > len(items) and total_count > page_size * page:
        remaining = total_count - page_size * page
        out["pagination_hint"] = (
            f"총 {total_count:,}건 중 {len(items)}건 반환 — 남은 {remaining:,}건은 cur_page를 증가시켜 순회."
        )

    return out


def _map_key(meta_code: str) -> str:
    """metaCode → 명료한 영문 key."""
    return _KEY_MAP.get(meta_code, meta_code)


def _maybe_num(key: str, value: Any) -> Any:
    """숫자형 변환 대상이면 int로 변환 시도."""
    if key not in _NUMERIC_KEYS:
        return value
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        v = value.strip()
        if v.isdigit():
            try:
                return int(v)
            except (ValueError, OverflowError):
                pass
    return value


def _record_to_dict(record: ET.Element) -> dict[str, Any]:
    """단일 <record> → flat dict.

    ScienceON XML 구조:
      <record rownum="1">
        <item metaCode="CN" metaName="CN"><![CDATA[NPAP12345]]></item>
        <item metaCode="Title" metaName="논문명"><![CDATA[Quantum...]]></item>
        ...
        <item metaCode="CallAPIInfo" metaGroupName="API호출정보" number="1">
          <item metaCode="..." metaName="..."><![CDATA[...]]></item>
          ...
        </item>
      </record>

    metaCode를 key로 사용, value는 CDATA 본문(빈 문자열은 제거).
    CallAPIInfo 등 중첩 그룹은 별도 dict로 묶음.
    """
    out: dict[str, Any] = {}
    if record.get("rownum"):
        out[_map_key("rownum")] = _to_int(record.get("rownum"))

    for child in record.findall("item"):
        code = child.get("metaCode") or child.get("metaName") or ""
        if not code or code in _AUTH_FIELDS:
            continue
        key = _map_key(code)

        # 중첩 그룹 (CallAPIInfo 등): 자식 item이 있는 경우
        nested = child.findall("item")
        if nested:
            group: dict[str, Any] = {}
            for sub in nested:
                sub_code = sub.get("metaCode") or sub.get("metaName") or ""
                if not sub_code or sub_code in _AUTH_FIELDS:
                    continue
                sub_key = _map_key(sub_code)
                sub_val = (sub.text or "").strip()
                if sub_val:
                    group[sub_key] = _maybe_num(sub_key, sub_val)
            if group:
                # 같은 key가 여러 번 나오면 리스트화
                if key in out:
                    if not isinstance(out[key], list):
                        out[key] = [out[key]]
                    out[key].append(group)
                else:
                    out[key] = group
        else:
            val = (child.text or "").strip()
            if val:
                # 일부 필드는 HTML 태그 포함 → 제거
                if code in ("Abstract", "Title", "Title2", "Keyword", "ScentTitle", "Content", "contents"):
                    val = _strip_html(val)
                out[key] = _maybe_num(key, val)

    return out


def parse_token_response(text: str) -> dict[str, Any]:
    """토큰 발급 응답 파싱(이미 JSON이라 거의 통과)."""
    import json
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"errorCode": "E_TOKEN_PARSE", "errorMessage": text[:500]}
