# KNOWLEDGE_MODEL.md v2 — Research Wiki 스키마 문서

> 스키마 변경 순서: 이 문서 먼저 갱신 → db/schema.ts 수정 → drizzle-kit generate → Neon dev 검증 → main 적용
> Python(Actions)은 raw SQL로 Neon 접근. 스키마 변경 PR에는 Python 쿼리 영향 체크 필수.

---

## §1 5단계 수집 파이프라인

```
raw_sources → sources → [품질 게이트 4단] → summaries → knowledge_items → knowledge_embeddings
```

| 단계 | 테이블 | 역할 |
|---|---|---|
| 1 | raw_sources | 원본 수집물. 파싱 전 Vercel Blob 업로드 + URL 기록 필수 |
| 2 | sources | 정규화 레코드. issuer + published_at 없으면 ingest 거부 |
| 3 | claims | Sonnet 추출 주장. Gate 3 기준이자 RAG 구조화 소스 |
| 4 | summaries | 한국어 6섹션 요약 (게이트 통과 문서만) |
| 5 | knowledge_items | 임베딩 청크 원본. published_at 메타 필수 |
| 5 | knowledge_embeddings | pgvector (1536d). 시점 가중 RAG 검색용 |
| - | review_log | 사람 판정 이력. 반려 피드백 루프의 원료 |

---

## §2 claims 스키마

| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | uuid PK | |
| source_id | uuid FK sources | cascade delete |
| issuer | text NOT NULL | 'Goldman Sachs', 'IMF' 등 — Hard Rule: 필수 |
| sector | text NOT NULL | 'power_equipment', 'ai_semis' 등 |
| entities | text[] | 언급 기업·제품 (선택) |
| claim_ko | text NOT NULL | 한국어 1문장 주장 |
| direction | text | bullish / bearish / neutral |
| horizon | text | '2027', 'H2 2026', 'long-term' |
| metrics | jsonb | `{"HBM CAGR": {"value": "40%", "span": "원문 스팬"}}` — 근거 스팬 필수 |
| published_at | date NOT NULL | 시점성의 기준축 — Hard Rule: 필수 |
| valid_until | date | time-decay 기준. null = 상시 유효 |
| supersedes | uuid | 동일 이슈어 뷰 변화 체인 (self-FK) |
| outcome | text | Phase 4: hit / miss / partial / open |

**추출 규칙:**
- 원문에 없는 수치 생성 금지 — metrics.span에 원문 근거 포함
- 불확실하면 빈 배열 반환 (0건 정상)
- 문서당 0~10건 상한
- claims 0건 문서는 knowledge_items 승격 금지 (Hard Rule)

---

## §2.5 품질 게이트 v2 — 4단 트리아지

### 설계 원칙
점수(간접 지표)가 아니라 추출 가능성(직접 증거)으로 판정. 사람은 경계 구간만 본다.

```
raw_source (pending)
   │
 [Gate 1] Haiku 하드필터 — 명백 탈락만 제거
   │   판단 최소화. 애매하면 통과시켜 Gate 2로
   │   거부 조건: 섹터 완전 무관 | 목차·광고 페이지 | 명백 중복
   │
 [Gate 2] Sonnet 루브릭 — 4차원 개별 점수 (합산 금지)
   │   relevance (1~5): 섹터 적합도
   │   density (1~5): 신규 수치·주장 밀도
   │   authority (1~5): 발행처·저자 신뢰도
   │   novelty (1~5): 기존 임베딩 top-5 유사도 대비 신규성
   │   앵커: knowledge/prompts/rubric_anchors.md (합격 2건·불합격 2건)
   │   → R2 루틴이 반려 사례로 앵커 교체
   │
 [Gate 3] claims 추출 — 추출 결과를 트리아지 입력으로 재활용
   │   claims 0건 = 원자화할 주장 없음 → 자동 반려
   │   metrics 포함 claims ≥1건 = 강한 통과 신호
   │
 [Triage] 3분류 (임계값은 knowledge/triage_config.yaml에 외부화)
   ├→ auto_accept: 전 차원 ≥ AUTO_ACCEPT_MIN AND claims ≥ AUTO_ACCEPT_CLAIMS
   ├→ review_queue: 그 외 (경계 구간)
   └→ auto_reject: 어느 차원 ≤ AUTO_REJECT_MAX OR claims = 0
```

### sources 상태 전이
```
pending → (Gate1 명백 탈락) → rejected
pending → (Gate2+Gate3+Triage) → auto_accepted | queued | rejected
queued  → (사람 /review) → accepted | rejected (+reason_tag in review_log)
```

### review_log 스키마

| 컬럼 | 설명 |
|---|---|
| decision | accept / reject |
| reason_tag | irrelevant / shallow / duplicate / stale — 반려 시 필수 |
| note | 자유 메모 (선택) |

### sources 추가 컬럼

| 컬럼 | 설명 |
|---|---|
| quality | `{relevance:4, density:3, authority:5, novelty:4}` Gate 2 결과 |
| gate_note | Gate 판정 근거 1줄 (감사용) |

---

## §3 임베딩 규격

- 모델: OpenAI text-embedding-3-small — **변경 금지 (D1)**
- 차원: 1536d
- 청크: knowledge_items 단위
- metadata 필수: `{published_at, sector, issuer, knowledge_item_id}`
- RAG 시 시점 가중: published_at 지수 감쇠, 반감기 180일 (Phase 4)

---

## §4 6섹션 요약 포맷

요약은 원문 구조 모방 금지 (Hard Rule). 항상 아래 6섹션 고정.

```
## 1. 핵심 주장
## 2. 주요 수치 및 전망
## 3. 근거 및 분석 방법론
## 4. 리스크 및 불확실성
## 5. 시사점 (한국 시장 관련)
## 6. 출처 정보
```

게이트 통과 문서(auto_accepted / accepted)에만 생성.

---

## §5 Python → DB 쿼리 영향 체크리스트

스키마 변경 PR 시 아래 파일의 SQL을 확인한다.

| 파일 | 접근 테이블 |
|---|---|
| ingestion/router.py | raw_sources, sources |
| ingestion/db.py | (공통 헬퍼) |
| knowledge/gate1_filter.py | sources |
| knowledge/gate2_rubric.py | sources, knowledge_embeddings |
| knowledge/extract_claims.py | sources, claims |
| knowledge/triage.py | sources |
| knowledge/summarize.py | sources, summaries |
| knowledge/embed.py | sources, knowledge_items, knowledge_embeddings |
| knowledge/pipeline.py | sources |
