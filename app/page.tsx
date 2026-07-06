// Session 0 플레이스홀더 랜딩. 실제 홈(섹터 wiki 인덱스)은 Phase 3.
export default function HomePage() {
  return (
    <div className="max-w-3xl mx-auto px-6 py-24">
      <h1 className="text-2xl font-semibold text-white mb-3">Research Wiki</h1>
      <p className="text-sm text-neutral-400 mb-8">
        글로벌 기관 리서치를 수집→지식화→wiki/RAG로 소비하는 개인 리서치 도구.
        현재 Session 0 스켈레톤 단계입니다.
      </p>
      <ul className="text-sm text-neutral-500 space-y-1.5 list-disc pl-5">
        <li>Phase 1 — DB 기반 + Ingestion 통합</li>
        <li>Phase 2 — Knowledge 스키마 v2 + 품질 게이트</li>
        <li>Phase 3 — 섹터 wiki 자동 생성 (/wiki/[sector])</li>
        <li>Phase 4 — RAG 고도화 + 전망 트래킹 (/chat, /scoreboard)</li>
      </ul>
      <p className="text-xs text-neutral-600 mt-8">전체 로드맵은 HANDOVER.md 참조.</p>
    </div>
  )
}
