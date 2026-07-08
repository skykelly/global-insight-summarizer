# Research Wiki — Claude Code Hand-over Plan (v2.1)

> 글로벌 기관 리서치를 정기 수집·지식화하고, 산업 트렌드 전망 wiki와 커스텀 RAG AI를 운영하는 개인 리서치 도구.
> 기존 자산 3개(homestyle-wiki, geo-wiki, equity-research-blog)를 재조합하여 Claude Code로 구축한다.

---

## 세션 상태 (2026-07-07 갱신)

### 완료된 작업

| 작업 | 커밋/상태 | 비고 |
|---|---|---|
| Vercel 미들웨어 500 수정 | `vercel.json` framework: nextjs 추가 | Edge Runtime DecompressionStream 호환 |
| raw_sources→sources 승격 누락 수정 | `ingestion/router.py` dual-write | pipeline.py가 sources만 읽는 구조 |
| sources.yaml 소스 전면 검증·교체 | 8개 활성, 9개 비활성 처리 | 2026-07-07 curl 실측 |
| IB 스크래퍼 날짜 추출 보강 | `scrapers/base.py` extract_page_date | JSON-LD→meta→time→15K 풀텍스트 폴백 |
| RSS UA 교체 (봇차단 방지) | `ingestion/channels/rss.py` | browser UA 적용 |
| MS 사이트 이전 대응 | `ingestion/channels/scrapers/ms.py` | /ideas→/insights/articles |
| equity-research-blog 시드 import | `ingestion/seed_equity_blog.py` | **DB 현황: 336건** (raw_sources=sources=336) |
| 2026+ 아티클 탐색 목록 | `docs/seed_articles_2026.md` | 239건 (IB 189 + McKinsey 50) |

### DB 현황 (2026-07-07 기준)

```
raw_sources: 336건  /  sources(pending): 336건
Jefferies       120건  (2024-08 ~ 2026-07)
J.P. Morgan     118건  (2024-11 ~ 2026-07)
Morgan Stanley   52건  (2024-01 ~ 2026-07)
Goldman Sachs    39건  (2024-10 ~ 2026-07)
BlackRock BII     5건
기타              2건
날짜 범위: 2023-05 ~ 2026-07-06
```

### 다음 세션 우선 작업

1. **knowledge 파이프라인 실행** — `python3 knowledge/gate1_filter.py` → `extract_claims.py`
   - 336건 pending → Gate1 필터링 → claims 추출
   - wiki 생성 조건: 섹터당 claims ≥ 5건

2. **content_text 보강** — `seed_equity_blog.py` (body fetch 없이 summary_ko만 사용함)
   - 현재 content_text = 한국어 요약 (200-500자)
   - 향상: `python3 ingestion/seed_equity_blog.py` (--no-fetch 제거) 로 원문 body fetch 백필 필요
   - 단, GS/JPM/MS 원문은 봇차단 가능성 있음

3. **McKinsey 50건 시드 추가** — `docs/seed_articles_2026.md`에 있는 McKinsey 아티클을 DB에 삽입
   - `ingestion/seed_equity_blog.py` 패턴으로 McKinsey 전용 one-off 스크립트 작성

4. **내일 09:00 Actions 정기 수집** — BIS/SemiAnalysis/Utility Dive/IEEE/GS/JPM/MS 추가 수집 예정

### 미해결 이슈

- IMF: 모든 접근 경로 봇차단(403). 수동 PDF 등록만 가능
- Oaktree(Howard Marks), BlackRock BII 전용 스크래퍼 미구현
- McKinsey RSS 본문 얇음 (summary 196자) — Gate2 밀도 심사에서 반려 가능성

---

- 작성일: 2026-07-06 (v2 — 뼈대를 homestyle-wiki로 교체, Vercel + Neon 확정 / v2.1 — 품질 게이트 v2 트리아지 설계 반영, Phase 5를 §8 Routines 운영 자동화로 대체)
- 개발 도구: Claude Code (Opus 4.8 = 설계/리뷰, Sonnet = 구현)
- 런타임 모델: Claude API (Haiku = 필터링, Sonnet = 구조화 추출/요약)
- 인프라: **Vercel(앱) + Neon(Postgres/pgvector) + GitHub Actions(파이프라인) + Vercel Blob(원본 아카이브)**
- 용도: 개인 리서치 전용 (외부 재배포 없음)

## v1 → v2 변경 요약

| 항목 | v1 | v2 |
|---|---|---|
| 뼈대 리포 | geo-wiki (Supabase + Railway) | **homestyle-wiki (Vercel + Drizzle + Postgres)** |
| DB | Supabase pgvector | **Neon + pgvector, Drizzle ORM으로 스키마 관리** |
| 배포 | Railway | **Vercel** (앱만. 파이프라인은 Actions) |
| 원본 아카이브 | Supabase storage | **Vercel Blob** |
| geo-wiki 역할 | 뼈대 | **패턴 공급원으로 강등** (ingest 설계·RSS 발굴·RAG 챗 패턴만 이식) |
| 품질 게이트 (v2.1) | 단일 LLM 점수 + 임계치 (geo-wiki 방식) | **4단 게이트 + 3-way 트리아지 + 반려 피드백 루프** (§2.5) |
| 운영 자동화 (v2.1) | Phase 5 수동 운영 | **Claude Routines(/schedule) 정비공 체계** (§8) |

---

## 1. 자산 재사용 맵

### homestyle-wiki → 뼈대 (최신 구현체, 재사용률 ~60%)

| 자산 | 처리 | 비고 |
|---|---|---|
| Next.js 앱 구조 (app/, components/, lib/) | **유지** | Vercel 배포 설정 포함. 도메인 콘텐츠만 교체 |
| Drizzle ORM + drizzle.config.ts + migrations/ | **유지 + 확장** | 스키마 v2(claims 등)를 Drizzle 스키마로 정의 |
| auth.ts + middleware.ts | **유지** | 개인 도구이므로 전체 잠금(본인 계정만) 기본값으로 |
| kb/wiki 마크다운 렌더링 파이프라인 | **유지** | wiki 페이지 자동 생성의 출력 타깃 |
| WIKI_GENERATOR_PLAN.md | **개정** | 리서치 도메인 generator 설계의 출발 문서 |
| scripts/ (Python) | **참고 후 대체** | ingestion/ 모듈로 흡수 |
| 인테리어 도메인 콘텐츠 (kb/wiki 문서, 시드 데이터) | **폐기** | 구조만 재사용 |

### geo-wiki → 패턴 공급원 (재사용률 ~20%)

| 자산 | 처리 | 비고 |
|---|---|---|
| ingest 단계 설계 (raw_sources→sources→summaries→knowledge_items→embeddings) | **패턴 이식** | 코드 복붙이 아닌 Drizzle 스키마로 재구현 |
| RSS 발굴 + LLM 스코어링 + 승인 워크플로우 | **패턴 이식** | 스코어링 모델을 Haiku로 교체 |
| RAG 챗봇 API 패턴 (/api/chat) | **패턴 이식** | pgvector 검색부는 Neon용으로 재작성 |
| KNOWLEDGE_MODEL.md, graph-rag-plan.md | **개정** | v2 스키마 문서의 출발점 |
| Supabase/Railway 관련 코드 일체 | **폐기** | |

### equity-research-blog → 수집 모듈 공급원 (재사용률 ~30%, v1과 동일)

| 자산 | 처리 | 비고 |
|---|---|---|
| gs/jpm/ms 스크래퍼 3종 | **이식** | ingestion/channels/scrapers/, 공통 인터페이스로 리팩터 |
| summarizer.py 한국어 요약 프롬프트 | **이식** | 6섹션 요약 프롬프트로 개정 |
| run_pipeline.py 오케스트레이션 | **참고** | sources.yaml 라우터로 일반화 |
| 정적 블로그(docs/), articles.json | **폐기** | |

---

## 2. 타깃 아키텍처 (v2)

**핵심 원칙: 무거운 작업은 Actions, 서빙만 Vercel.**
Vercel 서버리스 함수는 실행 시간 제한이 있어 크롤링·Playwright·Docling·백필 같은 장시간 작업에 부적합하다. 파이프라인(Python)은 전부 GitHub Actions에서 실행하고 Neon에 직접 쓴다. Vercel은 읽기 중심 앱 + 가벼운 API(RAG 챗, 승인 액션)만 담당한다.

```
                    ┌─ GitHub Actions (파이프라인 실행 환경) ─┐
                    │  daily-ingest.yml (09:00 KST)           │
                    │  weekly-digest.yml / discover.yml       │
                    │                                          │
sources.yaml ──────▶│  ingestion/ (Python)                    │
                    │   ├ channels/ rss·reader·crawl·scrapers │
                    │   ├ pdf/parse (Docling→Claude 폴백)     │
                    │   └ dedupe (content hash)               │
                    │  knowledge/ (Python)                    │
                    │   ├ filter (Haiku) → extract_claims     │
                    │   ├ summarize (Sonnet, 한국어 6섹션)    │
                    │   └ embed (OpenAI 3-small)              │
                    └───────┬──────────────────┬──────────────┘
                            │ psycopg (직접)    │ 원본 업로드
                            ▼                  ▼
                    ┌─ Neon Postgres ─┐   ┌─ Vercel Blob ─┐
                    │  pgvector        │   │  PDF/HTML 원본 │
                    │  Drizzle 스키마  │   │  {date}_{issuer}│
                    │  (dev 브랜치 분리)│   └───────────────┘
                    └────────┬─────────┘
                             │ Drizzle
                    ┌─ Vercel (Next.js 앱) ──────────────────┐
                    │  /wiki/[sector]  자동 생성 페이지       │
                    │  /chat           RAG (뷰 비교·시점 인지)│
                    │  /review         소스 승인 UI           │
                    │  /scoreboard     전망 트래킹 (Phase 4)  │
                    │  auth.ts         본인 전용 잠금          │
                    └─────────────────────────────────────────┘
```

### 디렉터리 구조

```
research-wiki/
├── app/ · components/ · lib/        # homestyle-wiki에서 복제 (Layer 3)
├── auth.ts · middleware.ts          # 유지 (전체 잠금)
├── db/
│   ├── schema.ts                    # Drizzle 스키마 (v2: claims 포함)
│   └── migrations/                  # drizzle-kit generate 산출물
├── ingestion/                       # Layer 1 (Python, Actions에서 실행)
│   ├── sources.yaml
│   ├── router.py                    # tier 라우팅 + 폴백 체인
│   ├── channels/ (rss·reader·crawl·scrapers/)
│   ├── pdf/parse.py
│   └── dedupe.py
├── knowledge/                       # Layer 2 (Python)
│   ├── filter.py                    # Haiku 관련성 필터
│   ├── extract_claims.py            # Sonnet claims 추출
│   ├── summarize.py                 # 한국어 6섹션
│   ├── embed.py                     # OpenAI 3-small → pgvector
│   └── generate_wiki.py             # 섹터 wiki 합성 → kb/wiki/*.md
├── kb/wiki/                         # 자동 생성 wiki 마크다운 (렌더링 소스)
├── .github/workflows/               # daily-ingest / weekly-digest / discover
├── CLAUDE.md
├── KNOWLEDGE_MODEL.md               # v2
└── docs/adr/
```

### 스키마 v2 핵심 (Drizzle로 정의, 개념은 v1과 동일)

```typescript
// db/schema.ts 발췌
export const claims = pgTable('claims', {
  id: uuid('id').primaryKey().defaultRandom(),
  sourceId: uuid('source_id').references(() => sources.id, { onDelete: 'cascade' }),
  issuer: text('issuer').notNull(),          // 'Goldman Sachs', 'IMF', '한투'
  sector: text('sector').notNull(),          // 'power_equipment', 'ai_semis'
  entities: text('entities').array(),
  claimKo: text('claim_ko').notNull(),       // 주장 한 문장 (한국어 정규화)
  direction: text('direction'),              // bullish / bearish / neutral
  horizon: text('horizon'),                  // '2027', 'H2 2026', 'long-term'
  metrics: jsonb('metrics'),                 // {"HBM CAGR": "40%"}
  publishedAt: date('published_at').notNull(),   // 시점성의 기준축
  validUntil: date('valid_until'),               // time-decay 기준
  supersedes: uuid('supersedes'),                // 동일 이슈어 뷰 변화 체인
  outcome: text('outcome'),                      // Phase 4: hit/miss/partial/open
}, (t) => [
  index().on(t.sector, t.publishedAt),
  index().on(t.issuer, t.sector),
]);
```

- pgvector: Neon에서 `CREATE EXTENSION vector` 후 Drizzle `vector({ dimensions: 1536 })` 타입 사용
- 모든 임베딩 청크에 published_at 메타 필수, RAG 검색 시 time-decay 가중
- **Neon 브랜칭 활용**: `dev` 브랜치를 상시 두고 Claude Code 개발/마이그레이션 테스트는 dev 브랜치에서. Vercel-Neon 통합의 PR별 preview 브랜치는 선택 적용

### 2.5 품질 게이트 v2 — 트리아지 설계 (v2.1 신규)

**배경.** geo-wiki의 "단일 LLM 점수 ≥6 통과" 방식은 실패가 확인됨: 점수 통과 문서도 품질이 낮아 매번 전수 재검토가 필요했다. 원인은 임계치가 아니라 구조 — (a) 단일 스칼라에 관련성·밀도·신뢰도가 뭉개짐 (b) LLM 절대평가는 6~8점에 뭉쳐 변별력 상실 (c) 캘리브레이션 부재로 점수 의미가 표류 (d) 반려 판단이 시스템에 축적되지 않음.

**설계 원칙: 점수(간접 지표)가 아니라 추출 가능성(직접 증거)으로 판정하고, 사람은 경계 구간만 본다.**

```
raw_source
   │
 [Gate 1] Haiku 하드필터 — 명백 탈락만 제거 (섹터 무관/목차·광고 페이지/중복)
   │        판단 최소화. 애매하면 통과시켜 Gate 2로
 [Gate 2] Sonnet 루브릭 평가 — 4차원 개별 점수 (합산 금지, 차원별 최소선)
   │        relevance(섹터 적합) / density(신규 수치·주장 밀도)
   │        / authority(발행처·저자) / novelty(기존 임베딩 top-k 대비 신규성)
   │        프롬프트에 합격 앵커 2건 + 불합격 앵커 2건 고정 포함 → 점수 표류 방지
 [Gate 3] 추출 기반 검증 — claims 추출 결과를 게이트로 재활용
   │        claims 0건 = 원자화할 주장 없음 → 자동 반려
   │        metrics 포함 claims ≥1건 = 강한 통과 신호
   ▼
 [Triage] auto_accept ────────────→ knowledge_items 승격 (사람 개입 없음)
          review_queue (경계 구간) → /review에서 사람 판정 + 사유 태그 1클릭
          auto_reject ───────────→ 반려 (원본은 Blob에 보존, 복구 가능)
```

트리아지 규칙(초기값, R2 루틴이 조정 제안): 전 차원 ≥4 AND claims ≥2 → auto_accept / 어느 차원이든 ≤2 OR claims=0 → auto_reject / 그 외 → review_queue. 가동 후 2~3주는 auto_accept의 10%를 샘플로 review_queue에 함께 넣어 캘리브레이션 검증.

**피드백 루프.** /review 반려 시 사유 태그(irrelevant / shallow / duplicate / stale) 필수 기록 → review_log 적재 → §8 R2 주간 루틴이 (a) 반려 패턴 분석 후 Gate 2 앵커 예시 교체 PR (b) 소스별 반려율 집계, 40% 초과 소스 비활성 제안. **review_queue 비율의 주간 추이가 시스템 건강 지표** — 줄지 않으면 게이트가 학습되지 않고 있다는 뜻.

```typescript
// db/schema.ts 추가분
export const sources_ext = { // sources 테이블에 컬럼 추가
  status: text('status').notNull().default('pending'),
  // pending | auto_accepted | queued | accepted | rejected
  quality: jsonb('quality'),        // {relevance:4, density:3, authority:5, novelty:4}
  gateNote: text('gate_note'),      // Gate 판정 근거 요약 (감사용)
};

export const reviewLog = pgTable('review_log', {
  id: uuid('id').primaryKey().defaultRandom(),
  sourceId: uuid('source_id').references(() => sources.id),
  decision: text('decision').notNull(),      // accept / reject
  reasonTag: text('reason_tag'),             // irrelevant/shallow/duplicate/stale
  note: text('note'),
  createdAt: timestamp('created_at').defaultNow(),
});
```

---

## 3. 사전 결정사항 (v2 확정본)

| # | 결정 | 확정안 | 근거 |
|---|---|---|---|
| D1 | 임베딩 | **OpenAI text-embedding-3-small (1536d) 유지** | Claude 임베딩 API 부재. Neon pgvector와 호환 |
| D2 | 생성 모델 | **Claude 통일**: Haiku(필터) / Sonnet(추출·요약·wiki·RAG) | 비용 계층화 |
| D3 | 인프라 | **Vercel + Neon + Actions + Vercel Blob** | 사용자 확정. homestyle-wiki가 이미 검증한 스택 |
| D4 | 시작 방식 | **homestyle-wiki 복제(신규 리포), 도메인 콘텐츠 제외** | 포크 아님. Neon도 신규 프로젝트 |
| D5 | 초기 섹터 | **전력기기 + AI 반도체** | 기존 섹터 분석 자산을 시드 claims로 |
| D6 | PDF 파서 | **Docling 1순위, Claude PDF 입력 폴백** | 표 구조 보존 필수 |
| D7 | 파이프라인 실행처 | **GitHub Actions 전담. Vercel 함수에서 크롤링 금지** | 서버리스 시간 제한·Playwright 미지원 |
| D8 | 접근 제어 | **auth 유지, 본인 계정 전용 잠금** | 개인 도구 + 미공개 원문 파생물 보호 |

Session 0 확인 항목: homestyle-wiki의 현재 DATABASE_URL이 이미 Neon인지 확인 (PLpgSQL 마이그레이션 존재로 Postgres 확정, 벤더는 .env 확인 필요). Neon이면 신규 Neon 프로젝트만 생성, 아니면 Drizzle 설정의 드라이버 호환(neon-http vs node-postgres)을 점검.

---

## 4. 신규 리포용 CLAUDE.md 초안 (v2)

```markdown
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

## Models (런타임)
- 관련성 필터/스코어링: claude-haiku-4-5
- claims 추출/요약/wiki 생성/RAG: claude-sonnet-4-6
- 임베딩: OpenAI text-embedding-3-small (1536d) — 변경 금지

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

## Commands
- npm run dev / build / typecheck / lint
- npx drizzle-kit generate && npx drizzle-kit migrate
- python ingestion/router.py --dry-run
- python ingestion/router.py --source <id>
- python knowledge/extract_claims.py --backfill

## Testing
- 스크래퍼: fixtures/ HTML 스냅샷 대상 파싱 테스트 (라이브 호출 금지)
- claims 추출: fixtures/golden_claims/ 골든 샘플 5건 스키마 검증
- DB 테스트는 Neon dev 브랜치 대상
```

---

## 5. Phase별 실행 계획 + Claude Code 세션 프롬프트 (v2)

원칙: 1 세션 = 1 Phase. 세션 시작은 Plan Mode(Opus 4.8) 승인 후 Sonnet 구현. Phase 간 `/clear`.

### Session 0 — 리포 셋업 & 자산 이식 감사 (0.5일)

사전 준비(사람): 세 리포를 ~/github/projects/에 클론, 신규 폴더에 이 문서를 **HANDOVER.md로 저장**, `claude` 실행 → `/model opus` → Plan Mode(Shift+Tab) → 아래 프롬프트 입력. 이후 모든 세션에서 사람이 입력하는 것은 [Claude Code 프롬프트] 블록뿐이며, 나머지 컨텍스트는 HANDOVER.md(참조 시 로드)와 CLAUDE.md(자동 로드)가 나른다.

완료 기준: research-wiki 리포 생성, Neon 신규 프로젝트(main + dev 브랜치), Vercel 프로젝트 연결, CLAUDE.md·sources.yaml 스켈레톤 커밋, 이식 대상 확정.

```
[Claude Code 프롬프트]
~/github/Obsidian/homestyle-wiki, ~/github/Obsidian/geo-wiki, ~/github/projects/equity-research-blog 세 리포를 읽고,
이 디렉터리에 research-wiki 프로젝트를 셋업해줘. HANDOVER.md §1~§3을 따른다.

1. homestyle-wiki의 앱 구조(app/, components/, lib/, auth.ts, middleware.ts,
   drizzle 설정, next.config)를 복제하되 인테리어 도메인 콘텐츠(kb/wiki 문서,
   시드 데이터, 도메인 특화 컴포넌트)는 제외. 제외 판단이 애매한 파일은 목록으로 보고
2. homestyle-wiki의 .env.example을 기준으로 신규 .env.example 작성 —
   DATABASE_URL(Neon), BLOB_READ_WRITE_TOKEN, ANTHROPIC_API_KEY, OPENAI_API_KEY.
   기존 DATABASE_URL이 Neon인지 확인하고 드라이버(neon-http vs pg) 호환을 점검
3. geo-wiki에서는 코드가 아니라 설계만 가져온다: ingest 단계 구조, RSS 발굴
   워크플로우, /api/chat RAG 패턴을 docs/patterns-from-geo-wiki.md로 요약 정리
4. equity-research-blog의 scraper/*.py를 ingestion/channels/scrapers/로 복사만
   (리팩터는 Phase 1), 파일 상단 TODO 주석으로 이식 계획 요약
5. CLAUDE.md는 HANDOVER.md §4로 생성, ingestion/sources.yaml 스켈레톤 생성
   (필드: id, name, url, tier, method, schedule, sector_tags, active)
6. 기능 구현 금지. 구조·문서·설정만.

끝나면 리스크(의존성 충돌, 하드코딩 도메인 로직, Drizzle 버전 이슈 등)를 보고해줘.
```

### Phase 1 — DB 기반 + Ingestion 통합 (4~6일)

완료 기준: Neon에 스키마 v1(raw_sources~embeddings) 마이그레이션 적용, sources.yaml 15개+ 등록, `router.py --dry-run` 정상, IB 스크래퍼 3종 공통 인터페이스 동작, PDF 1건 Docling 파싱→Blob 아카이브→raw_sources 저장, daily-ingest.yml 그린.

```
[Claude Code 프롬프트]
Phase 1: DB 기반과 수집 레이어를 구현한다. Plan Mode로 계획부터.

A. DB 기반
1. db/schema.ts — geo-wiki 패턴 문서(docs/patterns-from-geo-wiki.md)의 5단계
   구조를 Drizzle로 정의: raw_sources, sources, summaries, knowledge_items,
   knowledge_embeddings(vector 1536d). pgvector extension 마이그레이션 포함
2. drizzle-kit generate → Neon dev 브랜치에 적용 → 검증 후 main 적용
3. Python 파이프라인용 DB 접근: psycopg + 환경변수 DATABASE_URL.
   스키마 정의는 TypeScript(Drizzle)가 단일 진실, Python은 raw SQL로 접근

B. 수집 레이어 (v1 계획과 동일 사양)
4. ingestion/router.py — sources.yaml tier 라우팅, Tier 3 실패 폴백 훅
5. channels/rss.py(feedparser) · reader.py(Jina, 재시도 3회) · crawl.py(Crawl4AI)
6. scrapers/ gs/jpm/ms를 BaseScraper(fetch_list→fetch_article→normalize)로 리팩터
7. pdf/parse.py — Docling(표 보존), 실패 시 Claude PDF 입력 폴백.
   원본은 Vercel Blob에 {published}_{issuer}_{slug} 업로드, URL을 raw_sources에 기록
8. dedupe.py — URL 정규화 + SHA256, 동일 hash skip
9. .github/workflows/daily-ingest.yml — 09:00 KST, dry-run 옵션,
   Neon 접속은 Actions secrets의 DATABASE_URL 사용
10. fixtures/ 스냅샷 + 파싱 테스트

sources.yaml 초기 등록:
- Tier 1: IMF blog RSS, OECD RSS, McKinsey Insights RSS, BIS RSS
- Tier 2: GS Insights, JPM Insights, MS Ideas(기존 스크래퍼), Howard Marks Memos
- Tier 4: IMF WEO PDF, ARK Big Ideas PDF (수동 URL 등록)
- 섹터 태그: power_equipment, ai_semis
```

### Phase 2 — Knowledge 스키마 v2 & 품질 게이트 & Claims 추출 (4~6일)

완료 기준: claims + review_log 마이그레이션 적용(dev→main), 4단 게이트 파이프라인 가동, 트리아지 3분류 동작(auto_accept 승격 / review_queue 적재 / auto_reject), 골든 샘플 5건 통과, 한국어 6섹션 요약 가동. **claims 0건 문서가 knowledge_items로 승격되는 경로가 존재하지 않음을 테스트로 증명.**

```
[Claude Code 프롬프트]
Phase 2: 지식 레이어 확장 + 품질 게이트 v2. Plan Mode로 시작.
HANDOVER.md §2.5(트리아지 설계)를 먼저 정독할 것. 이 Phase의 최우선 목표는
"점수 통과했지만 저품질인 문서" 문제의 구조적 차단이다.

1. KNOWLEDGE_MODEL.md v2 개정 — §2 claims 스키마 + §2.5 게이트/트리아지 반영.
   문서 먼저 커밋
2. db/schema.ts — claims, review_log 테이블 추가, sources에 status/quality/
   gate_note 컬럼, knowledge_embeddings에 published_at.
   drizzle-kit generate → Neon dev 검증 → main 적용
3. knowledge/gate1_filter.py — Haiku 하드필터. 명백 탈락만 제거(섹터 무관/
   목차·광고/중복). 애매하면 통과. 판정 근거를 gate_note에 1줄 기록
4. knowledge/gate2_rubric.py — Sonnet 4차원 루브릭 (relevance/density/
   authority/novelty 각 1~5). 합산 점수 계산 금지. novelty는 기존 임베딩
   top-5 유사도를 컨텍스트로 제공해 판정. 앵커 예시는
   knowledge/prompts/rubric_anchors.md에서 로드 (합격 2건·불합격 2건,
   R2 루틴이 교체하는 파일이므로 하드코딩 금지)
5. knowledge/extract_claims.py — 원문→claims JSON (Sonnet).
   규칙: issuer/sector/direction/horizon/metrics/published_at 필수,
   원문에 없는 수치 생성 금지, 문서당 0~10개, 불확실하면 빈 배열,
   metrics에는 근거 원문 스팬 함께 저장.
   ※ Gate 3 겸용: claims 결과가 트리아지 입력이 된다
6. knowledge/triage.py — §2.5 규칙 구현: 전 차원 ≥4 AND claims ≥2 →
   auto_accept / 어느 차원 ≤2 OR claims=0 → auto_reject / 그 외 → queued.
   임계값은 config로 외부화 (하드코딩 금지). 가동 초기 캘리브레이션용
   auto_accept 10% 샘플링→queued 플래그 옵션 포함
7. knowledge/summarize.py — 한국어 6섹션 요약 (auto_accept/accepted 문서만 실행)
8. knowledge/embed.py — OpenAI 3-small (published_at 메타 포함)
9. /review 페이지 개정 — queued 문서만 표시, 승인/반려 + 반려 시
   reason_tag(irrelevant/shallow/duplicate/stale) 필수 선택 → review_log 기록
10. 테스트: golden_claims 5건 + 트리아지 경계 케이스(저밀도 홍보문서가
    auto_reject되는지, claims 0건 승격 차단) fixtures 검증

완료 후 기존 수집분 --backfill 실행 계획(볼륨·비용 추정)을 보고해줘.
```

### Phase 3 — Wiki 자동 생성 (1주)

완료 기준: /wiki/power_equipment, /wiki/ai_semis가 claims+summaries에서 자동 생성·갱신, 전 문장 [issuer, YYYY-MM] 부착, 상충 뷰 병기, 주간 Obsidian md 산출.

```
[Claude Code 프롬프트]
Phase 3: 섹터 wiki 자동 생성. Plan Mode로 시작.
homestyle-wiki의 WIKI_GENERATOR_PLAN.md와 kb/wiki 렌더링 파이프라인을 먼저 읽고,
그 구조를 최대한 재사용해줘.

1. knowledge/generate_wiki.py — 섹터별 claims를 (a) 컨센서스 (b) 상충 뷰
   (c) 뷰 변화(supersedes 체인) (d) 핵심 수치 테이블로 합성 (Sonnet),
   kb/wiki/{sector}.md로 출력. 모든 주장에 [issuer, YYYY-MM] 인라인 표기 필수.
   valid_until 경과 claims는 '과거 뷰' 섹션으로 강등
2. 트리거: 섹터별 신규 claims 5건 누적 시 or 주 1회 강제 (Actions)
3. app/wiki/[sector] — 기존 kb/wiki 마크다운 렌더러로 서빙 (신규 UI 최소화)
4. weekly-digest.yml — 신규 claims 요약 + 뷰 변화 하이라이트를 Obsidian 호환
   마크다운(frontmatter 포함)으로 output/에 생성, Actions artifact로도 업로드
```

### Phase 4 — RAG 고도화 & 전망 트래킹 (1~2주)

완료 기준: 챗봇이 "하우스별 뷰 비교"/"6개월 전 대비 뷰 변화" 질의 응답, time-decay 검색, /scoreboard 가동.

```
[Claude Code 프롬프트]
Phase 4: RAG 고도화. Plan Mode로 시작.
docs/patterns-from-geo-wiki.md의 /api/chat 패턴을 참조하되 Neon+Drizzle로 재구현.

1. /api/chat — pgvector 유사도 × 시점 가중(published_at 지수 감쇠, 반감기 180일).
   '과거 뷰 조회' 모드는 감쇠 off
2. 질의 라우터: 비교형 질의("하우스별", "누가 맞았", "뷰 변화") 감지 시
   claims 구조화 조회(Drizzle)를 컨텍스트에 추가 주입
3. 답변 프롬프트: 시점 명시 강제("GS는 2026년 1월 기준 ~로 전망"), 현재형 단정 금지
4. app/scoreboard — issuer×sector별 outcome 집계 + 수동 판정 UI
```

### Phase 5 — 운영 자동화 (Routines 이관)

v2.1에서 수동 운영 대신 **§8 Claude Routines 정비공 체계**로 대체. Phase 4 완료 후 §8의 R1→R2→R3→R4 순서로 `/schedule` 등록. Firecrawl($16) 도입은 Tier 3 실패 소스 5개 누적 시 결정(변동 없음).

---

## 6. 모델 사용 전략 (v1과 동일)

| 국면 | 모델 | 용도 |
|---|---|---|
| 개발 — 설계/리뷰 | Opus 4.8 (Plan Mode) | Phase 계획, 스키마 설계, 마이그레이션 리뷰 |
| 개발 — 구현 | Sonnet | 코드, 테스트, 리팩터 |
| 런타임 — 필터 | Haiku | 관련성 판단, RSS 후보 스코어링 |
| 런타임 — 추출/생성 | Sonnet | claims 추출, 6섹션 요약, wiki 합성, RAG |
| 런타임 — 임베딩 | OpenAI text-embedding-3-small | 변경 금지 |

예상 런타임 비용(일 20건): 월 $10~25. 인프라: Vercel Hobby $0 + Neon Free(0.5GB, 개인 볼륨 충분) + Actions 무료 구간 + Blob 소액 = **월 $0~5**로 시작 가능.

---

## 7. 리스크 & 완화 (v2)

1. **Vercel 함수 시간 제한**: 파이프라인을 Vercel에 넣으려는 유혹 → D7 하드룰. 크롤링·백필·wiki 생성은 전부 Actions
2. **Python(Actions)과 TypeScript(앱)의 스키마 이중화**: Drizzle이 단일 진실, Python은 raw SQL — 스키마 변경 시 Python 쿼리 grep 체크를 CLAUDE.md 룰로 강제. Phase 2부터 스키마 변경 PR에 Python 영향 체크리스트 포함
3. **스크래퍼 부패**: fixtures 테스트가 Actions에서 먼저 실패하도록, 파손 시 Jina Reader 폴백 강등
4. **Actions IP 차단**: 차단 소스는 Firecrawl 라우팅 폴백을 Phase 1부터 훅으로 준비
5. **claims 환각**: 골든 샘플 테스트 + "불확실하면 빈 배열" + metrics 원문 스팬 저장
6. **Neon Free 한계**: 0.5GB 스토리지·컴퓨트 자동 중지(cold start) — 개인 도구라 cold start 수용, 스토리지는 R4 루틴이 모니터링. PDF 원본은 반드시 Blob으로 (DB에 넣지 않기)
7. **스코프 크립**: homestyle-wiki의 인테리어 기능·geo-wiki의 GEO 기능 유입 차단 — Session 0에서 물리적 제외
8. **게이트 과잉 차단 (v2.1)**: 트리아지가 좋은 문서를 auto_reject할 위험 — 반려 원본은 Blob 보존으로 복구 가능, 초기 3주 auto_reject 주간 샘플 점검을 R2에 포함, 임계값은 config 외부화로 즉시 완화 가능
9. **루틴 폭주 (v2.1)**: Routines가 무한 재시도로 토큰 소진 — 모든 루틴에 "N회 시도 후 이슈만 남기고 종료" + 실행당 예산 상한 명시. 자가 머지 절대 금지

---

## 8. 자동화 운영 설계 — Claude Routines (v2.1 신규)

**원칙: 배관과 정비공의 분리.**
결정적 작업(크롤링→파싱→적재)은 GitHub Actions에 남긴다 — 에이전트로 옮기면 매 실행 토큰 소모 + 비결정성만 얻는다. Claude Routines(`/schedule`, Anthropic 클라우드 인프라에서 상주 실행, GitHub 이벤트 트리거 지원)는 **판단이 필요한 운영 업무**에만 투입한다. `/loop`는 세션 종료 시 소멸하므로 상시 운영이 아닌 개발 중 폴링(백필 모니터링 등)에만 사용.

**공통 하드룰 (모든 루틴 프롬프트에 포함)**
- 자가 머지 금지 — PR/이슈 생성까지만. 승인은 사람
- 3회 시도 실패 시 진단 요약 이슈만 남기고 종료 (무한 재시도 금지)
- 실행당 토큰 예산 상한 준수, 단순 집계 작업은 Haiku급으로 라우팅
- 수정 PR은 fixtures 테스트 통과를 전제 조건으로 명시

### R1 — 파이프라인 정비공 (트리거: daily-ingest workflow 실패 이벤트)

```
/schedule 등록 프롬프트:
research-wiki 리포의 daily-ingest 워크플로우가 실패하면 실행.
1. 실패 로그를 읽고 원인을 분류: 스크래퍼 파손 / 네트워크·IP 차단 /
   API 한도 / DB 연결 / 기타
2. 스크래퍼 파손이면: 해당 소스의 최신 HTML을 fixtures/로 저장,
   파서를 수정, fixtures 테스트 통과 확인 후 PR 생성
   (제목: [auto-fix] {source_id} 파서 수리, 본문에 원인·수정 요약)
3. IP 차단이면: sources.yaml에서 해당 소스에 fallback: firecrawl 플래그
   제안 PR
4. 원인 불명 또는 3회 시도 실패: 진단 요약만 이슈로 남기고 종료.
머지 금지. 실행당 예산 상한 준수.
```

### R2 — 주간 품질 감사 + 게이트 학습 (매주 일요일 22:00)

§2.5 피드백 루프의 실행 주체. "매번 재검토" 문제를 시간이 갈수록 줄이는 핵심 루틴.

```
/schedule 등록 프롬프트:
매주 일요일 22:00 실행. research-wiki의 품질 감사를 수행한다.
1. 지난 7일 review_log 분석 — 반려 사유(reason_tag) 분포, 게이트를
   통과했지만 사람이 반려한 사례의 공통 패턴 요약
2. 반려 패턴이 뚜렷하면 knowledge/prompts/rubric_anchors.md의 불합격
   앵커 예시 교체 PR 제안 (실제 반려 사례에서 발췌)
3. 소스별 반려율 집계 — 40% 초과 소스는 sources.yaml active: false 제안 PR
4. auto_accept 문서 5건 무작위 스팟체크 — 저품질 유입 여부 판정
5. auto_reject 문서 5건 무작위 스팟체크 — 과잉 차단 여부 판정 (초기 3주 필수)
6. review_queue 비율 주간 추이 계산 (건강 지표)
결과를 '주간 품질 리포트' 이슈로 생성: 지표 요약 + 제안 PR 링크.
머지 금지, 3회 실패 시 이슈만 남기고 종료.
```

### R3 — 주간 소스 발굴 (매주 금요일 18:00)

```
/schedule 등록 프롬프트:
매주 금요일 18:00 실행. sources.yaml의 sector_tags(power_equipment,
ai_semis 등)를 읽고, 웹 검색으로 아직 등록되지 않은 기관 리서치 소스
후보를 3~5개 발굴한다. 각 후보에 대해: RSS 유무 확인, tier 분류,
발행 빈도·최근성 확인. §2.5 authority 기준(기관 발행물 우선, 애그리게이터
제외)으로 스스로 선별한 뒤 sources.yaml 추가 제안 PR 생성.
후보가 기준 미달이면 PR 없이 '후보 없음' 코멘트만. 머지 금지.
```

### R4 — 월간 비용·용량 리포트 (매월 1일 09:00)

```
/schedule 등록 프롬프트:
매월 1일 09:00 실행. (1) Actions 로그에서 지난달 LLM 호출 건수·토큰
집계 (2) Neon 스토리지 사용량 확인, 0.4GB 초과 시 경고 (3) Vercel Blob
용량 확인 (4) 게이트별 통과율 월간 추이. 결과를 월간 운영 리포트
이슈로 생성. 분석·수정 시도 금지, 집계와 보고만 (경량 모델로 충분).
```

### 사람에게 남는 일 (설계 목표 상태)

| 주기 | 할 일 | 예상 소요 |
|---|---|---|
| 수시 | review_queue 판정 (경계 문서만, 사유 태그 1클릭) | 일 5분 이하 목표 |
| 수시 | 정비공(R1)·감사(R2)·발굴(R3)이 올린 PR 승인/반려 | 주 10~20분 |
| 주간 | R2 품질 리포트에서 review_queue 비율 추이 확인 | 5분 |
| 월간 | R4 비용 리포트 확인 | 5분 |
