// ============================================================================
// Research Wiki — Drizzle 스키마 (단일 진실)  ·  HANDOVER §2
// 스키마 변경 순서: 이 파일 수정 → npm run db:generate → Neon dev 검증 → main 적용
// ============================================================================

import {
  pgTable,
  text, date, jsonb, uuid, timestamp, index, uniqueIndex, customType, real, integer, boolean
} from 'drizzle-orm/pg-core'
import { sql } from 'drizzle-orm'

// OpenAI text-embedding-3-small (1536d) — D1, 변경 금지
export const vector = customType<{ data: number[]; driverData: string }>({
  dataType() { return 'vector(1536)' },
  toDriver(value) { return JSON.stringify(value) },
  fromDriver(value) { return JSON.parse(value as string) },
})

// ── Stage 1: raw_sources ─────────────────────────────────────────────────────
// 수집된 원본. 파싱 전에 Vercel Blob 업로드 + URL 기록이 Hard Rule.
// content_hash 가 같으면 재처리 skip (LLM 비용 가드).
export const raw_sources = pgTable('raw_sources', {
  id:             uuid('id').primaryKey().default(sql`gen_random_uuid()`),
  url:            text('url').notNull(),
  url_normalized: text('url_normalized').notNull(),  // 중복 판정용 정규화 URL
  content_hash:   text('content_hash').notNull(),     // SHA256 of raw content
  raw_content:    text('raw_content'),                // 원본 텍스트 (처음 8KB)
  blob_url:       text('blob_url'),                   // Vercel Blob 원본 아카이브 URL
  source_yaml_id: text('source_yaml_id').notNull(),   // sources.yaml id
  issuer:         text('issuer'),                     // 발행 기관 힌트
  fetched_at:     timestamp('fetched_at', { withTimezone: true }),
  created_at:     timestamp('created_at', { withTimezone: true }).defaultNow(),
}, (t) => [
  index('idx_raw_sources_hash').on(t.content_hash),
  index('idx_raw_sources_url').on(t.url_normalized),
])

// ── Stage 2: sources ─────────────────────────────────────────────────────────
// 정규화된 소스 레코드. issuer + published_at 이 없으면 ingest 거부 (Hard Rule).
// status: pending | auto_accepted | queued | accepted | rejected
export const sources = pgTable('sources', {
  id:           uuid('id').primaryKey().default(sql`gen_random_uuid()`),
  raw_source_id: uuid('raw_source_id').references(() => raw_sources.id, { onDelete: 'cascade' }),
  title:        text('title').notNull(),
  url:          text('url').notNull(),
  issuer:       text('issuer').notNull(),        // "Goldman Sachs", "IMF" 등 — 필수
  published_at: date('published_at').notNull(),  // 시점성의 기준축 — 필수
  sector_tags:  text('sector_tags').array().default(sql`'{}'`),
  content_text: text('content_text'),            // 정제된 텍스트 (LLM 처리용)
  blob_url:     text('blob_url'),                // Vercel Blob 원본 URL
  status:       text('status').notNull().default('pending'),
  quality:      jsonb('quality'),               // {relevance:4,density:3,authority:5,novelty:4}
  gate_note:    text('gate_note'),              // Gate 판정 근거 1줄 (감사용)
  created_at:   timestamp('created_at', { withTimezone: true }).defaultNow(),
  updated_at:   timestamp('updated_at', { withTimezone: true }).defaultNow(),
}, (t) => [
  index('idx_sources_issuer_pub').on(t.issuer, t.published_at),
  index('idx_sources_status').on(t.status),
  index('idx_sources_sector').on(t.sector_tags),
])

// ── Stage 3: summaries ───────────────────────────────────────────────────────
// 한국어 6섹션 요약. Phase 2 품질 게이트 통과 후에만 생성.
export const summaries = pgTable('summaries', {
  id:         uuid('id').primaryKey().default(sql`gen_random_uuid()`),
  source_id:  uuid('source_id').notNull().references(() => sources.id, { onDelete: 'cascade' }),
  content_ko: text('content_ko').notNull(),  // 6섹션 고정 포맷 (Hard Rule: 원문 구조 모방 금지)
  model:      text('model').notNull().default('claude-sonnet-4-6'),
  created_at: timestamp('created_at', { withTimezone: true }).defaultNow(),
})

// ── Stage 4: knowledge_items ─────────────────────────────────────────────────
// 지식 단위. 임베딩 청크의 원본. published_at 메타 필수 (time-decay RAG용).
export const knowledge_items = pgTable('knowledge_items', {
  id:          uuid('id').primaryKey().default(sql`gen_random_uuid()`),
  source_id:   uuid('source_id').notNull().references(() => sources.id, { onDelete: 'cascade' }),
  title:       text('title'),
  content:     text('content').notNull(),   // 임베딩 대상 텍스트 청크
  item_type:   text('item_type').notNull(), // 'summary' | 'claim_excerpt' | 'insight'
  published_at: date('published_at').notNull(),  // time-decay 기준, RAG 필수
  sector:      text('sector'),
  issuer:      text('issuer'),
  metadata:    jsonb('metadata').default(sql`'{}'`),
  created_at:  timestamp('created_at', { withTimezone: true }).defaultNow(),
}, (t) => [
  index('idx_ki_source').on(t.source_id),
  index('idx_ki_sector_pub').on(t.sector, t.published_at),
])

// ── Stage 5: knowledge_embeddings ────────────────────────────────────────────
// pgvector 임베딩. CREATE EXTENSION vector 마이그레이션 선행 필요.
// metadata 에 { published_at, sector, issuer, knowledge_item_id } 포함.
export const knowledge_embeddings = pgTable('knowledge_embeddings', {
  id:         uuid('id').primaryKey().default(sql`gen_random_uuid()`),
  ref_type:   text('ref_type').notNull(),  // 'knowledge_item' | 'source'
  ref_id:     uuid('ref_id').notNull(),
  content:    text('content').notNull(),
  embedding:  vector('embedding'),
  metadata:   jsonb('metadata').default(sql`'{}'`),
  // { published_at: "YYYY-MM-DD", sector: "...", issuer: "...", knowledge_item_id: "..." }
  created_at: timestamp('created_at', { withTimezone: true }).defaultNow(),
}, (t) => [
  index('idx_ke_ref').on(t.ref_type, t.ref_id),
])

// ── Phase 2: claims ──────────────────────────────────────────────────────────
// 구조화 지식 단위 (일반화됨 — KNOWLEDGE_MODEL.md §2).
// 원래 "추출된 주장"만 담았으나 Sector Trend Observatory 설계를 흡수하며
// item_type으로 concept/claim/trend/metric/risk/weak_signal/counter_signal/
// visual_insight/sector_shift 9종을 모두 담는 범용 테이블로 확장.
// 테이블명은 claims로 유지 (리네임 시 Python/TS 다수 파일의 raw SQL 파손 위험).
// ⚠ knowledge_items(RAG 임베딩 청크, 아래 Stage 4)와는 다른 테이블 — 혼동 주의.
// issuer + published_at 필수 (Hard Rule). 원문에 없는 수치 생성 금지.
// sector는 configs/taxonomy.yaml 의 sector id — 하드코딩 금지.
export const claims = pgTable('claims', {
  id:           uuid('id').primaryKey().default(sql`gen_random_uuid()`),
  source_id:    uuid('source_id').notNull().references(() => sources.id, { onDelete: 'cascade' }),
  issuer:       text('issuer').notNull(),       // Hard Rule: 필수
  sector:       text('sector').notNull(),       // configs/taxonomy.yaml sector id (예: 'ai_dc', 'power')
  related_sectors: text('related_sectors').array(), // 교차 섹터 (cross-sector spread 감지용)
  item_type:    text('item_type').notNull().default('claim'),
  // concept | claim | trend | metric | risk | weak_signal | counter_signal | visual_insight | sector_shift
  core_concept: text('core_concept'),           // configs/taxonomy.yaml concepts.id 참조 (느슨한 FK)
  canonical_title: text('canonical_title'),     // claim 외 item_type에서 주로 사용
  entities:     text('entities').array(),       // 언급 기업·제품
  claim_ko:     text('claim_ko').notNull(),     // 한국어 1문장 주장/요약
  direction:    text('direction'),             // bullish / bearish / neutral (투자 관점)
  trend_direction: text('trend_direction'),     // rising/falling/stable/mixed/uncertain (관측 관점, direction과 별도 축)
  horizon:      text('horizon'),               // 자유형: '2027', 'H2 2026', 'long-term'
  time_horizon: text('time_horizon'),           // 구조화 버킷: near_term/mid_term/long_term/structural
  metrics:      jsonb('metrics'),              // {"HBM CAGR": {"value":"40%","span":"원문"}}
  evidence:     jsonb('evidence'),              // {evidence_type, evidence_summary}
  mention_relevance_score:    real('mention_relevance_score'),
  importance_evidence_score:  real('importance_evidence_score'),
  novelty_score:  real('novelty_score'),
  anomaly_score:  real('anomaly_score'),
  confidence_score: real('confidence_score'),   // < 0.6 은 사람 검토 권장
  published_at: date('published_at').notNull(), // Hard Rule: 필수
  valid_until:  date('valid_until'),
  supersedes:   uuid('supersedes'),            // self-FK — 동일 이슈어 뷰 변화 체인
  outcome:      text('outcome'),               // Phase 4: hit/miss/partial/open
  created_at:   timestamp('created_at', { withTimezone: true }).defaultNow(),
}, (t) => [
  index('idx_claims_sector_pub').on(t.sector, t.published_at),
  index('idx_claims_issuer_sector').on(t.issuer, t.sector),
  index('idx_claims_source').on(t.source_id),
  index('idx_claims_concept').on(t.core_concept),
  index('idx_claims_item_type').on(t.item_type),
])

// ── Phase 2.1: concepts ───────────────────────────────────────────────────────
// 섹터 간 교차 컨셉 taxonomy. configs/taxonomy.yaml에서 upsert.
// status='candidate'는 claims 추출 중 taxonomy에 없는 core_concept 자동 발견분.
export const concepts = pgTable('concepts', {
  id:               uuid('id').primaryKey().default(sql`gen_random_uuid()`),
  slug:             text('slug').notNull().unique(),  // taxonomy.yaml concepts.id
  canonical_name:   text('canonical_name').notNull(),
  aliases:          text('aliases').array(),
  definition:       text('definition'),
  related_sectors:  text('related_sectors').array(),
  status:           text('status').notNull().default('active'), // active | candidate | merged
  first_seen_at:    date('first_seen_at'),
  last_seen_at:     date('last_seen_at'),
  created_at:       timestamp('created_at', { withTimezone: true }).defaultNow(),
  updated_at:       timestamp('updated_at', { withTimezone: true }).defaultNow(),
}, (t) => [
  index('idx_concepts_status').on(t.status),
])

// ── Phase 2.2: trend_scores ───────────────────────────────────────────────────
// 섹터·컨셉별 주기 집계. Mention(언급 강도)과 Importance(숫자 근거 강도)를
// 분리 — 합산해 단일 랭킹으로 만들지 않는다.
export const trend_scores = pgTable('trend_scores', {
  id:                 uuid('id').primaryKey().default(sql`gen_random_uuid()`),
  period_start:       date('period_start').notNull(),
  period_end:         date('period_end').notNull(),
  target_type:        text('target_type').notNull(),  // 'sector' | 'concept'
  target_id:          text('target_id').notNull(),    // sector id 또는 concept slug
  mention_score:      real('mention_score'),
  importance_score:   real('importance_score'),
  momentum_score:     real('momentum_score'),
  novelty_score:      real('novelty_score'),
  anomaly_score:      real('anomaly_score'),
  mention_count:      integer('mention_count'),
  source_diversity:   integer('source_diversity'),   // 서로 다른 issuer 수
  metric_count:       integer('metric_count'),       // metrics 포함 claims 수
  evidence_quality:   real('evidence_quality'),
  score_details:      jsonb('score_details'),         // 계산 근거 스냅샷 (감사용)
  created_at:         timestamp('created_at', { withTimezone: true }).defaultNow(),
}, (t) => [
  // UNIQUE 필수 — knowledge/scoring.py 가 이 조합으로 ON CONFLICT upsert 수행
  uniqueIndex('idx_ts_target_period').on(t.target_type, t.target_id, t.period_start),
])

// ── Phase 2.3: anomalies ──────────────────────────────────────────────────────
// 이상 징후 후보 — 확정 판단이 아니라 사람이 검토할 큐 (§2.5 트리아지와 동일 원칙).
export const anomalies = pgTable('anomalies', {
  id:                     uuid('id').primaryKey().default(sql`gen_random_uuid()`),
  detected_at:            timestamp('detected_at', { withTimezone: true }).defaultNow(),
  anomaly_type:           text('anomaly_type').notNull(),
  // mention_spike | source_diversity_jump | high_importance_low_mention |
  // counter_signal | metric_divergence | visual_only_signal | new_concept_emergence
  title:                  text('title'),
  description:            text('description'),
  related_concepts:       text('related_concepts').array(),
  related_sectors:        text('related_sectors').array(),
  related_claim_ids:      uuid('related_claim_ids').array(),
  previous_period:        jsonb('previous_period'),
  current_period:         jsonb('current_period'),
  severity:               text('severity'),        // low | medium | high
  review_required:        boolean('review_required').notNull().default(true),
  status:                 text('status').notNull().default('open'), // open | reviewed | dismissed
}, (t) => [
  index('idx_anomalies_status').on(t.status),
  index('idx_anomalies_type').on(t.anomaly_type),
])

// ── Phase 2: review_log ───────────────────────────────────────────────────────
// 사람 판정 이력. 반려 피드백 루프의 원료.
// reason_tag 없이 반려 불가 (Hard Rule). R2 루틴이 패턴 분석에 활용.
export const review_log = pgTable('review_log', {
  id:         uuid('id').primaryKey().default(sql`gen_random_uuid()`),
  source_id:  uuid('source_id').notNull().references(() => sources.id),
  decision:   text('decision').notNull(),   // accept / reject
  reason_tag: text('reason_tag'),           // irrelevant/shallow/duplicate/stale (반려 시 필수)
  note:       text('note'),
  created_at: timestamp('created_at', { withTimezone: true }).defaultNow(),
}, (t) => [
  index('idx_rl_source').on(t.source_id),
  index('idx_rl_decision').on(t.decision),
])

// ── Phase 4: chat_sessions ────────────────────────────────────────────────────
export const chat_sessions = pgTable('chat_sessions', {
  id:         uuid('id').primaryKey().default(sql`gen_random_uuid()`),
  mode:       text('mode').notNull().default('normal'),  // normal | historical
  created_at: timestamp('created_at', { withTimezone: true }).defaultNow(),
  updated_at: timestamp('updated_at', { withTimezone: true }).defaultNow(),
})

// ── Phase 4: chat_messages ────────────────────────────────────────────────────
export const chat_messages = pgTable('chat_messages', {
  id:         uuid('id').primaryKey().default(sql`gen_random_uuid()`),
  session_id: uuid('session_id').notNull().references(() => chat_sessions.id, { onDelete: 'cascade' }),
  role:       text('role').notNull(),     // user | assistant
  content:    text('content').notNull(),
  sources:    jsonb('sources'),           // [{title,url,issuer,published_at,sector}]
  created_at: timestamp('created_at', { withTimezone: true }).defaultNow(),
}, (t) => [
  index('idx_cm_session').on(t.session_id),
])

// ── 범용 설정 저장소 ─────────────────────────────────────────────────────────
export const settings = pgTable('settings', {
  key:        text('key').primaryKey(),
  value:      text('value'),
  updated_at: timestamp('updated_at', { withTimezone: true }).defaultNow(),
})
