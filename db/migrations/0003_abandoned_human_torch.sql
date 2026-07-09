CREATE TABLE "anomalies" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"detected_at" timestamp with time zone DEFAULT now(),
	"anomaly_type" text NOT NULL,
	"title" text,
	"description" text,
	"related_concepts" text[],
	"related_sectors" text[],
	"related_claim_ids" uuid[],
	"previous_period" jsonb,
	"current_period" jsonb,
	"severity" text,
	"review_required" boolean DEFAULT true NOT NULL,
	"status" text DEFAULT 'open' NOT NULL
);
--> statement-breakpoint
CREATE TABLE "concepts" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"slug" text NOT NULL,
	"canonical_name" text NOT NULL,
	"aliases" text[],
	"definition" text,
	"related_sectors" text[],
	"status" text DEFAULT 'active' NOT NULL,
	"first_seen_at" date,
	"last_seen_at" date,
	"created_at" timestamp with time zone DEFAULT now(),
	"updated_at" timestamp with time zone DEFAULT now(),
	CONSTRAINT "concepts_slug_unique" UNIQUE("slug")
);
--> statement-breakpoint
CREATE TABLE "trend_scores" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"period_start" date NOT NULL,
	"period_end" date NOT NULL,
	"target_type" text NOT NULL,
	"target_id" text NOT NULL,
	"mention_score" real,
	"importance_score" real,
	"momentum_score" real,
	"novelty_score" real,
	"anomaly_score" real,
	"mention_count" integer,
	"source_diversity" integer,
	"metric_count" integer,
	"evidence_quality" real,
	"score_details" jsonb,
	"created_at" timestamp with time zone DEFAULT now()
);
--> statement-breakpoint
ALTER TABLE "claims" ADD COLUMN "related_sectors" text[];--> statement-breakpoint
ALTER TABLE "claims" ADD COLUMN "item_type" text DEFAULT 'claim' NOT NULL;--> statement-breakpoint
ALTER TABLE "claims" ADD COLUMN "core_concept" text;--> statement-breakpoint
ALTER TABLE "claims" ADD COLUMN "canonical_title" text;--> statement-breakpoint
ALTER TABLE "claims" ADD COLUMN "trend_direction" text;--> statement-breakpoint
ALTER TABLE "claims" ADD COLUMN "time_horizon" text;--> statement-breakpoint
ALTER TABLE "claims" ADD COLUMN "evidence" jsonb;--> statement-breakpoint
ALTER TABLE "claims" ADD COLUMN "mention_relevance_score" real;--> statement-breakpoint
ALTER TABLE "claims" ADD COLUMN "importance_evidence_score" real;--> statement-breakpoint
ALTER TABLE "claims" ADD COLUMN "novelty_score" real;--> statement-breakpoint
ALTER TABLE "claims" ADD COLUMN "anomaly_score" real;--> statement-breakpoint
ALTER TABLE "claims" ADD COLUMN "confidence_score" real;--> statement-breakpoint
CREATE INDEX "idx_anomalies_status" ON "anomalies" USING btree ("status");--> statement-breakpoint
CREATE INDEX "idx_anomalies_type" ON "anomalies" USING btree ("anomaly_type");--> statement-breakpoint
CREATE INDEX "idx_concepts_status" ON "concepts" USING btree ("status");--> statement-breakpoint
CREATE INDEX "idx_ts_target_period" ON "trend_scores" USING btree ("target_type","target_id","period_start");--> statement-breakpoint
CREATE INDEX "idx_claims_concept" ON "claims" USING btree ("core_concept");--> statement-breakpoint
CREATE INDEX "idx_claims_item_type" ON "claims" USING btree ("item_type");