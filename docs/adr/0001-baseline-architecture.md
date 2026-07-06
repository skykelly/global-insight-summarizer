# ADR 0001 — 베이스라인 아키텍처 (v2)

- 상태: 확정 (HANDOVER §3 사전 결정사항 v2 확정본)
- 날짜: 2026-07-06

## 맥락
기존 자산 3개(homestyle-wiki, geo-wiki, equity-research-blog)를 재조합해 글로벌 기관
리서치 수집·지식화 도구를 구축. v1(geo-wiki 뼈대 / Supabase+Railway)에서 v2로 전환.

## 결정
| # | 결정 | 확정안 |
|---|---|---|
| D1 | 임베딩 | OpenAI text-embedding-3-small (1536d) — 변경 금지 |
| D2 | 생성 모델 | Claude: Haiku(필터) / Sonnet(추출·요약·wiki·RAG) |
| D3 | 인프라 | Vercel(앱) + Neon(pgvector) + GitHub Actions(파이프라인) + Vercel Blob(원본) |
| D4 | 시작 방식 | homestyle-wiki 복제(신규 리포, 포크 아님), 도메인 콘텐츠 제외 |
| D5 | 초기 섹터 | 전력기기(power_equipment) + AI 반도체(ai_semis) |
| D6 | PDF 파서 | Docling 1순위, Claude PDF 입력 폴백 |
| D7 | 파이프라인 실행처 | GitHub Actions 전담. Vercel 함수에서 크롤링 금지 |
| D8 | 접근 제어 | auth 유지, 본인 계정 전용 잠금 |

## 결과
- 스키마 단일 진실 = `db/schema.ts`(Drizzle). Python 파이프라인은 raw SQL 접근 → 스키마 이중화 리스크(§7-2)를 CLAUDE.md 룰로 관리.
- 무거운 작업(크롤링/파싱/백필/wiki 생성)은 전부 Actions. Vercel은 읽기 중심 앱 + 경량 API만.
- 후속 결정은 docs/adr/ 에 0002~ 로 기록.

## 참조
- 전체 설계: HANDOVER.md
- 품질 게이트 트리아지: HANDOVER §2.5 → Phase 2에서 KNOWLEDGE_MODEL.md 로 상술
- geo-wiki 이식 패턴: docs/patterns-from-geo-wiki.md
