"""15개 NTIS MCP 도구의 메타데이터를 한곳에서 정의한다."""

from __future__ import annotations

from .tool_registry import ToolRegistry


def initialize_registry() -> ToolRegistry:
    registry = ToolRegistry()

    # ===== 검색 도구 (6개) =====

    registry.register(
        name="search_rnd_projects",
        korean_name="국가R&D 과제 검색",
        description=(
            "국가R&D 과제를 검색. 연구목표·내용·기대효과, 예산(원 단위), 표준분류, "
            "수행기관·사업명·연구기간·6T분류 등 가장 풍부한 메타데이터 제공. "
            "연도별 중복은 자동 제거되어 최신 연도만 반환."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "검색어. AND=띄어쓰기, OR=|, NOT=!, 정확한구문=\"...\""},
                "search_field": {"type": "string", "description": "BI=전체(기본), TI=과제명, AU=책임자, OG=기관명, KW=키워드, AB=초록", "default": "BI"},
                "add_query": {"type": "string", "description": "추가 필터. 예: PY=2024/SAME, OG=한국과학기술원, AU=홍길동", "default": ""},
                "sort": {"type": "string", "description": "RANK/DESC, DATE/DESC, DATE/ASC", "default": "RANK/DESC"},
                "page": {"type": "integer", "description": "페이지 번호", "default": 1},
                "page_size": {"type": "integer", "description": "최대 100", "default": 10},
                "fetch_all": {"type": "boolean", "description": "True 시 전체 페이지 자동 순회 (집계/통계 시 필수)", "default": False},
                "max_fetch": {"type": "integer", "description": "fetch_all 시 최대 건수", "default": 2000},
            },
            "required": ["query"],
        },
        tags={"검색", "과제", "기초조사"},
        linked_tools=[
            "get_consignment_research",
            "get_related_content",
            "get_org_rnd_status",
            "recommend_std_classification",
        ],
        usage_pattern=(
            "1) 기초 탐색: page_size=10~20\n"
            "2) 상위 기관/키워드 분석: page_size=100\n"
            "3) 정량 합산 분석: fetch_all=True (모든 페이지 자동 순회)\n"
            "4) 결과 id → get_consignment_research / get_related_content 로 확장"
        ),
    )

    registry.register(
        name="search_research_papers",
        korean_name="국가R&D 성과 논문 검색",
        description=(
            "국가R&D 과제 연계 논문만 검색 (~19만 건). "
            "민간/순수 학문 논문은 포함되지 않음 → 전체 학술논문은 RISS·PubMed 안내."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "search_field": {"type": "string", "default": "BI"},
                "add_query": {"type": "string", "default": ""},
                "sort": {"type": "string", "default": "RANK/DESC"},
                "page": {"type": "integer", "default": 1},
                "page_size": {"type": "integer", "default": 10},
                "fetch_all": {"type": "boolean", "default": False},
                "max_fetch": {"type": "integer", "default": 2000},
            },
            "required": ["query"],
        },
        tags={"검색", "논문", "성과물"},
        linked_tools=["search_rnd_projects", "search_research_reports"],
        usage_pattern="project_id 역추적 시: 키워드 검색 후 결과의 project_id 필드를 클라이언트에서 매칭",
    )

    registry.register(
        name="search_patents",
        korean_name="국가R&D 성과 특허 검색",
        description=(
            "국가R&D 과제 연계 특허만 검색 (~38만 건). "
            "전체 특허는 KIPRIS 안내. 출원/등록 구분, 국내외 구분 포함."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "search_field": {"type": "string", "default": "BI"},
                "add_query": {"type": "string", "default": ""},
                "sort": {"type": "string", "default": "RANK/DESC"},
                "page": {"type": "integer", "default": 1},
                "page_size": {"type": "integer", "default": 10},
                "fetch_all": {"type": "boolean", "default": False},
                "max_fetch": {"type": "integer", "default": 2000},
            },
            "required": ["query"],
        },
        tags={"검색", "특허", "성과물", "지식재산"},
        linked_tools=["search_rnd_projects"],
    )

    registry.register(
        name="search_research_reports",
        korean_name="국가R&D 연구보고서 검색",
        description=(
            "국가R&D 과제의 최종·중간 연구보고서 검색. 논문/특허보다 연구 전체 내용 "
            "(방법·결과·한계 등) 서술. has_fulltext=true면 NTIS 원문 열람 가능."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "search_field": {"type": "string", "default": "BI"},
                "add_query": {"type": "string", "default": ""},
                "sort": {"type": "string", "default": "RANK/DESC"},
                "page": {"type": "integer", "default": 1},
                "page_size": {"type": "integer", "default": 10},
                "fetch_all": {"type": "boolean", "default": False},
                "max_fetch": {"type": "integer", "default": 2000},
            },
            "required": ["query"],
        },
        tags={"검색", "보고서", "성과물"},
        linked_tools=["search_rnd_projects"],
    )

    registry.register(
        name="search_research_equipment",
        korean_name="국가R&D 연구장비 검색",
        description=(
            "연구장비 검색. 장비명(국·영문), 모델, 제조사, 보유기관, 설치위치, 구매가, "
            "공동활용 가능 여부, 장비 특징(상세 설명) 제공. "
            "기관별 인프라 매핑과 공동활용 가능 장비 탐색에 유용."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "search_field": {"type": "string", "default": "BI"},
                "sort": {"type": "string", "default": "RANK/DESC"},
                "page": {"type": "integer", "default": 1},
                "page_size": {"type": "integer", "default": 10},
                "fetch_all": {"type": "boolean", "default": False},
                "max_fetch": {"type": "integer", "default": 2000},
            },
            "required": ["query"],
        },
        tags={"검색", "장비", "인프라"},
        linked_tools=["search_rnd_projects"],
    )

    registry.register(
        name="search_unified",
        korean_name="통합 검색",
        description=(
            "여러 R&D 성과 유형(과제·논문·특허·보고서·장비)을 한 번에 검색. "
            "collection_counts로 유형별 분포를 한눈에 파악. 초기 탐색에 유용."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "collection": {"type": "string", "description": "콤마 구분 (예: 'project,rpaper,rpatent')", "default": "project"},
                "search_field": {"type": "string", "default": "BI"},
                "sort": {"type": "string", "default": "RANK/DESC"},
                "page": {"type": "integer", "default": 1},
                "page_size": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        },
        tags={"검색", "통합", "분포파악"},
        linked_tools=[
            "search_rnd_projects",
            "search_research_papers",
            "search_patents",
        ],
        usage_pattern="주제 첫 탐색 시 사용 → 어느 유형에 데이터가 풍부한지 보고 전용 도구로 깊이 탐색",
    )

    # ===== 과제 상세 도구 (2개) =====

    registry.register(
        name="get_consignment_research",
        korean_name="위탁/공동연구 조회",
        description=(
            "과제의 위탁·공동연구 기관, 연구비 분담, 참여기간, 협력유형 조회. "
            "search_rnd_projects 결과의 id를 그대로 project_id에 전달."
        ),
        parameters={
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "과제 고유번호 (8~10자리)"},
            },
            "required": ["project_id"],
        },
        tags={"과제상세", "협력", "위탁연구"},
        linked_tools=["search_rnd_projects", "get_org_rnd_status"],
    )

    registry.register(
        name="get_org_rnd_status",
        korean_name="기관 R&D 현황 조회",
        description=(
            "수행기관의 국가R&D 포트폴리오: 연도별 과제 수·연구비·논문·특허·보고서, "
            "대표 한·영 키워드, 주요 연구분야. auto_resolve=True 시 동명이기관 "
            "자동 해결."
        ),
        parameters={
            "type": "object",
            "properties": {
                "org_name": {"type": "string", "description": "기관명. 정확 일치보다 부분 일치 가능", "default": ""},
                "org_bno": {"type": "string", "description": "사업자등록번호 10자리", "default": ""},
                "auto_resolve": {"type": "boolean", "description": "동명이기관 자동 해결", "default": True},
            },
        },
        tags={"기관분석", "기관현황", "포트폴리오"},
        linked_tools=["search_rnd_projects", "get_consignment_research"],
    )

    # ===== 분류 추천 도구 (3개) =====

    classification_params = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "연구 내용 (단순모드용, 150자/450바이트 이상 권장)", "default": ""},
            "detailed": {"type": "boolean", "description": "상세모드 (goal+abstract 사용)", "default": False},
            "goal": {"type": "string", "description": "[상세모드] 연구목표", "default": ""},
            "abstract": {"type": "string", "description": "[상세모드] 연구내용", "default": ""},
            "effects": {"type": "string", "description": "[상세모드] 기대효과", "default": ""},
            "kor_keywords": {"type": "string", "description": "국문 키워드(쉼표구분)", "default": ""},
            "eng_keywords": {"type": "string", "description": "영문 키워드(쉼표구분)", "default": ""},
        },
    }

    registry.register(
        name="recommend_std_classification",
        korean_name="과학기술표준분류 추천",
        description=(
            "과기부·교육부·환경부 등 범용 R&D 과제용 표준분류 추천. "
            "대/중/소 코드와 정확도(%) 최대 5개. 텍스트 150자(450바이트) 이상 권장."
        ),
        parameters=classification_params,
        tags={"분류추천", "표준분류", "과기부"},
        linked_tools=[
            "recommend_ht_classification",
            "recommend_it_classification",
            "get_classification_codes",
        ],
    )

    registry.register(
        name="recommend_ht_classification",
        korean_name="보건의료기술분류 추천",
        description=(
            "보건복지부·질병청·국립암센터 R&D용. 질환분류(KCD)·연구행위(MOHWR)·"
            "산업기술(MOTIE) 3종 동시 추천."
        ),
        parameters=classification_params,
        tags={"분류추천", "보건의료", "복지부"},
        linked_tools=[
            "recommend_std_classification",
            "get_classification_codes",
        ],
    )

    registry.register(
        name="recommend_it_classification",
        korean_name="산업기술분류 추천",
        description=(
            "산업부·중기부 R&D용 IT·BT·NT·ET·ST·CT 6T 기반 분류 추천. "
            "대/중/소 코드와 정확도(%) 최대 5개."
        ),
        parameters=classification_params,
        tags={"분류추천", "산업기술", "산업부"},
        linked_tools=[
            "recommend_std_classification",
            "get_classification_codes",
        ],
    )

    # ===== 부가 도구 (4개) =====

    registry.register(
        name="search_rnd_issues",
        korean_name="R&D 트렌드 이슈 조회",
        description=(
            "NTIS가 선정한 최신 R&D 트렌드 이슈. 이슈명·날짜·연관 과제 수·연관 키워드. "
            "query 빈 값이면 최신 5개. 이슈명으로 search_rnd_projects 재호출 패턴."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "검색 키워드. 빈 값이면 최신 이슈", "default": ""},
            },
        },
        tags={"트렌드", "이슈", "탐색시작점"},
        linked_tools=["search_rnd_projects"],
        usage_pattern="첫 탐색 → 이슈 발견 → 이슈명으로 search_rnd_projects 정량 분석",
    )

    registry.register(
        name="search_terminology",
        korean_name="국가R&D 용어사전 검색",
        description=(
            "과학기술 표준 용어의 한·영 명칭, 약어, 정의, 관련어 제공. "
            "표준 용어 확인이나 약어 풀이에 활용."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "search_field": {"type": "string", "description": "BI=전체, TI=용어명, AB=약어", "default": "BI"},
                "add_query": {"type": "string", "default": ""},
                "page": {"type": "integer", "default": 1},
                "page_size": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        },
        tags={"용어", "표준화", "사전"},
        linked_tools=["search_rnd_projects"],
    )

    registry.register(
        name="get_classification_codes",
        korean_name="분류코드 계층 조회",
        description=(
            "과학기술표준분류(NTIS001) 또는 국가중점기술(NTIS002) 코드 계층 조회. "
            "search_code 없으면 22개 최상위. search_code 입력 시 직접 자식 분류만. "
            "코드 규칙: 소(6자)[:4]=중, 중(4자)[:2]=대."
        ),
        parameters={
            "type": "object",
            "properties": {
                "code_type": {"type": "string", "description": "NTIS001=표준분류, NTIS002=국가중점기술"},
                "search_code": {"type": "string", "description": "조회할 분류 코드. 예: 'NA' → 수학 하위", "default": ""},
            },
            "required": ["code_type"],
        },
        tags={"분류코드", "계층탐색"},
        linked_tools=[
            "recommend_std_classification",
            "recommend_ht_classification",
            "recommend_it_classification",
        ],
    )

    registry.register(
        name="get_related_content",
        korean_name="유사 콘텐츠 AI 추천",
        description=(
            "특정 R&D 과제와 유사한 과제를 AI 기반으로 추천 (similarity_score 포함). "
            "현재 'project' 컨텐츠 타입만 지원. content_id는 과제 id 사용."
        ),
        parameters={
            "type": "object",
            "properties": {
                "content_type": {"type": "string", "description": "'project'만 지원"},
                "content_id": {"type": "string", "description": "과제 고유번호"},
            },
            "required": ["content_type", "content_id"],
        },
        tags={"AI추천", "유사검색", "확장탐색"},
        linked_tools=["search_rnd_projects"],
    )

    # ===== 메타 도구 (1개) =====

    registry.register(
        name="get_ntis_tool_info",
        korean_name="NTIS 도구 정보 조회",
        description=(
            "NTIS MCP 도구의 상세 정보·연관 도구·활용 패턴을 조회. "
            "어떤 도구를 사용해야 할지 모를 때 먼저 호출. "
            "tool_name 없이 호출하면 전체 도구 카테고리별 목록 반환."
        ),
        parameters={
            "type": "object",
            "properties": {
                "tool_name": {"type": "string", "description": "조회할 도구명. 빈 값이면 전체 목록", "default": ""},
                "tag": {"type": "string", "description": "특정 태그로 도구 필터링", "default": ""},
            },
        },
        tags={"메타", "도구탐색", "도움말"},
    )

    return registry
