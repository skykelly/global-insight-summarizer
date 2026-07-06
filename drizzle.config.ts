import { defineConfig } from 'drizzle-kit'

// HANDOVER §2: db/schema.ts 가 스키마의 단일 진실. drizzle-kit generate 산출물은 db/migrations/.
// 마이그레이션은 Neon dev 브랜치에서 먼저 검증 후 main 적용 (CLAUDE.md Hard Rules).
export default defineConfig({
  schema: './db/schema.ts',
  out: './db/migrations',
  dialect: 'postgresql',
  dbCredentials: { url: process.env.DATABASE_URL_UNPOOLED! },
})
