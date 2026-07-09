# Research Wiki

글로벌 기관 리서치(IB·국제기구·컨설팅·국내 증권사)를 수집→지식화→wiki/RAG로 소비하는 개인 리서치 도구.
homestyle-wiki(앱 뼈대·Drizzle·Vercel)를 기반으로, geo-wiki(ingest·RAG 패턴)와
equity-research-blog(IB 스크래퍼)를 재조합한 시스템.

## Architecture
- 전체 설계·로드맵·세션 프롬프트: 리포 루트의 HANDOVER.md (구현 전 반드시 해당 Phase 섹션 정독)
- 앱(Vercel): Next.js 15 — /wiki/[sector], /chat(RAG), /review(승인), /scoreboard
- 파이프라인(GitHub Actions, Python): ingestion/ → knowledge/ → Neon 직접 write
- DB(Neon): Postgres + pgvector. 스키마는 db/schema.ts(Drizzle)가 단일 진실
- 원본 아카이브(Vercel Blob): PDF/HTML 원본, {published}_{issuer}_{slug} 명명
- 스키마 문서: KNOWLEDGE_MODEL.md — 스키마 수정 시 이 문서부터 갱신
- geo-wiki 이식 패턴 참조: docs/patterns-from-geo-wiki.md

## Models (런타임)
- 관련성 필터/스코어링: OPENAI_MODEL_FILTER (기본 gpt-4o-mini)
- claims 추출/요약/wiki 생성/RAG: OPENAI_MODEL_MAIN (기본 gpt-4o)
- 임베딩: OpenAI text-embedding-3-small (1536d) — 변경 금지
- LLM 공급자는 OpenAI로 단일화. 호출은 knowledge/llm_client.py(파이썬)·lib/openai.ts(TS)로 집약

## Hard Rules
- Vercel 함수에서 크롤링/장시간 작업 금지. 파이프라인은 Actions 전용
- 스키마 변경은 db/schema.ts 수정 → drizzle-kit generate → 마이그레이션 커밋 순서만.
  Neon 콘솔 수동 변경 금지
- 개발/마이그레이션 테스트는 Neon dev 브랜치에서. main 브랜치 직접 실험 금지
- 원문 보존 필수: 파싱 전 원본을 Blob에 업로드하고 URL을 raw_sources에 기록
- 모든 claim에 issuer, published_at 필수. 없으면 ingest 거부
- LLM 파싱은 content hash 변경 시에만 (비용 가드)
- 요약은 원문 구조 모방 금지 — 6섹션 고정 포맷
- 품질 게이트: 단일 합산 점수 게이트 금지. 4차원 루브릭(차원별 최소선) +
  앵커 예시 고정 + claims 0건 문서는 knowledge_items 승격 금지 (KNOWLEDGE_MODEL.md §게이트)
- /review 반려 시 reason_tag 없이 반려 불가 (피드백 루프의 원료)
- 외부 재배포 없음. 공개 배포 기능 추가 금지 (auth 잠금 유지)
- Python(Actions)은 raw SQL로 Neon 접근. 스키마 변경 PR에는 Python 쿼리 영향 체크 포함 (§7-2)

## Commands
- npm run dev / build / typecheck / lint
- npx drizzle-kit generate && npx drizzle-kit migrate
- python3 ingestion/router.py --dry-run
- python3 ingestion/router.py --source <id>
- python3 knowledge/extract_claims.py --backfill

## Testing
- 스크래퍼: fixtures/ HTML 스냅샷 대상 파싱 테스트 (라이브 호출 금지)
- claims 추출: fixtures/golden_claims/ 골든 샘플 5건 스키마 검증
- DB 테스트는 Neon dev 브랜치 대상
