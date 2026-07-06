# Research Wiki

글로벌 기관 리서치(IB·국제기구·컨설팅·국내 증권사)를 정기 수집→지식화→wiki/RAG로
소비하는 **개인 리서치 도구**. 외부 재배포 없음.

> 현재 상태: **Session 0 스켈레톤** (구조·문서·설정만. 기능 미구현)

## 스택
- 앱: Next.js 15 + Drizzle ORM + Auth.js v5 → **Vercel**
- DB: **Neon** Postgres + pgvector
- 파이프라인: Python → **GitHub Actions** (Vercel 함수에서 크롤링 금지)
- 원본 아카이브: **Vercel Blob**
- LLM: Claude Haiku(필터)/Sonnet(추출·요약·RAG), OpenAI 임베딩(3-small)

## 구조
```
app/ · components/ · lib/   앱 (homestyle-wiki 뼈대에서 복제, 도메인 콘텐츠 제외)
auth.ts · middleware.ts     본인 전용 잠금
db/schema.ts · db/migrations/   Drizzle 스키마 단일 진실 (Phase 1~2 확장)
ingestion/                  Layer 1 — 수집 (Python, Actions)
  sources.yaml              소스 레지스트리
  channels/scrapers/        equity-research-blog 스크래퍼 (복사만, Phase 1 리팩터)
knowledge/                  Layer 2 — 지식화 (Python)
kb/wiki/                    자동 생성 wiki 마크다운 출력 타깃
docs/patterns-from-geo-wiki.md   geo-wiki 이식 패턴(설계)
docs/adr/                   아키텍처 결정 기록
CLAUDE.md · HANDOVER.md     운영 룰 / 전체 설계·로드맵
```

## 셋업
```bash
cp .env.example .env      # 값 채우기 (Neon, Blob, Anthropic, OpenAI, Auth)
npm install
npm run dev
```
스키마: `npm run db:generate` → Neon dev 브랜치 검증 → main 적용.

## 로드맵
Phase 1(DB+수집) → 2(스키마 v2+품질 게이트) → 3(wiki 생성) → 4(RAG+트래킹) → §8 Routines 운영.
세부 프롬프트는 **HANDOVER.md** 참조.
