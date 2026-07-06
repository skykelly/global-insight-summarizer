CREATE TABLE "claims" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"source_id" uuid NOT NULL,
	"issuer" text NOT NULL,
	"sector" text NOT NULL,
	"entities" text[],
	"claim_ko" text NOT NULL,
	"direction" text,
	"horizon" text,
	"metrics" jsonb,
	"published_at" date NOT NULL,
	"valid_until" date,
	"supersedes" uuid,
	"outcome" text,
	"created_at" timestamp with time zone DEFAULT now()
);
--> statement-breakpoint
CREATE TABLE "review_log" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"source_id" uuid NOT NULL,
	"decision" text NOT NULL,
	"reason_tag" text,
	"note" text,
	"created_at" timestamp with time zone DEFAULT now()
);
--> statement-breakpoint
ALTER TABLE "sources" ADD COLUMN "quality" jsonb;--> statement-breakpoint
ALTER TABLE "sources" ADD COLUMN "gate_note" text;--> statement-breakpoint
ALTER TABLE "claims" ADD CONSTRAINT "claims_source_id_sources_id_fk" FOREIGN KEY ("source_id") REFERENCES "public"."sources"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "review_log" ADD CONSTRAINT "review_log_source_id_sources_id_fk" FOREIGN KEY ("source_id") REFERENCES "public"."sources"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
CREATE INDEX "idx_claims_sector_pub" ON "claims" USING btree ("sector","published_at");--> statement-breakpoint
CREATE INDEX "idx_claims_issuer_sector" ON "claims" USING btree ("issuer","sector");--> statement-breakpoint
CREATE INDEX "idx_claims_source" ON "claims" USING btree ("source_id");--> statement-breakpoint
CREATE INDEX "idx_rl_source" ON "review_log" USING btree ("source_id");--> statement-breakpoint
CREATE INDEX "idx_rl_decision" ON "review_log" USING btree ("decision");