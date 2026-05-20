import json
import logging
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

import httpx

from .cache import get_cached, set_cached
from .config import NTISConfig

logger = logging.getLogger("mcp-ntis")

# NTIS API endpoints
PJT_SEARCH_URL = "https://www.ntis.go.kr/rndopen/openApi/pjtSearch/project"
NAT_RND_SEARCH_URL = "https://www.ntis.go.kr/rndopen/openApi/natRnDSearch"
TOTAL_SEARCH_URL = "https://www.ntis.go.kr/rndopen/openApi/totalRstSearch"
PROJECT_U_ORG_URL = "https://www.ntis.go.kr/rndopen/openApi/projectuOrg"
RCMNCLS_URL = "https://www.ntis.go.kr/rndopen/openApi/rcmncls"
ORG_RND_INFO_URL = "https://www.ntis.go.kr/rndopen/openApi/orgRndInfo"
ISSUE_RND_URL = "https://www.ntis.go.kr/rndopen/openApi/issue"
NTIS_DIC_URL = "https://www.ntis.go.kr/rndopen/openApi/ntisDic"
TARGET_SEARCH_URL = "https://www.ntis.go.kr/rndopen/openApi/targetSearch"
CONN_CONTENT_URL = "https://www.ntis.go.kr/rndopen/openApi/ConnectionContent"

SPAN_RE = re.compile(r'<span[^>]*>|</span>', re.IGNORECASE)
WHITESPACE_RE = re.compile(r'\s+')
XML_ESCAPE_RE = re.compile(r'_x[0-9A-Fa-f]{4}_')  # e.g. _x005F_, _x000D_

_SCI_TYPE_MAP = {"01": "SCI", "02": "비SCI", "03": "SCIE", "04": "SSCI", "05": "A&HCI"}
_PAPER_TYPE_MAP = {"01": "학술지", "02": "학술대회", "03": "학위논문"}


def _strip_html(text: Optional[str]) -> str:
    if not text:
        return ""
    return SPAN_RE.sub("", text).strip()


def _elem_text(elem: Optional[ET.Element]) -> str:
    if elem is None:
        return ""
    text = "".join(elem.itertext())
    return _strip_html(text.strip())


def _child_text(parent: ET.Element, tag: str) -> str:
    return _elem_text(parent.find(tag))


def _clean_text(text: str) -> str:
    """NTIS 원문 텍스트의 노이즈 제거."""
    if not text:
        return ""
    # XML 이스케이프 아티팩트 제거 (_x005F_ 등)
    text = XML_ESCAPE_RE.sub("", text)
    # 앞에 붙는 위치 마커 "..." 또는 줄바꿈 제거
    text = text.lstrip(". \t\n\r")
    # 연속 공백 → 단일 공백
    text = WHITESPACE_RE.sub(" ", text).strip()
    return text


def _clean_date(d: str) -> str:
    """날짜에서 시간 부분(00:00:00.0) 제거."""
    if not d:
        return ""
    return d.split(" ")[0].split(".")[0].strip()


def _parse_keyword(kw_elem: Optional[ET.Element]) -> Dict[str, List[str]]:
    if kw_elem is None:
        return {"korean": [], "english": []}
    kor_raw = _elem_text(kw_elem.find("Korean"))
    eng_raw = _elem_text(kw_elem.find("English"))
    return {
        "korean": [k.strip() for k in kor_raw.split(",") if k.strip()] if kor_raw else [],
        "english": [k.strip() for k in eng_raw.split(",") if k.strip()] if eng_raw else [],
    }


def _parse_search_meta(root: ET.Element) -> Dict[str, Any]:
    return {
        "total_hits": int(root.findtext("TOTALHITS") or 0),
        "start_position": int(root.findtext("STARTPOSITION") or 1),
        "hits": int(root.findtext("HITS") or 0),
        "search_time": float(root.findtext("SEARCHTIME") or 0),
    }


def _parse_project_hit(hit: ET.Element) -> Dict[str, Any]:
    pt = hit.find("ProjectTitle")
    kw = _parse_keyword(hit.find("Keyword"))
    goal = hit.find("Goal")
    abstract = hit.find("Abstract")
    effect = hit.find("Effect")
    period = hit.find("ProjectPeriod")
    ministry = hit.find("Ministry")
    research_agency = hit.find("ResearchAgency")
    budget_project = hit.find("BudgetProject")
    manage_agency = hit.find("ManageAgency")
    perform_agent = hit.find("PerformAgent")
    six_tech = hit.find("SixTechnology")
    dev_phases = hit.find("DevelopmentPhases")
    apply_area = hit.find("ApplyArea")

    sc_list = []
    for sc in hit.findall("ScienceClass"):
        large = sc.find("Large")
        medium = sc.find("Medium")
        small = sc.find("Small")
        if small is not None and _elem_text(small):
            sc_list.append({
                "large": {"code": large.get("code", "") if large is not None else "", "name": _elem_text(large)},
                "medium": {"code": medium.get("code", "") if medium is not None else "", "name": _elem_text(medium)},
                "small": {"code": small.get("code", "") if small is not None else "", "name": _elem_text(small)},
            })

    title_kor = _clean_text(WHITESPACE_RE.sub(" ", _elem_text(pt.find("Korean") if pt is not None else None)))
    title_eng = _clean_text(_elem_text(pt.find("English") if pt is not None else None))

    goal_text = _clean_text(_elem_text(goal.find("Full") if goal is not None else None))[:300]
    abstract_text = _clean_text(_elem_text(abstract.find("Teaser") if abstract is not None else None))
    effect_text = _clean_text(_elem_text(effect.find("Full") if effect is not None else None))[:300]

    funds_raw = _child_text(hit, "GovernmentFunds")
    total_funds_raw = _child_text(hit, "TotalFunds")

    return {
        "id": _child_text(hit, "ProjectNumber"),
        "title": title_kor,
        "title_eng": title_eng,
        "manager": _elem_text(hit.find("Manager/Name")),
        "institution": _elem_text(research_agency.find("Name") if research_agency is not None else None),
        "institution_type": _elem_text(perform_agent),
        "ministry": _elem_text(ministry),
        "manage_agency": _elem_text(manage_agency.find("Name") if manage_agency is not None else None),
        "budget_project": _elem_text(budget_project.find("Name") if budget_project is not None else None),
        "year": _child_text(hit, "ProjectYear"),
        "period_start": _clean_date(_elem_text(period.find("Start") if period is not None else None)),
        "period_end": _clean_date(_elem_text(period.find("End") if period is not None else None)),
        "total_start": _clean_date(_elem_text(period.find("TotalStart") if period is not None else None)),
        "total_end": _clean_date(_elem_text(period.find("TotalEnd") if period is not None else None)),
        "government_funds_krw": int(funds_raw) if funds_raw.isdigit() else 0,
        "total_funds_krw": int(total_funds_raw) if total_funds_raw.isdigit() else 0,
        "goal": goal_text,
        "abstract": abstract_text,
        "effect": effect_text,
        "keywords": kw,
        "science_class": sc_list,
        "six_technology": _elem_text(six_tech),
        "develop_phases": _elem_text(dev_phases),
        "apply_area": {
            "first": _elem_text(apply_area.find("First") if apply_area is not None else None),
            "second": _elem_text(apply_area.find("Second") if apply_area is not None else None),
            "third": _elem_text(apply_area.find("Third") if apply_area is not None else None),
        } if apply_area is not None else {},
    }


def _dedup_projects(items: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """같은 과제명+책임자 기준으로 중복 제거. 최신 연도 레코드를 남긴다."""
    seen: Dict[str, Dict[str, Any]] = {}
    for item in items:
        key = (item.get("title", "")[:40], item.get("manager", ""))
        existing = seen.get(str(key))
        if existing is None or (item.get("year", "") > existing.get("year", "")):
            seen[str(key)] = item
    unique = list(seen.values())
    removed = len(items) - len(unique)
    return unique, removed


def _parse_paper_hit(hit: ET.Element) -> Dict[str, Any]:
    kw = _parse_keyword(hit.find("Keyword"))
    abstract = hit.find("Abstract")
    ministry = hit.find("MinistryName")
    perform_agency = hit.find("PerformAgency")
    perform_agent = hit.find("PerformAgent")

    sc_list = []
    for tag in ["ScienceClass1", "ScienceClass2", "ScienceClass3"]:
        sc = hit.find(tag)
        if sc is not None and _elem_text(sc):
            sc_list.append({"level": tag[-1], "code": sc.get("code", ""), "name": _elem_text(sc)})

    sci_raw = _child_text(hit, "SciType")
    paper_type_raw = _child_text(hit, "PaperType")

    return {
        "id": _child_text(hit, "ResultID"),
        "title": _clean_text(_child_text(hit, "ResultTitle")),
        "journal": _child_text(hit, "JournalName"),
        "issn": _child_text(hit, "IssnNumber"),
        "authors": _child_text(hit, "Author"),
        "abstract": _clean_text(_elem_text(abstract.find("Teaser") if abstract is not None else None)),
        "keywords": kw,
        "pub_year": _child_text(hit, "PubYear"),
        "paper_type": _PAPER_TYPE_MAP.get(paper_type_raw, paper_type_raw),
        "sci_type": _SCI_TYPE_MAP.get(sci_raw, sci_raw),
        "nation_type": _child_text(hit, "NationType"),
        "has_fulltext": _child_text(hit, "SourceFlag") == "Y",
        "project_id": _child_text(hit, "ProjectID"),
        "project_title": _clean_text(_child_text(hit, "ProjectTitle")),
        "institution": _elem_text(perform_agency.find("Name") if perform_agency is not None else None) or _elem_text(perform_agent),
        "ministry": {
            "name": _elem_text(ministry),
            "code": ministry.get("code", "") if ministry is not None else "",
        },
        "science_class": sc_list,
    }


def _parse_patent_hit(hit: ET.Element) -> Dict[str, Any]:
    ministry = hit.find("MinistryName")
    perform_agency = hit.find("PerformAgency")
    perform_agent = hit.find("PerformAgent")
    regist_country = hit.find("RegistCountry")
    regist_type = hit.find("RegistType")
    ipr_type = hit.find("IprType")

    sc_list = []
    for tag in ["ScienceClass1", "ScienceClass2", "ScienceClass3"]:
        sc = hit.find(tag)
        if sc is not None and _elem_text(sc):
            sc_list.append({"level": tag[-1], "code": sc.get("code", ""), "name": _elem_text(sc)})

    return {
        "id": _child_text(hit, "ResultID"),
        "title": _clean_text(_child_text(hit, "ResultTitle")),
        "year": _child_text(hit, "Year"),
        "regist_country": _elem_text(regist_country),
        "regist_number": _child_text(hit, "RegistNumber"),
        "registrant": _child_text(hit, "Registrant"),
        "regist_type": _elem_text(regist_type),
        "ipr_type": _elem_text(ipr_type),
        "project_id": _child_text(hit, "ProjectID"),
        "project_title": _clean_text(_child_text(hit, "ProjectTitle")),
        "institution": _elem_text(perform_agency.find("Name") if perform_agency is not None else None) or _elem_text(perform_agent),
        "ministry": {
            "name": _elem_text(ministry),
            "code": ministry.get("code", "") if ministry is not None else "",
        },
        "science_class": sc_list,
    }


def _parse_research_hit(hit: ET.Element) -> Dict[str, Any]:
    abstract = hit.find("Abstract")
    kw = _parse_keyword(hit.find("Keyword"))
    ministry = hit.find("MinistryName")
    perform_agency = hit.find("PerformAgency")

    sc_list = []
    for tag in ["ScienceClass1", "ScienceClass2", "ScienceClass3"]:
        sc = hit.find(tag)
        if sc is not None and _elem_text(sc):
            sc_list.append({"level": tag[-1], "code": sc.get("code", ""), "name": _elem_text(sc)})

    return {
        "id": _child_text(hit, "ResultID"),
        "title": _clean_text(_child_text(hit, "ResultTitle")),
        "year": _child_text(hit, "Year"),
        "authors": _child_text(hit, "Author"),
        "abstract": _clean_text(_elem_text(abstract.find("Teaser") if abstract is not None else None)),
        "keywords": kw,
        "has_fulltext": _child_text(hit, "SourceFlag") == "Y",
        "project_id": _child_text(hit, "ProjectID"),
        "project_title": _clean_text(_child_text(hit, "ProjectTitle")),
        "institution": _elem_text(perform_agency.find("Name") if perform_agency is not None else None),
        "ministry": {
            "name": _elem_text(ministry),
            "code": ministry.get("code", "") if ministry is not None else "",
        },
        "science_class": sc_list,
    }


def _parse_equip_hit(hit: ET.Element) -> Dict[str, Any]:
    """연구장비(requip)는 다른 도구와 XML 구조가 다름.
    실제 구조: EquipID, Title/Korean, KeepOrganization/Name, Feature/Teaser, Manufacturer, Price 등.
    """
    title = hit.find("Title")
    keep_org = hit.find("KeepOrganization")
    feature = hit.find("Feature")
    ministry = hit.find("MinistryName")
    price_elem = hit.find("Price")

    sc_list = []
    for tag in ["ScienceClass1", "ScienceClass2", "ScienceClass3"]:
        sc = hit.find(tag)
        if sc is not None and _elem_text(sc):
            sc_list.append({"level": tag[-1], "code": sc.get("code", ""), "name": _elem_text(sc)})

    price_raw = _elem_text(price_elem) if price_elem is not None else ""
    return {
        "id": _child_text(hit, "EquipID"),
        "equip_no": _child_text(hit, "EquipNO"),
        "title": _clean_text(_elem_text(title.find("Korean") if title is not None else None)),
        "title_eng": _clean_text(_elem_text(title.find("English") if title is not None else None)),
        "model": _child_text(hit, "Model"),
        "manufacturer": _child_text(hit, "Manufacturer"),
        "institution": _elem_text(keep_org.find("Name") if keep_org is not None else None),
        "install_location": _clean_text(_child_text(hit, "InstallLocation")),
        "feature": _clean_text(_elem_text(feature.find("Teaser") if feature is not None else None)),
        "buy_date": _clean_date(_child_text(hit, "BuyDate")),
        "year": _child_text(hit, "Year"),
        "price_krw": int(price_raw) if price_raw.isdigit() else 0,
        "acquisition_method": price_elem.get("open", "") if price_elem is not None else "",
        "use_scope": _child_text(hit, "UseScope"),
        "use_type": _child_text(hit, "UseTypeName"),
        "equipment_class": _child_text(hit, "EquipmentClassName"),
        "project_id": _child_text(hit, "BudgetProjectNumber"),
        "project_title": _clean_text(_child_text(hit, "BudgetProject")),
        "ministry": {
            "name": _elem_text(ministry),
            "code": ministry.get("code", "") if ministry is not None else "",
        },
        "science_class": sc_list,
    }


def _parse_consignment_hit(hit: ET.Element) -> Dict[str, Any]:
    pt = hit.find("ProjectTitle")
    manager = hit.find("Manager")
    period = hit.find("ProjectPeriod")
    perform_agent = hit.find("PerformAgent")
    country = hit.find("Country")

    return {
        "id": hit.get("NO", ""),
        "project_number": _child_text(hit, "ProjectNumber"),
        "commission_number": _child_text(hit, "CommissionNumber"),
        "year": _child_text(hit, "ProjectYear"),
        "title": _clean_text(_elem_text(pt.find("Korean") if pt is not None else None)),
        "commission_title": _clean_text(_elem_text(pt.find("Commission") if pt is not None else None)),
        "manager": _elem_text(manager.find("Name") if manager is not None else None),
        "commission_manager": _elem_text(hit.find("CommissionManager/Name")),
        "order_agency": _child_text(hit, "OrderAgency"),
        "lead_agency": _child_text(hit, "LeadAgency"),
        "commission_lead_agency": _child_text(hit, "CommissionLeadAgency"),
        "commission_type": _child_text(hit, "CommissionType"),
        "institution_type": _elem_text(perform_agent),
        "country": _elem_text(country),
        "period": {
            "start": _clean_date(_elem_text(period.find("Start") if period is not None else None)),
            "end": _clean_date(_elem_text(period.find("End") if period is not None else None)),
            "total": _elem_text(period.find("Total") if period is not None else None),
        },
        "researcher_count": _child_text(hit, "ResearcherCount"),
        "collaborative_research_funds_krw": _child_text(hit, "CollaborativeResearchFunds"),
        "consignment_project_funds_krw": _child_text(hit, "ConsignmentProjectResearchFunds"),
        "participate_type": _child_text(hit, "ParticipateType"),
        "participate_country": _child_text(hit, "ParticipateCountry"),
    }


def _parse_org_rnd_info(root: ET.Element) -> Dict[str, Any]:
    header = root.find("header")
    result_code = header.findtext("resultCode") if header is not None else root.findtext(".//resultCode") or ""
    result_msg = header.findtext("resultMsg") if header is not None else root.findtext(".//resultMsg") or ""

    body = root.find("body")
    if body is None:
        return {"result_code": result_code, "result_msg": result_msg}

    num_of_list = int(body.findtext("numOfList") or "0")
    org_names = [elem.text or "" for elem in body.findall("orgName")]

    if num_of_list > 1:
        return {
            "result_code": result_code,
            "result_msg": result_msg,
            "disambiguation": True,
            "matching_org_names": org_names,
            "hint": "기관명이 여러 기관과 일치합니다. 아래 목록 중 정확한 기관명으로 다시 조회하거나 org_bno(사업자등록번호)를 사용하세요.",
        }

    rnd_status = []
    for item in body.findall(".//rndStatusList/item"):
        rnd_status.append({
            "year": item.findtext("year") or "",
            "project_count": item.findtext("pjtCnt") or "",
            "rnd_budget_krw": item.findtext("rndBudget") or "",
            "gov_budget_krw": item.findtext("govBudget") or "",
            "paper_count": item.findtext("paperCnt") or "",
            "patent_count": item.findtext("patentCnt") or "",
            "report_count": item.findtext("reportCnt") or "",
        })
    return {
        "result_code": result_code,
        "result_msg": result_msg,
        "org_name": org_names[0] if org_names else "",
        "org_page_url": body.findtext("orgPageInfo") or "",
        "top_kor_keywords": body.findtext("rndKorKeyword") or "",
        "top_eng_keywords": body.findtext("rndEngKeyword") or "",
        "top_categories": body.findtext("rndCategory") or "",
        "rnd_status": rnd_status,
    }


def _parse_issue_list(root: ET.Element) -> Dict[str, Any]:
    issues = []
    for item in root.findall(".//list"):
        # rltdKywdList는 <kywd> 자식 요소로 구성
        kw_elem = item.find("rltdKywdList")
        if kw_elem is not None:
            keywords = [kw.text.strip() for kw in kw_elem.findall("kywd") if kw.text]
        else:
            kywds_raw = item.findtext("rltdKywdList") or ""
            keywords = [k.strip() for k in kywds_raw.split(",") if k.strip()]

        issues.append({
            "id": item.findtext("topicNo") or "",
            "name": item.findtext("topicNm") or "",
            "date": item.findtext("extrDt") or "",
            "related_project_count": int(item.findtext("rltdPjtCnt") or 0),
            "related_keywords": keywords,
            "has_image": item.findtext("imgOfferYn") == "Y",
        })
    # searchListCnt가 실제 필드명
    total = root.findtext("searchListCnt") or root.findtext("selectListCnt") or str(len(issues))
    return {
        "total": int(total),
        "items": issues,
    }


def _parse_terminology_hit(hit: ET.Element) -> Dict[str, Any]:
    return {
        "id": _child_text(hit, "TermSn"),
        "korean": _child_text(hit, "KorWord"),
        "english": _child_text(hit, "EngWord"),
        "abbreviation": _child_text(hit, "MainAbrv"),
        "standard_class": _child_text(hit, "SntStdCls"),
        "related_words": _child_text(hit, "RelWord"),
        "definition": _child_text(hit, "TermDctn"),
        "term_class": _child_text(hit, "TermCls"),
    }


def _parse_classification_codes(root: ET.Element) -> Dict[str, Any]:
    status = root.find("status")

    def _cdata(elem: Optional[ET.Element], tag: str) -> str:
        val = elem.findtext(tag) if elem is not None else None
        if not val or val == "null":
            return ""
        return val.strip()

    items = []
    for dataset in root.findall(".//dataset"):
        desc = _cdata(dataset, "classCdExplan")
        name_eng = _cdata(dataset, "classCdNmEng")
        items.append({
            "code": _cdata(dataset, "classCd"),
            "name": _cdata(dataset, "classCdNm"),
            "name_eng": name_eng,
            "description": desc,
            "parent_code": _cdata(dataset, "upperClassCd"),
            "kind_code": _cdata(dataset, "kindCd"),
            "kind_name": _cdata(dataset, "kindCdNm"),
        })
    return {
        "result_code": status.findtext("recode") if status is not None else "",
        "result_msg": status.findtext("remsg") if status is not None else "",
        "total": len(items),
        "items": items,
    }


def _parse_related_content(root: ET.Element, content_type: str) -> Dict[str, Any]:
    meta = _parse_search_meta(root)
    items = []
    for hit in root.findall(".//HIT"):
        sitid = hit.get("SITID", content_type)
        item: Dict[str, Any] = {
            "type": sitid,
            "id": _child_text(hit, "ResultID") or _child_text(hit, "ProjectNumber"),
            "title": _clean_text(
                _child_text(hit, "ResultTitle")
                or _elem_text(hit.find("ProjectTitle/Korean") if hit.find("ProjectTitle") is not None else None)
            ),
        }
        items.append(item)
    return {**meta, "content_type": content_type, "items": items}


def _parse_classification_result(root: ET.Element) -> Dict[str, Any]:
    """과학기술표준분류·산업기술분류 공통 파서.
    표준분류: <RESULT><Result_1 .../></RESULT>
    산업기술분류: <RESULT><MOTIE><Result_1 .../></MOTIE></RESULT>
    두 구조 모두 처리.
    """
    status = root.find("STATUS")
    result_code = status.findtext("ResultCode") if status is not None else ""
    result_msg = status.findtext("ResultMsg") if status is not None else ""

    recommendations = []
    result_elem = root.find("RESULT")
    if result_elem is not None:
        # MOTIE 래퍼가 있으면 그 안의 Result_* 사용, 없으면 RESULT 직접
        container = result_elem.find("MOTIE")
        if container is None:
            container = result_elem
        seen_codes = set()
        for child in container:
            if child.tag.startswith("Result_"):
                small_code = child.get("SCLS_CD", "")
                # 동일 소분류 코드 중복 제거
                if small_code and small_code in seen_codes:
                    continue
                if small_code:
                    seen_codes.add(small_code)
                rank = child.tag.split("_", 1)[1]
                recommendations.append({
                    "rank": rank,
                    "large_code": child.get("LCLS_CD", ""),
                    "large_name": child.get("LCLS_NM", ""),
                    "medium_code": child.get("MCLS_CD", ""),
                    "medium_name": child.get("MCLS_NM", ""),
                    "small_code": small_code,
                    "small_name": child.get("SCLS_NM", ""),
                    "accuracy": child.get("SCLS_WEIGHT", ""),
                })

    # 텍스트 길이/품질 오류를 error_type으로 분류
    error_type = None
    if result_code == "-1002":
        error_type = "text_too_short"
    elif result_code == "-2002":
        error_type = "insufficient_terms"

    out = {
        "result_code": result_code,
        "result_msg": result_msg,
        "recommendations": recommendations,
    }
    if error_type:
        out["error_type"] = error_type
    return out


def _parse_ht_classification_result(root: ET.Element) -> Dict[str, Any]:
    """보건의료 분류 응답 파서. 동일 코드 중복은 자동 제거."""
    status = root.find("STATUS")
    result_code = status.findtext("ResultCode") if status is not None else ""
    result_msg = status.findtext("ResultMsg") if status is not None else ""

    result_elem = root.find("RESULT")
    mohwd, mohwr, motie = [], [], []
    if result_elem is not None:
        # 질환분류 (KCD)
        mohwd_elem = result_elem.find("MOHWD")
        if mohwd_elem is not None:
            seen = set()
            for child in mohwd_elem:
                if child.tag.startswith("Result_"):
                    code = child.get("DCLS_CD", "")
                    if code and code in seen:
                        continue
                    if code:
                        seen.add(code)
                    mohwd.append({
                        "rank": child.tag.split("_", 1)[1],
                        "disease_code": code,
                        "disease_name": child.get("DCLS_NM", ""),
                        "accuracy": child.get("DCLS_WEIGHT", ""),
                    })
        # 연구행위분류
        mohwr_elem = result_elem.find("MOHWR")
        if mohwr_elem is not None:
            seen = set()
            for child in mohwr_elem:
                if child.tag.startswith("Result_"):
                    code = child.get("MCLS_CD", "")
                    if code and code in seen:
                        continue
                    if code:
                        seen.add(code)
                    mohwr.append({
                        "rank": child.tag.split("_", 1)[1],
                        "large_code": child.get("LCLS_CD", ""),
                        "large_name": child.get("LCLS_NM", ""),
                        "medium_code": code,
                        "medium_name": child.get("MCLS_NM", ""),
                        "accuracy": child.get("MCLS_WEIGHT", ""),
                    })
        # 산업기술 (MOTIE)
        motie_elem = result_elem.find("MOTIE")
        if motie_elem is not None:
            seen = set()
            for child in motie_elem:
                if child.tag.startswith("Result_"):
                    code = child.get("SCLS_CD", "")
                    if code and code in seen:
                        continue
                    if code:
                        seen.add(code)
                    motie.append({
                        "rank": child.tag.split("_", 1)[1],
                        "large_code": child.get("LCLS_CD", ""),
                        "large_name": child.get("LCLS_NM", ""),
                        "medium_code": child.get("MCLS_CD", ""),
                        "medium_name": child.get("MCLS_NM", ""),
                        "small_code": code,
                        "small_name": child.get("SCLS_NM", ""),
                        "accuracy": child.get("SCLS_WEIGHT", ""),
                    })

    error_type = None
    if result_code == "-1002":
        error_type = "text_too_short"
    elif result_code == "-2002":
        error_type = "insufficient_terms"

    out = {
        "result_code": result_code,
        "result_msg": result_msg,
        "disease_classification": mohwd,
        "research_output_classification": mohwr,
        "industry_classification": motie,
    }
    if error_type:
        out["error_type"] = error_type
    return out


class NTISClient:
    def __init__(self, config: NTISConfig):
        self.config = config
        self._http: Optional[httpx.AsyncClient] = None

    @property
    def http(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0))
        return self._http

    async def close(self) -> None:
        if self._http and not self._http.is_closed:
            await self._http.aclose()

    def _base_params(self) -> Dict[str, str]:
        params: Dict[str, str] = {"apprvKey": self.config.api_key}
        if self.config.user_id:
            params["userId"] = self.config.user_id
        return params

    def _new_params(self) -> Dict[str, str]:
        """issue/targetSearch 등 신규 백엔드용 파라미터."""
        key = self.config.new_api_key or self.config.api_key
        params: Dict[str, str] = {"apprvKey": key}
        if self.config.user_id:
            params["userId"] = self.config.user_id
        return params

    async def _get(self, url: str, params: Dict[str, Any]) -> str:
        cached = get_cached(url, params, self.config.cache_ttl_hours)
        if cached is not None:
            logger.debug(f"캐시 히트: {url}")
            return cached

        response = await self.http.get(url, params=params)
        response.raise_for_status()
        text = response.text

        # NTIS API 오류 응답 확인 (XML 형식만)
        if not text.strip().startswith("{") and ("<ERROR>" in text or "<error>" in text):
            try:
                root = ET.fromstring(text)
                error = root.find(".//ERROR") or root.find(".//error")
                if error is None and root.tag.lower() == "error":
                    error = root
                if error is not None:
                    code = error.findtext("CODE") or error.findtext("code") or ""
                    message = (
                        error.findtext("MESSAGE")
                        or error.findtext("message")
                        or (error.text or "").strip()
                        or "알 수 없는 오류"
                    )
                    raise ValueError(f"NTIS API 오류 (코드 {code}): {message}")
            except ET.ParseError:
                pass

        set_cached(url, params, text)
        return text

    async def search_projects(
        self,
        query: str,
        search_field: str = "BI",
        add_query: str = "",
        sort: str = "RANK/DESC",
        start: int = 1,
        count: int = 10,
        deduplicate: bool = True,
        fetch_all: bool = False,
        max_fetch: int = 2000,
    ) -> Dict[str, Any]:
        """과제 검색. fetch_all=True 시 모든 페이지를 자동 순회하여 전체 결과 반환
        (단가 합산·통계 분석 등 정확한 집계에 필요). max_fetch로 상한 설정.
        """
        async def _one_page(s: int, c: int) -> tuple:
            params = {
                **self._base_params(),
                "collection": "project",
                "SRWR": query,
                "searchFd": search_field,
                "searchRnkn": sort,
                "startPosition": s,
                "displayCnt": c,
            }
            if add_query:
                params["addQuery"] = add_query
            xml_text = await self._get(PJT_SEARCH_URL, params)
            root = ET.fromstring(xml_text)
            return _parse_search_meta(root), [_parse_project_hit(hit) for hit in root.findall(".//HIT")]

        meta, items = await _one_page(start, count)

        if fetch_all:
            total = meta.get("total_hits", 0)
            cap = min(total, max_fetch)
            cur_start = start + count
            page_size = 100  # 자동 순회는 항상 최대 페이지 크기 사용
            while cur_start <= cap and len(items) < cap:
                _, more = await _one_page(cur_start, page_size)
                if not more:
                    break
                items.extend(more)
                cur_start += page_size
            if total > len(items):
                meta["fetch_all_truncated"] = (
                    f"max_fetch={max_fetch} 한도로 {len(items)}/{total}건만 가져왔습니다."
                )

        if deduplicate and items:
            items, removed = _dedup_projects(items)
            if removed > 0:
                meta["deduplicated"] = removed
                meta["note"] = (
                    f"연도별 중복 {removed}건 제거됨 (NTIS는 동일 과제를 연도별로 별도 기록). "
                    "최신 연도 레코드를 표시합니다."
                )

        # 페이지네이션 경고 (fetch_all=False일 때만 의미 있음)
        total = meta.get("total_hits", 0)
        if not fetch_all and total > start - 1 + len(items):
            remaining = total - (start - 1 + len(items))
            meta["pagination_warning"] = (
                f"총 {total}건 중 {len(items)}건만 반환됨 (남은 {remaining}건). "
                f"정확한 집계·통계 분석이 필요하면 fetch_all=True 사용 또는 "
                f"start={start + count}부터 page 증가시켜 순회. 최대 page_size=100."
            )

        return {**meta, "items": items}

    async def search_results(
        self,
        collection: str,
        query: str,
        search_field: str = "BI",
        add_query: str = "",
        sort: str = "RANK/DESC",
        start: int = 1,
        count: int = 10,
        fetch_all: bool = False,
        max_fetch: int = 2000,
    ) -> Dict[str, Any]:
        """논문/특허/보고서/장비 검색. fetch_all=True 시 모든 페이지 순회."""
        parsers = {
            "rpaper": _parse_paper_hit,
            "rpatent": _parse_patent_hit,
            "rresearch": _parse_research_hit,
            "requip": _parse_equip_hit,
        }
        parser = parsers.get(collection, _parse_research_hit)

        async def _one_page(s: int, c: int) -> tuple:
            params = {
                **self._base_params(),
                "collection": collection,
                "SRWR": query,
                "searchFd": search_field,
                "searchRnkn": sort,
                "startPosition": s,
                "displayCnt": c,
            }
            if add_query:
                params["addQuery"] = add_query
            xml_text = await self._get(NAT_RND_SEARCH_URL, params)
            root = ET.fromstring(xml_text)
            return _parse_search_meta(root), [parser(hit) for hit in root.findall(".//HIT")]

        meta, items = await _one_page(start, count)

        if fetch_all:
            total = meta.get("total_hits", 0)
            cap = min(total, max_fetch)
            cur_start = start + count
            page_size = 100
            while cur_start <= cap and len(items) < cap:
                _, more = await _one_page(cur_start, page_size)
                if not more:
                    break
                items.extend(more)
                cur_start += page_size
            if total > len(items):
                meta["fetch_all_truncated"] = (
                    f"max_fetch={max_fetch} 한도로 {len(items)}/{total}건만 가져왔습니다."
                )

        # 페이지네이션 경고
        total = meta.get("total_hits", 0)
        if not fetch_all and total > start - 1 + len(items):
            remaining = total - (start - 1 + len(items))
            meta["pagination_warning"] = (
                f"총 {total}건 중 {len(items)}건만 반환됨 (남은 {remaining}건). "
                f"정확한 집계·통계 분석이 필요하면 fetch_all=True 사용 또는 "
                f"start={start + count}부터 page 증가시켜 순회. 최대 page_size=100."
            )

        return {**meta, "collection": collection, "items": items}

    async def search_unified(
        self,
        collection: str,
        query: str,
        search_field: str = "BI",
        sort: str = "RANK/DESC",
        start: int = 1,
        count: int = 10,
    ) -> Dict[str, Any]:
        # totalRstSearch는 다른 검색 API와 달리 'query' 파라미터명 사용 (SRWR 아님)
        params = {
            **self._base_params(),
            "collection": collection,
            "query": query,
            "searchFd": search_field,
            "searchRnkn": sort,
            "startPosition": start,
            "displayCnt": count,
        }
        xml_text = await self._get(TOTAL_SEARCH_URL, params)
        root = ET.fromstring(xml_text)
        meta = _parse_search_meta(root)

        count_list = {}
        for col in root.findall(".//COLCOUNT"):
            count_list[col.get("NAME", "")] = int(col.text or 0)

        # totalRstSearch의 SITID는 PJK(과제), PAP(논문), PAT(특허), RFR(보고서), EQU(장비)
        items = []
        for hit in root.findall(".//HIT"):
            sitid = hit.get("SITID", "")
            if sitid == "PAP":
                items.append(_parse_paper_hit(hit))
            elif sitid == "PAT":
                items.append(_parse_patent_hit(hit))
            elif sitid in ("PJK", "project"):
                items.append(_parse_project_hit(hit))
            elif sitid == "EQU":
                items.append(_parse_equip_hit(hit))
            elif sitid in ("RFR", "RES"):
                items.append(_parse_research_hit(hit))
            else:
                items.append(_parse_research_hit(hit))

        # 페이지네이션 경고
        total = meta.get("total_hits", 0)
        if total > start - 1 + len(items):
            remaining = total - (start - 1 + len(items))
            meta["pagination_warning"] = (
                f"총 {total}건 중 {len(items)}건만 반환됨 (남은 {remaining}건). "
                f"정확한 집계가 필요하면 start={start + count}부터 추가 호출하세요. "
                f"최대 page_size=100."
            )

        return {**meta, "collection": collection, "collection_counts": count_list, "items": items}

    async def get_consignment_research(self, pjt_id: str) -> Dict[str, Any]:
        params = {**self._base_params(), "pjtId": pjt_id}
        xml_text = await self._get(PROJECT_U_ORG_URL, params)
        root = ET.fromstring(xml_text)
        meta = _parse_search_meta(root)
        items = [_parse_consignment_hit(hit) for hit in root.findall(".//HIT")]
        return {**meta, "items": items}

    async def get_org_rnd_status(
        self,
        org_name: str = "",
        org_bno: str = "",
        auto_resolve: bool = True,
    ) -> Dict[str, Any]:
        """기관 R&D 현황 조회.
        auto_resolve=True 시 동명이기관 disambiguation 처리:
        1) 입력값과 정확히 일치하는 후보가 있으면 우선 선택
        2) 없으면 가장 본원으로 추정되는 후보(짧고, 산학협력단/병원/부설 등 접미사 없음) 선택
        3) NTIS API 한계로 강제 정확 매칭이 안 되면 명확한 안내 메시지로 응답
        """
        params: Dict[str, Any] = {**self._base_params()}
        if org_bno:
            params["reqOrgBno"] = org_bno
        if org_name:
            params["reqOrgNm"] = org_name
        xml_text = await self._get(ORG_RND_INFO_URL, params)
        root = ET.fromstring(xml_text)
        result = _parse_org_rnd_info(root)

        if not auto_resolve or not result.get("disambiguation"):
            return result

        candidates = list(dict.fromkeys(result.get("matching_org_names", [])))
        if not candidates:
            return result

        # 후보 점수 휴리스틱
        SUFFIX_PENALTY = ("산학협력단", "병원", "부설", "분사무소", "캠퍼스", "_")

        def score(name: str) -> tuple:
            return (
                0 if name == org_name else 1,
                sum(1 for k in SUFFIX_PENALTY if k in name),
                len(name),
            )

        ordered = sorted(candidates, key=score)
        # 각 후보를 점수 순으로 시도하되, 실제 R&D 데이터(rnd_status)가 있는 첫 후보를 채택
        first_resolved = None  # disambiguation은 해소됐지만 데이터가 없는 첫 후보
        for chosen in ordered:
            retry_params = {**self._base_params(), "reqOrgNm": chosen}
            retry_xml = await self._get(ORG_RND_INFO_URL, retry_params)
            retry_result = _parse_org_rnd_info(ET.fromstring(retry_xml))
            if retry_result.get("disambiguation"):
                continue
            if retry_result.get("rnd_status"):
                retry_result["auto_resolved"] = {
                    "requested": org_name,
                    "resolved_to": chosen,
                    "other_candidates": [c for c in candidates if c != chosen],
                }
                return retry_result
            if first_resolved is None:
                first_resolved = (chosen, retry_result)

        # R&D 데이터가 있는 후보가 없으면 disambiguation은 해소되지만 데이터 없는 첫 후보 반환
        if first_resolved is not None:
            chosen, retry_result = first_resolved
            retry_result["auto_resolved"] = {
                "requested": org_name,
                "resolved_to": chosen,
                "other_candidates": [c for c in candidates if c != chosen],
                "warning": "선택된 기관에 R&D 데이터가 없습니다. 다른 후보를 명시적으로 시도해보세요.",
            }
            return retry_result

        # 모든 후보로도 단일 매칭 실패 — NTIS API 한계
        result["hint"] = (
            f"'{org_name}'은 {len(candidates)}개 기관과 매칭됩니다. "
            f"NTIS API는 부분 일치만 지원하므로 정확한 데이터를 얻으려면 "
            f"matching_org_names의 정확한 이름 또는 사업자등록번호(org_bno)로 재호출하세요."
        )
        return result

    async def search_rnd_issues(self, query: str = "") -> Dict[str, Any]:
        params: Dict[str, Any] = {**self._new_params()}
        if query:
            params["SRWR"] = query
        xml_text = await self._get(ISSUE_RND_URL, params)
        root = ET.fromstring(xml_text)
        return _parse_issue_list(root)

    async def search_terminology(
        self,
        query: str,
        search_field: str = "BI",
        add_query: str = "",
        sort: str = "RANK/DESC",
        start: int = 1,
        count: int = 10,
    ) -> Dict[str, Any]:
        # ntisDic API는 신규 API 키(NTIS_NEW_API_KEY)를 apprvKey로 사용
        key = self.config.new_api_key or self.config.api_key
        params: Dict[str, Any] = {
            "apprvKey": key,
            "query": query,
            "searchField": search_field,
            "sortby": sort,
            "startPosition": start,
            "displayCount": count,
        }
        if self.config.user_id:
            params["userId"] = self.config.user_id
        if add_query:
            params["addQuery"] = add_query
        xml_text = await self._get(NTIS_DIC_URL, params)
        root = ET.fromstring(xml_text)
        meta = _parse_search_meta(root)
        items = [_parse_terminology_hit(hit) for hit in root.findall(".//HIT")]
        return {**meta, "items": items}

    async def get_classification_codes(
        self,
        code_type: str,
        search_code: str = "",
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            **self._new_params(),
            "rqstSlctCd": code_type,
        }
        xml_text = await self._get(TARGET_SEARCH_URL, params)
        root = ET.fromstring(xml_text)
        result = _parse_classification_codes(root)
        all_items = result["items"]

        if search_code:
            children = [item for item in all_items if item["parent_code"] == search_code]
            if not children:
                children = [item for item in all_items if item["code"] == search_code]
            result["items"] = children
        else:
            # Return only top-level codes (parent is a kind number like '01','02')
            result["items"] = [
                item for item in all_items
                if len(item["parent_code"]) <= 2 and item["parent_code"].isdigit()
            ]

        result["total"] = len(result["items"])
        return result

    async def get_related_content(
        self,
        content_type: str,
        content_id: str,
    ) -> Dict[str, Any]:
        # NTIS ConnectionContent API는 현재 project만 지원
        if content_type != "project":
            return {
                "total_hits": 0,
                "hits": 0,
                "content_type": content_type,
                "items": [],
                "error": (
                    f"NTIS AI 유사 콘텐츠 추천은 현재 'project'만 지원합니다 "
                    f"(요청 type: '{content_type}'). 논문/특허/보고서 유사 검색이 필요하면 "
                    f"search_research_papers / search_patents / search_research_reports의 "
                    f"키워드 검색을 사용하세요."
                ),
            }
        # project는 pjtId 파라미터 사용
        params: Dict[str, Any] = {
            **self._base_params(),
            "collection": content_type,
            "pjtId": content_id,
        }
        text = await self._get(CONN_CONTENT_URL, params)
        text = text.strip()
        if text.startswith("{"):
            data = json.loads(text)
            items = data.get("items", [])
            if not data.get("exist", False):
                return {
                    "total_hits": 0,
                    "hits": 0,
                    "content_type": content_type,
                    "content_id": content_id,
                    "items": [],
                    "note": f"과제 id '{content_id}'가 NTIS AI 추천 DB에 등록되지 않았거나 유사 콘텐츠가 없습니다.",
                }
            # 정상 응답: items의 형식을 다른 도구 응답과 일관되게 정규화
            normalized = []
            for it in items:
                normalized.append({
                    "id": it.get("PJT_ID", ""),
                    "title": _clean_text(it.get("KOR_PJT_NM", "")),
                    "title_eng": _clean_text(it.get("ENG_PJT_NM", "")),
                    "similarity_score": it.get("similarity_score", 0),
                    "institution": _clean_text(it.get("RSCH_AGNC_NM", "")),
                    "year": it.get("PJT_YR", ""),
                })
            return {
                "total_hits": data.get("count", len(normalized)),
                "hits": len(normalized),
                "content_type": content_type,
                "content_id": content_id,
                "source_title": _clean_text(data.get("KOR_PJT_NM", "")),
                "items": normalized,
            }
        # XML 폴백 (예외 응답)
        root = ET.fromstring(text)
        return _parse_related_content(root, content_type)

    async def recommend_std_classification(
        self,
        text: str,
        detailed: bool = False,
        goal: str = "",
        abstract: str = "",
        effects: str = "",
        kor_keywords: str = "",
        eng_keywords: str = "",
    ) -> Dict[str, Any]:
        collection = "rcmnclsdtl" if detailed else "rcmncls"
        params: Dict[str, Any] = {
            **self._base_params(),
            "collection": collection,
        }
        if self.config.org_cd:
            params["orgCd"] = self.config.org_cd

        if detailed:
            params["rschGoalAbstract"] = goal or text
            params["rschAbstract"] = abstract or text
            if effects:
                params["expEfctAbstract"] = effects
            if kor_keywords:
                params["korKywd"] = kor_keywords
            if eng_keywords:
                params["engKywd"] = eng_keywords
        else:
            params["rqstDes"] = text

        xml_text = await self._get(RCMNCLS_URL, params)
        root = ET.fromstring(xml_text)
        return _parse_classification_result(root)

    async def recommend_ht_classification(
        self,
        text: str,
        detailed: bool = False,
        goal: str = "",
        abstract: str = "",
        effects: str = "",
        kor_keywords: str = "",
        eng_keywords: str = "",
    ) -> Dict[str, Any]:
        collection = "rcmnhtclsdtl" if detailed else "rcmnhtcls"
        params: Dict[str, Any] = {
            **self._base_params(),
            "collection": collection,
        }
        if self.config.org_cd:
            params["orgCd"] = self.config.org_cd

        if detailed:
            params["rschGoalAbstract"] = goal or text
            params["rschAbstract"] = abstract or text
            if effects:
                params["expEfctAbstract"] = effects
            if kor_keywords:
                params["korKywd"] = kor_keywords
            if eng_keywords:
                params["engKywd"] = eng_keywords
        else:
            params["rqstDes"] = text

        xml_text = await self._get(RCMNCLS_URL, params)
        root = ET.fromstring(xml_text)
        return _parse_ht_classification_result(root)

    async def recommend_it_classification(
        self,
        text: str,
        detailed: bool = False,
        goal: str = "",
        abstract: str = "",
        effects: str = "",
        kor_keywords: str = "",
        eng_keywords: str = "",
    ) -> Dict[str, Any]:
        collection = "rcmnitclsdtl" if detailed else "rcmnitcls"
        params: Dict[str, Any] = {
            **self._base_params(),
            "collection": collection,
        }
        if self.config.org_cd:
            params["orgCd"] = self.config.org_cd

        if detailed:
            params["rschGoalAbstract"] = goal or text
            params["rschAbstract"] = abstract or text
            if effects:
                params["expEfctAbstract"] = effects
            if kor_keywords:
                params["korKywd"] = kor_keywords
            if eng_keywords:
                params["engKywd"] = eng_keywords
        else:
            params["rqstDes"] = text

        xml_text = await self._get(RCMNCLS_URL, params)
        root = ET.fromstring(xml_text)
        return _parse_classification_result(root)
