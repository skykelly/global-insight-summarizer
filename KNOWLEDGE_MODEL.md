# KNOWLEDGE_MODEL.md v2 — Research Wiki 스키마 문서

> 스키마 변경 순서: 이 문서 먼저 갱신 → db/schema.ts 수정 → drizzle-kit generate → Neon dev 검증 → main 적용
> Python(Actions)은 raw SQL로 Neon 접근. 스키마 변경 PR에는 Python 쿼리 영향 체크 필수.

---

## §1 5단계 수집 파이프라인

```
raw_sources → sources → [품질 게이트 4단] → summaries → knowledge_items → knowledge_embeddings
                              │
                              └─ claims (Gate 3 겸 구조화 지식 단위) ─┬─ concepts (taxonomy upsert)
                                                                      └─ trend_scores / anomalies (집계·감지)
```

| 단계 | 테이블 | 역할 |
|---|---|---|
| 1 | raw_sources | 원본 수집물. 파싱 전 Vercel Blob 업로드 + URL 기록 필수 |
| 2 | sources | 정규화 레코드. issuer + published_at 없으면 ingest 거부 |
| 3 | claims | 추출된 구조화 지식 단위. Gate 3 기준이자 RAG 구조화 소스 (§2) |
| 4 | summaries | 한국어 6섹션 요약 (게이트 통과 문서만) |
| 5 | knowledge_items | **RAG 임베딩 청크 원본** — claims와는 별개 테이블(§주의 참고) |
| 5 | knowledge_embeddings | pgvector (1536d). 시점 가중 RAG 검색용 |
| - | review_log | 사람 판정 이력. 반려 피드백 루프의 원료 |
| - | concepts | 섹터 간 교차 컨셉 taxonomy (§2.1). configs/taxonomy.yaml에서 upsert |
| - | trend_scores | 섹터·컨셉별 주기 집계 — Mention/Importance 2축 (§2.2) |
| - | anomalies | 이상 징후 후보 — 사람 검토 큐 (§2.3) |

**⚠️ 이름 유의:** `claims`(구조화 지식 단위 — item_type로 concept/claim/trend/metric 등 표현)와
`knowledge_items`(RAG 청크 메타데이터, item_type은 'summary'|'claim_excerpt'|'insight' 고정 3종)는
**서로 다른 테이블**이다. Observatory 설계 문서(seed doc)가 말하는 "knowledge item"은
이 스키마의 `claims`에 해당한다 — 혼동 시 embed.py(knowledge_items 대상)와
extract_claims.py(claims 대상)를 반드시 구분해서 볼 것.

---

## §2 claims 스키마 (일반화됨 — 구조화 지식 단위)

claims는 원래 "추출된 주장(claim)"만 담았으나, Sector Trend Observatory 설계
(docs/ib_asset_manager_sector_trend_seed.md §3 공통 추출 스키마)를 흡수하며
9종 item_type을 모두 담는 범용 "지식 단위" 테이블로 확장되었다. 테이블명은
하위 호환을 위해 `claims`로 유지한다(리네임 시 Python 6개·TS 3개 파일의 raw SQL이
전부 깨지고, 실제 프로덕션 데이터 마이그레이션 리스크가 커서 이름 유지가 더 안전하다고 판단).

| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | uuid PK | |
| source_id | uuid FK sources | cascade delete |
| issuer | text NOT NULL | 'Goldman Sachs', 'IMF' 등 — Hard Rule: 필수 |
| sector | text NOT NULL | **configs/taxonomy.yaml의 sector id 중 하나** (구 'power_equipment'/'ai_semis' 아님, §2.1) |
| related_sectors | text[] | 교차 섹터 (cross-sector spread 감지용) |
| item_type | text NOT NULL DEFAULT 'claim' | concept \| claim \| trend \| metric \| risk \| weak_signal \| counter_signal \| visual_insight \| sector_shift |
| core_concept | text | configs/taxonomy.yaml concepts.id 참조 (느슨한 FK — concept 테이블에 없으면 후보로 upsert) |
| canonical_title | text | item 제목 (claim 외 item_type에서 주로 사용) |
| entities | text[] | 언급 기업·제품 (선택) |
| claim_ko | text NOT NULL | 한국어 1문장 주장/요약 |
| direction | text | bullish / bearish / neutral (투자 관점) |
| trend_direction | text | rising / falling / stable / mixed / uncertain (Observatory 관측 관점 — direction과 다른 축, 병존) |
| horizon | text | 자유형 시간값: '2027', 'H2 2026', 'long-term' |
| time_horizon | text | 구조화 버킷: near_term / mid_term / long_term / structural |
| metrics | jsonb | `{"HBM CAGR": {"value": "40%", "span": "원문 스팬"}}` — 근거 스팬 필수 |
| evidence | jsonb | `{evidence_type, evidence_summary}` — text/table/chart/image/transcript 구분 |
| mention_relevance_score | real | 개별 item의 언급 관련도 (0~100, trend_scores 집계의 입력) |
| importance_evidence_score | real | 개별 item의 숫자 근거 강도 (0~100) |
| novelty_score | real | 기존 임베딩 대비 신규성 (0~100) |
| anomaly_score | real | 이상 징후 후보 강도 (0~100) |
| confidence_score | real | 추출 신뢰도 (0~1). < 0.6 은 사람 검토 권장 |
| published_at | date NOT NULL | 시점성의 기준축 — Hard Rule: 필수 |
| valid_until | date | time-decay 기준. null = 상시 유효 |
| supersedes | uuid | 동일 이슈어 뷰 변화 체인 (self-FK) |
| outcome | text | Phase 4: hit / miss / partial / open |

**추출 규칙:**
- 원문에 없는 수치 생성 금지 — metrics.span에 원문 근거 포함
- 불확실하면 빈 배열 반환 (0건 정상)
- 문서당 0~10건 상한
- claims 0건 문서는 knowledge_items(RAG 청크) 승격 금지 (Hard Rule)
- sector는 반드시 configs/taxonomy.yaml에 정의된 id — 프롬프트는 하드코딩 금지, taxonomy 로더에서 동적 생성

---

## §2.1 Taxonomy — 섹터 · 컨셉

**단일 진실은 configs/taxonomy.yaml.** 하드코딩 금지 — gate1_filter/gate2_rubric/
extract_claims의 프롬프트, generate_wiki의 섹터 목록, app/observatory(Antenna UI)가
전부 이 파일에서 로드한다. 섹터 id는 Antenna UI(app/observatory/data.ts)와 1:1 일치.

- 10개 섹터(rank_seed 1~10), 1차 구현은 상위 5개만 `active: true`
  (ai_dc, power, semi, aisw, pm). 나머지 5개(robot/health/defense/fin/consumer)는
  `active: false` — 위키는 stub("2차 확장 대기") 상태, claims 추출 대상에서는 제외하지 않되
  우선순위가 낮다.
- 30개 컨셉, 각각 `related_sectors`로 주 섹터(+교차 섹터) 연결
- 구 2섹터 체계(D5: power_equipment, ai_semis)는 `legacy_alias`로 남겨 마이그레이션 참고용으로만 사용.
  신규 claims.sector·sources.sector_tags는 전부 새 10개 id를 쓴다.

### concepts 테이블

| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | uuid PK | |
| slug | text UNIQUE NOT NULL | taxonomy.yaml concepts.id (예: 'ai_power_bottleneck') |
| canonical_name | text NOT NULL | 'AI Power Bottleneck' |
| aliases | text[] | 유사 표현 (정규화 매칭용) |
| definition | text | |
| related_sectors | text[] | sector id 배열 |
| status | text DEFAULT 'active' | active \| candidate(자동 발견) \| merged |
| first_seen_at | date | |
| last_seen_at | date | |
| created_at / updated_at | timestamp | |

`status='candidate'`는 claims 추출 중 taxonomy.yaml에 없는 core_concept이 발견되면
자동 생성 — 사람이 검토 후 taxonomy.yaml에 승격하거나 기존 concept의 alias로 병합.

---

## §2.2 trend_scores — Mention/Importance 2축 집계

주기(예: 주간)별로 섹터·컨셉의 "얼마나 언급되는가"(Mention)와
"숫자 근거로 볼 때 얼마나 중요한가"(Importance)를 **분리** 집계한다. 합산해 단일
랭킹으로 만들지 않는다(Hard Rule과 동일한 원칙 — 단일 스칼라는 변별력을 잃는다).

| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | uuid PK | |
| period_start / period_end | date | 집계 기간 |
| target_type | text NOT NULL | 'sector' \| 'concept' |
| target_id | text NOT NULL | sector id 또는 concept slug |
| mention_score | real | 0~100 |
| importance_score | real | 0~100 |
| momentum_score | real | 전기 대비 변화 |
| novelty_score | real | |
| anomaly_score | real | |
| mention_count | integer | |
| source_diversity | integer | 서로 다른 issuer 수 |
| metric_count | integer | metrics 포함 claims 수 |
| evidence_quality | real | |
| score_details | jsonb | 계산 근거 스냅샷 (감사용) |

UNIQUE(target_type, target_id, period_start) — 재계산 시 upsert.

---

## §2.3 anomalies — 이상 징후 후보

Anomaly는 확정 판단이 아니라 **사람이 검토할 후보**로 저장한다(원칙은 §2.5 트리아지와 동일 —
직접 증거로 판정하고 경계는 사람이 본다).

| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | uuid PK | |
| detected_at | timestamp | |
| anomaly_type | text NOT NULL | mention_spike \| source_diversity_jump \| high_importance_low_mention \| counter_signal \| metric_divergence \| visual_only_signal \| new_concept_emergence |
| title / description | text | |
| related_concepts / related_sectors | text[] | |
| related_claim_ids | uuid[] | 근거 claims |
| previous_period / current_period | jsonb | 비교 스냅샷 |
| severity | text | low \| medium \| high |
| review_required | boolean DEFAULT true | |
| status | text DEFAULT 'open' | open \| reviewed \| dismissed |

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
| knowledge/gate1_filter.py | sources (taxonomy.yaml에서 섹터 목록 로드) |
| knowledge/gate2_rubric.py | sources, knowledge_embeddings (taxonomy.yaml에서 섹터 목록 로드) |
| knowledge/extract_claims.py | sources, claims, concepts (taxonomy.yaml에서 섹터·컨셉 로드) |
| knowledge/triage.py | sources, claims |
| knowledge/generate_wiki.py | sources, claims, summaries (taxonomy.yaml에서 SECTORS 로드) |
| knowledge/summarize.py | sources, summaries |
| knowledge/embed.py | sources, knowledge_items, knowledge_embeddings |
| knowledge/pipeline.py | sources |
| knowledge/scoring.py | claims, sources, trend_scores (UPSERT) |
| knowledge/anomaly.py | trend_scores, claims, concepts, anomalies (INSERT) |
| knowledge/trend_report.py | trend_scores, anomalies (읽기 전용) |
