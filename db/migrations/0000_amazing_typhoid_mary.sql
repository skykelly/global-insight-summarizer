-- pgvector extension — Neon에서 CREATE EXTENSION 은 관리자 권한 필요.
-- Neon 콘솔 → SQL Editor 에서 먼저 실행하거나 Neon 대시보드 Extensions 탭 활용.
CREATE EXTENSION IF NOT EXISTS vector;
--> statement-breakpoint
CREATE TABLE "knowledge_embeddings" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"ref_type" text NOT NULL,
	"ref_id" uuid NOT NULL,
	"content" text NOT NULL,
	"embedding" vector(1536),
	"metadata" jsonb DEFAULT '{}',
	"created_at" timestamp with time zone DEFAULT now()
);
--> statement-breakpoint
CREATE TABLE "knowledge_items" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"source_id" uuid NOT NULL,
	"title" text,
	"content" text NOT NULL,
	"item_type" text NOT NULL,
	"published_at" date NOT NULL,
	"sector" text,
	"issuer" text,
	"metadata" jsonb DEFAULT '{}',
	"created_at" timestamp with time zone DEFAULT now()
);
--> statement-breakpoint
CREATE TABLE "raw_sources" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"url" text NOT NULL,
	"url_normalized" text NOT NULL,
	"content_hash" text NOT NULL,
	"raw_content" text,
	"blob_url" text,
	"source_yaml_id" text NOT NULL,
	"issuer" text,
	"fetched_at" timestamp with time zone,
	"created_at" timestamp with time zone DEFAULT now()
);
--> statement-breakpoint
CREATE TABLE "settings" (
	"key" text PRIMARY KEY NOT NULL,
	"value" text,
	"updated_at" timestamp with time zone DEFAULT now()
);
--> statement-breakpoint
CREATE TABLE "sources" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"raw_source_id" uuid,
	"title" text NOT NULL,
	"url" text NOT NULL,
	"issuer" text NOT NULL,
	"published_at" date NOT NULL,
	"sector_tags" text[] DEFAULT '{}',
	"content_text" text,
	"blob_url" text,
	"status" text DEFAULT 'pending' NOT NULL,
	"created_at" timestamp with time zone DEFAULT now(),
	"updated_at" timestamp with time zone DEFAULT now()
);
--> statement-breakpoint
CREATE TABLE "summaries" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"source_id" uuid NOT NULL,
	"content_ko" text NOT NULL,
	"model" text DEFAULT 'claude-sonnet-4-6' NOT NULL,
	"created_at" timestamp with time zone DEFAULT now()
);
--> statement-breakpoint
ALTER TABLE "knowledge_items" ADD CONSTRAINT "knowledge_items_source_id_sources_id_fk" FOREIGN KEY ("source_id") REFERENCES "public"."sources"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "sources" ADD CONSTRAINT "sources_raw_source_id_raw_sources_id_fk" FOREIGN KEY ("raw_source_id") REFERENCES "public"."raw_sources"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "summaries" ADD CONSTRAINT "summaries_source_id_sources_id_fk" FOREIGN KEY ("source_id") REFERENCES "public"."sources"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
CREATE INDEX "idx_ke_ref" ON "knowledge_embeddings" USING btree ("ref_type","ref_id");--> statement-breakpoint
CREATE INDEX "idx_ki_source" ON "knowledge_items" USING btree ("source_id");--> statement-breakpoint
CREATE INDEX "idx_ki_sector_pub" ON "knowledge_items" USING btree ("sector","published_at");--> statement-breakpoint
CREATE INDEX "idx_raw_sources_hash" ON "raw_sources" USING btree ("content_hash");--> statement-breakpoint
CREATE INDEX "idx_raw_sources_url" ON "raw_sources" USING btree ("url_normalized");--> statement-breakpoint
CREATE INDEX "idx_sources_issuer_pub" ON "sources" USING btree ("issuer","published_at");--> statement-breakpoint
CREATE INDEX "idx_sources_status" ON "sources" USING btree ("status");--> statement-breakpoint
CREATE INDEX "idx_sources_sector" ON "sources" USING btree ("sector_tags");