---
title: "IB · 운용사 관심 섹터 1~10위 트렌드 시드"
version: "0.1"
created_at: "2026-07-08"
source_seed: "seed_articles_2026.md"
purpose: "Trend Intelligence Memory System / Sector Trend Observatory MVP의 초기 knowledge seed"
status: "draft"
---

# IB · 운용사 관심 섹터 1~10위 트렌드 시드

## 0. 문서 목적

이 문서는 `seed_articles_2026.md`에 포함된 2026년 이후 Goldman Sachs, J.P. Morgan, Morgan Stanley, BlackRock BII, Jefferies, McKinsey 공개 인사이트 기사 목록을 바탕으로, 이전 분석에서 도출한 **최근 IB / 운용사 관심 섹터 1~10위**를 MVP 개발용 시드 지식으로 정리한 것이다.

1. 반복 수집 대상 기사에서 어떤 **섹터, 컨셉, 주장, 동향, 숫자, 이미지/표 근거**를 추출해야 하는지 정의한다.
2. 향후 MVP가 기사 단위 요약이 아니라 **핵심 지식 항목 단위**로 트렌드를 축적할 수 있도록 초기 taxonomy를 제공한다.
3. 많이 언급되는 주제와 실제 중요도가 높은 주제를 구분할 수 있도록 **Mention Score**와 **Importance Score**의 판단 기준을 설계한다.
4. 이상 징후 감지를 위해 각 섹터별로 관찰해야 할 변곡점, 반대 신호, weak signal을 정의한다.

---

## 1. 입력 데이터 개요

`seed_articles_2026.md`는 2026년 1월 1일 이후 수집 대상 공개 기사 239건을 포함한다.

| 소스 | 건수 | 성격 |
|---|---:|---|
| Goldman Sachs | 29 | IB public insight, AI, 데이터센터, 에너지, private credit, 로봇 |
| J.P. Morgan | 76 | 글로벌 리서치, IB, 결제, 헬스케어, 부동산, 방산, 거시 |
| Morgan Stanley | 37 | thematic investing, AI, 에너지, 금융, GLP-1, 소비, 반도체 |
| BlackRock BII | 4 | 자산배분, 에너지 안보, 거시 리스크 |
| Jefferies | 43 | PE, 세컨더리, 에너지, AI, 소프트웨어, 산업재 |
| McKinsey | 50 | 산업별 구조 변화, AI, 데이터센터, 반도체, 배터리, 원전, 바이오 |

이 문서에서는 위 기사 목록을 기반으로 10개 관심 섹터를 정리하되, 각 섹터를 “투자 대상”이 아니라 **관찰 대상 트렌드 클러스터**로 정의한다.

---

## 2. 전체 우선순위 요약

| Rank | 섹터 클러스터 | 관찰 관점 | 핵심 질문 |
|---:|---|---|---|
| 1 | AI 인프라 / 데이터센터 / 전력 | AI CapEx의 물리 인프라 확산 | AI 수요가 데이터센터, 전력, 냉각, 금융 구조로 어떻게 확산되는가? |
| 2 | 전력망 / 에너지 안보 / 배터리 / 원전 | 전기화와 에너지 안정성 | 전력 부족이 산업 경쟁력과 투자 흐름을 어떻게 바꾸는가? |
| 3 | 반도체 / 메모리 / AI 컴퓨트 | AI compute bottleneck | GPU 이후 병목은 메모리, 패키징, inference cost 중 어디로 이동하는가? |
| 4 | AI 소프트웨어 / Agent / 생산성 전환 | 기업 운영모델의 AI화 | Copilot을 넘어 Agentic Operating Model로 이동하는가? |
| 5 | 프라이빗마켓 / 인프라 금융 / 세컨더리 | 자본 조달 구조 변화 | AI 인프라와 에너지 투자를 누가 장기 자본으로 뒷받침하는가? |
| 6 | 로봇 / Physical AI / 자율주행 | AI의 물리 세계 확장 | 로봇, 휴머노이드, 로보택시가 어떤 산업에서 먼저 확산되는가? |
| 7 | 헬스케어 / 바이오 / GLP-1 / AI R&D | 의료·바이오 혁신과 소비 파급 | GLP-1, AI R&D, 의료 생산성이 산업 전반에 어떤 파급을 주는가? |
| 8 | 방산 / 우주 / 조선 / 산업 리질리언스 | 지정학과 재산업화 | 국방비, 공급망, 조선, 우주가 산업 투자 테마로 확산되는가? |
| 9 | 금융 인프라 / 결제 / 디지털자산 | 금융 운영 인프라 재편 | 결제, 토큰화, embedded finance가 금융산업 구조를 어떻게 바꾸는가? |
| 10 | 소비 / 미디어 / 게임 / 프리미엄 여행 | 선택적 소비와 AI 콘텐츠 | 소비 둔화 속에서도 프리미엄·이벤트·AI 콘텐츠가 어디서 성장하는가? |

---

## 3. 공통 추출 스키마

각 기사에서 섹터별로 아래 객체를 추출한다.

```json
{
  "knowledge_item_id": "ki_YYYYMMDD_000001",
  "article_id": "source_date_slug",
  "item_type": "concept | claim | trend | metric | risk | weak_signal | counter_signal | visual_insight | sector_shift",
  "canonical_title": "",
  "summary": "",
  "core_concept": "",
  "claim": "",
  "trend_direction": "rising | falling | stable | mixed | uncertain",
  "time_horizon": "near_term | mid_term | long_term | structural",
  "primary_sector": "",
  "related_sectors": [],
  "themes": [],
  "entities": {
    "companies": [],
    "regions": [],
    "technologies": [],
    "asset_classes": []
  },
  "metrics": [
    {
      "metric_name": "",
      "value": null,
      "unit": "",
      "year": null,
      "region": "",
      "context": "forecast | historical | target | estimate"
    }
  ],
  "evidence": {
    "source_article_title": "",
    "source_url": "",
    "evidence_type": "text | table | chart | image | transcript",
    "evidence_summary": ""
  },
  "visual_assets": [],
  "tables": [],
  "mention_relevance_score": 0,
  "importance_evidence_score": 0,
  "novelty_score": 0,
  "anomaly_score": 0,
  "confidence_score": 0
}
```

---

# 1위. AI 인프라 / 데이터센터 / 전력

## 1.1 섹터 정의

AI 인프라 / 데이터센터 / 전력은 AI 모델 학습과 추론을 가능하게 하는 물리적·디지털 기반 시설 전체를 의미한다. 기존에는 GPU, 서버, 클라우드가 중심이었다면, 최근 IB·운용사 관심은 데이터센터 부지, 전력 접속, 냉각, 송전망, 발전원, 자본 조달, 데이터센터 운영 효율로 확산되고 있다.

이 섹터는 단순한 IT 인프라가 아니라 **AI 산업의 생산설비**로 보아야 한다.

## 1.2 핵심 컨셉

| 컨셉 | 설명 |
|---|---|
| AI CapEx Buildout | hyperscaler와 AI 기업의 대규모 인프라 투자 사이클 |
| Data Center Power Demand | 데이터센터 전력 수요의 구조적 증가 |
| AI Power Bottleneck | AI 확산의 병목이 컴퓨트에서 전력으로 이동하는 현상 |
| Grid Interconnection Delay | 데이터센터 신규 부지가 전력망 연결 지연으로 늦어지는 문제 |
| Cooling Constraint | 고밀도 AI 서버의 열관리, 수랭, CDU, 액침냉각 수요 증가 |
| Private Data Center Financing | 데이터센터 투자가 private markets, infra fund, private credit으로 확산 |
| Colocation Capacity Race | colocation 데이터센터 사업자의 AI 수요 대응 경쟁 |

## 1.3 핵심 주장 / 동향

- AI 인프라 투자는 GPU 구매를 넘어 데이터센터, 전력, 냉각, 송전망, 부동산, 장기 전력계약, 인프라 금융으로 확산되고 있다.
- 데이터센터의 병목은 “서버를 살 수 있느냐”에서 “전력을 제때 확보할 수 있느냐”로 이동하고 있다.
- 데이터센터 증설 계획은 발표보다 실제 가동까지 지연될 수 있으며, 지연 요인은 전력망 접속, 냉각, 인허가, 부지 확보, financing이다.
- AI 인프라의 수혜 범위는 반도체 기업뿐 아니라 전력기기, 냉각 솔루션, ESS, 원전, 부동산, 인프라 펀드로 확산된다.
- 아시아 데이터센터 시장은 AI 수요, 클라우드 확산, 데이터 주권, 전력 조달 역량에 따라 국가별 격차가 커질 수 있다.

## 1.4 대표 Seed Articles

| 날짜 | 소스 | 제목 | 관찰 포인트 |
|---|---|---|---|
| 2026-06-12 | Goldman Sachs | Private Markets Are Expected to Have a Growing Role in Data Center Financing | AI 데이터센터 투자와 private financing 연결 |
| 2026-06-10 | Goldman Sachs | The Outlook for Data Centers in Asia | 아시아 데이터센터 수요와 지역별 성장 |
| 2026-05-20 | Goldman Sachs | US Data Center Power Demand Projected to Double by 2027 | 데이터센터 전력 수요 증가 |
| 2026-05-01 | Goldman Sachs | Tracking Trillions: The Assumptions Shaping the Scale of the AI Build-Out | AI buildout 규모와 가정 |
| 2026-06-30 | McKinsey | Colocation data centers: The infrastructure race behind AI | colocation 데이터센터 인프라 경쟁 |
| 2026-02-12 | Jefferies | Data Centers Face Growing Policy Headwinds | 데이터센터 정책·규제 리스크 |
| 2026-06-27 | Morgan Stanley | The Race to Power the AI Economy | AI 경제를 뒷받침하는 전력 경쟁 |
| 2026-06-23 | BlackRock BII | Energy security in a world shaped | AI 전력 수요와 에너지 안보 |

## 1.5 MVP 추출 대상

```json
{
  "primary_sector": "AI Infrastructure / Data Center",
  "must_extract": [
    "data center capacity",
    "power demand forecast",
    "AI CapEx estimate",
    "grid connection delay",
    "cooling technology",
    "private financing structure",
    "regional capacity shift"
  ],
  "core_metrics": [
    "GW demand",
    "MW per campus",
    "capex amount",
    "data center capacity",
    "power usage effectiveness",
    "construction delay duration",
    "financing volume"
  ]
}
```

## 1.6 이상 징후 감지 규칙

| 이상 유형 | 감지 로직 |
|---|---|
| Mention Spike | `data center`, `AI power`, `grid`, `cooling` 언급이 30일 평균 대비 급증 |
| Source Migration | 전문 기술 매체에서 시작된 전력 병목 논의가 IB·운용사 리포트로 이동 |
| Cross-sector Spread | 데이터센터 이슈가 부동산, 에너지, private credit 기사로 확산 |
| Metric Divergence | 데이터센터 전력 수요 전망치가 소스별로 크게 다름 |
| Visual-only Signal | 본문보다 표·차트에서 데이터센터 수요 수치가 더 크게 제시됨 |

---

# 2위. 전력망 / 에너지 안보 / 배터리 / 원전

## 2.1 섹터 정의

전력망 / 에너지 안보 / 배터리 / 원전은 AI, 전기차, 산업 전기화, 제조 리쇼어링, 냉방 수요가 만들어내는 전력 수요 증가에 대응하는 인프라 섹터다. 이 섹터는 에너지 전환과 에너지 안보가 결합되는 영역이며, 최근에는 AI 데이터센터가 새로운 수요 동인으로 추가되었다.

## 2.2 핵심 컨셉

| 컨셉 | 설명 |
|---|---|
| Electrification Wave | 산업·교통·건물의 전기화 |
| Energy Security Premium | 지정학 불확실성 속 안정적 에너지 공급의 프리미엄 |
| Grid Modernization | 송전망·배전망 증설과 디지털화 |
| Utility-scale Battery | 전력망 안정화와 재생에너지 보완용 대형 ESS |
| Nuclear Renaissance | AI 전력 수요, 탈탄소, 에너지 안보가 원전 재평가로 연결 |
| Gas Bridge | 전력 수요 급증기에 LNG·가스발전이 과도기 역할을 하는 현상 |
| Power Equipment Shortage | 변압기, 스위치기어, 터빈, 케이블 등 전력 장비 병목 |

## 2.3 핵심 주장 / 동향

- AI 데이터센터와 전기화는 전력 수요 성장률을 구조적으로 높이고 있다.
- 전력망 투자 부족은 AI 인프라 확장의 핵심 제약으로 부상하고 있다.
- 에너지 안보 관점에서 원전, LNG, 재생에너지, ESS가 모두 재평가되고 있다.
- 배터리는 EV 전용 성장 테마에서 grid storage와 데이터센터 안정성 테마로 확장되고 있다.
- 아시아와 유럽은 에너지 전환, 산업정책, 전력 가격 경쟁력이 복합적으로 작동한다.

## 2.4 대표 Seed Articles

| 날짜 | 소스 | 제목 | 관찰 포인트 |
|---|---|---|---|
| 2026-06-27 | Morgan Stanley | The Race to Power the AI Economy | AI 경제와 전력 수요 |
| 2026-06-16 | Morgan Stanley | Energy: Transitioning to Resilience | 에너지 전환의 초점이 resilience로 이동 |
| 2026-06-12 | Morgan Stanley | Asia’s Energy Buildout Gains Momentum | 아시아 에너지 인프라 투자 |
| 2026-05-05 | Goldman Sachs | The Energy Crunch Could Accelerate Europe’s Shift to Electrification | 유럽 에너지 병목과 전기화 |
| 2026-04-10 | J.P. Morgan | Energy outlook 2026: Mitigating volatility with a diverse energy mix | 다원화된 에너지 믹스 |
| 2026-05-04 | Jefferies | Five Trends Shaping the Future of Power and Utilities | 전력·유틸리티 핵심 트렌드 |
| 2026-06-30 | McKinsey | Batteries: Scaling the engine of electrification | 배터리와 전기화 |
| 2026-06-30 | McKinsey | Nuclear power: A renaissance in the making | 원전 재부상 |

## 2.5 MVP 추출 대상

```json
{
  "primary_sector": "Power Grid / Energy Security / Battery / Nuclear",
  "must_extract": [
    "power demand growth",
    "grid investment",
    "battery storage capacity",
    "nuclear capacity outlook",
    "energy security claim",
    "power equipment bottleneck",
    "regional energy capex"
  ],
  "core_metrics": [
    "electricity demand CAGR",
    "grid capex",
    "battery TWh demand",
    "nuclear GW capacity",
    "energy price index",
    "interconnection queue duration"
  ]
}
```

## 2.6 이상 징후 감지 규칙

| 이상 유형 | 감지 로직 |
|---|---|
| Silent Risk | 전력 수요·grid delay 숫자는 커지는데 기사 언급은 적음 |
| Sector Shift | AI 기사보다 에너지·유틸리티 기사에서 데이터센터 언급 증가 |
| Policy Shock | 원전, LNG, 송전망, ESS 관련 정부 예산·규제 변화 등장 |
| Metric Breakout | 배터리/원전/전력망 수요 전망이 기존 추세를 벗어남 |
| Counter Signal | 재생에너지 또는 원전 투자에 대한 비용·인허가 회의론 증가 |

---

# 3위. 반도체 / 메모리 / AI 컴퓨트

## 3.1 섹터 정의

반도체 / 메모리 / AI 컴퓨트는 AI 모델의 학습과 추론을 수행하는 칩, 메모리, 패키징, 네트워크, 광연결, 반도체 장비·소재까지 포함하는 클러스터다. 최근 관심은 GPU 자체에서 HBM, advanced packaging, inference cost, custom silicon, co-packaged optics로 확산되고 있다.

## 3.2 핵심 컨셉

| 컨셉 | 설명 |
|---|---|
| Compute as New Economy | compute capacity가 경제 성장의 핵심 생산요소로 부상 |
| Memory Wall | AI 성능 병목이 연산보다 메모리 대역폭으로 이동 |
| HBM Cycle | AI 서버 수요와 고대역폭 메모리 수요의 연결 |
| Advanced Packaging Constraint | CoWoS, 2.5D/3D packaging, interposer 병목 |
| Inference Cost Compression | 추론 비용을 낮추기 위한 칩·모델·시스템 최적화 |
| Custom Silicon | hyperscaler의 자체 AI accelerator 개발 |
| Co-packaged Optics | 데이터센터 내부 연결 병목 해소를 위한 광연결 기술 |

## 3.3 핵심 주장 / 동향

- AI 반도체 투자 논의는 GPU 공급 부족을 넘어 메모리, 패키징, 네트워크, 전력효율로 이동하고 있다.
- 학습보다 추론 사용량이 커질수록 inference cost와 전력 효율이 핵심 경쟁력이 된다.
- HBM, advanced packaging, custom silicon은 AI CapEx의 다음 수혜 영역이다.
- 반도체 공급망은 기술 병목뿐 아니라 지정학, 수출통제, 리쇼어링, 전략적 공급망 재편의 영향을 받는다.
- 한국은 메모리와 패키징 생태계 관점에서 이 클러스터와 직접 연결된다.

## 3.4 대표 Seed Articles

| 날짜 | 소스 | 제목 | 관찰 포인트 |
|---|---|---|---|
| 2026-05-22 | Goldman Sachs | How Hedge Funds Are Trading Semiconductor Stocks | 헤지펀드의 반도체 포지셔닝 |
| 2026-03-20 | Morgan Stanley | The EDGE: Semiconductor Supercycle — Fact or Fiction? | 반도체 슈퍼사이클 논쟁 |
| 2026-03-17 | Morgan Stanley | Jensen Huang: Compute Is the New Economy | compute의 경제적 의미 |
| 2026-06-30 | McKinsey | Semiconductors: Etching the new map of strategic supply | 반도체 전략 공급망 |
| 2026-06-25 | McKinsey | Frontiers of compute: The technologies to reduce AI inference costs | inference cost 절감 기술 |
| 2026-02-10 | Jefferies | Is the AI Investment Cycle Shifting Toward Memory Suppliers? | AI 투자 사이클의 메모리 이동 |

## 3.5 MVP 추출 대상

```json
{
  "primary_sector": "Semiconductor / Memory / AI Compute",
  "must_extract": [
    "GPU demand",
    "HBM demand",
    "advanced packaging capacity",
    "inference cost",
    "custom silicon adoption",
    "semiconductor capex",
    "supply chain reshoring"
  ],
  "core_metrics": [
    "semiconductor market size",
    "AI accelerator revenue",
    "HBM bit demand",
    "packaging capacity",
    "inference cost per token",
    "capex amount"
  ]
}
```

## 3.6 이상 징후 감지 규칙

| 이상 유형 | 감지 로직 |
|---|---|
| Bottleneck Migration | GPU에서 HBM, 패키징, 광연결, 전력효율로 언급 이동 |
| Counter Signal | AI 반도체 과잉투자, 재고, ROI 회의론 증가 |
| Metric Divergence | AI 반도체 시장 규모 전망치가 소스별로 크게 차이 |
| Supply Shock | 수출통제, 지정학, 특정 장비·소재 병목 기사 등장 |
| Undercovered Importance | 기사 수는 적지만 수치 근거가 큰 패키징·광연결 신호 |

---

# 4위. AI 소프트웨어 / Agent / 생산성 전환

## 4.1 섹터 정의

AI 소프트웨어 / Agent / 생산성 전환은 기업이 AI를 단순 도구로 사용하는 수준을 넘어, 업무 프로세스, 제품, 고객경험, 운영모델을 AI 중심으로 재설계하는 영역이다. 이 섹터는 SaaS, IT Services, Agentic AI, AI coding, customer care AI, 금융 AI, enterprise knowledge system을 포함한다.

## 4.2 핵심 컨셉

| 컨셉 | 설명 |
|---|---|
| Agentic Operating Model | 여러 AI Agent가 업무 단위로 협업하는 운영모델 |
| AI-native Workflow | 기존 업무에 AI를 붙이는 것이 아니라 업무 자체를 재설계 |
| Copilot to Autonomous Agent | 보조형 AI에서 자율 실행형 AI로 이동 |
| Context as Moat | AI 성능의 차별화 요소가 모델보다 맥락·데이터·지식으로 이동 |
| AI Software Production System | 소프트웨어 개발 프로세스가 AI로 재편되는 현상 |
| IT Services Disruption | SI·IT 서비스 산업이 AI 자동화로 구조적 영향을 받는 현상 |
| AI ROI Proof | AI 투자 효과를 생산성, 매출, 비용, 품질로 검증해야 하는 압력 |

## 4.3 핵심 주장 / 동향

- AI 소프트웨어의 가치는 기능 탑재보다 업무 운영모델 전환에서 나온다.
- 기업은 단일 Copilot보다 업무 목적별 Agent Team으로 이동할 가능성이 높다.
- AI의 성과 차이는 기업 내부 데이터, knowledge structure, context engineering에서 발생한다.
- IT 서비스와 소프트웨어 개발은 AI disruption의 초기 사례가 될 가능성이 있다.
- AI 도입의 다음 과제는 생산성 향상이 아니라 매출, 고객경험, 운영 민첩성까지 확장하는 것이다.

## 4.4 대표 Seed Articles

| 날짜 | 소스 | 제목 | 관찰 포인트 |
|---|---|---|---|
| 2026-05-11 | Goldman Sachs | Will the Corporate Investment in AI Pay Off? | 기업 AI 투자 ROI |
| 2026-04-23 | Goldman Sachs | Cybersecurity Firms Show Software Industry How to Navigate AI | AI 시대 소프트웨어 산업 대응 |
| 2026-03-12 | J.P. Morgan | AI in Finance: From Copilot to Autonomous Agent | 금융 AI의 Agent 전환 |
| 2026-03-23 | Morgan Stanley | 4 Ways the AI Supercycle Is Changing How Companies Operate | AI supercycle과 기업 운영 변화 |
| 2026-06-16 | Jefferies | AI Is Disrupting the Entire Economy, Not Just the Tech Stack | AI가 기술 스택을 넘어 경제 전반 disrupt |
| 2026-05-21 | Jefferies | Why Context Is the Only Thing That Matters in AI | context 중심 AI 경쟁력 |
| 2026-03-12 | Jefferies | Is IT Services the First Real Example of AI Disruption? | IT 서비스 disruption |
| 2026-06-24 | McKinsey | AI-powered software development: How technology is rewriting the rules | AI coding과 SW 개발 변화 |
| 2026-06-24 | McKinsey | How KPN is building an agentic AI engine for customer care | 고객관리 Agentic AI |
| 2026-06-23 | McKinsey | Beyond productivity: How AI creates value in private equity | AI value creation |

## 4.5 MVP 추출 대상

```json
{
  "primary_sector": "AI Software / Agentic AI / Productivity Transformation",
  "must_extract": [
    "agentic AI use case",
    "workflow automation",
    "AI ROI metric",
    "software development productivity",
    "customer care automation",
    "context engineering",
    "IT services disruption"
  ],
  "core_metrics": [
    "productivity improvement",
    "cost reduction",
    "revenue uplift",
    "time saved",
    "developer productivity",
    "customer service resolution rate"
  ]
}
```

## 4.6 이상 징후 감지 규칙

| 이상 유형 | 감지 로직 |
|---|---|
| Claim Shift | AI ROI 회의론에서 AI value creation 사례로 주장 이동 |
| Source Migration | 기술 블로그의 Agent 논의가 IB·PE 리포트로 확산 |
| Counter Signal | AI 도입 실패, hallucination, 보안, privacy 리스크 언급 증가 |
| Sector Spread | AI Agent 논의가 금융, 헬스케어, 고객센터, 소프트웨어 개발로 확산 |
| New Concept | context engineering, AI operating model 같은 새 용어 등장 |

---

# 5위. 프라이빗마켓 / 인프라 금융 / 세컨더리

## 5.1 섹터 정의

프라이빗마켓 / 인프라 금융 / 세컨더리는 데이터센터, 에너지, 전력망, 부동산, 방산, 산업 인프라 등 대규모 장기 투자를 지원하는 자본 구조를 의미한다. AI 인프라 투자 규모가 커지면서 공모시장이나 기업 자체 현금흐름만으로 감당하기 어려워지고, private credit, infrastructure fund, secondaries, co-investment가 중요해지고 있다.

## 5.2 핵심 컨셉

| 컨셉 | 설명 |
|---|---|
| Private Credit Expansion | 은행 대출과 공모채를 대체/보완하는 private credit 성장 |
| Infrastructure Secondaries | 인프라 자산의 세컨더리 거래 증가 |
| Data Center Financing Gap | AI 데이터센터 투자 규모와 전통 금융의 조달 간극 |
| Co-investment Secondary | LP/GP가 유동성을 확보하는 세컨더리 구조 |
| Real Assets as Inflation Hedge | 인프라·부동산이 인플레이션 헤지 자산으로 재평가 |
| PE Value Creation with AI | PE 포트폴리오 기업에 AI를 적용해 가치 창출 |
| IPO Reopening | private growth 기업의 exit 환경 변화 |

## 5.3 핵심 주장 / 동향

- AI 데이터센터와 전력 인프라는 장기 자본을 필요로 하며 private markets의 역할이 커질 수 있다.
- 세컨더리 시장은 단순 유동성 수단에서 인프라 자산 재가격화와 포트폴리오 재조정 수단으로 확장되고 있다.
- private credit은 금리·유동성·스트레스 환경에서 성과와 리스크가 동시에 주목받는다.
- 데이터센터, 에너지, 유틸리티, 인프라 자산은 프라이빗마켓의 핵심 투자 테마로 이동하고 있다.
- AI는 PE 포트폴리오 value creation의 운영 도구가 되고 있다.

## 5.4 대표 Seed Articles

| 날짜 | 소스 | 제목 | 관찰 포인트 |
|---|---|---|---|
| 2026-06-12 | Goldman Sachs | Private Markets Are Expected to Have a Growing Role in Data Center Financing | 데이터센터와 private markets |
| 2026-03-26 | Goldman Sachs | The Outlook for Private Credit amid Rising Market Stress | private credit 리스크/기회 |
| 2026-02-12 | Goldman Sachs | Private Credit: The $2 Trillion Asset Class | private credit 자산군 |
| 2026-04-08 | J.P. Morgan | Private credit: Performance vs. liquidity | private credit 성과와 유동성 |
| 2026-06-17 | Jefferies | Private Equity’s New Liquidity Engine | PE 세컨더리 유동성 |
| 2026-06-09 | Jefferies | Infrastructure Secondaries Hit Their Stride | 인프라 세컨더리 성장 |
| 2026-05-20 | Jefferies | How Europe Became a Defining Force in the Global Secondary Market | 유럽 세컨더리 시장 |
| 2026-06-25 | McKinsey | Unlocking full potential: Five practices reshaping PE value creation | PE value creation |
| 2026-06-23 | McKinsey | Beyond productivity: How AI creates value in private equity | PE에서 AI 가치 창출 |

## 5.5 MVP 추출 대상

```json
{
  "primary_sector": "Private Markets / Infrastructure Finance / Secondaries",
  "must_extract": [
    "private credit volume",
    "infrastructure secondaries volume",
    "data center financing need",
    "co-investment trend",
    "PE value creation lever",
    "fundraising condition",
    "liquidity risk"
  ],
  "core_metrics": [
    "AUM",
    "fundraising volume",
    "transaction volume",
    "deal count",
    "default rate",
    "liquidity discount",
    "IRR"
  ]
}
```

## 5.6 이상 징후 감지 규칙

| 이상 유형 | 감지 로직 |
|---|---|
| Asset-class Shift | AI/데이터센터 논의가 equity에서 private credit/infra fund로 이동 |
| Liquidity Stress | private credit 성과 대비 유동성 리스크 언급 증가 |
| Secondary Spike | secondaries 거래량·기사 수 급증 |
| Undercovered Importance | 인프라 금융 규모는 큰데 기사 언급이 낮은 영역 |
| Counter Signal | default, refinancing, valuation markdown 관련 부정 신호 증가 |

---

# 6위. 로봇 / Physical AI / 자율주행

## 6.1 섹터 정의

로봇 / Physical AI / 자율주행은 AI가 소프트웨어 영역을 넘어 제조, 물류, 이동, 서비스, 국방 등 물리 세계에서 실행 능력을 갖추는 영역이다. 휴머노이드 로봇, 산업용 로봇, 물류 자동화, 로보택시, 자율주행 fleet, 센서·액추에이터·제어기 공급망을 포함한다.

## 6.2 핵심 컨셉

| 컨셉 | 설명 |
|---|---|
| Physical AI | AI가 물리 환경을 인식하고 행동하는 능력 |
| Humanoid Supply Chain | 휴머노이드 로봇 부품·모터·센서·제어 생태계 |
| Robotaxi Commercialization | 자율주행 택시의 상용화와 fleet 확장 |
| Embodied AI | AI가 신체 또는 장치를 통해 실행하는 형태 |
| Manufacturing Automation | 제조 공정의 로봇·AI 자동화 |
| Sensor-actuator Stack | 물리 AI 구현을 위한 센서, 액추에이터, 제어 계층 |
| Safety and Reliability Barrier | 물리 AI 상용화의 안전성·신뢰성 병목 |

## 6.3 핵심 주장 / 동향

- AI 모델 성능 개선은 로봇과 자율주행의 인식·계획·제어 능력 향상으로 연결된다.
- 휴머노이드 로봇은 단기적으로 범용 가정보다 제조·물류·특수 현장에서 먼저 확산될 가능성이 높다.
- 한국은 자동차 부품, 모터, 센서, 정밀제조 기반에서 휴머노이드 공급망 기회를 가질 수 있다.
- 로보택시는 규제, 안전성, fleet 운영비, 지도/센서 비용, 보험이 상용화 속도를 좌우한다.
- Physical AI는 AI 인프라와 달리 하드웨어 원가, 현장 reliability, 유지보수 체계가 중요하다.

## 6.4 대표 Seed Articles

| 날짜 | 소스 | 제목 | 관찰 포인트 |
|---|---|---|---|
| 2026-06-25 | Goldman Sachs | South Korea's Growing Role in Humanoid Robot Development | 한국 휴머노이드 로봇 공급망 |
| 2026-04-30 | Goldman Sachs | Robotaxis Are Forecast to Become a $400 Billion Market in 2035 | 로보택시 시장 전망 |
| 2026-06-24 | McKinsey | The age of thinking machines: Perspectives on the future of robotics | robotics와 Physical AI |
| 2026-04-23 | Goldman Sachs | When AI Learns How the World Works | world model과 물리 AI 가능성 |
| 2026-06-26 | J.P. Morgan | AI, defense and IPOs drive industrial innovation | AI와 산업 혁신 |

## 6.5 MVP 추출 대상

```json
{
  "primary_sector": "Robotics / Physical AI / Autonomous Mobility",
  "must_extract": [
    "humanoid robot forecast",
    "robotaxi market size",
    "physical AI use case",
    "sensor actuator supply chain",
    "manufacturing automation",
    "safety regulation",
    "fleet economics"
  ],
  "core_metrics": [
    "robot unit shipments",
    "market size",
    "fleet size",
    "cost per robot",
    "autonomous miles",
    "accident rate",
    "labor substitution potential"
  ]
}
```

## 6.6 이상 징후 감지 규칙

| 이상 유형 | 감지 로직 |
|---|---|
| Commercialization Spike | 로봇/로보택시 pilot에서 상용 fleet으로 언급 전환 |
| Korea Signal | 한국 공급망, 모터, 센서, 부품 관련 언급 증가 |
| Counter Signal | 사고, 규제, 비용, 안전성 리스크 증가 |
| Sector Spread | 제조·물류 외에 헬스케어, 리테일, 방산으로 적용 범위 확산 |
| Weak Signal | world model, embodied AI, physical foundation model 언급 증가 |

---

# 7위. 헬스케어 / 바이오 / GLP-1 / AI R&D

## 7.1 섹터 정의

헬스케어 / 바이오 / GLP-1 / AI R&D는 제약·바이오, 의료서비스, medtech, healthcare payment, obesity drug, AI 기반 신약개발을 포함한다. 최근 관심은 GLP-1 시장 확대와 바이오파마 R&D 생산성, 의료 노동력·비용 문제, cross-border M&A와 partnership으로 나뉜다.

## 7.2 핵심 컨셉

| 컨셉 | 설명 |
|---|---|
| GLP-1 Consumer Spillover | 비만 치료제가 식품, 웰니스, 보험, 리테일에 미치는 파급 |
| Biopharma R&D Productivity | 신약개발 생산성 개선 이슈 |
| AI-driven Drug Discovery | AI를 활용한 신약 후보 탐색과 임상 설계 |
| Healthcare Labor Productivity | 의료 인력 부족과 생산성 개선 |
| Medtech Deal Cycle | medtech와 biopharma M&A, partnership 회복 |
| Healthcare Payment Infrastructure | 의료 결제·보험 지급·working capital 개선 |
| Women’s Health Gap | 여성 건강 격차 해소와 경제적 기회 |

## 7.3 핵심 주장 / 동향

- GLP-1은 제약 시장뿐 아니라 소비재, 식품, 피트니스, 보험, 헬스케어 서비스에 구조적 영향을 줄 수 있다.
- 바이오파마 R&D는 AI와 데이터 기반 실험 설계로 효율화 가능성이 커지고 있다.
- 의료서비스는 인력 부족, 비용 압력, payment complexity를 해결하기 위한 디지털·AI 도입이 필요하다.
- biopharma와 medtech는 금리, 규제, 임상 리스크에도 불구하고 M&A와 partnership 회복 가능성이 있다.
- 헬스케어의 미래는 약물 혁신, care delivery, payment infrastructure가 함께 변화하는 방향이다.

## 7.4 대표 Seed Articles

| 날짜 | 소스 | 제목 | 관찰 포인트 |
|---|---|---|---|
| 2026-06-27 | J.P. Morgan | Healthcare markets outlook: A “dynamic” landscape ripe for M&A deals and cross-border partnerships | 헬스케어 M&A와 partnership |
| 2026-04-16 | J.P. Morgan | Biopharma and medtech activity in Q1 2026 | 바이오파마·medtech deal activity |
| 2026-06-05 | J.P. Morgan | Turning liquidity challenges into growth for the healthcare industry | 헬스케어 working capital |
| 2026-05-09 | Morgan Stanley | Obesity Drugs Are Scaling Fast | obesity drug 시장 확대 |
| 2026-03-08 | Morgan Stanley | GLP-1 Drugs: Transforming Healthcare and Consumer Industries | GLP-1의 산업 파급 |
| 2026-06-30 | McKinsey | Biopharma R&D: The evolving formula for discovery and development | 바이오파마 R&D 변화 |
| 2026-06-29 | McKinsey | From linear gates to learning loops: Rewiring biopharma R&D with AI | AI 기반 바이오파마 R&D |
| 2026-07-02 | McKinsey | The real future of work in healthcare | 의료 업무의 미래 |
| 2026-07-01 | McKinsey | Closing the women’s health gap | women’s health opportunity |

## 7.5 MVP 추출 대상

```json
{
  "primary_sector": "Healthcare / Biopharma / GLP-1 / AI R&D",
  "must_extract": [
    "GLP-1 market forecast",
    "consumer spillover",
    "biopharma R&D productivity",
    "AI drug discovery",
    "healthcare M&A",
    "medtech activity",
    "healthcare labor shortage"
  ],
  "core_metrics": [
    "drug market size",
    "patient count",
    "R&D cycle time",
    "clinical success rate",
    "deal volume",
    "healthcare labor shortage",
    "cost reduction"
  ]
}
```

## 7.6 이상 징후 감지 규칙

| 이상 유형 | 감지 로직 |
|---|---|
| Spillover Signal | GLP-1이 헬스케어 외 소비재·보험·리테일 기사에 등장 |
| Deal Cycle Shift | biopharma/medtech M&A, cross-border partnership 언급 증가 |
| Counter Signal | GLP-1 부작용, 가격, 보험 적용 제한, 특허 리스크 증가 |
| AI R&D Breakout | AI 신약개발의 임상 성공, cycle time 단축 근거 등장 |
| Metric Divergence | GLP-1 시장 규모 전망이 소스별로 크게 다름 |

---

# 8위. 방산 / 우주 / 조선 / 산업 리질리언스

## 8.1 섹터 정의

방산 / 우주 / 조선 / 산업 리질리언스는 지정학, 국방비 증가, 공급망 재편, 산업정책, 제조 역량 회복을 배경으로 부상하는 클러스터다. AI와 로봇, 우주, 사이버, 조선, 항공방산, critical manufacturing이 함께 연결된다.

## 8.2 핵심 컨셉

| 컨셉 | 설명 |
|---|---|
| Defense Reindustrialization | 국방비 증가가 제조·조선·항공·전자산업 투자로 확산 |
| Space Economy | 위성, 우주통신, 방산, 우주 태양광 등 우주 관련 경제 |
| Shipbuilding Revival | 미국 및 동맹국의 조선업 재건 논의 |
| Resilience Boom | 공급망·안보·에너지 리스크에 대응하는 산업 리질리언스 투자 |
| Dual-use Technology | 민간·군사용 양쪽에 쓰이는 AI, 로봇, 센서, 우주 기술 |
| Friendshoring | 지정학적 동맹 기반 공급망 재편 |
| Industrial Innovation IPO | AI·방산·산업재 기업의 IPO/M&A 가능성 |

## 8.3 핵심 주장 / 동향

- 지정학적 긴장은 방산비 증가와 공급망 재편을 통해 산업 투자 테마로 전환되고 있다.
- 조선, 항공, 우주, 방산 전자, 사이버, AI는 국가 안보와 산업 경쟁력이 결합되는 영역이다.
- 우주경제는 방산, 통신, 관측, 에너지, 데이터 인프라와 연결될 수 있다.
- 산업 리질리언스는 단순 비용 효율보다 안정성, redundancy, sovereign capacity를 중시한다.
- 방산·우주·조선 테마는 정치·예산·규제에 민감하므로 정책 데이터와 함께 추적해야 한다.

## 8.4 대표 Seed Articles

| 날짜 | 소스 | 제목 | 관찰 포인트 |
|---|---|---|---|
| 2026-07-01 | J.P. Morgan | Turning the tide: Revitalizing the US shipbuilding industry | 미국 조선업 재건 |
| 2026-06-26 | J.P. Morgan | AI, defense and IPOs drive industrial innovation | AI, 방산, IPO와 산업혁신 |
| 2026-06-24 | J.P. Morgan | The final frontier: How solar power and defense spending are propelling the space economy | 우주경제와 방산비 |
| 2026-04-11 | J.P. Morgan | A balancing act: The trade-off between debt and defense | 재정과 국방비 균형 |
| 2026-05-11 | Jefferies | Amid Aerospace & Defense Boom, Investors Continue to See Opportunities in Business Aviation | 항공방산 boom |
| 2026-05-20 | Morgan Stanley | Investing in the Resilience Boom | resilience boom |
| 2026-06-03 | Morgan Stanley | Geopolitical Shifts: Rewiring Global Trade | 글로벌 무역 재편 |
| 2026-06-25 | McKinsey | How companies can strengthen their geopolitical risk readiness | 기업 지정학 리스크 대응 |

## 8.5 MVP 추출 대상

```json
{
  "primary_sector": "Defense / Space / Shipbuilding / Industrial Resilience",
  "must_extract": [
    "defense spending",
    "shipbuilding capacity",
    "space economy",
    "geopolitical risk",
    "supply chain rewiring",
    "friendshoring",
    "dual-use AI"
  ],
  "core_metrics": [
    "defense budget",
    "shipbuilding backlog",
    "satellite launch count",
    "space market size",
    "reshoring investment",
    "supply chain concentration"
  ]
}
```

## 8.6 이상 징후 감지 규칙

| 이상 유형 | 감지 로직 |
|---|---|
| Policy Budget Spike | 국방비, 조선 보조금, 우주 예산 관련 숫자 급증 |
| Sector Coupling | AI·로봇·방산·조선이 같은 기사에서 함께 등장 |
| Geography Shift | 미국 중심 논의가 유럽, 한국, 일본, 중동으로 확산 |
| Counter Signal | 재정 부담, 정치 반대, 프로젝트 지연 리스크 증가 |
| Weak Signal | 우주 태양광, dual-use robotics, autonomous defense system 언급 증가 |

---

# 9위. 금융 인프라 / 결제 / 디지털자산

## 9.1 섹터 정의

금융 인프라 / 결제 / 디지털자산은 금융기관과 기업의 결제, treasury, liquidity, embedded finance, virtual card, tokenization, blockchain, digital asset custody를 포함한다. 이 섹터는 전통 금융업의 수익성보다 금융 운영 인프라의 재편에 초점을 둔다.

## 9.2 핵심 컨셉

| 컨셉 | 설명 |
|---|---|
| Payments Intelligence | 결제 데이터와 AI를 활용한 commerce advantage |
| Embedded Finance | 비금융 서비스 안에 금융 기능을 내재화 |
| Virtual B2B Cards | B2B 결제의 디지털 카드화 |
| Treasury Transformation | 기업 자금관리의 디지털·자동화 전환 |
| Institutional Blockchain | 기관금융의 블록체인·토큰화 도입 |
| Digital Asset Banking | 은행의 디지털자산 기회와 위협 |
| Account Takeover Defense | AI 시대 금융 보안과 fraud 방어 |

## 9.3 핵심 주장 / 동향

- 결제 스택은 단순 비용센터가 아니라 고객 데이터, 상거래 인사이트, 운영 효율의 원천이 되고 있다.
- embedded finance와 API 기반 금융은 SME, healthcare, commerce에서 금융 접근성을 높인다.
- 기관용 블록체인과 디지털자산은 투기자산보다 settlement, custody, tokenization 인프라 관점으로 이동하고 있다.
- AI와 사이버 리스크가 결합되면서 금융 보안, fraud detection, account takeover 방지가 중요해지고 있다.
- 기업 treasury는 멀티통화, 유동성, collateral, 실시간 결제 관리 방향으로 고도화된다.

## 9.4 대표 Seed Articles

| 날짜 | 소스 | 제목 | 관찰 포인트 |
|---|---|---|---|
| 2026-06-30 | J.P. Morgan | The biggest commerce advantage is hiding in your payment stack | 결제 스택과 commerce advantage |
| 2026-04-24 | J.P. Morgan | Payments Outlook: Five shifts powering payments | 결제 산업 변화 |
| 2026-03-31 | J.P. Morgan | Virtual cards: The future of B2B payments | B2B virtual card |
| 2026-05-20 | J.P. Morgan | BILL gives small and midsize businesses access to credit in minutes with Embedded Finance | embedded finance |
| 2026-06-03 | J.P. Morgan | Convergence in motion: Inside the institutional blockchain shift | 기관 블록체인 전환 |
| 2026-06-05 | Morgan Stanley | Banks Evaluate Opportunity—and Threat—of Digital Assets | 은행과 디지털자산 |
| 2026-06-24 | Morgan Stanley | How AI, Capital Deployment and Consumer Resilience Are Reshaping Finance | 금융산업 재편 |
| 2026-06-23 | McKinsey | Five client-led shifts reshaping European wealth management | wealth management 변화 |

## 9.5 MVP 추출 대상

```json
{
  "primary_sector": "Financial Infrastructure / Payments / Digital Assets",
  "must_extract": [
    "payments modernization",
    "embedded finance",
    "B2B virtual card",
    "institutional blockchain",
    "digital asset custody",
    "treasury transformation",
    "fraud detection"
  ],
  "core_metrics": [
    "payment volume",
    "transaction cost",
    "fraud loss",
    "settlement time",
    "digital asset AUM",
    "embedded finance credit volume"
  ]
}
```

## 9.6 이상 징후 감지 규칙

| 이상 유형 | 감지 로직 |
|---|---|
| Institutional Adoption | 디지털자산/블록체인 논의가 retail에서 institutional로 이동 |
| Fraud Spike | AI 관련 fraud, account takeover, ransomware 결제 리스크 증가 |
| Sector Spread | 결제 인프라가 healthcare, commerce, travel, SME 기사로 확산 |
| Counter Signal | 디지털자산 규제, custody 사고, bank risk 언급 증가 |
| New Concept | payment stack intelligence, programmable treasury 같은 개념 등장 |

---

# 10위. 소비 / 미디어 / 게임 / 프리미엄 여행

## 10.1 섹터 정의

소비 / 미디어 / 게임 / 프리미엄 여행은 전체 소비 둔화 환경에서도 특정 세그먼트에서 선택적으로 성장하는 테마를 다룬다. 여기에는 프리미엄 카드·여행, 월드컵 이벤트, 미디어 M&A, AI 게임, 럭셔리 회복/둔화, 반려동물 소비, consumer tech renaissance가 포함된다.

## 10.2 핵심 컨셉

| 컨셉 | 설명 |
|---|---|
| Selective Consumer Spending | 소비자가 전체 지출을 줄이면서도 특정 경험·프리미엄 영역에는 지출 |
| Premium Travel Rewards | 프리미엄 카드와 여행 리워드의 성장 |
| Event-driven Commerce | 월드컵 등 글로벌 이벤트가 미디어·음료·결제·여행 소비를 자극 |
| AI + Gaming Profit Pool | AI가 게임 제작, 운영, 수익화에 미치는 영향 |
| Media Consolidation | 스트리밍·미디어 기업 간 M&A와 통합 |
| Luxury Caution | 럭셔리 시장의 회복 지연 또는 신중한 소비 |
| Consumer Tech Renaissance | AI와 플랫폼 변화에 따른 소비자 기술 서비스 재부상 |

## 10.3 핵심 주장 / 동향

- 소비 환경은 균일하게 성장하거나 둔화하지 않고, 프리미엄 경험·이벤트·AI 콘텐츠 중심으로 선택적 성장이 나타난다.
- 월드컵 같은 글로벌 이벤트는 미디어, 음료, 결제, 여행, 광고 시장에 단기 수요를 만든다.
- AI는 게임 제작비, 콘텐츠 생산, 개인화, 운영 효율에 영향을 줄 수 있다.
- 럭셔리와 반려동물 소비는 소비자 심리와 소득 양극화의 민감한 지표가 된다.
- 미디어 산업은 M&A, IP, 스포츠 이벤트, 광고 수익모델 재편 관점에서 관찰해야 한다.

## 10.4 대표 Seed Articles

| 날짜 | 소스 | 제목 | 관찰 포인트 |
|---|---|---|---|
| 2026-06-17 | J.P. Morgan | Are we there yet? Five trends shaping summer travel in 2026 | 여름 여행 수요 |
| 2026-06-05 | J.P. Morgan | Beyond the stadium: Where fans go, spend follows | 스포츠 이벤트와 소비 |
| 2026-05-26 | J.P. Morgan | The Paramount-Warner Bros. merger | 미디어 M&A |
| 2026-06-19 | Morgan Stanley | Travel Rewards Fuel Growth of Premium Credit Cards | 프리미엄 카드·여행 리워드 |
| 2026-06-16 | Morgan Stanley | Media and Beverages Score at World Cup | 월드컵, 미디어, 음료 |
| 2026-05-20 | Morgan Stanley | The $22 Billion Profit Opportunity in AI + Gaming | AI와 게임 이익 기회 |
| 2026-05-09 | Morgan Stanley | Luxury Outlook: From Contraction to Caution | 럭셔리 소비 전망 |
| 2026-06-27 | Morgan Stanley | Pet Owners Tighten the Leash on Spending | 반려동물 소비 둔화 |
| 2026-05-21 | Jefferies | Anish Acharya on the Consumer Tech Renaissance and a YouTube Moment for Software | consumer tech renaissance |
| 2026-07-01 | McKinsey | Lights, camera, algorithm: How AI is rewriting the rules of film and TV | AI와 영화·TV |

## 10.5 MVP 추출 대상

```json
{
  "primary_sector": "Consumer / Media / Gaming / Premium Travel",
  "must_extract": [
    "premium travel demand",
    "event-driven spending",
    "AI gaming profit pool",
    "media M&A",
    "luxury outlook",
    "consumer sentiment",
    "selective spending"
  ],
  "core_metrics": [
    "travel spend",
    "card spend",
    "media revenue",
    "gaming profit pool",
    "luxury sales growth",
    "event attendance",
    "advertising revenue"
  ]
}
```

## 10.6 이상 징후 감지 규칙

| 이상 유형 | 감지 로직 |
|---|---|
| Selective Rebound | 전체 소비 둔화 속 프리미엄 여행·이벤트 소비 증가 |
| AI Content Shift | AI가 게임, 영화, TV 제작 경제성에 미치는 영향 언급 증가 |
| Event Spike | 월드컵 등 이벤트 전후 미디어·음료·결제 기사 급증 |
| Counter Signal | 럭셔리, 반려동물, 여행 지출 둔화 신호 증가 |
| Sector Coupling | 미디어·게임·결제·광고가 같은 기사에서 연결 |

---

# 11. 섹터 간 관계 지도

## 11.1 핵심 연결 구조

```text
AI Infrastructure / Data Center
  ├─ Power Grid / Energy Security
  ├─ Semiconductor / Memory / AI Compute
  ├─ Private Markets / Infrastructure Finance
  ├─ Cooling / HVAC / ESS
  └─ AI Software / Agentic Operations

Power Grid / Energy
  ├─ Battery / ESS
  ├─ Nuclear
  ├─ LNG / Gas Bridge
  ├─ Data Center Power
  └─ Industrial Resilience

AI Software / Agentic AI
  ├─ Financial Infrastructure
  ├─ Healthcare Productivity
  ├─ Software Development
  ├─ Customer Care
  └─ PE Value Creation

Physical AI / Robotics
  ├─ Semiconductor / Sensors
  ├─ Industrial Automation
  ├─ Defense
  ├─ Autonomous Mobility
  └─ Manufacturing Resilience
```

## 11.2 특히 중요한 교차 컨셉

| 교차 컨셉 | 연결 섹터 | 관찰 의미 |
|---|---|---|
| AI Power Bottleneck | AI 인프라, 전력망, 에너지, 데이터센터 금융 | AI 성장이 전력 투자로 전이 |
| Inference Cost Compression | 반도체, AI 소프트웨어, 데이터센터 | AI 사용량 증가의 경제성 병목 |
| Agentic Operating Model | AI 소프트웨어, 금융, 헬스케어, PE | 기업 업무 구조 변화 |
| Resilience Boom | 에너지, 방산, 조선, 공급망, 인프라 | 효율성보다 안정성 중시 |
| Private Infrastructure Financing | 데이터센터, 전력망, private credit | 자본 조달 구조 변화 |
| GLP-1 Consumer Spillover | 헬스케어, 소비, 보험, 리테일 | 약물이 소비 구조에 미치는 영향 |
| Physical AI | 로봇, 제조, 방산, 반도체 | AI가 물리 실행력으로 확장 |

---

# 12. MVP 초기 Taxonomy 제안

## 12.1 Sector Taxonomy

```yaml
sectors:
  - id: ai_infrastructure_data_center
    name: "AI Infrastructure / Data Center"
    rank_seed: 1
  - id: power_grid_energy_security
    name: "Power Grid / Energy Security / Battery / Nuclear"
    rank_seed: 2
  - id: semiconductor_ai_compute
    name: "Semiconductor / Memory / AI Compute"
    rank_seed: 3
  - id: ai_software_agentic_ai
    name: "AI Software / Agentic AI / Productivity Transformation"
    rank_seed: 4
  - id: private_markets_infra_finance
    name: "Private Markets / Infrastructure Finance / Secondaries"
    rank_seed: 5
  - id: robotics_physical_ai_autonomy
    name: "Robotics / Physical AI / Autonomous Mobility"
    rank_seed: 6
  - id: healthcare_biopharma_glp1
    name: "Healthcare / Biopharma / GLP-1 / AI R&D"
    rank_seed: 7
  - id: defense_space_shipbuilding_resilience
    name: "Defense / Space / Shipbuilding / Industrial Resilience"
    rank_seed: 8
  - id: financial_infrastructure_payments
    name: "Financial Infrastructure / Payments / Digital Assets"
    rank_seed: 9
  - id: consumer_media_gaming_travel
    name: "Consumer / Media / Gaming / Premium Travel"
    rank_seed: 10
```

## 12.2 Concept Taxonomy

```yaml
concepts:
  - AI Power Bottleneck
  - Data Center Financing Gap
  - Grid Interconnection Delay
  - Cooling Constraint
  - AI CapEx Spillover
  - Electrification Wave
  - Energy Security Premium
  - Nuclear Renaissance
  - Memory Wall
  - HBM Cycle
  - Advanced Packaging Constraint
  - Inference Cost Compression
  - Agentic Operating Model
  - Context as Moat
  - IT Services Disruption
  - Private Credit Expansion
  - Infrastructure Secondaries
  - Physical AI
  - Humanoid Supply Chain
  - Robotaxi Commercialization
  - GLP-1 Consumer Spillover
  - AI-driven Drug Discovery
  - Defense Reindustrialization
  - Space Economy
  - Shipbuilding Revival
  - Payments Intelligence
  - Institutional Blockchain
  - Selective Consumer Spending
  - AI + Gaming Profit Pool
  - Event-driven Commerce
```

---

# 13. MVP 점수화 기준

## 13.1 Mention Score: 많이 언급되는 정도

```text
Mention Score =
  0.30 × normalized_mention_count
+ 0.20 × source_diversity_score
+ 0.15 × weighted_source_score
+ 0.15 × recency_score
+ 0.10 × cross_sector_spread_score
+ 0.10 × momentum_score
```

해석:

| 점수 | 의미 |
|---:|---|
| 80~100 | 여러 소스에서 반복적으로 강하게 언급 |
| 60~79 | 명확한 관심 형성 |
| 40~59 | 일부 소스에서 관찰되는 중간 신호 |
| 20~39 | 약한 신호 또는 초기 신호 |
| 0~19 | 현재 거의 언급되지 않음 |

## 13.2 Importance Score: 숫자 기반 중요도

```text
Importance Score =
  0.20 × market_size_score
+ 0.15 × growth_rate_score
+ 0.15 × capex_score
+ 0.15 × bottleneck_score
+ 0.10 × policy_support_score
+ 0.10 × supply_chain_criticality_score
+ 0.10 × evidence_quality_score
+ 0.05 × time_horizon_score
```

해석:

| 점수 | 의미 |
|---:|---|
| 80~100 | 구조적으로 큰 시장·자본·정책·병목을 동반 |
| 60~79 | 산업적으로 의미 있는 성장/변화 가능성 |
| 40~59 | 제한적 근거 또는 특정 세그먼트 중심 |
| 20~39 | 아직 근거 약함 |
| 0~19 | 중요도 판단 불가 |

## 13.3 두 축 조합 해석

| 유형 | Mention Score | Importance Score | 의미 |
|---|---:|---:|---|
| Mainstream Structural Trend | 높음 | 높음 | 이미 크고 많이 언급되는 핵심 트렌드 |
| Hype / Noise | 높음 | 낮음 | 많이 언급되지만 숫자 근거가 약함 |
| Undercovered Structural Trend | 낮음 | 높음 | 아직 덜 언급되지만 구조적으로 중요 |
| Weak Signal | 낮음 | 중간 | 초기 관찰 대상 |
| Declining Attention | 하락 | 높음 | 중요하지만 관심이 식는 중 |
| Anomaly Candidate | 급등/급락 | 불확실 | 사람 검토 필요 |

---

# 14. MVP에서 우선 구현할 리포트 구조

## 14.1 Weekly Trend Memory Update

```markdown
# Weekly Trend Memory Update

## 신규 수집 현황
- 신규 기사 수:
- 신규 knowledge item 수:
- 신규 concept 후보:
- 신규 metric 수:
- 신규 visual asset 수:

## 이번 주 많이 언급된 컨셉
| Rank | Concept | Mention Score | 관련 섹터 | 주요 소스 |

## 숫자 근거가 강한 컨셉
| Rank | Concept | Importance Score | 핵심 Metric | 주요 소스 |

## 이상 징후 후보
| Type | Description | Related Sectors | Severity | Review Required |

## 신규 Weak Signal
| Concept | First Seen | Source | Why It Matters |
```

## 14.2 Sector Detail Page

각 섹터별 상세 페이지는 이 문서의 1~10위 구조를 그대로 사용한다.

```markdown
# [Sector Name]

## Definition
## Core Concepts
## Claims / Trends
## Representative Articles
## Extractable Metrics
## Knowledge Item Examples
## Anomaly Rules
## Related Sectors
```

---

# 15. MVP 개발 시 우선순위

## 15.1 1차 ingestion 우선 섹터

가장 먼저 구현할 섹터는 아래 5개다.

1. AI Infrastructure / Data Center
2. Power Grid / Energy Security
3. Semiconductor / Memory / AI Compute
4. AI Software / Agentic AI
5. Private Markets / Infrastructure Finance

이유는 다음과 같다.

- seed 기사 내 반복 언급이 많다.
- 서로 강하게 연결되어 있어 트렌드 확산 감지에 적합하다.
- 숫자 기반 근거를 추출하기 쉽다.
- 이미지·표·차트가 많이 포함될 가능성이 높다.
- 이후 LG 관점의 사업 기회 매핑으로 확장하기 쉽다.

## 15.2 2차 확장 섹터

6. Robotics / Physical AI / Autonomous Mobility
7. Healthcare / Biopharma / GLP-1 / AI R&D
8. Defense / Space / Shipbuilding / Industrial Resilience

이들은 기사 수는 상대적으로 적지만 weak signal과 anomaly detection에 적합하다.

## 15.3 3차 확장 섹터

9. Financial Infrastructure / Payments / Digital Assets
10. Consumer / Media / Gaming / Premium Travel

이들은 직접적인 대형 산업 CapEx보다 business model, 소비, 금융 운영 구조 변화에 가깝다. MVP 초기에는 낮은 우선순위로 두되, cross-sector spread를 관찰한다.

---

# 16. 다음 단계: 개발용 입력으로 전환

이 문서를 바탕으로 다음 단계에서는 아래 산출물을 만들도록 지시할 수 있다.

```text
1. configs/sectors.yaml
2. configs/concepts.yaml
3. configs/source_registry.yaml
4. db/schema.sql
5. scripts/import_seed_articles.py
6. app/extraction/knowledge_item_schema.py
7. app/scoring/mention_score.py
8. app/scoring/importance_score.py
9. app/anomaly/anomaly_rules.py
10. app/reports/weekly_trend_memory_update.py
```

MVP의 첫 개발 목표는 다음과 같이 정의한다.

```text
seed_articles_2026.md의 239개 기사를 DB에 적재하고,
각 기사를 10개 섹터 taxonomy와 concept taxonomy에 매핑한 뒤,
핵심 knowledge item, metric, table, visual asset을 추출할 수 있는
Trend Intelligence Memory System의 기본 골격을 만든다.
```
