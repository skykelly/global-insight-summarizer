// app/observatory/data.ts
// Antenna 프로토타입(Claude Design)에서 추출한 시드 데이터.
// 프로토타입의 static 데이터를 그대로 옮긴 것 — 이후 단계에서 Neon/Drizzle 쿼리로 교체할 자리.
// 원본: prototype/antenna.html 의 DCLogic Component (seed doc v0.1)

export type Source = { name: string; short: string; bg: string; n: number };
export type Sector = {
  id: string;
  rank: number;
  name: string;
  mention: number;
  importance: number;
  tag: string;
  up: boolean;
};
export type Article = {
  id: number;
  src: string;
  title: string;
  kr: string;
  date: string;
  sector: string;
};
export type Signal = {
  key: string;
  kw: string;
  delta: string;
  up: boolean;
  sector: string;
  type: string;
  why: string;
  srcs: string;
};
export type WikiParagraph = { t: string; ref: string };
export type WikiSection = { h: string; body: WikiParagraph[] };
export type WikiEntry = { count: number; refIds: number[]; sections: WikiSection[] };
export type Brief = { week: string; title: string; sum: string; meta: string };
export type Spike = {
  key: string;
  kw: string;
  type: string;
  delta: string;
  up: boolean;
  desc: string;
};

export const sources: Record<string, Source> = {
  gs: { name: 'Goldman Sachs', short: 'GS', bg: '#1D3A6E', n: 29 },
  jpm: { name: 'J.P. Morgan', short: 'JPM', bg: '#4A3A24', n: 76 },
  ms: { name: 'Morgan Stanley', short: 'MS', bg: '#17406B', n: 37 },
  bii: { name: 'BlackRock BII', short: 'BII', bg: '#171C26', n: 4 },
  jf: { name: 'Jefferies', short: 'JEF', bg: '#3A2E4A', n: 43 },
  mk: { name: 'McKinsey', short: 'McK', bg: '#0E5A45', n: 50 },
};

export const sectors: Sector[] = [
  { id: 'ai_dc', rank: 1, name: 'AI 인프라·데이터센터', mention: 92, importance: 88, tag: '구조적 트렌드', up: true },
  { id: 'power', rank: 2, name: '전력망·에너지 안보', mention: 84, importance: 90, tag: '구조적 트렌드', up: true },
  { id: 'semi', rank: 3, name: '반도체·AI 컴퓨트', mention: 81, importance: 84, tag: '구조적 트렌드', up: true },
  { id: 'aisw', rank: 4, name: 'AI 소프트웨어·Agent', mention: 78, importance: 62, tag: '과열 점검', up: true },
  { id: 'pm', rank: 5, name: '프라이빗마켓·인프라 금융', mention: 64, importance: 82, tag: '저커버·고중요', up: true },
  { id: 'robot', rank: 6, name: '로봇·Physical AI', mention: 58, importance: 66, tag: '약한 신호', up: true },
  { id: 'health', rank: 7, name: '헬스케어·GLP-1', mention: 55, importance: 70, tag: '저커버·고중요', up: false },
  { id: 'defense', rank: 8, name: '방산·우주·조선', mention: 52, importance: 68, tag: '약한 신호', up: true },
  { id: 'fin', rank: 9, name: '금융 인프라·결제·디지털자산', mention: 48, importance: 60, tag: '약한 신호', up: true },
  { id: 'consumer', rank: 10, name: '소비·미디어·게임', mention: 41, importance: 45, tag: '관심 하락', up: false },
];

export const articles: Article[] = [
  { id: 13, src: 'jpm', title: 'Turning the tide: Revitalizing the US shipbuilding industry', kr: '미국 조선업 재건 논의 — 국방비·산업정책과 결합된 재산업화 테마', date: '7.1', sector: 'defense' },
  { id: 1, src: 'mk', title: 'Colocation data centers: The infrastructure race behind AI', kr: 'AI 수요에 대응하는 colocation 데이터센터 인프라 경쟁', date: '6.30', sector: 'ai_dc' },
  { id: 16, src: 'mk', title: 'Nuclear power: A renaissance in the making', kr: 'AI 전력 수요·탈탄소·에너지 안보가 결합된 원전 재평가', date: '6.30', sector: 'power' },
  { id: 2, src: 'ms', title: 'The Race to Power the AI Economy', kr: 'AI 경제를 뒷받침하는 전력 확보 경쟁 — 병목은 컴퓨트에서 전력으로', date: '6.27', sector: 'power' },
  { id: 3, src: 'gs', title: "South Korea's Growing Role in Humanoid Robot Development", kr: '한국의 모터·센서·정밀제조 기반 휴머노이드 공급망 기회', date: '6.25', sector: 'robot' },
  { id: 7, src: 'mk', title: 'Frontiers of compute: The technologies to reduce AI inference costs', kr: 'AI 추론 비용(inference cost)을 낮추는 칩·시스템 기술 지도', date: '6.25', sector: 'semi' },
  { id: 4, src: 'bii', title: 'Energy security in a world reshaped', kr: 'AI 전력 수요와 에너지 안보 — 자산배분 관점의 재평가', date: '6.23', sector: 'power' },
  { id: 15, src: 'ms', title: 'The $22 Billion Profit Opportunity in AI + Gaming', kr: 'AI가 게임 제작·운영·수익화에 만드는 이익 풀', date: '6.20', sector: 'consumer' },
  { id: 17, src: 'ms', title: 'Energy: Transitioning to Resilience', kr: '에너지 전환의 초점이 효율에서 resilience(안정성)로 이동', date: '6.16', sector: 'power' },
  { id: 5, src: 'gs', title: 'Private Markets Are Expected to Have a Growing Role in Data Center Financing', kr: '데이터센터 파이낸싱 갭 — private markets·infra fund의 역할 확대', date: '6.12', sector: 'pm' },
  { id: 11, src: 'jf', title: 'Infrastructure Secondaries Hit Their Stride', kr: '인프라 세컨더리 거래 본격화 — 유동성 수단에서 재가격화 수단으로', date: '6.9', sector: 'pm' },
  { id: 14, src: 'jpm', title: 'Convergence in motion: Inside the institutional blockchain shift', kr: '기관금융의 블록체인 전환 — settlement·custody·토큰화 인프라 관점', date: '6.3', sector: 'fin' },
  { id: 10, src: 'jf', title: 'Why Context Is the Only Thing That Matters in AI', kr: 'AI 경쟁력의 축이 모델에서 맥락·데이터·지식(Context as Moat)으로', date: '5.21', sector: 'aisw' },
  { id: 6, src: 'gs', title: 'US Data Center Power Demand Projected to Double by 2027', kr: '미국 데이터센터 전력 수요 2027년까지 2배 전망', date: '5.20', sector: 'ai_dc' },
  { id: 12, src: 'ms', title: 'Obesity Drugs Are Scaling Fast', kr: 'GLP-1 시장 확대 — 소비재·보험·리테일로의 spillover 관찰', date: '5.9', sector: 'health' },
  { id: 9, src: 'jpm', title: 'AI in Finance: From Copilot to Autonomous Agent', kr: '금융 AI의 전환 — 보조형 Copilot에서 자율 실행형 Agent로', date: '3.12', sector: 'aisw' },
  { id: 8, src: 'jf', title: 'Is the AI Investment Cycle Shifting Toward Memory Suppliers?', kr: 'AI 투자 사이클의 메모리 이동 — GPU 다음 병목 논쟁', date: '2.10', sector: 'semi' },
];

export const signalsData: Signal[] = [
  { key: 'bottleneck', kw: 'AI Power Bottleneck', delta: '+214%', up: true, sector: 'power', type: 'Mention Spike', why: 'GS 전력 수요 2배 전망 이후 MS·BII 동조 — 데이터센터·에너지·금융 기사로 교차 확산', srcs: 'GS · MS · BII' },
  { key: 'agentic', kw: 'Agentic Operating Model', delta: '+121%', up: true, sector: 'aisw', type: 'Source Migration', why: '기술 매체의 Agent 논의가 JPM·Jefferies·McKinsey 리포트로 이동', srcs: 'JPM · JEF · McK' },
  { key: 'inference', kw: 'Inference Cost Compression', delta: '+96%', up: true, sector: 'semi', type: 'Bottleneck Migration', why: 'GPU 공급 논의가 메모리·패키징·추론 비용으로 이동 중', srcs: 'McK · JEF' },
  { key: 'secondaries', kw: 'Infrastructure Secondaries', delta: '+58%', up: true, sector: 'pm', type: 'Undercovered', why: '기사 수 대비 거래량·수치 근거가 큰 저커버·고중요 신호', srcs: 'JEF · GS' },
];

export const wikiData: Record<string, WikiEntry> = {
  ai_dc: {
    count: 61,
    refIds: [6, 1, 5, 2],
    sections: [
      { h: '개요', body: [
        { t: 'AI 인프라·데이터센터 섹터는 AI 모델 학습과 추론을 가능하게 하는 물리적·디지털 기반 시설 전체를 다룬다. 기존에는 GPU·서버·클라우드가 중심이었다면, 최근 IB·운용사의 관심은 데이터센터 부지, 전력 접속, 냉각, 송전망, 자본 조달, 운영 효율로 확산되고 있다.', ref: '' },
        { t: '이 섹터는 단순한 IT 인프라가 아니라 "AI 산업의 생산설비"로 관찰한다. 관심 섹터 1위이며, Mention 92 · Importance 88의 메인스트림 구조적 트렌드다.', ref: '' },
      ]},
      { h: '핵심 컨셉', body: [
        { t: 'AI Power Bottleneck — AI 확산의 병목이 컴퓨트에서 전력으로 이동하는 현상. 미국 데이터센터 전력 수요는 2027년까지 2배로 전망된다.', ref: '1' },
        { t: 'Grid Interconnection Delay · Cooling Constraint — 신규 부지의 전력망 접속 지연과 고밀도 AI 서버의 열관리(수랭·CDU·액침냉각)가 실제 가동 시점을 좌우한다.', ref: '2' },
        { t: 'Private Data Center Financing — 데이터센터 투자가 private markets, infra fund, private credit으로 확산. AI 인프라 투자 규모가 공모시장과 기업 현금흐름을 넘어서는 데서 발생하는 자본 조달 구조 변화.', ref: '3' },
        { t: 'Colocation Capacity Race — colocation 사업자의 AI 수요 대응 경쟁. 발표된 증설 계획과 실제 가동 사이의 지연이 핵심 관찰 포인트다.', ref: '2' },
      ]},
      { h: '핵심 주장 · 동향', body: [
        { t: 'AI 인프라 투자는 GPU 구매를 넘어 데이터센터, 전력, 냉각, 송전망, 부동산, 장기 전력계약, 인프라 금융으로 확산되고 있다. 병목은 "서버를 살 수 있느냐"에서 "전력을 제때 확보할 수 있느냐"로 이동했다.', ref: '4' },
        { t: '수혜 범위는 반도체 기업뿐 아니라 전력기기, 냉각 솔루션, ESS, 원전, 부동산, 인프라 펀드로 확산된다. 아시아 데이터센터 시장은 전력 조달 역량과 데이터 주권에 따라 국가별 격차가 커질 수 있다.', ref: '' },
      ]},
      { h: '이상 징후 감지 규칙', body: [
        { t: 'Mention Spike — data center, AI power, grid, cooling 언급이 30일 평균 대비 급증. Source Migration — 기술 매체의 전력 병목 논의가 IB·운용사 리포트로 이동.', ref: '' },
        { t: 'Cross-sector Spread — 데이터센터 이슈가 부동산·에너지·private credit 기사로 확산. Metric Divergence — 전력 수요 전망치가 소스별로 크게 갈릴 때 사람 검토 대상.', ref: '' },
      ]},
      { h: '관련 섹터', body: [
        { t: '전력망·에너지 안보(2위), 반도체·AI 컴퓨트(3위), 프라이빗마켓·인프라 금융(5위)과 강하게 연결된다. 최상위 교차 컨셉인 AI Power Bottleneck은 본 섹터와 전력망 섹터를 잇고, Data Center Financing Gap은 프라이빗마켓 섹터로 이어진다.', ref: '' },
      ]},
    ],
  },
  power: {
    count: 47,
    refIds: [2, 4, 16, 17],
    sections: [
      { h: '개요', body: [
        { t: '전력망·에너지 안보 섹터는 AI, 전기차, 산업 전기화, 리쇼어링, 냉방 수요가 만드는 전력 수요 증가에 대응하는 인프라 클러스터다. 에너지 전환과 에너지 안보가 결합되는 영역이며, 최근에는 AI 데이터센터가 새로운 수요 동인으로 추가됐다.', ref: '' },
        { t: '관심 섹터 2위. Mention 84 · Importance 90으로, 언급보다 숫자 근거가 더 큰 — 여전히 저평가 여지가 있는 — 구조적 트렌드다.', ref: '' },
      ]},
      { h: '핵심 컨셉', body: [
        { t: 'Nuclear Renaissance — AI 전력 수요, 탈탄소, 에너지 안보가 원전 재평가로 연결되는 현상.', ref: '3' },
        { t: 'Power Equipment Shortage — 변압기, 스위치기어, 터빈, 케이블 등 전력 장비 병목. Utility-scale Battery — 배터리가 EV 테마에서 grid storage·데이터센터 안정성 테마로 확장.', ref: '1' },
        { t: 'Energy Security Premium · Gas Bridge — 지정학 불확실성 속 안정적 공급의 프리미엄과, 수요 급증기 LNG·가스발전의 과도기 역할.', ref: '2' },
      ]},
      { h: '핵심 주장 · 동향', body: [
        { t: 'AI 데이터센터와 전기화는 전력 수요 성장률을 구조적으로 높이고 있으며, 전력망 투자 부족은 AI 인프라 확장의 핵심 제약으로 부상했다.', ref: '1' },
        { t: '에너지 안보 관점에서 원전, LNG, 재생에너지, ESS가 모두 재평가되고 있다. 에너지 전환의 초점은 효율에서 resilience로 이동 중이다.', ref: '4' },
      ]},
      { h: '이상 징후 감지 규칙', body: [
        { t: 'Silent Risk — 전력 수요·grid delay 숫자는 커지는데 기사 언급은 적은 상태. Sector Shift — AI 기사보다 에너지·유틸리티 기사에서 데이터센터 언급이 늘어나는 이동.', ref: '' },
        { t: 'Policy Shock — 원전·LNG·송전망·ESS 관련 정부 예산·규제 변화 등장. Counter Signal — 재생에너지 또는 원전 투자에 대한 비용·인허가 회의론 증가.', ref: '' },
      ]},
      { h: '관련 섹터', body: [
        { t: 'AI 인프라·데이터센터(1위)의 전력 수요가 본 섹터의 1차 동인이며, 배터리·원전·LNG를 거쳐 방산·산업 리질리언스(8위), 인프라 금융(5위)으로 확산된다.', ref: '' },
      ]},
    ],
  },
};

export const briefsData: Brief[] = [
  { week: '7월 1주차 · 2026.07.06', title: 'AI의 병목은 전력이다', sum: '최다 언급 컨셉은 AI Power Bottleneck. GS 전력 수요 2배 전망에 MS·BII 동조, 데이터센터 파이낸싱은 private markets로 확산.', meta: '신규 기사 18건 · knowledge item 42건 · 신규 컨셉 2건' },
  { week: '6월 4주차 · 2026.06.29', title: 'Agentic Operating Model, IB 리포트로 이동', sum: '기술 매체의 Agent 논의가 JPM·Jefferies·McKinsey 리포트로 이동(Source Migration). Context as Moat 개념 첫 관측.', meta: '신규 기사 21건 · knowledge item 38건 · weak signal 3건' },
  { week: '6월 3주차 · 2026.06.22', title: 'Infrastructure Secondaries — 저커버·고중요', sum: '기사 수는 적지만 거래량 근거가 큰 Undercovered Structural Trend로 분류. 유럽 세컨더리 시장 확산 관찰.', meta: '신규 기사 16건 · knowledge item 29건 · 이상 징후 1건' },
];

export const spikesData: Spike[] = [
  { key: 'bottleneck', kw: 'AI Power Bottleneck', type: 'Mention Spike', delta: '+214%', up: true, desc: 'data center·grid·cooling 언급, 30일 평균 대비 급증 · 전력망·에너지 안보' },
  { key: 'agentic', kw: 'Agentic Operating Model', type: 'Source Migration', delta: '+121%', up: true, desc: '기술 매체 → IB·PE 리포트로 논의 주체 이동 · AI 소프트웨어' },
  { key: 'inference', kw: 'Inference Cost Compression', type: 'Bottleneck Migration', delta: '+96%', up: true, desc: 'GPU → 메모리·패키징·추론 비용으로 언급 이동 · 반도체' },
  { key: 'secondaries', kw: 'Infrastructure Secondaries', type: 'Undercovered', delta: '+58%', up: true, desc: '언급은 적고 수치 근거는 큼 — Importance 82 vs Mention 64 · 프라이빗마켓' },
  { key: 'glp', kw: 'GLP-1 Consumer Spillover', type: 'Cross-sector Spread', delta: '+42%', up: true, desc: 'GLP-1이 소비재·보험·리테일 기사에 등장 · 헬스케어 → 소비' },
];

export const sectorName = (id: string) => sectors.find((x) => x.id === id)?.name ?? id;
