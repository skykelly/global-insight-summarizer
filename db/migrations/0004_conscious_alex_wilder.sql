DROP INDEX "idx_ts_target_period";--> statement-breakpoint
CREATE UNIQUE INDEX "idx_ts_target_period" ON "trend_scores" USING btree ("target_type","target_id","period_start");