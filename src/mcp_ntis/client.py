import json
import logging
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

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


def _strip_html(text: Optional[str]) -> str:
    if not text:
        return ""
    return SPAN_RE.sub("", text).strip()


def _elem_text(elem: Optional[ET.Element]) -> str:
    if elem is None:
        return ""
    # itertext() handles both HTML-escaped and XML-child span tags
    text = "".join(elem.itertext())
    return _strip_html(text.strip())


def _child_text(parent: ET.Element, tag: str) -> str:
    return _elem_text(parent.find(tag))


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
        sc_list.append({
            "large": {"code": large.get("code", "") if large is not None else "", "name": _elem_text(large)},
            "medium": {"code": medium.get("code", "") if medium is not None else "", "name": _elem_text(medium)},
            "small": {"code": small.get("code", "") if small is not None else "", "name": _elem_text(small)},
        })

    return {
        "id": _child_text(hit, "ProjectNumber"),
        "title_kor": _elem_text(pt.find("Korean") if pt is not None else None),
        "title_eng": _elem_text(pt.find("English") if pt is not None else None),
        "manager": _elem_text(hit.find("Manager/Name")),
        "goal": _elem_text(goal.find("Teaser") if goal is not None else None),
        "abstract": _elem_text(abstract.find("Teaser") if abstract is not None else None),
        "effect": _elem_text(effect.find("Teaser") if effect is not None else None),
        "keywords": kw,
        "year": _child_text(hit, "ProjectYear"),
        "period_start": _elem_text(period.find("Start") if period is not None else None),
        "period_end": _elem_text(period.find("End") if period is not None else None),
        "total_start": _elem_text(period.find("TotalStart") if period is not None else None),
        "total_end": _elem_text(period.find("TotalEnd") if period is not None else None),
        "ministry": {
            "name": _elem_text(ministry),
            "code": ministry.get("code", "") if ministry is not None else "",
        },
        "research_agency": _elem_text(research_agency.find("Name") if research_agency is not None else None),
        "budget_project": _elem_text(budget_project.find("Name") if budget_project is not None else None),
        "manage_agency": _elem_text(manage_agency.find("Name") if manage_agency is not None else None),
        "perform_agent": {
            "name": _elem_text(perform_agent),
            "code": perform_agent.get("code", "") if perform_agent is not None else "",
        },
        "six_technology": _elem_text(six_tech),
        "develop_phases": {
            "name": _elem_text(dev_phases),
            "code": dev_phases.get("code", "") if dev_phases is not None else "",
        },
        "government_funds": _child_text(hit, "GovernmentFunds"),
        "total_funds": _child_text(hit, "TotalFunds"),
        "science_class": sc_list,
        "apply_area": {
            "first": _elem_text(apply_area.find("First") if apply_area is not None else None),
            "second": _elem_text(apply_area.find("Second") if apply_area is not None else None),
            "third": _elem_text(apply_area.find("Third") if apply_area is not None else None),
        } if apply_area is not None else {},
    }


def _parse_paper_hit(hit: ET.Element) -> Dict[str, Any]:
    kw = _parse_keyword(hit.find("Keyword"))
    abstract = hit.find("Abstract")
    ministry = hit.find("MinistryName")
    perform_agency = hit.find("PerformAgency")
    perform_agent = hit.find("PerformAgent")

    sc_list = []
    for tag in ["ScienceClass1", "ScienceClass2", "ScienceClass3"]:
        sc = hit.find(tag)
        if sc is not None:
            sc_list.append({"level": tag[-1], "code": sc.get("code", ""), "name": _elem_text(sc)})

    return {
        "id": _child_text(hit, "ResultID"),
        "title": _child_text(hit, "ResultTitle"),
        "journal": _child_text(hit, "JournalName"),
        "issn": _child_text(hit, "IssnNumber"),
        "authors": _child_text(hit, "Author"),
        "abstract": _elem_text(abstract.find("Teaser") if abstract is not None else None),
        "keywords": kw,
        "pub_year": _child_text(hit, "PubYear"),
        "paper_type": _child_text(hit, "PaperType"),
        "sci_type": _child_text(hit, "SciType"),
        "nation_type": _child_text(hit, "NationType"),
        "source_flag": _child_text(hit, "SourceFlag"),
        "project_id": _child_text(hit, "ProjectID"),
        "project_title": _child_text(hit, "ProjectTitle"),
        "ministry": {
            "name": _elem_text(ministry),
            "code": ministry.get("code", "") if ministry is not None else "",
        },
        "perform_agency": {
            "name": _elem_text(perform_agency),
            "code": perform_agency.get("code", "") if perform_agency is not None else "",
        },
        "perform_agent": {
            "name": _elem_text(perform_agent),
            "code": perform_agent.get("code", "") if perform_agent is not None else "",
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
        if sc is not None:
            sc_list.append({"level": tag[-1], "code": sc.get("code", ""), "name": _elem_text(sc)})

    return {
        "id": _child_text(hit, "ResultID"),
        "title": _child_text(hit, "ResultTitle"),
        "year": _child_text(hit, "Year"),
        "regist_country": {
            "name": _elem_text(regist_country),
            "code": regist_country.get("code", "") if regist_country is not None else "",
        },
        "regist_number": _child_text(hit, "RegistNumber"),
        "registrant": _child_text(hit, "Registrant"),
        "regist_type": {
            "name": _elem_text(regist_type),
            "code": regist_type.get("code", "") if regist_type is not None else "",
        },
        "ipr_type": {
            "name": _elem_text(ipr_type),
            "code": ipr_type.get("code", "") if ipr_type is not None else "",
        },
        "project_id": _child_text(hit, "ProjectID"),
        "project_title": _child_text(hit, "ProjectTitle"),
        "ministry": {
            "name": _elem_text(ministry),
            "code": ministry.get("code", "") if ministry is not None else "",
        },
        "perform_agency": {
            "name": _elem_text(perform_agency),
            "code": perform_agency.get("code", "") if perform_agency is not None else "",
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
        if sc is not None:
            sc_list.append({"level": tag[-1], "code": sc.get("code", ""), "name": _elem_text(sc)})

    return {
        "id": _child_text(hit, "ResultID"),
        "title": _child_text(hit, "ResultTitle"),
        "year": _child_text(hit, "Year"),
        "authors": _child_text(hit, "Author"),
        "abstract": _elem_text(abstract.find("Teaser") if abstract is not None else None),
        "keywords": kw,
        "source_flag": _child_text(hit, "SourceFlag"),
        "project_id": _child_text(hit, "ProjectID"),
        "project_title": _child_text(hit, "ProjectTitle"),
        "ministry": {
            "name": _elem_text(ministry),
            "code": ministry.get("code", "") if ministry is not None else "",
        },
        "perform_agency": {
            "name": _elem_text(perform_agency),
            "code": perform_agency.get("code", "") if perform_agency is not None else "",
        },
        "science_class": sc_list,
    }


def _parse_equip_hit(hit: ET.Element) -> Dict[str, Any]:
    ministry = hit.find("MinistryName")
    perform_agency = hit.find("PerformAgency")

    sc_list = []
    for tag in ["ScienceClass1", "ScienceClass2", "ScienceClass3"]:
        sc = hit.find(tag)
        if sc is not None:
            sc_list.append({"level": tag[-1], "code": sc.get("code", ""), "name": _elem_text(sc)})

    return {
        "id": _child_text(hit, "ResultID"),
        "title": _child_text(hit, "ResultTitle"),
        "year": _child_text(hit, "Year"),
        "project_id": _child_text(hit, "ProjectID"),
        "project_title": _child_text(hit, "ProjectTitle"),
        "ministry": {
            "name": _elem_text(ministry),
            "code": ministry.get("code", "") if ministry is not None else "",
        },
        "perform_agency": {
            "name": _elem_text(perform_agency),
            "code": perform_agency.get("code", "") if perform_agency is not None else "",
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
        "title_kor": _elem_text(pt.find("Korean") if pt is not None else None),
        "title_eng": _elem_text(pt.find("English") if pt is not None else None),
        "commission_title": _elem_text(pt.find("Commission") if pt is not None else None),
        "manager": _elem_text(manager.find("Name") if manager is not None else None),
        "commission_manager": _elem_text(hit.find("CommissionManager/Name")),
        "order_agency": _child_text(hit, "OrderAgency"),
        "lead_agency": _child_text(hit, "LeadAgency"),
        "commission_lead_agency": _child_text(hit, "CommissionLeadAgency"),
        "commission_type": _child_text(hit, "CommissionType"),
        "perform_agent": {
            "name": _elem_text(perform_agent),
            "code": perform_agent.get("code", "") if perform_agent is not None else "",
        },
        "country": {
            "name": _elem_text(country),
            "code": country.get("code", "") if country is not None else "",
        },
        "period": {
            "start": _elem_text(period.find("Start") if period is not None else None),
            "end": _elem_text(period.find("End") if period is not None else None),
            "total": _elem_text(period.find("Total") if period is not None else None),
        },
        "researcher_count": _child_text(hit, "ResearcherCount"),
        "collaborative_research_funds": _child_text(hit, "CollaborativeResearchFunds"),
        "consignment_project_funds": _child_text(hit, "ConsignmentProjectResearchFunds"),
        "collaborative_fund_expense": _child_text(hit, "CollaborativeResearchFundExpense"),
        "participate_type": _child_text(hit, "ParticipateType"),
        "participate_country": _child_text(hit, "ParticipateCountry"),
        "participate_researcher_count": _child_text(hit, "ParticipateResearcherNumber"),
    }


def _parse_org_rnd_info(root: ET.Element) -> Dict[str, Any]:
    rnd_status = []
    for item in root.findall(".//rndStatusList/item"):
        rnd_status.append({
            "year": item.findtext("year") or "",
            "project_count": item.findtext("pjtCnt") or "",
            "rnd_budget": item.findtext("rndBudget") or "",
            "gov_budget": item.findtext("govBudget") or "",
            "paper_count": item.findtext("paperCnt") or "",
            "patent_count": item.findtext("patentCnt") or "",
            "report_count": item.findtext("reportCnt") or "",
        })
    return {
        "result_code": root.findtext("resultCode") or "",
        "result_msg": root.findtext("resultMsg") or "",
        "org_name": root.findtext("orgName") or "",
        "org_page_url": root.findtext("orgPageInfo") or "",
        "top_kor_keywords": root.findtext("rndKorKeyword") or "",
        "top_eng_keywords": root.findtext("rndEngKeyword") or "",
        "top_categories": root.findtext("rndCategory") or "",
        "rnd_status": rnd_status,
    }


def _parse_issue_list(root: ET.Element) -> Dict[str, Any]:
    issues = []
    for item in root.findall(".//list"):
        kywds_raw = item.findtext("rltdKywdList") or ""
        issues.append({
            "id": item.findtext("topicNo") or "",
            "name": item.findtext("topicNm") or "",
            "date": item.findtext("extrDt") or "",
            "related_project_count": item.findtext("rltdPjtCnt") or "",
            "related_keywords": [k.strip() for k in kywds_raw.split(",") if k.strip()],
            "has_image": item.findtext("imgOfferYn") == "Y",
        })
    return {
        "total": root.findtext("selectListCnt") or str(len(issues)),
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
    items = []
    for dataset in root.findall(".//dataset"):
        item: Dict[str, Any] = {
            "code": dataset.findtext("cd") or "",
            "name": dataset.findtext("cdNm") or "",
            "name_eng": dataset.findtext("cdNmEng") or "",
            "description": dataset.findtext("cdExplan") or "",
            "parent_code": dataset.findtext("upperCd") or "",
        }
        class_cd = dataset.findtext("classCd")
        if class_cd:
            item["class_code"] = class_cd
            item["class_name"] = dataset.findtext("classCdNm") or ""
            item["kind_code"] = dataset.findtext("kindCd") or ""
            item["kind_name"] = dataset.findtext("kindCdNm") or ""
        items.append(item)
    return {
        "result_code": status.findtext("recode") if status is not None else "",
        "result_msg": status.findtext("remsg") if status is not None else "",
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
            "title": (
                _child_text(hit, "ResultTitle")
                or _elem_text(hit.find("ProjectTitle/Korean") if hit.find("ProjectTitle") is not None else None)
            ),
        }
        items.append(item)
    return {**meta, "content_type": content_type, "items": items}


def _parse_classification_result(root: ET.Element) -> Dict[str, Any]:
    status = root.find("STATUS")
    result_code = status.findtext("ResultCode") if status is not None else ""
    result_msg = status.findtext("ResultMsg") if status is not None else ""

    recommendations = []
    result_elem = root.find("RESULT")
    if result_elem is not None:
        for child in result_elem:
            if child.tag.startswith("Result_"):
                rank = child.tag.split("_", 1)[1]
                recommendations.append({
                    "rank": rank,
                    "large_code": child.get("LCLS_CD", ""),
                    "large_name": child.get("LCLS_NM", ""),
                    "medium_code": child.get("MCLS_CD", ""),
                    "medium_name": child.get("MCLS_NM", ""),
                    "small_code": child.get("SCLS_CD", ""),
                    "small_name": child.get("SCLS_NM", ""),
                    "accuracy": child.get("SCLS_WEIGHT", ""),
                })

    return {
        "result_code": result_code,
        "result_msg": result_msg,
        "recommendations": recommendations,
    }


def _parse_ht_classification_result(root: ET.Element) -> Dict[str, Any]:
    status = root.find("STATUS")
    result_code = status.findtext("ResultCode") if status is not None else ""
    result_msg = status.findtext("ResultMsg") if status is not None else ""

    result_elem = root.find("RESULT")
    mohwd = []
    mohwr = []
    if result_elem is not None:
        mohwd_elem = result_elem.find("MOHWD")
        if mohwd_elem is not None:
            for child in mohwd_elem:
                if child.tag.startswith("Result_"):
                    mohwd.append({
                        "rank": child.tag.split("_", 1)[1],
                        "large_code": child.get("LCLS_CD", ""),
                        "large_name": child.get("LCLS_NM", ""),
                        "medium_code": child.get("MCLS_CD", ""),
                        "medium_name": child.get("MCLS_NM", ""),
                        "accuracy": child.get("MCLS_WEIGHT", ""),
                    })
        mohwr_elem = result_elem.find("MOHWR")
        if mohwr_elem is not None:
            for child in mohwr_elem:
                if child.tag.startswith("Result_"):
                    mohwr.append({
                        "rank": child.tag.split("_", 1)[1],
                        "large_code": child.get("LCLS_CD", ""),
                        "large_name": child.get("LCLS_NM", ""),
                        "medium_code": child.get("MCLS_CD", ""),
                        "medium_name": child.get("MCLS_NM", ""),
                        "accuracy": child.get("MCLS_WEIGHT", ""),
                    })

    return {
        "result_code": result_code,
        "result_msg": result_msg,
        "disease_classification": mohwd,
        "research_output_classification": mohwr,
    }


class NTISClient:
    def __init__(self, config: NTISConfig):
        self.config = config
        self._http: Optional[httpx.AsyncClient] = None

    @property
    def http(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(timeout=30.0)
        return self._http

    async def close(self) -> None:
        if self._http and not self._http.is_closed:
            await self._http.aclose()

    def _base_params(self) -> Dict[str, str]:
        params: Dict[str, str] = {"apprvKey": self.config.api_key}
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

        # NTIS API 오류 응답 확인
        if "<ERROR>" in text or "<error>" in text:
            try:
                root = ET.fromstring(text)
                error = root.find(".//ERROR") or root.find(".//error")
                if error is not None:
                    code = error.findtext("CODE") or error.findtext("code") or ""
                    message = error.findtext("MESSAGE") or error.findtext("message") or "알 수 없는 오류"
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
    ) -> Dict[str, Any]:
        params = {
            **self._base_params(),
            "collection": "project",
            "SRWR": query,
            "searchFd": search_field,
            "searchRnkn": sort,
            "startPosition": start,
            "displayCnt": count,
        }
        if add_query:
            params["addQuery"] = add_query

        xml_text = await self._get(PJT_SEARCH_URL, params)
        root = ET.fromstring(xml_text)
        meta = _parse_search_meta(root)
        items = [_parse_project_hit(hit) for hit in root.findall(".//HIT")]
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
    ) -> Dict[str, Any]:
        params = {
            **self._base_params(),
            "collection": collection,
            "SRWR": query,
            "searchFd": search_field,
            "searchRnkn": sort,
            "startPosition": start,
            "displayCnt": count,
        }
        if add_query:
            params["addQuery"] = add_query

        xml_text = await self._get(NAT_RND_SEARCH_URL, params)
        root = ET.fromstring(xml_text)
        meta = _parse_search_meta(root)

        parsers = {
            "rpaper": _parse_paper_hit,
            "rpatent": _parse_patent_hit,
            "rresearch": _parse_research_hit,
            "requip": _parse_equip_hit,
        }
        parser = parsers.get(collection, _parse_research_hit)
        items = [parser(hit) for hit in root.findall(".//HIT")]
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
        params = {
            **self._base_params(),
            "collection": collection,
            "SRWR": query,
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

        items = []
        for hit in root.findall(".//HIT"):
            sitid = hit.get("SITID", "")
            if sitid == "PAP":
                items.append(_parse_paper_hit(hit))
            elif sitid == "PAT":
                items.append(_parse_patent_hit(hit))
            elif sitid == "project":
                items.append(_parse_project_hit(hit))
            else:
                items.append(_parse_research_hit(hit))

        return {**meta, "collection": collection, "collection_counts": count_list, "items": items}

    async def get_consignment_research(self, pjt_id: str) -> Dict[str, Any]:
        params = {**self._base_params(), "pjtId": pjt_id}
        xml_text = await self._get(PROJECT_U_ORG_URL, params)
        root = ET.fromstring(xml_text)
        meta = _parse_search_meta(root)
        items = [_parse_consignment_hit(hit) for hit in root.findall(".//HIT")]
        return {**meta, "items": items}

    async def get_org_rnd_status(self, org_name: str = "", org_bno: str = "") -> Dict[str, Any]:
        params: Dict[str, Any] = {**self._base_params()}
        if org_bno:
            params["reqOrgBno"] = org_bno
        if org_name:
            params["reqOrgNm"] = org_name
        xml_text = await self._get(ORG_RND_INFO_URL, params)
        root = ET.fromstring(xml_text)
        return _parse_org_rnd_info(root)

    async def search_rnd_issues(self, query: str = "") -> Dict[str, Any]:
        params: Dict[str, Any] = {**self._base_params()}
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
        params: Dict[str, Any] = {
            "userKey": self.config.api_key,
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
            **self._base_params(),
            "rqstSlctCd": code_type,
        }
        if search_code:
            params["rqstSearchCd"] = search_code
        xml_text = await self._get(TARGET_SEARCH_URL, params)
        root = ET.fromstring(xml_text)
        return _parse_classification_codes(root)

    async def get_related_content(
        self,
        content_type: str,
        content_id: str,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            **self._base_params(),
            "collection": content_type,
            "id": content_id,
        }
        xml_text = await self._get(CONN_CONTENT_URL, params)
        root = ET.fromstring(xml_text)
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
