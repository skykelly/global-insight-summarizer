import { db } from '@/lib/db'
import { sources } from '@/db/schema'
import { eq, sql } from 'drizzle-orm'
import ReviewCard from './ReviewCard'

type QualityScores = { relevance?: number; density?: number; authority?: number; novelty?: number }

export const dynamic = 'force-dynamic'

export default async function ReviewPage() {
  const rawQueued = await db
    .select({
      id: sources.id,
      title: sources.title,
      url: sources.url,
      issuer: sources.issuer,
      published_at: sources.published_at,
      sector_tags: sources.sector_tags,
      quality: sources.quality,
      gate_note: sources.gate_note,
      claims_count: sql<number>`(SELECT COUNT(*) FROM claims WHERE claims.source_id = ${sources.id})`,
    })
    .from(sources)
    .where(eq(sources.status, 'queued'))
    .orderBy(sources.created_at)

  const queued = rawQueued.map((s) => ({
    ...s,
    quality: (s.quality ?? null) as QualityScores | null,
  }))

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-xl font-semibold text-white">검토 대기열</h1>
          <p className="text-sm text-neutral-500 mt-1">
            품질 게이트 경계 구간 문서 — 승인 또는 반려
          </p>
        </div>
        <span className="text-sm text-neutral-400 bg-neutral-800 px-3 py-1 rounded-full">
          {queued.length}건
        </span>
      </div>

      {queued.length === 0 ? (
        <p className="text-sm text-neutral-500 py-12 text-center">
          검토 대기 중인 문서가 없습니다.
        </p>
      ) : (
        <div className="space-y-4">
          {queued.map((source) => (
            <ReviewCard key={source.id} source={source} />
          ))}
        </div>
      )}
    </div>
  )
}
