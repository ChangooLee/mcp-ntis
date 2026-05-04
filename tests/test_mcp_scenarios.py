"""
LLM이 실제 사용하는 복합 시나리오 기반 MCP 도구 가치 검증 테스트.

5개 시나리오:
  S1. 양자컴퓨팅 트렌드 → 과제 → 논문·특허 교차 분석
  S2. 연구기관(ETRI) 과제 발굴 → 기관 R&D 현황 심층 조회
  S3. 나노배터리 과제 → 위탁연구 구조 → 연관콘텐츠 추천 체인
  S4. 용어 정의 → 분류코드 탐색 → 분류추천 → 코드 기반 과제검색
  S5. 이슈 탐지 → 보건의료분류 + 산업기술분류 동시 추천 비교
"""
import json
import os
import sys

import pytest

os.environ.setdefault("NTIS_API_KEY", "lg814619kv046cp808fk")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mcp_ntis.cache import set_cached
from mcp_ntis.client import (
    CONN_CONTENT_URL,
    ISSUE_RND_URL,
    NAT_RND_SEARCH_URL,
    NTIS_DIC_URL,
    ORG_RND_INFO_URL,
    PJT_SEARCH_URL,
    PROJECT_U_ORG_URL,
    RCMNCLS_URL,
    TARGET_SEARCH_URL,
    NTISClient,
)
from mcp_ntis.config import NTISConfig

API_KEY = "lg814619kv046cp808fk"


def client() -> NTISClient:
    return NTISClient(NTISConfig(api_key=API_KEY))


def inject(url: str, params: dict, xml: str) -> None:
    set_cached(url, params, xml)


# ═══════════════════════════════════════════════════════════════════════════════
# 공통 XML 픽스처
# ═══════════════════════════════════════════════════════════════════════════════

QUANTUM_PROJECTS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<RESULT>
  <TOTALHITS>482</TOTALHITS>
  <STARTPOSITION>1</STARTPOSITION>
  <HITS>3</HITS>
  <SEARCHTIME>0.12</SEARCHTIME>
  <RESULTSET>
    <HIT>
      <ProjectNumber>1711198164</ProjectNumber>
      <ProjectTitle>
        <Korean><span class="search_word">양자컴퓨팅</span> 기반 암호체계 연구</Korean>
        <English>Quantum Computing Based Cryptography Research</English>
      </ProjectTitle>
      <Manager><Name>김양자</Name></Manager>
      <Goal><Teaser>양자컴퓨터 환경에서 안전한 암호 프로토콜 설계 및 검증</Teaser></Goal>
      <Abstract><Teaser>양자내성암호 표준화를 위한 격자기반 암호 알고리즘 연구개발</Teaser></Abstract>
      <Effect><Teaser>포스트양자 시대 국가 사이버보안 역량 강화</Teaser></Effect>
      <Keyword><Korean>양자컴퓨팅,양자암호,격자기반암호,포스트양자</Korean><English>quantum computing,quantum cryptography,lattice-based,post-quantum</English></Keyword>
      <ProjectYear>2023</ProjectYear>
      <ProjectPeriod><Start>20210301</Start><End>20251231</End><TotalStart>20210301</TotalStart><TotalEnd>20251231</TotalEnd></ProjectPeriod>
      <Ministry code="1711">과학기술정보통신부</Ministry>
      <ResearchAgency><Name>한국연구재단</Name></ResearchAgency>
      <BudgetProject><Name>기초연구사업</Name></BudgetProject>
      <ManageAgency><Name>한국연구재단</Name></ManageAgency>
      <PerformAgent code="12345">한국과학기술원</PerformAgent>
      <SixTechnology>정보전자</SixTechnology>
      <DevelopmentPhases code="02">응용연구</DevelopmentPhases>
      <GovernmentFunds>800000</GovernmentFunds>
      <TotalFunds>850000</TotalFunds>
      <ScienceClass>
        <Large code="060000">정보통신</Large>
        <Medium code="060400">정보보호</Medium>
        <Small code="060401">암호이론</Small>
      </ScienceClass>
      <ApplyArea>
        <First>과학기술</First>
        <Second>정보통신</Second>
        <Third>보안</Third>
      </ApplyArea>
    </HIT>
    <HIT>
      <ProjectNumber>1711198200</ProjectNumber>
      <ProjectTitle>
        <Korean>초전도 <span class="search_word">양자컴퓨터</span> 오류정정 기술개발</Korean>
        <English>Superconducting Quantum Computer Error Correction</English>
      </ProjectTitle>
      <Manager><Name>이초전</Name></Manager>
      <Goal><Teaser>초전도 큐비트 기반 오류정정 코드 구현 및 신뢰성 향상</Teaser></Goal>
      <Abstract><Teaser>surface code를 활용한 논리 큐비트 구현 및 게이트 충실도 99.9% 달성</Teaser></Abstract>
      <Effect><Teaser>실용적 양자컴퓨터 구현을 위한 핵심 기반기술 확보</Teaser></Effect>
      <Keyword><Korean>양자컴퓨터,초전도,큐비트,오류정정</Korean><English>quantum computer,superconductor,qubit,error correction</English></Keyword>
      <ProjectYear>2023</ProjectYear>
      <ProjectPeriod><Start>20220101</Start><End>20261231</End><TotalStart>20220101</TotalStart><TotalEnd>20261231</TotalEnd></ProjectPeriod>
      <Ministry code="1711">과학기술정보통신부</Ministry>
      <ResearchAgency><Name>정보통신기획평가원</Name></ResearchAgency>
      <BudgetProject><Name>ICT혁신기술개발사업</Name></BudgetProject>
      <ManageAgency><Name>정보통신기획평가원</Name></ManageAgency>
      <PerformAgent code="67890">한국전자통신연구원</PerformAgent>
      <SixTechnology>정보전자</SixTechnology>
      <DevelopmentPhases code="03">개발연구</DevelopmentPhases>
      <GovernmentFunds>3500000</GovernmentFunds>
      <TotalFunds>3600000</TotalFunds>
      <ScienceClass>
        <Large code="060000">정보통신</Large>
        <Medium code="060100">컴퓨터하드웨어</Medium>
        <Small code="060101">양자정보처리</Small>
      </ScienceClass>
      <ApplyArea>
        <First>과학기술</First>
        <Second>물리</Second>
        <Third>양자물리</Third>
      </ApplyArea>
    </HIT>
    <HIT>
      <ProjectNumber>1711198250</ProjectNumber>
      <ProjectTitle>
        <Korean><span class="search_word">양자</span> 시뮬레이터를 활용한 신소재 발견</Korean>
        <English>Novel Material Discovery via Quantum Simulator</English>
      </ProjectTitle>
      <Manager><Name>박신소</Name></Manager>
      <Goal><Teaser>양자 시뮬레이션으로 배터리·촉매 소재 특성 예측</Teaser></Goal>
      <Abstract><Teaser>변분 양자 고유값 분해(VQE) 알고리즘으로 분자 에너지 계산 정확도 향상</Teaser></Abstract>
      <Effect><Teaser>차세대 에너지소재·의약품 후보물질 발굴 가속화</Teaser></Effect>
      <Keyword><Korean>양자시뮬레이터,신소재,VQE,분자시뮬레이션</Korean><English>quantum simulator,novel material,VQE,molecular simulation</English></Keyword>
      <ProjectYear>2023</ProjectYear>
      <ProjectPeriod><Start>20230101</Start><End>20271231</End><TotalStart>20230101</TotalStart><TotalEnd>20271231</TotalEnd></ProjectPeriod>
      <Ministry code="1711">과학기술정보통신부</Ministry>
      <ResearchAgency><Name>한국연구재단</Name></ResearchAgency>
      <BudgetProject><Name>미래소재디스커버리사업</Name></BudgetProject>
      <ManageAgency><Name>한국연구재단</Name></ManageAgency>
      <PerformAgent code="11111">서울대학교</PerformAgent>
      <SixTechnology>나노소재</SixTechnology>
      <DevelopmentPhases code="01">기초연구</DevelopmentPhases>
      <GovernmentFunds>600000</GovernmentFunds>
      <TotalFunds>620000</TotalFunds>
      <ScienceClass>
        <Large code="090000">나노 및 소재</Large>
        <Medium code="090100">나노소재</Medium>
        <Small code="090102">에너지나노소재</Small>
      </ScienceClass>
      <ApplyArea>
        <First>과학기술</First>
        <Second>화학</Second>
        <Third>계산화학</Third>
      </ApplyArea>
    </HIT>
  </RESULTSET>
</RESULT>"""

QUANTUM_PAPERS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<RESULT>
  <TOTALHITS>1240</TOTALHITS>
  <STARTPOSITION>1</STARTPOSITION>
  <HITS>3</HITS>
  <SEARCHTIME>0.09</SEARCHTIME>
  <RESULTSET>
    <HIT>
      <ResultID>PAP-2023-001234</ResultID>
      <ResultTitle>Fault-tolerant quantum computation with surface codes</ResultTitle>
      <JournalName>Nature Physics</JournalName>
      <IssnNumber>1745-2473</IssnNumber>
      <Author>이초전, 김양자, John Smith</Author>
      <Abstract><Teaser>surface code 기반 내결함성 양자계산 구현 실험적 검증. 논리 오류율 0.1% 이하 달성.</Teaser></Abstract>
      <Keyword><Korean>양자오류정정,surface code,내결함성</Korean><English>quantum error correction,surface code,fault tolerant</English></Keyword>
      <PubYear>2023</PubYear>
      <PaperType>학술지</PaperType>
      <SciType>SCI</SciType>
      <NationType>국외</NationType>
      <SourceFlag>Y</SourceFlag>
      <ProjectID>1711198200</ProjectID>
      <ProjectTitle>초전도 양자컴퓨터 오류정정 기술개발</ProjectTitle>
      <MinistryName code="1711">과학기술정보통신부</MinistryName>
      <PerformAgency code="67890"><span class="search_word">한국전자통신연구원</span></PerformAgency>
      <PerformAgent code="02">대학</PerformAgent>
      <ScienceClass1 code="060101">양자정보처리</ScienceClass1>
    </HIT>
    <HIT>
      <ResultID>PAP-2023-005678</ResultID>
      <ResultTitle>양자 우월성 검증을 위한 랜덤 회로 샘플링 실험</ResultTitle>
      <JournalName>Physical Review Letters</JournalName>
      <IssnNumber>0031-9007</IssnNumber>
      <Author>박양자, 최큐빗</Author>
      <Abstract><Teaser>53큐비트 프로세서를 이용한 양자 우월성 실험. 고전 슈퍼컴퓨터 대비 10억배 이상 속도 우위 확인.</Teaser></Abstract>
      <Keyword><Korean>양자우월성,랜덤회로샘플링,양자프로세서</Korean><English>quantum supremacy,random circuit sampling,quantum processor</English></Keyword>
      <PubYear>2022</PubYear>
      <PaperType>학술지</PaperType>
      <SciType>SCI</SciType>
      <NationType>국외</NationType>
      <SourceFlag>Y</SourceFlag>
      <ProjectID>1711198200</ProjectID>
      <ProjectTitle>초전도 양자컴퓨터 오류정정 기술개발</ProjectTitle>
      <MinistryName code="1711">과학기술정보통신부</MinistryName>
      <PerformAgency code="67890">한국전자통신연구원</PerformAgency>
      <PerformAgent code="02">대학</PerformAgent>
      <ScienceClass1 code="060101">양자정보처리</ScienceClass1>
    </HIT>
    <HIT>
      <ResultID>PAP-2023-009012</ResultID>
      <ResultTitle>격자기반 암호의 NIST 표준화 동향 분석</ResultTitle>
      <JournalName>정보보호학회논문지</JournalName>
      <IssnNumber>1598-3986</IssnNumber>
      <Author>김보안, 이암호</Author>
      <Abstract><Teaser>NIST PQC 표준화 최종 후보 4종 분석. Kyber, Dilithium 알고리즘 성능 비교.</Teaser></Abstract>
      <Keyword><Korean>양자내성암호,격자암호,NIST표준화</Korean><English>post-quantum cryptography,lattice cryptography,NIST standardization</English></Keyword>
      <PubYear>2023</PubYear>
      <PaperType>학술지</PaperType>
      <SciType>비SCI</SciType>
      <NationType>국내</NationType>
      <SourceFlag>N</SourceFlag>
      <ProjectID>1711198164</ProjectID>
      <ProjectTitle>양자컴퓨팅 기반 암호체계 연구</ProjectTitle>
      <MinistryName code="1711">과학기술정보통신부</MinistryName>
      <PerformAgency code="12345">한국과학기술원</PerformAgency>
      <PerformAgent code="02">대학</PerformAgent>
      <ScienceClass1 code="060401">암호이론</ScienceClass1>
    </HIT>
  </RESULTSET>
</RESULT>"""

QUANTUM_PATENTS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<RESULT>
  <TOTALHITS>356</TOTALHITS>
  <STARTPOSITION>1</STARTPOSITION>
  <HITS>3</HITS>
  <SEARCHTIME>0.07</SEARCHTIME>
  <RESULTSET>
    <HIT>
      <ResultID>PAT-KR-2023-0001</ResultID>
      <ResultTitle>초전도 큐비트 결어긋남 억제 구조 및 방법</ResultTitle>
      <Year>2023</Year>
      <RegistCountry code="KR">대한민국</RegistCountry>
      <RegistNumber>10-2023-0081234</RegistNumber>
      <Registrant>한국전자통신연구원</Registrant>
      <RegistType code="01">출원</RegistType>
      <IprType code="01">특허</IprType>
      <ProjectID>1711198200</ProjectID>
      <ProjectTitle>초전도 양자컴퓨터 오류정정 기술개발</ProjectTitle>
      <MinistryName code="1711">과학기술정보통신부</MinistryName>
      <PerformAgency code="67890">한국전자통신연구원</PerformAgency>
      <ScienceClass1 code="060101">양자정보처리</ScienceClass1>
    </HIT>
    <HIT>
      <ResultID>PAT-US-2023-0002</ResultID>
      <ResultTitle>Lattice-based post-quantum encryption method</ResultTitle>
      <Year>2023</Year>
      <RegistCountry code="US">미국</RegistCountry>
      <RegistNumber>US17/234567</RegistNumber>
      <Registrant>한국과학기술원</Registrant>
      <RegistType code="01">출원</RegistType>
      <IprType code="01">특허</IprType>
      <ProjectID>1711198164</ProjectID>
      <ProjectTitle>양자컴퓨팅 기반 암호체계 연구</ProjectTitle>
      <MinistryName code="1711">과학기술정보통신부</MinistryName>
      <PerformAgency code="12345">한국과학기술원</PerformAgency>
      <ScienceClass1 code="060401">암호이론</ScienceClass1>
    </HIT>
    <HIT>
      <ResultID>PAT-KR-2022-0003</ResultID>
      <ResultTitle>양자 시뮬레이션을 이용한 분자 에너지 계산 장치</ResultTitle>
      <Year>2022</Year>
      <RegistCountry code="KR">대한민국</RegistCountry>
      <RegistNumber>10-2022-0176543</RegistNumber>
      <Registrant>서울대학교</Registrant>
      <RegistType code="02">등록</RegistType>
      <IprType code="01">특허</IprType>
      <ProjectID>1711198250</ProjectID>
      <ProjectTitle>양자 시뮬레이터를 활용한 신소재 발견</ProjectTitle>
      <MinistryName code="1711">과학기술정보통신부</MinistryName>
      <PerformAgency code="11111">서울대학교</PerformAgency>
      <ScienceClass1 code="090102">에너지나노소재</ScienceClass1>
    </HIT>
  </RESULTSET>
</RESULT>"""

ETRI_PROJECTS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<RESULT>
  <TOTALHITS>3840</TOTALHITS>
  <STARTPOSITION>1</STARTPOSITION>
  <HITS>3</HITS>
  <SEARCHTIME>0.14</SEARCHTIME>
  <RESULTSET>
    <HIT>
      <ProjectNumber>1711198300</ProjectNumber>
      <ProjectTitle>
        <Korean>6G 초고신뢰 저지연 통신 핵심기술 개발</Korean>
        <English>6G Ultra-Reliable Low-Latency Communication Core Technology</English>
      </ProjectTitle>
      <Manager><Name>최육지</Name></Manager>
      <Goal><Teaser>6G 표준 선도를 위한 URLLC 핵심 기술 개발 및 실증</Teaser></Goal>
      <Abstract><Teaser>RIS 기반 빔포밍, AI 기반 채널 추정, 테라헤르츠 통신 기술 개발로 1ms 이하 지연 달성</Teaser></Abstract>
      <Effect><Teaser>국제 6G 표준 기여 및 통신 장비 수출 경쟁력 강화</Teaser></Effect>
      <Keyword><Korean>6G,URLLC,RIS,테라헤르츠,빔포밍</Korean><English>6G,URLLC,RIS,terahertz,beamforming</English></Keyword>
      <ProjectYear>2023</ProjectYear>
      <ProjectPeriod><Start>20220601</Start><End>20271231</End><TotalStart>20220601</TotalStart><TotalEnd>20271231</TotalEnd></ProjectPeriod>
      <Ministry code="1711">과학기술정보통신부</Ministry>
      <ResearchAgency><Name>정보통신기획평가원</Name></ResearchAgency>
      <BudgetProject><Name>6G핵심기술개발사업</Name></BudgetProject>
      <ManageAgency><Name>정보통신기획평가원</Name></ManageAgency>
      <PerformAgent code="67890">한국전자통신연구원</PerformAgent>
      <SixTechnology>정보전자</SixTechnology>
      <DevelopmentPhases code="03">개발연구</DevelopmentPhases>
      <GovernmentFunds>5200000</GovernmentFunds>
      <TotalFunds>5500000</TotalFunds>
      <ScienceClass>
        <Large code="060000">정보통신</Large>
        <Medium code="060200">통신</Medium>
        <Small code="060201">이동통신</Small>
      </ScienceClass>
    </HIT>
    <HIT>
      <ProjectNumber>1711198350</ProjectNumber>
      <ProjectTitle>
        <Korean>경량 엣지AI 반도체 설계 플랫폼 구축</Korean>
        <English>Lightweight Edge AI Semiconductor Design Platform</English>
      </ProjectTitle>
      <Manager><Name>정반도</Name></Manager>
      <Goal><Teaser>IoT 기기용 초저전력 AI 추론 NPU 설계 자동화 플랫폼 개발</Teaser></Goal>
      <Abstract><Teaser>신경망 압축, HW-SW 공동 설계, 자동 최적화로 1mW 이하 AI 추론 칩 구현</Teaser></Abstract>
      <Effect><Teaser>엣지 AI 디바이스 시장 선점 및 반도체 설계 수출 기반 마련</Teaser></Effect>
      <Keyword><Korean>엣지AI,NPU,경량화,신경망압축,IoT</Korean><English>edge AI,NPU,lightweight,neural compression,IoT</English></Keyword>
      <ProjectYear>2023</ProjectYear>
      <ProjectPeriod><Start>20230101</Start><End>20271231</End><TotalStart>20230101</TotalStart><TotalEnd>20271231</TotalEnd></ProjectPeriod>
      <Ministry code="1711">과학기술정보통신부</Ministry>
      <ResearchAgency><Name>정보통신기획평가원</Name></ResearchAgency>
      <BudgetProject><Name>인공지능반도체원천기술개발</Name></BudgetProject>
      <ManageAgency><Name>정보통신기획평가원</Name></ManageAgency>
      <PerformAgent code="67890">한국전자통신연구원</PerformAgent>
      <SixTechnology>정보전자</SixTechnology>
      <DevelopmentPhases code="03">개발연구</DevelopmentPhases>
      <GovernmentFunds>4800000</GovernmentFunds>
      <TotalFunds>5000000</TotalFunds>
      <ScienceClass>
        <Large code="060000">정보통신</Large>
        <Medium code="060300">반도체</Medium>
        <Small code="060302">시스템반도체</Small>
      </ScienceClass>
    </HIT>
    <HIT>
      <ProjectNumber>1711198200</ProjectNumber>
      <ProjectTitle>
        <Korean>초전도 양자컴퓨터 오류정정 기술개발</Korean>
        <English>Superconducting Quantum Computer Error Correction</English>
      </ProjectTitle>
      <Manager><Name>이초전</Name></Manager>
      <Goal><Teaser>초전도 큐비트 기반 오류정정 코드 구현</Teaser></Goal>
      <Abstract><Teaser>surface code 논리 큐비트 구현 및 게이트 충실도 99.9% 달성</Teaser></Abstract>
      <Effect><Teaser>실용적 양자컴퓨터 구현 핵심 기반기술 확보</Teaser></Effect>
      <Keyword><Korean>양자컴퓨터,초전도,큐비트</Korean><English>quantum computer,superconductor,qubit</English></Keyword>
      <ProjectYear>2022</ProjectYear>
      <ProjectPeriod><Start>20220101</Start><End>20261231</End><TotalStart>20220101</TotalStart><TotalEnd>20261231</TotalEnd></ProjectPeriod>
      <Ministry code="1711">과학기술정보통신부</Ministry>
      <ResearchAgency><Name>정보통신기획평가원</Name></ResearchAgency>
      <BudgetProject><Name>ICT혁신기술개발사업</Name></BudgetProject>
      <ManageAgency><Name>정보통신기획평가원</Name></ManageAgency>
      <PerformAgent code="67890">한국전자통신연구원</PerformAgent>
      <SixTechnology>정보전자</SixTechnology>
      <DevelopmentPhases code="03">개발연구</DevelopmentPhases>
      <GovernmentFunds>3500000</GovernmentFunds>
      <TotalFunds>3600000</TotalFunds>
      <ScienceClass>
        <Large code="060000">정보통신</Large>
        <Medium code="060100">컴퓨터하드웨어</Medium>
        <Small code="060101">양자정보처리</Small>
      </ScienceClass>
    </HIT>
  </RESULTSET>
</RESULT>"""

ETRI_ORG_XML = """<?xml version="1.0" encoding="UTF-8"?>
<orgRndInfo>
  <resultCode>00</resultCode>
  <resultMsg>정상처리</resultMsg>
  <orgName>한국전자통신연구원</orgName>
  <orgPageInfo>https://www.ntis.go.kr/rndopen/inst/instIntroInfo.do?instOrgCd=67890</orgPageInfo>
  <rndKorKeyword>인공지능,통신,반도체,보안,양자</rndKorKeyword>
  <rndEngKeyword>AI,communication,semiconductor,security,quantum</rndEngKeyword>
  <rndCategory>정보통신,전기전자,융합기술</rndCategory>
  <numOfList>5</numOfList>
  <rndStatusList>
    <item><year>2023</year><pjtCnt>850</pjtCnt><rndBudget>620000</rndBudget><govBudget>580000</govBudget><paperCnt>2100</paperCnt><patentCnt>1450</patentCnt><reportCnt>780</reportCnt></item>
    <item><year>2022</year><pjtCnt>820</pjtCnt><rndBudget>590000</rndBudget><govBudget>550000</govBudget><paperCnt>1980</paperCnt><patentCnt>1380</patentCnt><reportCnt>740</reportCnt></item>
    <item><year>2021</year><pjtCnt>790</pjtCnt><rndBudget>560000</rndBudget><govBudget>520000</govBudget><paperCnt>1850</paperCnt><patentCnt>1300</patentCnt><reportCnt>700</reportCnt></item>
    <item><year>2020</year><pjtCnt>760</pjtCnt><rndBudget>530000</rndBudget><govBudget>490000</govBudget><paperCnt>1720</paperCnt><patentCnt>1240</patentCnt><reportCnt>660</reportCnt></item>
    <item><year>2019</year><pjtCnt>730</pjtCnt><rndBudget>500000</rndBudget><govBudget>460000</govBudget><paperCnt>1600</paperCnt><patentCnt>1180</patentCnt><reportCnt>620</reportCnt></item>
  </rndStatusList>
</orgRndInfo>"""

NANO_BATTERY_PROJECTS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<RESULT>
  <TOTALHITS>218</TOTALHITS>
  <STARTPOSITION>1</STARTPOSITION>
  <HITS>2</HITS>
  <SEARCHTIME>0.10</SEARCHTIME>
  <RESULTSET>
    <HIT>
      <ProjectNumber>1415180100</ProjectNumber>
      <ProjectTitle>
        <Korean>나노구조 실리콘 음극재 기반 고에너지 배터리 개발</Korean>
        <English>High-energy Battery with Nanostructured Silicon Anode</English>
      </ProjectTitle>
      <Manager><Name>한실리</Name></Manager>
      <Goal><Teaser>실리콘 나노와이어 음극재로 에너지밀도 500Wh/kg 배터리 구현</Teaser></Goal>
      <Abstract><Teaser>실리콘의 부피팽창 문제를 나노구조 설계로 해결, 3000사이클 이상 장수명 달성</Teaser></Abstract>
      <Effect><Teaser>전기차 1회 충전 주행거리 600km 이상 실현 기반 확보</Teaser></Effect>
      <Keyword><Korean>나노실리콘,음극재,리튬이온배터리,에너지밀도</Korean><English>nano silicon,anode,lithium-ion battery,energy density</English></Keyword>
      <ProjectYear>2023</ProjectYear>
      <ProjectPeriod><Start>20210901</Start><End>20251231</End><TotalStart>20210901</TotalStart><TotalEnd>20251231</TotalEnd></ProjectPeriod>
      <Ministry code="1450">산업통상자원부</Ministry>
      <ResearchAgency><Name>한국에너지기술평가원</Name></ResearchAgency>
      <BudgetProject><Name>에너지기술개발사업</Name></BudgetProject>
      <ManageAgency><Name>한국에너지기술평가원</Name></ManageAgency>
      <PerformAgent code="22222">삼성SDI(주)</PerformAgent>
      <SixTechnology>나노소재</SixTechnology>
      <DevelopmentPhases code="03">개발연구</DevelopmentPhases>
      <GovernmentFunds>2500000</GovernmentFunds>
      <TotalFunds>5000000</TotalFunds>
      <ScienceClass>
        <Large code="090000">나노 및 소재</Large>
        <Medium code="090100">나노소재</Medium>
        <Small code="090103">에너지저장소재</Small>
      </ScienceClass>
      <ApplyArea>
        <First>산업기술</First>
        <Second>에너지</Second>
        <Third>배터리</Third>
      </ApplyArea>
    </HIT>
    <HIT>
      <ProjectNumber>1415180150</ProjectNumber>
      <ProjectTitle>
        <Korean>나노복합체 양극재를 이용한 전고체 배터리 상용화 기술</Korean>
        <English>All-Solid-State Battery Commercialization with Nano-composite Cathode</English>
      </ProjectTitle>
      <Manager><Name>오전고</Name></Manager>
      <Goal><Teaser>황화물계 고체전해질과 나노복합 양극재 계면 최적화로 전고체 배터리 상용화</Teaser></Goal>
      <Abstract><Teaser>나노코팅 기술 적용으로 계면저항 90% 저감 달성, 실온 이온전도도 10mS/cm 이상</Teaser></Abstract>
      <Effect><Teaser>전기차·ESS 시장 선점 및 배터리 화재사고 근본 해결</Teaser></Effect>
      <Keyword><Korean>전고체배터리,나노복합체,황화물전해질,계면저항</Korean><English>all-solid-state battery,nanocomposite,sulfide electrolyte,interface resistance</English></Keyword>
      <ProjectYear>2023</ProjectYear>
      <ProjectPeriod><Start>20230301</Start><End>20271231</End><TotalStart>20230301</TotalStart><TotalEnd>20271231</TotalEnd></ProjectPeriod>
      <Ministry code="1450">산업통상자원부</Ministry>
      <ResearchAgency><Name>한국에너지기술평가원</Name></ResearchAgency>
      <BudgetProject><Name>이차전지핵심기술개발사업</Name></BudgetProject>
      <ManageAgency><Name>한국에너지기술평가원</Name></ManageAgency>
      <PerformAgent code="33333">LG에너지솔루션(주)</PerformAgent>
      <SixTechnology>나노소재</SixTechnology>
      <DevelopmentPhases code="03">개발연구</DevelopmentPhases>
      <GovernmentFunds>3800000</GovernmentFunds>
      <TotalFunds>8000000</TotalFunds>
      <ScienceClass>
        <Large code="090000">나노 및 소재</Large>
        <Medium code="090200">에너지소재</Medium>
        <Small code="090201">이차전지소재</Small>
      </ScienceClass>
      <ApplyArea>
        <First>산업기술</First>
        <Second>에너지</Second>
        <Third>전지</Third>
      </ApplyArea>
    </HIT>
  </RESULTSET>
</RESULT>"""

CONSIGNMENT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<RESULT>
  <TOTALHITS>3</TOTALHITS>
  <STARTPOSITION>1</STARTPOSITION>
  <HITS>3</HITS>
  <SEARCHTIME>0.06</SEARCHTIME>
  <RESULTSET>
    <HIT NO="1">
      <ProjectNumber>1415180100</ProjectNumber>
      <CommissionNumber>1415180100-C01</CommissionNumber>
      <ProjectYear>2023</ProjectYear>
      <ProjectTitle>
        <Korean>나노구조 실리콘 음극재 기반 고에너지 배터리 개발</Korean>
        <English>High-energy Battery with Nanostructured Silicon Anode</English>
        <Commission>나노실리콘 합성 및 표면처리 기술 개발</Commission>
      </ProjectTitle>
      <Manager><Name>한실리</Name></Manager>
      <CommissionManager><Name>이위탁</Name></CommissionManager>
      <OrderAgency>삼성SDI(주)</OrderAgency>
      <LeadAgency>삼성SDI(주)</LeadAgency>
      <CommissionLeadAgency>포항공과대학교</CommissionLeadAgency>
      <CommissionType>위탁</CommissionType>
      <PerformAgent code="02">대학</PerformAgent>
      <Country code="KR">한국</Country>
      <ProjectPeriod>
        <Start>20210901</Start>
        <End>20251231</End>
        <Total>60개월</Total>
      </ProjectPeriod>
      <ResearcherCount>8</ResearcherCount>
      <CollaborativeResearchFunds>0</CollaborativeResearchFunds>
      <ConsignmentProjectResearchFunds>350000</ConsignmentProjectResearchFunds>
      <CollaborativeResearchFundExpense>0</CollaborativeResearchFundExpense>
      <ParticipateType>국내</ParticipateType>
      <ParticipateCountry>한국</ParticipateCountry>
      <ParticipateResearcherNumber>0</ParticipateResearcherNumber>
    </HIT>
    <HIT NO="2">
      <ProjectNumber>1415180100</ProjectNumber>
      <CommissionNumber>1415180100-C02</CommissionNumber>
      <ProjectYear>2023</ProjectYear>
      <ProjectTitle>
        <Korean>나노구조 실리콘 음극재 기반 고에너지 배터리 개발</Korean>
        <Commission>배터리 셀 설계 및 팩 집적화 연구</Commission>
      </ProjectTitle>
      <Manager><Name>한실리</Name></Manager>
      <CommissionManager><Name>김팩</Name></CommissionManager>
      <OrderAgency>삼성SDI(주)</OrderAgency>
      <LeadAgency>삼성SDI(주)</LeadAgency>
      <CommissionLeadAgency>한양대학교</CommissionLeadAgency>
      <CommissionType>위탁</CommissionType>
      <PerformAgent code="02">대학</PerformAgent>
      <Country code="KR">한국</Country>
      <ProjectPeriod>
        <Start>20210901</Start>
        <End>20251231</End>
        <Total>60개월</Total>
      </ProjectPeriod>
      <ResearcherCount>5</ResearcherCount>
      <CollaborativeResearchFunds>0</CollaborativeResearchFunds>
      <ConsignmentProjectResearchFunds>180000</ConsignmentProjectResearchFunds>
      <CollaborativeResearchFundExpense>0</CollaborativeResearchFundExpense>
      <ParticipateType>국내</ParticipateType>
    </HIT>
    <HIT NO="3">
      <ProjectNumber>1415180100</ProjectNumber>
      <CommissionNumber>1415180100-J01</CommissionNumber>
      <ProjectYear>2023</ProjectYear>
      <ProjectTitle>
        <Korean>나노구조 실리콘 음극재 기반 고에너지 배터리 개발</Korean>
        <Commission>충방전 특성 분석 및 수명 예측 AI 모델 개발</Commission>
      </ProjectTitle>
      <Manager><Name>한실리</Name></Manager>
      <CommissionManager><Name>박수명</Name></CommissionManager>
      <OrderAgency>삼성SDI(주)</OrderAgency>
      <LeadAgency>삼성SDI(주)</LeadAgency>
      <CommissionLeadAgency>KAIST</CommissionLeadAgency>
      <CommissionType>공동</CommissionType>
      <PerformAgent code="02">대학</PerformAgent>
      <Country code="KR">한국</Country>
      <ProjectPeriod>
        <Start>20230101</Start>
        <End>20251231</End>
        <Total>36개월</Total>
      </ProjectPeriod>
      <ResearcherCount>6</ResearcherCount>
      <CollaborativeResearchFunds>200000</CollaborativeResearchFunds>
      <ConsignmentProjectResearchFunds>0</ConsignmentProjectResearchFunds>
      <CollaborativeResearchFundExpense>200000</CollaborativeResearchFundExpense>
      <ParticipateType>국내</ParticipateType>
    </HIT>
  </RESULTSET>
</RESULT>"""

RELATED_CONTENT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<RESULT>
  <TOTALHITS>8</TOTALHITS>
  <STARTPOSITION>1</STARTPOSITION>
  <HITS>4</HITS>
  <SEARCHTIME>0.11</SEARCHTIME>
  <RESULTSET>
    <HIT SITID="project">
      <ProjectNumber>1415180200</ProjectNumber>
      <ProjectTitle><Korean>나노복합 음극재 리튬금속 배터리 개발</Korean></ProjectTitle>
    </HIT>
    <HIT SITID="project">
      <ProjectNumber>1415180250</ProjectNumber>
      <ProjectTitle><Korean>CNT 탄소나노튜브 기반 고용량 전극소재 연구</Korean></ProjectTitle>
    </HIT>
    <HIT SITID="project">
      <ProjectNumber>1415180300</ProjectNumber>
      <ProjectTitle><Korean>실리콘-탄소 복합체 음극재 파일럿 스케일업</Korean></ProjectTitle>
    </HIT>
    <HIT SITID="project">
      <ProjectNumber>1415180350</ProjectNumber>
      <ProjectTitle><Korean>배터리 팩 열관리 시스템 나노유체 냉각기술</Korean></ProjectTitle>
    </HIT>
  </RESULTSET>
</RESULT>"""

METAVERSE_TERM_XML = """<?xml version="1.0" encoding="UTF-8"?>
<RESULT>
  <TOTALHITS>4</TOTALHITS>
  <STARTPOSITION>1</STARTPOSITION>
  <HITS>4</HITS>
  <SEARCHTIME>0.04</SEARCHTIME>
  <RESULTSET>
    <HIT>
      <TermSn>30001</TermSn>
      <KorWord>메타버스</KorWord>
      <EngWord>Metaverse</EngWord>
      <MainAbrv></MainAbrv>
      <SntStdCls>정보통신</SntStdCls>
      <RelWord>가상현실,증강현실,디지털트윈,XR</RelWord>
      <TermDctn>현실과 가상이 결합된 3차원 초연결 가상공간으로, 아바타를 통해 경제·사회·문화 활동이 가능한 플랫폼</TermDctn>
      <TermCls>기술용어</TermCls>
    </HIT>
    <HIT>
      <TermSn>30002</TermSn>
      <KorWord>디지털트윈</KorWord>
      <EngWord>Digital Twin</EngWord>
      <MainAbrv>DT</MainAbrv>
      <SntStdCls>정보통신</SntStdCls>
      <RelWord>메타버스,IoT,시뮬레이션,가상모델</RelWord>
      <TermDctn>물리적 객체나 시스템을 디지털 공간에 동일하게 복제한 가상 모델. 실시간 데이터 동기화로 예측·최적화 지원</TermDctn>
      <TermCls>기술용어</TermCls>
    </HIT>
    <HIT>
      <TermSn>30003</TermSn>
      <KorWord>확장현실</KorWord>
      <EngWord>Extended Reality</EngWord>
      <MainAbrv>XR</MainAbrv>
      <SntStdCls>정보통신</SntStdCls>
      <RelWord>메타버스,가상현실,증강현실,혼합현실</RelWord>
      <TermDctn>VR·AR·MR을 포괄하는 개념으로, 현실과 가상환경의 스펙트럼 전체를 지칭하는 기술 총칭</TermDctn>
      <TermCls>기술용어</TermCls>
    </HIT>
    <HIT>
      <TermSn>30004</TermSn>
      <KorWord>아바타</KorWord>
      <EngWord>Avatar</EngWord>
      <MainAbrv></MainAbrv>
      <SntStdCls>정보통신</SntStdCls>
      <RelWord>메타버스,가상현실,사용자인터페이스</RelWord>
      <TermDctn>메타버스·가상공간에서 사용자를 대리하는 디지털 분신. 3D 모델 또는 캐릭터 형태</TermDctn>
      <TermCls>기술용어</TermCls>
    </HIT>
  </RESULTSET>
</RESULT>"""

ICT_CODES_XML = """<?xml version="1.0" encoding="UTF-8"?>
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
      <cdExplan>정보·통신 분야의 연구개발</cdExplan>
      <upperCd>000000</upperCd>
    </dataset>
    <dataset>
      <cd>060100</cd>
      <cdNm>컴퓨터하드웨어</cdNm>
      <cdNmEng>Computer Hardware</cdNmEng>
      <cdExplan>컴퓨터 하드웨어 및 주변기기</cdExplan>
      <upperCd>060000</upperCd>
    </dataset>
    <dataset>
      <cd>060200</cd>
      <cdNm>소프트웨어</cdNm>
      <cdNmEng>Software</cdNmEng>
      <cdExplan>소프트웨어 기술 및 플랫폼</cdExplan>
      <upperCd>060000</upperCd>
    </dataset>
    <dataset>
      <cd>060210</cd>
      <cdNm>가상현실/증강현실</cdNm>
      <cdNmEng>Virtual/Augmented Reality</cdNmEng>
      <cdExplan>VR·AR·메타버스 관련 소프트웨어 기술</cdExplan>
      <upperCd>060200</upperCd>
    </dataset>
    <dataset>
      <cd>060211</cd>
      <cdNm>메타버스플랫폼</cdNm>
      <cdNmEng>Metaverse Platform</cdNmEng>
      <cdExplan>메타버스 서비스 플랫폼 및 인터페이스</cdExplan>
      <upperCd>060210</upperCd>
    </dataset>
  </contents>
</ntis>"""

METAVERSE_PROJECTS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<RESULT>
  <TOTALHITS>645</TOTALHITS>
  <STARTPOSITION>1</STARTPOSITION>
  <HITS>2</HITS>
  <SEARCHTIME>0.09</SEARCHTIME>
  <RESULTSET>
    <HIT>
      <ProjectNumber>1711199001</ProjectNumber>
      <ProjectTitle>
        <Korean>메타버스 기반 원격협업 플랫폼 기술 개발</Korean>
        <English>Metaverse-based Remote Collaboration Platform Technology</English>
      </ProjectTitle>
      <Manager><Name>손메타</Name></Manager>
      <Goal><Teaser>실감형 아바타·공간음향·햅틱 피드백 통합 메타버스 협업 플랫폼 구현</Teaser></Goal>
      <Abstract><Teaser>WebXR 기반 크로스플랫폼 메타버스로 지연 50ms 이하 실시간 협업 구현. 디지털트윈 연계로 산업현장 원격작업 지원</Teaser></Abstract>
      <Effect><Teaser>비대면 업무환경 혁신 및 메타버스 산업 생태계 활성화</Teaser></Effect>
      <Keyword><Korean>메타버스,원격협업,아바타,디지털트윈,WebXR</Korean><English>metaverse,remote collaboration,avatar,digital twin,WebXR</English></Keyword>
      <ProjectYear>2023</ProjectYear>
      <ProjectPeriod><Start>20220401</Start><End>20261231</End><TotalStart>20220401</TotalStart><TotalEnd>20261231</TotalEnd></ProjectPeriod>
      <Ministry code="1711">과학기술정보통신부</Ministry>
      <ResearchAgency><Name>정보통신기획평가원</Name></ResearchAgency>
      <BudgetProject><Name>메타버스서비스원천기술개발</Name></BudgetProject>
      <ManageAgency><Name>정보통신기획평가원</Name></ManageAgency>
      <PerformAgent code="44444">네이버클라우드(주)</PerformAgent>
      <SixTechnology>정보전자</SixTechnology>
      <DevelopmentPhases code="03">개발연구</DevelopmentPhases>
      <GovernmentFunds>3200000</GovernmentFunds>
      <TotalFunds>4000000</TotalFunds>
      <ScienceClass>
        <Large code="060000">정보통신</Large>
        <Medium code="060200">소프트웨어</Medium>
        <Small code="060211">메타버스플랫폼</Small>
      </ScienceClass>
    </HIT>
    <HIT>
      <ProjectNumber>1711199050</ProjectNumber>
      <ProjectTitle>
        <Korean>교육·훈련 특화 메타버스 콘텐츠 저작도구 개발</Korean>
        <English>Metaverse Content Authoring Tool for Education and Training</English>
      </ProjectTitle>
      <Manager><Name>권교육</Name></Manager>
      <Goal><Teaser>비전문가도 3D 메타버스 교육 콘텐츠를 쉽게 제작할 수 있는 노코드 저작도구 개발</Teaser></Goal>
      <Abstract><Teaser>AI 기반 자동 3D 모델 생성, 행동 스크립팅 엔진, 실시간 협력 편집 기능 통합</Teaser></Abstract>
      <Effect><Teaser>교육 콘텐츠 제작 비용 80% 절감 및 실감교육 확산 기반 마련</Teaser></Effect>
      <Keyword><Korean>메타버스,교육,저작도구,노코드,AI생성</Korean><English>metaverse,education,authoring tool,no-code,AI generation</English></Keyword>
      <ProjectYear>2023</ProjectYear>
      <ProjectPeriod><Start>20230601</Start><End>20271231</End><TotalStart>20230601</TotalStart><TotalEnd>20271231</TotalEnd></ProjectPeriod>
      <Ministry code="1711">과학기술정보통신부</Ministry>
      <ResearchAgency><Name>정보통신기획평가원</Name></ResearchAgency>
      <BudgetProject><Name>메타버스서비스원천기술개발</Name></BudgetProject>
      <ManageAgency><Name>정보통신기획평가원</Name></ManageAgency>
      <PerformAgent code="55555">한국과학기술연구원</PerformAgent>
      <SixTechnology>정보전자</SixTechnology>
      <DevelopmentPhases code="03">개발연구</DevelopmentPhases>
      <GovernmentFunds>2800000</GovernmentFunds>
      <TotalFunds>3200000</TotalFunds>
      <ScienceClass>
        <Large code="060000">정보통신</Large>
        <Medium code="060200">소프트웨어</Medium>
        <Small code="060211">메타버스플랫폼</Small>
      </ScienceClass>
    </HIT>
  </RESULTSET>
</RESULT>"""

AI_HEALTH_ISSUE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<NewestIssue>
  <selectListCnt>2</selectListCnt>
  <list>
    <topicNo>20240201</topicNo>
    <topicNm>AI 의료진단 정확도 혁신</topicNm>
    <extrDt>20240401</extrDt>
    <rltdPjtCnt>3820</rltdPjtCnt>
    <url01>https://www.ntis.go.kr/doc/ai-health-001</url01>
    <url02>https://www.ntis.go.kr/doc/ai-health-002</url02>
    <rltdKywdList>인공지능,의료영상,딥러닝,진단보조,FDA승인</rltdKywdList>
    <imgOfferYn>Y</imgOfferYn>
  </list>
  <list>
    <topicNo>20240202</topicNo>
    <topicNm>디지털 바이오마커 기반 정밀의료</topicNm>
    <extrDt>20240328</extrDt>
    <rltdPjtCnt>1640</rltdPjtCnt>
    <url01>https://www.ntis.go.kr/doc/ai-health-003</url01>
    <url02>https://www.ntis.go.kr/doc/ai-health-004</url02>
    <rltdKywdList>바이오마커,웨어러블,정밀의료,유전체</rltdKywdList>
    <imgOfferYn>Y</imgOfferYn>
  </list>
</NewestIssue>"""

HT_CLS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<NTIS>
  <STATUS>
    <ResultCode>00</ResultCode>
    <ResultMsg>정상처리</ResultMsg>
  </STATUS>
  <RESULT>
    <MOHWD>
      <Result_1 LCLS_CD="C" LCLS_NM="종양" MCLS_CD="C04" MCLS_NM="신생물(종양)" MCLS_WEIGHT="87.3"/>
      <Result_2 LCLS_CD="B" LCLS_NM="감염·기생충" MCLS_CD="B99" MCLS_NM="달리분류되지않은질환" MCLS_WEIGHT="5.1"/>
      <Result_3 LCLS_CD="Z" LCLS_NM="특수목적코드" MCLS_CD="Z12" MCLS_NM="종양선별검사" MCLS_WEIGHT="4.2"/>
    </MOHWD>
    <MOHWR>
      <Result_1 LCLS_CD="D" LCLS_NM="진단" MCLS_CD="D02" MCLS_NM="영상진단" MCLS_WEIGHT="91.5"/>
      <Result_2 LCLS_CD="D" LCLS_NM="진단" MCLS_CD="D01" MCLS_NM="검사" MCLS_WEIGHT="6.2"/>
      <Result_3 LCLS_CD="T" LCLS_NM="기술" MCLS_CD="T05" MCLS_NM="인공지능/빅데이터" MCLS_WEIGHT="2.3"/>
    </MOHWR>
  </RESULT>
</NTIS>"""

IT_CLS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<NTIS>
  <STATUS>
    <ResultCode>00</ResultCode>
    <ResultMsg>정상처리</ResultMsg>
  </STATUS>
  <RESULT>
    <Result_1 LCLS_CD="IT" LCLS_NM="정보통신" MCLS_CD="IT02" MCLS_NM="소프트웨어/콘텐츠" SCLS_CD="IT0207" SCLS_NM="AI/빅데이터" SCLS_WEIGHT="89.2"/>
    <Result_2 LCLS_CD="BT" LCLS_NM="바이오기술" MCLS_CD="BT04" MCLS_NM="의료기기/의료IT" SCLS_CD="BT0401" SCLS_NM="의료영상진단기기" SCLS_WEIGHT="7.4"/>
    <Result_3 LCLS_CD="IT" LCLS_NM="정보통신" MCLS_CD="IT04" MCLS_NM="네트워크/통신" SCLS_CD="IT0409" SCLS_NM="클라우드서비스" SCLS_WEIGHT="3.4"/>
  </RESULT>
</NTIS>"""

AI_HEALTH_RESEARCH_TEXT = (
    "딥러닝 기반 의료영상 분석 AI 시스템 개발. "
    "CT·MRI·병리슬라이드 이미지에서 암·뇌졸중·당뇨망막증 자동 진단. "
    "멀티모달 트랜스포머 아키텍처로 방사선과 전문의 수준 정확도 달성. "
    "FDA·식약처 인허가 지원 임상시험 데이터 확보 및 규제 대응 프레임워크 구축."
)


# ═══════════════════════════════════════════════════════════════════════════════
# 캐시 주입 유틸리티
# ═══════════════════════════════════════════════════════════════════════════════

def _pjt_params(query, search_field="BI", add_query="", sort="RANK/DESC", start=1, count=10):
    p = {"apprvKey": API_KEY, "collection": "project", "SRWR": query,
         "searchFd": search_field, "searchRnkn": sort, "startPosition": start, "displayCnt": count}
    if add_query:
        p["addQuery"] = add_query
    return p

def _nat_params(collection, query, search_field="BI", add_query="", sort="RANK/DESC", start=1, count=10):
    p = {"apprvKey": API_KEY, "collection": collection, "SRWR": query,
         "searchFd": search_field, "searchRnkn": sort, "startPosition": start, "displayCnt": count}
    if add_query:
        p["addQuery"] = add_query
    return p

def _rcmn_params(collection, text="", goal="", abstract="", effects="", kor_kw="", eng_kw=""):
    p = {"apprvKey": API_KEY, "collection": collection}
    if text:
        p["rqstDes"] = text
    else:
        p["rschGoalAbstract"] = goal
        p["rschAbstract"] = abstract
        if effects:
            p["expEfctAbstract"] = effects
    return p


# ═══════════════════════════════════════════════════════════════════════════════
# 시나리오 S1: 양자컴퓨팅 트렌드 → 과제·논문·특허 교차 분석
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_s1_quantum_cross_analysis():
    """S1: 양자컴퓨팅 분야 과제 3건 → 논문 3건 → 특허 3건 교차분석.

    LLM이 실제 수행하는 패턴:
      1) 과제 검색으로 주요 수행기관·연구방향 파악
      2) 동일 쿼리로 논문 검색 → SCI/비SCI, 국내/국외 분포 파악
      3) 특허 검색 → 출원인, 등록국가 분포 파악
      4) 세 결과를 교차 분석 → 과제-논문-특허 연계율 계산
    """
    inject(PJT_SEARCH_URL, _pjt_params("양자컴퓨팅"), QUANTUM_PROJECTS_XML)
    inject(NAT_RND_SEARCH_URL, _nat_params("rpaper", "양자컴퓨팅"), QUANTUM_PAPERS_XML)
    inject(NAT_RND_SEARCH_URL, _nat_params("rpatent", "양자컴퓨팅"), QUANTUM_PATENTS_XML)

    c = client()
    projects = await c.search_projects(query="양자컴퓨팅")
    papers = await c.search_results(collection="rpaper", query="양자컴퓨팅")
    patents = await c.search_results(collection="rpatent", query="양자컴퓨팅")

    # ── 과제 검증 ──
    assert projects["total_hits"] == 482
    assert len(projects["items"]) == 3
    pjt_ids = {p["id"] for p in projects["items"]}
    assert "1711198164" in pjt_ids  # 암호체계
    assert "1711198200" in pjt_ids  # 오류정정
    assert "1711198250" in pjt_ids  # 신소재발견

    # span 태그 완전 제거 확인
    for pjt in projects["items"]:
        assert "<span" not in pjt["title_kor"]
        assert "양자컴퓨팅" in pjt["title_kor"] or "양자컴퓨터" in pjt["title_kor"] or "양자" in pjt["title_kor"]

    # 분류 코드 포함 확인
    for pjt in projects["items"]:
        assert len(pjt["science_class"]) > 0
        assert pjt["science_class"][0]["large"]["code"] != ""

    # ── 논문 검증 ──
    assert papers["total_hits"] == 1240
    assert len(papers["items"]) == 3
    sci_papers = [p for p in papers["items"] if p["sci_type"] == "SCI"]
    domestic_papers = [p for p in papers["items"] if p["nation_type"] == "국내"]
    assert len(sci_papers) == 2
    assert len(domestic_papers) == 1

    # 논문-과제 연계 확인
    paper_project_ids = {p["project_id"] for p in papers["items"] if p["project_id"]}
    overlap = pjt_ids & paper_project_ids
    assert len(overlap) >= 2  # 과제 2건 이상이 논문으로 이어짐

    # 논문 기관 span 제거 확인
    for paper in papers["items"]:
        assert "<span" not in paper["perform_agency"]["name"]

    # ── 특허 검증 ──
    assert patents["total_hits"] == 356
    patent_applicants = {p["registrant"] for p in patents["items"]}
    assert "한국전자통신연구원" in patent_applicants
    assert "한국과학기술원" in patent_applicants

    # 국내/해외 특허 분포
    domestic_patents = [p for p in patents["items"] if p["regist_country"]["code"] == "KR"]
    intl_patents = [p for p in patents["items"] if p["regist_country"]["code"] != "KR"]
    assert len(domestic_patents) == 2
    assert len(intl_patents) == 1

    # 특허-과제 연계 확인
    patent_project_ids = {p["project_id"] for p in patents["items"] if p["project_id"]}
    assert len(pjt_ids & patent_project_ids) >= 2

    print("\n[S1] 양자컴퓨팅 교차분석 완료")
    print(f"  과제 {projects['total_hits']}건 | 논문 {papers['total_hits']}건 | 특허 {patents['total_hits']}건")
    print(f"  과제-논문 연계: {len(overlap)}/{len(projects['items'])}건")
    print(f"  SCI 논문: {len(sci_papers)}건 / 국내 논문: {len(domestic_papers)}건")
    print(f"  국내특허: {len(domestic_patents)}건 / 해외특허: {len(intl_patents)}건")
    for pjt in projects["items"]:
        print(f"  ▷ [{pjt['id']}] {pjt['title_kor']}")
        print(f"     수행: {pjt['perform_agent']['name']} | 정부출연: {int(pjt['government_funds']):,}천원")


# ═══════════════════════════════════════════════════════════════════════════════
# 시나리오 S2: ETRI 과제 발굴 → 기관 R&D 심층 현황 조회
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_s2_etri_org_intelligence():
    """S2: 기관(ETRI) 과제 목록 → 연도별 R&D 성장 추이 분석.

    LLM 시나리오: "한국전자통신연구원(ETRI)이 어떤 분야를 연구하고,
    최근 5년간 얼마나 성장했는지 분석해줘"
    """
    inject(PJT_SEARCH_URL, _pjt_params("한국전자통신연구원", search_field="OG", count=3),
           ETRI_PROJECTS_XML)
    inject(ORG_RND_INFO_URL, {"apprvKey": API_KEY, "reqOrgNm": "한국전자통신연구원"}, ETRI_ORG_XML)

    c = client()
    projects = await c.search_projects(query="한국전자통신연구원", search_field="OG", count=3)
    org_status = await c.get_org_rnd_status(org_name="한국전자통신연구원")

    # ── 과제 다양성 확인 ──
    assert projects["total_hits"] == 3840
    research_areas = {pjt["science_class"][0]["large"]["name"] for pjt in projects["items"]
                      if pjt["science_class"]}
    assert "정보통신" in research_areas  # 단일 기관이지만 다양한 세부분야

    budgets = [int(pjt["government_funds"]) for pjt in projects["items"]]
    assert max(budgets) == 5200000  # 6G 사업이 최대 예산

    # ── 기관 현황 성장 추이 ──
    assert org_status["result_code"] == "00"
    status_list = org_status["rnd_status"]
    assert len(status_list) == 5

    years = [int(s["year"]) for s in status_list]
    assert years == sorted(years, reverse=True)  # 최신순 정렬

    paper_counts = [int(s["paper_count"]) for s in status_list]
    assert paper_counts[0] > paper_counts[-1]  # 논문 증가 추세

    patent_counts = [int(s["patent_count"]) for s in status_list]
    growth_rate = (patent_counts[0] - patent_counts[-1]) / patent_counts[-1] * 100
    assert growth_rate > 20  # 5년간 특허 20% 이상 성장

    # ── 키워드 포함 확인 ──
    assert "인공지능" in org_status["top_kor_keywords"]
    assert "양자" in org_status["top_kor_keywords"]

    print("\n[S2] ETRI R&D 역량 분석 완료")
    print(f"  수행기관: {org_status['org_name']}")
    print(f"  대표 키워드: {org_status['top_kor_keywords']}")
    print(f"  활성 과제: {projects['total_hits']:,}건")
    for s in status_list:
        gov_b = int(s["gov_budget"])
        print(f"  {s['year']}년: 과제 {s['project_count']}건 | 정부연구비 {gov_b:,}천원 | "
              f"논문 {s['paper_count']}건 | 특허 {s['patent_count']}건")


# ═══════════════════════════════════════════════════════════════════════════════
# 시나리오 S3: 나노배터리 과제 → 위탁구조 파악 → 연관콘텐츠 추천 체인
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_s3_nanobattery_research_ecosystem():
    """S3: 과제 탐색 → 연구 생태계(위탁기관) → AI 유사과제 추천 체인.

    LLM 시나리오: "나노소재 배터리 연구에서 어떤 대학·기업이 협력하고,
    유사 연구가 더 있는지 추천받고 싶어"
    """
    inject(PJT_SEARCH_URL, _pjt_params("나노 배터리"), NANO_BATTERY_PROJECTS_XML)
    inject(PROJECT_U_ORG_URL, {"apprvKey": API_KEY, "pjtId": "1415180100"}, CONSIGNMENT_XML)
    inject(CONN_CONTENT_URL, {"apprvKey": API_KEY, "collection": "project", "id": "1415180100"},
           RELATED_CONTENT_XML)

    c = client()
    projects = await c.search_projects(query="나노 배터리")
    main_pjt_id = projects["items"][0]["id"]

    consignment = await c.get_consignment_research(pjt_id=main_pjt_id)
    related = await c.get_related_content(content_type="project", content_id=main_pjt_id)

    # ── 과제 기본 검증 ──
    assert projects["total_hits"] == 218
    first_pjt = projects["items"][0]
    assert first_pjt["id"] == "1415180100"
    assert "나노" in first_pjt["title_kor"]
    assert first_pjt["perform_agent"]["name"] == "삼성SDI(주)"

    # ── 위탁 구조 분석 ──
    assert consignment["total_hits"] == 3
    commission_types = {c["commission_type"] for c in consignment["items"]}
    assert "위탁" in commission_types
    assert "공동" in commission_types

    # 참여 기관 목록
    participant_agencies = {c["commission_lead_agency"] for c in consignment["items"]}
    universities = {"포항공과대학교", "한양대학교", "KAIST"}
    assert participant_agencies == universities

    # 위탁연구비 합산
    total_commission_funds = sum(
        int(c["consignment_project_funds"]) for c in consignment["items"]
        if c["consignment_project_funds"]
    )
    assert total_commission_funds == 530000  # 350000 + 180000

    # 공동연구비 별도
    total_collaborative_funds = sum(
        int(c["collaborative_research_funds"]) for c in consignment["items"]
        if c["collaborative_research_funds"]
    )
    assert total_collaborative_funds == 200000

    # ── 연관콘텐츠 추천 ──
    assert related["total_hits"] == 8
    assert len(related["items"]) == 4
    related_titles = [r["title"] for r in related["items"]]
    assert all("배터리" in t or "음극재" in t or "탄소" in t or "나노" in t for t in related_titles)

    print("\n[S3] 나노배터리 연구 생태계 분석 완료")
    print(f"  주과제: [{first_pjt['id']}] {first_pjt['title_kor']}")
    print(f"  주관기관: {first_pjt['perform_agent']['name']}")
    for item in consignment["items"]:
        funds = int(item["consignment_project_funds"] or item["collaborative_research_funds"] or 0)
        print(f"  {'위탁' if item['commission_type']=='위탁' else '공동'} {item['commission_lead_agency']}: "
              f"{funds:,}천원 | 연구원 {item['researcher_count']}명")
    print(f"  AI 유사과제 추천 {related['total_hits']}건 중 상위 {len(related['items'])}건:")
    for r in related["items"]:
        print(f"    → [{r['id']}] {r['title']}")


# ═══════════════════════════════════════════════════════════════════════════════
# 시나리오 S4: 용어 정의 → 분류코드 탐색 → 분류추천 → 코드기반 과제 검색
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_s4_metaverse_knowledge_chain():
    """S4: 신기술 용어 정의 → 표준분류체계 탐색 → 관련 과제 발굴 체인.

    LLM 시나리오: "메타버스 관련 R&D를 분석하려는데,
    표준 용어와 분류체계부터 파악하고 실제 연구과제를 찾아줘"
    """
    # 용어사전 조회
    inject(NTIS_DIC_URL, {"userKey": API_KEY, "query": "메타버스", "searchField": "BI",
                           "sortby": "RANK/DESC", "startPosition": 1, "displayCount": 10},
           METAVERSE_TERM_XML)
    # 분류코드 탐색 (ICT 대분류)
    inject(TARGET_SEARCH_URL, {"apprvKey": API_KEY, "rqstSlctCd": "NTIS001"}, ICT_CODES_XML)
    # 메타버스 과제 검색
    inject(PJT_SEARCH_URL, _pjt_params("메타버스"), METAVERSE_PROJECTS_XML)

    c = client()
    terms = await c.search_terminology(query="메타버스")
    codes = await c.get_classification_codes(code_type="NTIS001")
    projects = await c.search_projects(query="메타버스")

    # ── 용어 정의 검증 ──
    assert terms["total_hits"] == 4
    term_words = {t["korean"] for t in terms["items"]}
    assert "메타버스" in term_words
    assert "디지털트윈" in term_words
    assert "확장현실" in term_words

    metaverse_term = next(t for t in terms["items"] if t["korean"] == "메타버스")
    assert "3차원" in metaverse_term["definition"] or "가상공간" in metaverse_term["definition"]

    xr_term = next(t for t in terms["items"] if t["korean"] == "확장현실")
    assert xr_term["abbreviation"] == "XR"
    assert "VR" in xr_term["definition"] and "AR" in xr_term["definition"]

    # ── 분류코드 계층 탐색 ──
    codes_by_code = {item["code"]: item for item in codes["items"]}
    assert "060000" in codes_by_code  # 정보통신 대분류
    assert "060210" in codes_by_code  # VR/AR 중분류
    assert "060211" in codes_by_code  # 메타버스플랫폼 소분류

    # 계층 구조 검증
    assert codes_by_code["060210"]["parent_code"] == "060200"
    assert codes_by_code["060211"]["parent_code"] == "060210"

    # ── 메타버스 과제 분석 ──
    assert projects["total_hits"] == 645
    for pjt in projects["items"]:
        assert pjt["science_class"][0]["small"]["code"] == "060211"  # 정확한 분류 매핑

    # 사업명 확인
    budget_projects = {pjt["budget_project"] for pjt in projects["items"]}
    assert "메타버스서비스원천기술개발" in budget_projects

    print("\n[S4] 메타버스 지식체계 → 과제 발굴 체인 완료")
    print(f"  관련 표준용어 {terms['total_hits']}건:")
    for t in terms["items"]:
        abbr = f" ({t['abbreviation']})" if t["abbreviation"] else ""
        print(f"    {t['korean']}{abbr}: {t['definition'][:40]}...")
    print(f"  분류코드 탐색: 060000→060200→060210→060211 (메타버스플랫폼)")
    print(f"  관련 과제 {projects['total_hits']}건 | 샘플:")
    for pjt in projects["items"]:
        print(f"    [{pjt['id']}] {pjt['title_kor']}")
        print(f"      수행: {pjt['perform_agent']['name']} | 정부출연: {int(pjt['government_funds']):,}천원")


# ═══════════════════════════════════════════════════════════════════════════════
# 시나리오 S5: 의료AI 이슈 탐지 → 보건의료 + 산업기술 이중 분류추천 비교
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_s5_medical_ai_dual_classification():
    """S5: 의료AI 트렌드 이슈 파악 → 보건의료분류 + 산업기술분류 동시 추천 비교.

    LLM 시나리오: "AI 의료진단 R&D 과제를 등록하려는데,
    현재 트렌드 파악하고, 보건의료기술분류와 산업기술분류 코드 둘 다 추천받아줘"
    """
    inject(ISSUE_RND_URL, {"apprvKey": API_KEY, "SRWR": "AI 의료진단"}, AI_HEALTH_ISSUE_XML)

    ht_params = _rcmn_params("rcmnhtcls", text=AI_HEALTH_RESEARCH_TEXT)
    it_params = _rcmn_params("rcmnitcls", text=AI_HEALTH_RESEARCH_TEXT)
    inject(RCMNCLS_URL, ht_params, HT_CLS_XML)
    inject(RCMNCLS_URL, it_params, IT_CLS_XML)

    c = client()
    issues = await c.search_rnd_issues(query="AI 의료진단")
    ht_cls = await c.recommend_ht_classification(text=AI_HEALTH_RESEARCH_TEXT)
    it_cls = await c.recommend_it_classification(text=AI_HEALTH_RESEARCH_TEXT)

    # ── 트렌드 이슈 ──
    assert len(issues["items"]) == 2
    issue_names = [i["name"] for i in issues["items"]]
    assert "AI 의료진단 정확도 혁신" in issue_names

    ai_health_issue = issues["items"][0]
    assert int(ai_health_issue["related_project_count"]) > 3000
    assert "인공지능" in ai_health_issue["related_keywords"]
    assert ai_health_issue["has_image"] is True

    # ── 보건의료기술분류 추천 ──
    assert ht_cls["result_code"] == "00"
    assert len(ht_cls["disease_classification"]) == 3  # 질환별
    assert len(ht_cls["research_output_classification"]) == 3  # 연구행위별

    # 최상위 질환 분류: 종양(암) 87.3%
    top_disease = ht_cls["disease_classification"][0]
    assert top_disease["large_name"] == "종양"
    assert float(top_disease["accuracy"]) > 80

    # 최상위 연구행위 분류: 영상진단 91.5%
    top_output = ht_cls["research_output_classification"][0]
    assert top_output["medium_name"] == "영상진단"
    assert float(top_output["accuracy"]) > 90

    # ── 산업기술분류 추천 ──
    assert it_cls["result_code"] == "00"
    assert len(it_cls["recommendations"]) == 3

    top_it = it_cls["recommendations"][0]
    assert top_it["large_name"] == "정보통신"
    assert "AI" in top_it["small_name"] or "빅데이터" in top_it["small_name"]
    assert float(top_it["accuracy"]) > 85

    # ── 두 분류체계 비교 분석 ──
    ht_top_accuracy = float(ht_cls["research_output_classification"][0]["accuracy"])
    it_top_accuracy = float(it_cls["recommendations"][0]["accuracy"])
    # 두 체계 모두 높은 신뢰도
    assert ht_top_accuracy > 85 and it_top_accuracy > 85

    print("\n[S5] 의료AI 이중 분류추천 비교 완료")
    print(f"  트렌드 이슈: '{ai_health_issue['name']}' (연관과제 {ai_health_issue['related_project_count']}건)")
    print(f"  트렌드 키워드: {', '.join(ai_health_issue['related_keywords'])}")
    print()
    print("  [보건의료기술분류] 질환별:")
    for r in ht_cls["disease_classification"]:
        print(f"    {r['rank']}위: {r['large_name']} > {r['medium_name']} ({r['accuracy']}%)")
    print("  [보건의료기술분류] 연구행위별:")
    for r in ht_cls["research_output_classification"]:
        print(f"    {r['rank']}위: {r['large_name']} > {r['medium_name']} ({r['accuracy']}%)")
    print()
    print("  [산업기술분류]:")
    for r in it_cls["recommendations"]:
        print(f"    {r['rank']}위: {r['large_name']} > {r['medium_name']} > {r['small_name']} ({r['accuracy']}%)")
