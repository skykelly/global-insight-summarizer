// ============================================================================
// Research Wiki — Drizzle 스키마 (단일 진실)  ·  HANDOVER §2
// 스키마 변경 순서: 이 파일 수정 → npm run db:generate → Neon dev 검증 → main 적용
// ============================================================================

import {
  pgTable,
  text, date, jsonb, uuid, timestamp, index, customType
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
// Phase 2 에서 status 값 확장: pending|auto_accepted|queued|accepted|rejected
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
  // pending: 수집 완료, 지식화 대기
  // processing: 지식 파이프라인 실행 중
  // done: 지식화 완료
  // failed: 처리 실패
  // Phase 2 추가: auto_accepted | queued | accepted | rejected (게이트 통과 상태)
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

// ── 범용 설정 저장소 ─────────────────────────────────────────────────────────
export const settings = pgTable('settings', {
  key:        text('key').primaryKey(),
  value:      text('value'),
  updated_at: timestamp('updated_at', { withTimezone: true }).defaultNow(),
})
