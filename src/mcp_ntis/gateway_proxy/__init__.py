"""게이트웨이 프록시 모드.

`NTIS_GATEWAY_URL`이 설정되면 in-process 도구 등록을 건너뛰고,
원격 게이트웨이의 /tools 메타에서 도구 목록을 받아 LLM·MCP 클라이언트에
프록시 도구로 노출한다.

선택 시나리오:
  - 게이트웨이 운영자 (NTIS·ScienceON·DataON 키 보유) → NTIS_GATEWAY_URL 비움
  - 일반 사용자 (게이트웨이 URL+토큰만 보유) → NTIS_GATEWAY_URL/API_KEY 설정
"""
