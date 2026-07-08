'use client';

// app/observatory/AntennaApp.tsx
// Antenna 프로토타입(Claude Design / DCLogic)을 Next.js(React 19) 클라이언트 컴포넌트로 포팅한 것.
// 원본: prototype/antenna.html — 상태 기반 5개 화면(홈/피드/위키/챗/알림)을 그대로 재현.
// 데이터는 ./data.ts (프로토타입 static seed), 이후 단계에서 Neon/Drizzle로 교체.

import { useMemo, useState, type CSSProperties } from 'react';
import {
  sources,
  sectors,
  articles,
  signalsData,
  wikiData,
  briefsData,
  spikesData,
  sectorName,
  type Article,
} from './data';

type Cite = { label: string; go: () => void };
type Message = { role: 'user' | 'bot'; text: string; cites: Cite[] };
type Nav = 'dash' | 'feed' | 'wiki' | 'chat' | 'alerts';

const serif = "'Newsreader','Noto Serif KR',ui-serif,Georgia,serif";

// ---------- style helpers (프로토타입 헬퍼 이식) ----------
function badgeSt(srcId: string): CSSProperties {
  const s = sources[srcId];
  return {
    flex: 'none',
    background: s.bg,
    color: '#fff',
    fontSize: 10,
    fontWeight: 700,
    borderRadius: 5,
    padding: '4px 6px',
    letterSpacing: '.03em',
    minWidth: 26,
    textAlign: 'center',
  };
}
function deltaSt(up: boolean, big?: boolean): CSSProperties {
  return {
    color: up ? '#C4442A' : '#2A5FC4',
    fontWeight: 700,
    fontSize: big ? 15 : 12,
    fontVariantNumeric: 'tabular-nums',
    flex: 'none',
  };
}
function tagSt(tag: string): CSSProperties {
  const map: Record<string, [string, string]> = {
    '구조적 트렌드': ['rgba(14,90,69,.1)', '#0E5A45'],
    '과열 점검': ['rgba(196,68,42,.1)', '#C4442A'],
    '저커버·고중요': ['rgba(29,58,110,.1)', '#1D3A6E'],
    '약한 신호': ['rgba(33,40,50,.07)', '#5A564C'],
    '관심 하락': ['rgba(33,40,50,.05)', '#8A857A'],
  };
  const [bg, color] = map[tag] || map['약한 신호'];
  return { flex: 'none', width: 86, textAlign: 'center', fontSize: 10.5, fontWeight: 700, background: bg, color, borderRadius: 5, padding: '4px 0' };
}
function chipSt(active: boolean): CSSProperties {
  return {
    fontSize: 12,
    fontWeight: active ? 700 : 500,
    cursor: 'pointer',
    borderRadius: 15,
    padding: '6px 13px',
    background: active ? '#171C26' : '#fff',
    color: active ? '#F0EFE6' : '#5A564C',
    border: active ? '1px solid #171C26' : '1px solid rgba(33,40,50,.15)',
  };
}
function toggleSts(on: boolean) {
  return {
    trackSt: { flex: 'none', width: 36, height: 21, borderRadius: 11, cursor: 'pointer', padding: 2, boxSizing: 'border-box', background: on ? '#0E5A45' : 'rgba(33,40,50,.18)', transition: 'background .15s' } as CSSProperties,
    knobSt: { width: 17, height: 17, borderRadius: 9, background: '#fff', transform: on ? 'translateX(15px)' : 'none', transition: 'transform .15s' } as CSSProperties,
  };
}
function Spark({ seed }: { seed: number }) {
  const pts: string[] = [];
  for (let i = 0; i < 12; i++) {
    const y = 30 - (Math.sin(i * 0.7 + seed) * 6 + i * 1.7 + (i > 8 ? (i - 8) * 3 : 0));
    pts.push(i * 19.5 + 2 + ',' + Math.max(3, y).toFixed(1));
  }
  return (
    <svg viewBox="0 0 218 36" style={{ width: '100%', height: 36, display: 'block' }}>
      <polyline points={pts.join(' ')} fill="none" stroke="#8FC6B4" strokeWidth={2} strokeLinecap="round" />
    </svg>
  );
}

const card: CSSProperties = { background: '#fff', border: '1px solid rgba(33,40,50,.1)', borderRadius: 10, padding: 20 };

const NAVS: Nav[] = ['dash', 'feed', 'wiki', 'chat', 'alerts'];

export default function AntennaApp({ initialNav, initialWikiSector }: { initialNav?: string; initialWikiSector?: string } = {}) {
  const [nav, setNav] = useState<Nav>(NAVS.includes(initialNav as Nav) ? (initialNav as Nav) : 'dash');
  const [wikiSector, setWikiSector] = useState(initialWikiSector && sectors.some((s) => s.id === initialWikiSector) ? initialWikiSector : 'ai_dc');
  const [selSrc, setSelSrc] = useState('all');
  const [selSector, setSelSector] = useState('all');
  const [chatInput, setChatInput] = useState('');
  const [typing, setTyping] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    { role: 'bot', text: '안녕하세요. 2026년 1월 이후 수집된 공개 인사이트 239건과 10개 섹터 위키를 기반으로 답변합니다.\n무엇이 궁금하세요?', cites: [] },
  ]);
  const [spikeOn, setSpikeOn] = useState<Record<string, boolean>>({ bottleneck: true, inference: false, secondaries: true, agentic: false, glp: false });
  const [channelOn, setChannelOn] = useState<Record<string, boolean>>({ push: true, mail: false });

  const goWiki = (s: string) => { setWikiSector(s); setNav('wiki'); };

  function botReply(q: string): Message {
    const t = q.toLowerCase();
    const mk = (text: string, cites: Cite[]): Message => ({ role: 'bot', text, cites });
    const cw = (label: string, sector: string): Cite => ({ label, go: () => goWiki(sector) });
    const cf = (label: string): Cite => ({ label, go: () => setNav('feed') });
    if (t.includes('전력') || t.includes('bottleneck') || t.includes('데이터센터') || t.includes('power') || t.includes('그리드')) {
      return mk('AI Power Bottleneck에 대한 기관별 시각:\n\n1. Goldman Sachs — 미국 데이터센터 전력 수요가 2027년까지 2배. 병목은 서버 조달이 아니라 전력 확보 [1]\n2. Morgan Stanley — "AI 경제를 뒷받침하는 전력 경쟁". 에너지 전환의 초점이 resilience로 이동 [2]\n3. BlackRock BII — 에너지 안보 관점에서 원전·LNG·ESS를 자산배분 차원에서 재평가 [3]\n\n교차 신호: 데이터센터 파이낸싱이 private markets로 확산 중(GS) — 5위 섹터와의 연결 고리입니다.', [cf('[1] GS · DC Power Demand ×2'), cf('[2] MS · Race to Power'), cf('[3] BII · Energy security'), cw('전력망·에너지 안보 위키 →', 'power')]);
    }
    if (t.includes('반도체') || t.includes('메모리') || t.includes('inference') || t.includes('추론') || t.includes('hbm')) {
      return mk('반도체·AI 컴퓨트의 핵심 논점은 병목의 이동입니다:\n\n· Jefferies — AI 투자 사이클이 GPU에서 메모리 공급사로 이동하는지 논쟁 제기 [1]\n· McKinsey — 추론 비용(inference cost)을 낮추는 기술이 다음 경쟁력. Memory Wall·advanced packaging이 관찰 대상 [2]\n\n감지 규칙상 "Bottleneck Migration" 이상 징후가 +96%로 발동 중입니다.', [cf('[1] JEF · Memory Suppliers'), cf('[2] McK · Frontiers of compute'), cw('반도체 위키 (준비 중) →', 'semi')]);
    }
    if (t.includes('agent') || t.includes('에이전트') || t.includes('소프트웨어') || t.includes('생산성')) {
      return mk('AI 소프트웨어·Agent 섹터는 Mention 78 vs Importance 62로 "과열 점검" 구간입니다:\n\n· JPM — 금융 AI가 Copilot에서 Autonomous Agent로 이동 [1]\n· Jefferies — 차별화 요소는 모델이 아니라 맥락·데이터·지식(Context as Moat) [2]\n\n언급은 많지만 ROI 숫자 근거가 상대적으로 약해, Hype/Noise 여부를 가르는 AI ROI Proof 지표를 추적 중입니다.', [cf('[1] JPM · Copilot to Agent'), cf('[2] JEF · Context Is the Only Thing')]);
    }
    if (t.includes('세컨더리') || t.includes('프라이빗') || t.includes('저커버') || t.includes('undercover') || t.includes('인프라 금융')) {
      return mk('저커버·고중요(Undercovered Structural Trend) 시그널 1순위는 프라이빗마켓·인프라 금융입니다 (Mention 64 vs Importance 82):\n\n· Jefferies — 인프라 세컨더리 거래가 유동성 수단을 넘어 재가격화 수단으로 확장 [1]\n· GS — AI 데이터센터 파이낸싱 갭을 private markets가 메울 것으로 전망 [2]\n\n기사 수 대비 거래량·AUM 근거가 커서 관심이 뒤따라올 가능성이 있는 구간입니다.', [cf('[1] JEF · Infra Secondaries'), cf('[2] GS · DC Financing'), cw('프라이빗마켓 위키 (준비 중) →', 'pm')]);
    }
    if (t.includes('아이디어') || t.includes('브레인')) {
      return mk('현재 스코어보드 기준 브레인스토밍 각도 세 가지:\n\n1. 저커버 추격 — Importance가 Mention보다 큰 프라이빗마켓(5위)·헬스케어(7위): 관심이 숫자를 따라올 후보\n2. 병목의 병목 — AI Power Bottleneck 다음 단계인 변압기·냉각·ESS 밸류체인\n3. 과열 검증 — AI 소프트웨어(4위)의 ROI Proof: Hype인지 구조 전환인지 가르는 지표 추적\n\n각 각도의 근거 아티클을 더 파볼까요?', [cf('피드에서 근거 보기'), cw('AI 인프라 위키 →', 'ai_dc')]);
    }
    return mk('이번 주 핵심: 최다 언급 컨셉은 AI Power Bottleneck(+214%, Mention Spike)이고, 저커버·고중요 1순위는 Infrastructure Secondaries입니다. Weekly Trend Memory Update "AI의 병목은 전력이다"에 정리되어 있습니다.\n\n특정 섹터·컨셉을 지정하시면 출처와 함께 더 깊게 답변드릴게요.', [cw('AI 인프라·데이터센터 위키 →', 'ai_dc'), cf('이번 주 아티클 보기')]);
  }

  function send(text?: string) {
    const q = (text !== undefined ? text : chatInput).trim();
    if (!q || typing) return;
    setMessages((m) => [...m, { role: 'user', text: q, cites: [] }]);
    setChatInput('');
    setTyping(true);
    setTimeout(() => {
      setMessages((m) => [...m, botReply(q)]);
      setTyping(false);
    }, 900);
  }

  const icons: Record<Nav, string> = { dash: '◈', feed: '☰', wiki: '❡', chat: '✦', alerts: '◉' };
  const titles: Record<Nav, string> = { dash: '홈', feed: '아티클 피드', wiki: '섹터 위키', chat: 'AI 챗', alerts: '트렌드 알림' };
  const navOrder: Nav[] = ['dash', 'feed', 'wiki', 'chat', 'alerts'];
  const alertCount = Object.values(spikeOn).filter(Boolean).length;

  // ---------- derived ----------
  const signals = signalsData.map((sg) => ({ ...sg, sectorNm: sectorName(sg.sector) }));
  const feed: Article[] = useMemo(
    () => articles.filter((a) => (selSrc === 'all' || a.src === selSrc) && (selSector === 'all' || a.sector === selSector)),
    [selSrc, selSector],
  );
  const wSec = sectors.find((x) => x.id === wikiSector)!;
  const wd = wikiData[wikiSector];
  const wikiSections = (wd ? wd.sections : []).map((sec, i) => ({ ...sec, anchor: 'wsec-' + i }));
  const wikiRefs = (wd ? wd.refIds : []).map((id, i) => {
    const a = articles.find((x) => x.id === id)!;
    return { n: i + 1, title: a.title, srcName: sources[a.src].name, date: '2026.' + a.date };
  });
  const wikiArticleCount = articles.filter((a) => a.sector === wikiSector).length;
  const wikiSrcAgg: Record<string, number> = {};
  articles.filter((a) => a.sector === wikiSector).forEach((a) => { wikiSrcAgg[a.src] = (wikiSrcAgg[a.src] || 0) + 1; });
  const wikiSrcs = Object.entries(wikiSrcAgg).map(([id, n]) => ({ short: sources[id].short, name: sources[id].name, n: wd ? n * 8 : n, id }));
  const srcChipDefs: [string, string][] = [['all', '전체 239'], ['gs', 'GS 29'], ['jpm', 'JPM 76'], ['ms', 'MS 37'], ['bii', 'BlackRock BII 4'], ['jf', 'Jefferies 43'], ['mk', 'McKinsey 50']];

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden', background: '#F5F2EB', color: '#212832', fontFamily: "'Pretendard Variable',Pretendard,-apple-system,BlinkMacSystemFont,system-ui,sans-serif" }}>
      <style>{`
        @keyframes fadeUp { from { opacity:0; transform:translateY(8px) } to { opacity:1; transform:none } }
        @keyframes blink { 0%,100%{opacity:.2} 50%{opacity:1} }
        .ant-hgreen:hover { border-color:#0E5A45 !important }
        .ant-op:hover { opacity:.75 }
        .ant-ul:hover { text-decoration:underline }
      `}</style>

      {/* ============ SIDEBAR ============ */}
      <div style={{ width: 224, flex: 'none', background: '#171C26', color: '#EDEAE1', display: 'flex', flexDirection: 'column', padding: '22px 14px 16px' }}>
        <div style={{ padding: '0 10px 22px', borderBottom: '1px solid rgba(237,234,225,.12)' }}>
          <div style={{ fontFamily: serif, fontStyle: 'italic', fontWeight: 600, fontSize: 24, letterSpacing: '.5px' }}>Antenna</div>
          <div style={{ fontSize: 11, color: 'rgba(237,234,225,.55)', marginTop: 4, letterSpacing: '.04em' }}>글로벌 리서치 인텔리전스</div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2, marginTop: 16 }}>
          {navOrder.map((id) => (
            <div key={id} onClick={() => setNav(id)} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px', borderRadius: 7, cursor: 'pointer', fontSize: 13.5, fontWeight: nav === id ? 700 : 500, background: nav === id ? 'rgba(237,234,225,.1)' : 'transparent', color: nav === id ? '#fff' : 'rgba(237,234,225,.65)' }}>
              <span style={{ display: 'inline-flex', width: 16, justifyContent: 'center' }}>{icons[id]}</span>
              <span>{titles[id]}</span>
              {id === 'alerts' && <span style={{ marginLeft: 'auto', background: '#C4442A', color: '#fff', fontSize: 10, fontWeight: 700, borderRadius: 9, padding: '2px 7px' }}>3</span>}
            </div>
          ))}
        </div>
        <div onClick={() => setNav('alerts')} style={{ marginTop: 'auto', background: 'rgba(14,90,69,.35)', border: '1px solid rgba(14,90,69,.6)', borderRadius: 8, padding: 12, cursor: 'pointer' }}>
          <div style={{ fontSize: 10, letterSpacing: '.08em', color: '#8FC6B4', fontWeight: 700 }}>WEEKLY TREND MEMORY · 7월 1주</div>
          <div style={{ fontFamily: serif, fontSize: 15, marginTop: 5, lineHeight: 1.35 }}>AI의 병목은 전력이다</div>
          <div style={{ fontSize: 11, color: 'rgba(237,234,225,.5)', marginTop: 6 }}>신규 기사 18건 · knowledge item 42건</div>
        </div>
        <div style={{ fontSize: 10, color: 'rgba(237,234,225,.35)', padding: '14px 10px 0' }}>수집 239건 · 2026.07.08 06:00 갱신</div>
      </div>

      {/* ============ MAIN ============ */}
      <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
        {/* topbar */}
        <div style={{ flex: 'none', display: 'flex', alignItems: 'center', gap: 16, padding: '14px 32px', borderBottom: '1px solid rgba(33,40,50,.1)', background: 'rgba(245,242,235,.9)' }}>
          <div style={{ fontWeight: 700, fontSize: 15 }}>{titles[nav]}</div>
          <div style={{ fontSize: 12, color: '#8A857A' }}>2026년 7월 8일 화요일</div>
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 10 }}>
            <input placeholder="키워드·컨셉·기관 검색" style={{ width: 240, padding: '8px 12px', border: '1px solid rgba(33,40,50,.15)', borderRadius: 7, background: '#fff', fontSize: 12.5, fontFamily: 'inherit', outline: 'none' }} />
            <div onClick={() => setNav('alerts')} className="ant-hgreen" style={{ position: 'relative', cursor: 'pointer', padding: '7px 9px', border: '1px solid rgba(33,40,50,.15)', borderRadius: 7, background: '#fff' }}>
              <span style={{ fontSize: 13 }}>◉</span>
              <span style={{ position: 'absolute', top: -5, right: -5, background: '#C4442A', color: '#fff', fontSize: 9, fontWeight: 700, borderRadius: 8, padding: '1px 5px' }}>{alertCount}</span>
            </div>
          </div>
        </div>

        <div style={{ flex: 1, overflowY: 'auto' }}>
          <div style={{ maxWidth: 1160, margin: '0 auto', padding: '28px 32px 64px' }}>

            {/* ============ DASHBOARD ============ */}
            {nav === 'dash' && (
              <div style={{ animation: 'fadeUp .35s ease both' }}>
                <div style={{ fontSize: 12, color: '#8A857A', letterSpacing: '.06em', fontWeight: 600 }}>TODAY&rsquo;S SENSING · 24시간 내 신규 아티클 12건 · 신규 knowledge item 27건</div>
                <h1 style={{ fontFamily: serif, fontWeight: 600, fontSize: 34, margin: '8px 0 24px' }}>오늘의 시그널</h1>

                {/* variant: briefing hero (default) */}
                <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 14 }}>
                  <div style={{ background: '#0E5A45', color: '#F0EFE6', borderRadius: 12, padding: 28, display: 'flex', flexDirection: 'column', gap: 14 }}>
                    <div style={{ fontSize: 10.5, letterSpacing: '.1em', fontWeight: 700, color: '#8FC6B4' }}>WEEKLY TREND MEMORY UPDATE · 7월 1주차</div>
                    <div style={{ fontFamily: serif, fontSize: 30, fontWeight: 600, lineHeight: 1.25 }}>AI의 병목은 전력이다</div>
                    <div style={{ fontSize: 13.5, lineHeight: 1.7, color: 'rgba(240,239,230,.85)' }}>이번 주 최다 언급 컨셉은 &lsquo;AI Power Bottleneck&rsquo;. GS는 미국 데이터센터 전력 수요 2027년 2배 전망을 제시했고, MS·BlackRock BII가 전력·에너지 안보 관점으로 동조. 데이터센터 파이낸싱은 private markets로 확산 중이다.</div>
                    <div onClick={() => setNav('alerts')} style={{ marginTop: 'auto', alignSelf: 'flex-start', background: '#F0EFE6', color: '#0E5A45', fontWeight: 700, fontSize: 12.5, borderRadius: 7, padding: '9px 16px', cursor: 'pointer' }}>업데이트 전문 보기 →</div>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {signals.map((sg) => (
                      <div key={sg.key} onClick={() => goWiki(sg.sector)} className="ant-hgreen" style={{ background: '#fff', border: '1px solid rgba(33,40,50,.1)', borderRadius: 9, padding: '12px 14px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 12 }}>
                        <span style={deltaSt(sg.up, true)}>{sg.delta}</span>
                        <span style={{ fontSize: 13.5, fontWeight: 600, minWidth: 0 }}>{sg.kw}</span>
                        <span style={{ marginLeft: 'auto', flex: 'none', fontSize: 10.5, color: '#8A857A' }}>{sg.type}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* shared lower row */}
                <div style={{ display: 'grid', gridTemplateColumns: '1.25fr .75fr', gap: 14, marginTop: 14 }}>
                  <div style={card}>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 6, flexWrap: 'wrap' }}>
                      <div style={{ fontWeight: 700, fontSize: 14 }}>섹터 스코어보드</div>
                      <div style={{ fontSize: 11, color: '#8A857A' }}>언급 강도(Mention)와 숫자 근거(Importance)를 분리해 과열과 저커버를 구분합니다</div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 14, fontSize: 10.5, color: '#8A857A', marginBottom: 12 }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}><span style={{ width: 14, height: 5, background: '#0E5A45', borderRadius: 2 }} />Mention</span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}><span style={{ width: 14, height: 5, background: '#1D3A6E', borderRadius: 2 }} />Importance</span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                      {sectors.map((m) => (
                        <div key={m.id} onClick={() => goWiki(m.id)} className="ant-op" style={{ display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer' }}>
                          <div style={{ width: 178, flex: 'none', fontSize: 12.5, fontWeight: 600, display: 'flex', gap: 7, alignItems: 'baseline' }}>
                            <span style={{ color: '#8A857A', fontSize: 11, fontVariantNumeric: 'tabular-nums' }}>{m.rank}</span>
                            <span>{m.name}</span>
                          </div>
                          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 3 }}>
                            <div style={{ height: 5, background: 'rgba(33,40,50,.07)', borderRadius: 3, overflow: 'hidden' }}><div style={{ width: m.mention + '%', height: '100%', background: '#0E5A45', borderRadius: 3 }} /></div>
                            <div style={{ height: 5, background: 'rgba(33,40,50,.07)', borderRadius: 3, overflow: 'hidden' }}><div style={{ width: m.importance + '%', height: '100%', background: '#1D3A6E', borderRadius: 3 }} /></div>
                          </div>
                          <div style={{ width: 44, flex: 'none', textAlign: 'right', fontSize: 11.5, fontVariantNumeric: 'tabular-nums', color: '#5A564C' }}>{m.mention} · {m.importance}</div>
                          <span style={tagSt(m.tag)}>{m.tag}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div style={card}>
                    <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 12 }}>
                      <div style={{ fontWeight: 700, fontSize: 14 }}>최신 수집 아티클</div>
                      <div onClick={() => setNav('feed')} className="ant-ul" style={{ fontSize: 11.5, color: '#0E5A45', fontWeight: 600, cursor: 'pointer' }}>피드 전체 →</div>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      {articles.slice(0, 5).map((a) => (
                        <div key={a.id} onClick={() => setNav('feed')} className="ant-op" style={{ display: 'flex', gap: 10, alignItems: 'flex-start', padding: '9px 0', borderBottom: '1px solid rgba(33,40,50,.06)', cursor: 'pointer' }}>
                          <span style={badgeSt(a.src)}>{sources[a.src].short}</span>
                          <div style={{ minWidth: 0 }}>
                            <div style={{ fontSize: 12.5, fontWeight: 600, lineHeight: 1.35 }}>{a.title}</div>
                            <div style={{ fontSize: 11, color: '#8A857A', marginTop: 3 }}>{a.date} · {sectorName(a.sector)}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* ============ FEED ============ */}
            {nav === 'feed' && (
              <div style={{ animation: 'fadeUp .35s ease both' }}>
                <h1 style={{ fontFamily: serif, fontWeight: 600, fontSize: 34, margin: '0 0 6px' }}>아티클 피드</h1>
                <div style={{ fontSize: 12.5, color: '#8A857A', marginBottom: 20 }}>2026년 1월 이후 글로벌 IB·운용사·컨설팅 공개 인사이트 239건 수집 · 대표 기사를 표시합니다.</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 10 }}>
                  {srcChipDefs.map(([id, label]) => (
                    <div key={id} onClick={() => setSelSrc(id)} style={chipSt(selSrc === id)}>{label}</div>
                  ))}
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 20 }}>
                  {[{ id: 'all', name: '모든 섹터' }, ...sectors].map((s) => (
                    <div key={s.id} onClick={() => setSelSector(s.id)} style={chipSt(selSector === s.id)}>{s.name}</div>
                  ))}
                </div>
                <div style={{ fontSize: 11.5, color: '#8A857A', marginBottom: 10 }}>대표 기사 {feed.length}건</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {feed.map((a) => {
                    const sec = sectors.find((x) => x.id === a.sector)!;
                    return (
                      <div key={a.id} className="ant-hgreen" style={{ background: '#fff', border: '1px solid rgba(33,40,50,.1)', borderRadius: 10, padding: '16px 18px', display: 'flex', gap: 14, alignItems: 'flex-start' }}>
                        <span style={badgeSt(a.src)}>{sources[a.src].short}</span>
                        <div style={{ minWidth: 0, flex: 1 }}>
                          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, flexWrap: 'wrap' }}>
                            <span style={{ fontSize: 14.5, fontWeight: 700 }}>{a.title}</span>
                            <span style={{ fontSize: 11, color: '#8A857A' }}>{sources[a.src].name} · {a.date}</span>
                          </div>
                          <div style={{ fontSize: 12.5, color: '#5A564C', lineHeight: 1.55, marginTop: 5 }}>{a.kr}</div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 9, flexWrap: 'wrap' }}>
                            <span onClick={() => goWiki(a.sector)} style={{ fontSize: 11, fontWeight: 700, color: '#0E5A45', background: 'rgba(14,90,69,.08)', borderRadius: 5, padding: '3px 8px', cursor: 'pointer' }}>{sec.name} 위키 →</span>
                            <span style={{ fontSize: 11, fontWeight: 700, color: '#5A564C', background: 'rgba(33,40,50,.05)', borderRadius: 5, padding: '3px 8px' }}>M {sec.mention} · I {sec.importance}</span>
                            <span onClick={() => setNav('chat')} style={{ marginLeft: 'auto', fontSize: 11, color: '#8A857A', cursor: 'pointer' }}>AI에게 질문 ↗</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* ============ WIKI ============ */}
            {nav === 'wiki' && (
              <div style={{ animation: 'fadeUp .35s ease both' }}>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 22 }}>
                  {sectors.map((s) => (
                    <div key={s.id} onClick={() => setWikiSector(s.id)} style={chipSt(wikiSector === s.id)}>{s.rank} · {s.name}</div>
                  ))}
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 28, alignItems: 'flex-start' }}>
                  {/* TOC */}
                  <div style={{ width: 150, flex: 'none', position: 'sticky', top: 0, fontSize: 12 }}>
                    <div style={{ fontSize: 10.5, letterSpacing: '.08em', fontWeight: 700, color: '#8A857A', marginBottom: 10 }}>목차</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 7, borderLeft: '2px solid rgba(33,40,50,.1)', paddingLeft: 12 }}>
                      {wikiSections.map((sec) => (
                        <a key={sec.anchor} href={'#' + sec.anchor} style={{ color: '#5A564C', fontSize: 12 }}>{sec.h}</a>
                      ))}
                      {wikiRefs.length > 0 && <a href="#wiki-refs" style={{ color: '#5A564C', fontSize: 12 }}>각주 · 대표 기사</a>}
                    </div>
                  </div>
                  {/* article */}
                  <div style={{ flex: '1 1 420px', minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, borderBottom: '1px solid rgba(33,40,50,.15)', paddingBottom: 12 }}>
                      <span style={{ flex: 'none', whiteSpace: 'nowrap', fontFamily: serif, fontSize: 16, color: '#8A857A' }}>{wSec.rank}위</span>
                      <h1 style={{ fontFamily: serif, fontWeight: 600, fontSize: 32, margin: 0 }}>{wSec.name}</h1>
                    </div>
                    <div style={{ fontSize: 11.5, color: '#8A857A', margin: '10px 0 6px' }}>
                      최종 갱신 2026-07-08 · 수집 아티클 {wd ? wd.count : wikiArticleCount}건 기반 자동 생성
                      {wikiRefs.length > 0 && <span> · <a href="#wiki-refs">대표 기사 {wikiRefs.length}건</a></span>}
                    </div>
                    {!wd && (
                      <div style={{ background: '#fff', border: '1px dashed rgba(33,40,50,.25)', borderRadius: 10, padding: 28, marginTop: 16, fontSize: 13.5, color: '#5A564C', lineHeight: 1.7 }}>
                        이 섹터의 위키는 2차 확장(ingestion) 대기 중입니다. 관련 대표 기사 {wikiArticleCount}건이 수집되어 있으며, 우선 구현 5개 섹터 이후 자동 생성됩니다.
                        <div onClick={() => setNav('feed')} style={{ marginTop: 12, color: '#0E5A45', fontWeight: 700, cursor: 'pointer' }}>수집된 아티클 보기 →</div>
                      </div>
                    )}
                    {wikiSections.map((sec) => (
                      <div key={sec.anchor}>
                        <h2 id={sec.anchor} style={{ fontFamily: serif, fontWeight: 600, fontSize: 22, margin: '30px 0 4px', borderBottom: '1px solid rgba(33,40,50,.08)', paddingBottom: 7 }}>{sec.h}</h2>
                        {sec.body.map((p, j) => (
                          <p key={j} style={{ fontSize: 14, lineHeight: 1.8, color: '#33322C', margin: '12px 0', textWrap: 'pretty' }}>
                            {p.t}
                            {p.ref && <a href="#wiki-refs" style={{ fontSize: 11, verticalAlign: 'super' }}> [{p.ref}]</a>}
                          </p>
                        ))}
                      </div>
                    ))}
                    {wikiRefs.length > 0 && (
                      <>
                        <h2 id="wiki-refs" style={{ fontFamily: serif, fontWeight: 600, fontSize: 20, margin: '36px 0 10px', borderBottom: '1px solid rgba(33,40,50,.08)', paddingBottom: 7 }}>각주 · 대표 기사</h2>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                          {wikiRefs.map((r) => (
                            <div key={r.n} style={{ display: 'flex', gap: 10, fontSize: 12.5, alignItems: 'baseline', flexWrap: 'wrap' }}>
                              <span style={{ color: '#8A857A', fontVariantNumeric: 'tabular-nums' }}>[{r.n}]</span>
                              <span style={{ fontWeight: 600 }}>{r.title}</span>
                              <span style={{ color: '#8A857A' }}>{r.srcName} · {r.date}</span>
                              <span onClick={() => setNav('feed')} className="ant-ul" style={{ color: '#0E5A45', fontWeight: 600, cursor: 'pointer', fontSize: 11.5 }}>피드에서 보기</span>
                            </div>
                          ))}
                        </div>
                      </>
                    )}
                  </div>
                  {/* rail */}
                  <div style={{ width: 250, flex: '1 1 250px', maxWidth: 340, display: 'flex', flexDirection: 'column', gap: 12, position: 'sticky', top: 0 }}>
                    <div style={{ background: '#171C26', color: '#EDEAE1', borderRadius: 10, padding: 18 }}>
                      <div style={{ display: 'flex', gap: 18 }}>
                        <div>
                          <div style={{ fontSize: 10, letterSpacing: '.07em', fontWeight: 700, color: '#8FC6B4' }}>MENTION</div>
                          <div style={{ fontFamily: serif, fontSize: 38, fontWeight: 600, marginTop: 2 }}>{wSec.mention}</div>
                        </div>
                        <div>
                          <div style={{ fontSize: 10, letterSpacing: '.07em', fontWeight: 700, color: '#9EB6E8' }}>IMPORTANCE</div>
                          <div style={{ fontFamily: serif, fontSize: 38, fontWeight: 600, marginTop: 2 }}>{wSec.importance}</div>
                        </div>
                      </div>
                      <div style={{ fontSize: 11, color: '#EDEAE1', background: 'rgba(237,234,225,.1)', borderRadius: 5, padding: '4px 8px', display: 'inline-block', marginTop: 10, fontWeight: 600 }}>{wSec.tag}</div>
                      <div style={{ marginTop: 12 }}><Spark seed={wSec.mention} /></div>
                      <div style={{ fontSize: 10.5, color: 'rgba(237,234,225,.5)', marginTop: 6 }}>최근 12주 언급량 추이</div>
                    </div>
                    <div style={{ background: '#fff', border: '1px solid rgba(33,40,50,.1)', borderRadius: 10, padding: 16 }}>
                      <div style={{ fontSize: 11, fontWeight: 700, color: '#8A857A', letterSpacing: '.06em', marginBottom: 10 }}>주요 커버 기관</div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                        {wikiSrcs.map((s) => (
                          <div key={s.id} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5 }}>
                            <span style={badgeSt(s.id)}>{s.short}</span>
                            <span style={{ fontWeight: 600 }}>{s.name}</span>
                            <span style={{ marginLeft: 'auto', color: '#8A857A', fontSize: 11 }}>{s.n}건</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div onClick={() => setNav('chat')} style={{ background: 'rgba(14,90,69,.08)', border: '1px solid rgba(14,90,69,.3)', borderRadius: 10, padding: 14, cursor: 'pointer' }}>
                      <div style={{ fontSize: 12.5, fontWeight: 700, color: '#0E5A45' }}>이 위키를 AI에게 질문하기 →</div>
                      <div style={{ fontSize: 11.5, color: '#5A564C', marginTop: 4 }}>요약, 반대 신호, 교차 섹터 연결까지</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* ============ CHAT ============ */}
            {nav === 'chat' && (
              <div style={{ animation: 'fadeUp .35s ease both', maxWidth: 780, margin: '0 auto', display: 'flex', flexDirection: 'column', minHeight: 'calc(100vh - 180px)' }}>
                <h1 style={{ fontFamily: serif, fontWeight: 600, fontSize: 34, margin: '0 0 4px' }}>리서치 어시스턴트</h1>
                <div style={{ fontSize: 12, color: '#8A857A', marginBottom: 24 }}>수집된 아티클 239건과 10개 섹터 위키를 근거로 답합니다. 모든 답변에는 출처가 붙습니다.</div>
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 14 }}>
                  {messages.map((m, i) => (
                    <div key={i} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
                      <div style={m.role === 'user'
                        ? { maxWidth: '78%', background: '#171C26', color: '#F0EFE6', borderRadius: '14px 14px 3px 14px', padding: '12px 16px' }
                        : { maxWidth: '85%', background: '#fff', border: '1px solid rgba(33,40,50,.1)', borderRadius: '14px 14px 14px 3px', padding: '14px 18px' }}>
                        <div style={{ fontSize: 13.5, lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>{m.text}</div>
                        {m.cites.length > 0 && (
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 10 }}>
                            {m.cites.map((c, k) => (
                              <span key={k} onClick={c.go} style={{ fontSize: 11, fontWeight: 600, color: '#0E5A45', background: 'rgba(14,90,69,.08)', border: '1px solid rgba(14,90,69,.25)', borderRadius: 5, padding: '3px 8px', cursor: 'pointer' }}>{c.label} ↗</span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  {typing && (
                    <div style={{ alignSelf: 'flex-start', background: '#fff', border: '1px solid rgba(33,40,50,.1)', borderRadius: 12, padding: '12px 16px', fontSize: 13, color: '#8A857A' }}>
                      <span style={{ animation: 'blink 1.2s infinite' }}>●</span>
                      <span style={{ animation: 'blink 1.2s .2s infinite' }}>●</span>
                      <span style={{ animation: 'blink 1.2s .4s infinite' }}>●</span>
                    </div>
                  )}
                </div>
                {messages.length < 3 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 20 }}>
                    {['AI Power Bottleneck, 기관별 시각 차이를 요약해줘', '저커버·고중요(Undercovered) 시그널은 뭐가 있어?', '지금 시그널로 투자 아이디어 브레인스토밍 해줘'].map((q) => (
                      <div key={q} onClick={() => send(q)} className="ant-hgreen" style={{ fontSize: 12.5, color: '#33322C', background: '#fff', border: '1px solid rgba(33,40,50,.15)', borderRadius: 16, padding: '8px 14px', cursor: 'pointer' }}>{q}</div>
                    ))}
                  </div>
                )}
                <div style={{ display: 'flex', gap: 8, marginTop: 16, position: 'sticky', bottom: 0, background: '#F5F2EB', padding: '10px 0 4px' }}>
                  <input value={chatInput} onChange={(e) => setChatInput(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') send(); }} placeholder="예: AI Power Bottleneck, 기관별 시각 차이를 요약해줘" style={{ flex: 1, padding: '13px 16px', border: '1px solid rgba(33,40,50,.18)', borderRadius: 9, fontSize: 13.5, fontFamily: 'inherit', outline: 'none', background: '#fff' }} />
                  <div onClick={() => send()} style={{ background: '#0E5A45', color: '#fff', fontWeight: 700, fontSize: 13, borderRadius: 9, padding: '13px 20px', cursor: 'pointer', display: 'flex', alignItems: 'center' }}>전송</div>
                </div>
                <div style={{ fontSize: 10.5, color: '#8A857A', marginTop: 8 }}>투자 판단의 근거 자료이며, 투자 권유가 아닙니다.</div>
              </div>
            )}

            {/* ============ ALERTS ============ */}
            {nav === 'alerts' && (
              <div style={{ animation: 'fadeUp .35s ease both' }}>
                <h1 style={{ fontFamily: serif, fontWeight: 600, fontSize: 34, margin: '0 0 6px' }}>트렌드 센싱</h1>
                <div style={{ fontSize: 12.5, color: '#8A857A', marginBottom: 24 }}>이상 징후(anomaly) 감지 규칙 기반 알림과 Weekly Trend Memory Update 아카이브.</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, alignItems: 'start' }}>
                  <div style={card}>
                    <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 14 }}>이상 징후 후보 <span style={{ fontSize: 11, color: '#C4442A', fontWeight: 700 }}>● LIVE</span></div>
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      {spikesData.map((sp) => {
                        const on = spikeOn[sp.key];
                        const { trackSt, knobSt } = toggleSts(on);
                        return (
                          <div key={sp.key} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '11px 0', borderBottom: '1px solid rgba(33,40,50,.06)' }}>
                            <div style={{ minWidth: 0, flex: 1 }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 7, flexWrap: 'wrap' }}>
                                <span style={{ flex: 'none', fontSize: 10, fontWeight: 700, letterSpacing: '.03em', color: '#1D3A6E', background: 'rgba(29,58,110,.08)', borderRadius: 4, padding: '3px 7px' }}>{sp.type}</span>
                                <span style={{ fontSize: 13.5, fontWeight: 700 }}>{sp.kw}</span>
                              </div>
                              <div style={{ fontSize: 11, color: '#8A857A', marginTop: 4 }}>{sp.desc}</div>
                            </div>
                            <span style={deltaSt(sp.up, true)}>{sp.delta}</span>
                            <div onClick={() => setSpikeOn((s) => ({ ...s, [sp.key]: !s[sp.key] }))} style={trackSt}><div style={knobSt} /></div>
                          </div>
                        );
                      })}
                    </div>
                    <div style={{ fontSize: 11, color: '#8A857A', marginTop: 12 }}>토글을 켜면 해당 규칙 발동 시 푸시 알림</div>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    <div style={card}>
                      <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>Weekly Trend Memory Update</div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                        {briefsData.map((b) => (
                          <div key={b.week} className="ant-hgreen" style={{ border: '1px solid rgba(33,40,50,.09)', borderRadius: 9, padding: 14, cursor: 'pointer' }}>
                            <div style={{ fontSize: 10.5, letterSpacing: '.07em', fontWeight: 700, color: '#0E5A45' }}>{b.week}</div>
                            <div style={{ fontFamily: serif, fontSize: 17, fontWeight: 600, marginTop: 5 }}>{b.title}</div>
                            <div style={{ fontSize: 12, color: '#5A564C', lineHeight: 1.6, marginTop: 6 }}>{b.sum}</div>
                            <div style={{ fontSize: 11, color: '#8A857A', marginTop: 8 }}>{b.meta}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div style={card}>
                      <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>알림 채널</div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                        {[{ key: 'push', name: '푸시 알림', desc: '이상 징후 감지 즉시 (일 최대 5건)' }, { key: 'mail', name: '이메일 다이제스트', desc: '매일 오전 7시, Weekly Update 포함' }].map((c) => {
                          const { trackSt, knobSt } = toggleSts(channelOn[c.key]);
                          return (
                            <div key={c.key} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                              <div style={{ flex: 1 }}>
                                <div style={{ fontSize: 13, fontWeight: 600 }}>{c.name}</div>
                                <div style={{ fontSize: 11, color: '#8A857A', marginTop: 2 }}>{c.desc}</div>
                              </div>
                              <div onClick={() => setChannelOn((s) => ({ ...s, [c.key]: !s[c.key] }))} style={trackSt}><div style={knobSt} /></div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

          </div>
        </div>
      </div>
    </div>
  );
}
