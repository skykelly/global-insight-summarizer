import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { sources, review_log } from '@/db/schema'
import { eq } from 'drizzle-orm'
import { auth } from '@/auth'

type Params = { params: Promise<{ id: string }> }

export async function POST(req: NextRequest, { params }: Params) {
  const session = await auth()
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const { id } = await params
  const body = await req.json() as {
    decision: 'accept' | 'reject'
    reason_tag?: string
    note?: string
  }

  const { decision, reason_tag, note } = body

  if (!['accept', 'reject'].includes(decision)) {
    return NextResponse.json({ error: 'Invalid decision' }, { status: 400 })
  }

  // Hard Rule: 반려 시 reason_tag 필수
  if (decision === 'reject' && !reason_tag) {
    return NextResponse.json({ error: 'reason_tag required for rejection' }, { status: 400 })
  }

  const [existing] = await db
    .select({ status: sources.status })
    .from(sources)
    .where(eq(sources.id, id))

  if (!existing) {
    return NextResponse.json({ error: 'Source not found' }, { status: 404 })
  }

  if (!['queued', 'pending'].includes(existing.status)) {
    return NextResponse.json({ error: 'Source is not in review queue' }, { status: 409 })
  }

  const newStatus = decision === 'accept' ? 'accepted' : 'rejected'

  await db.transaction(async (tx) => {
    await tx
      .update(sources)
      .set({ status: newStatus, updated_at: new Date() })
      .where(eq(sources.id, id))

    await tx.insert(review_log).values({
      source_id: id,
      decision,
      reason_tag: reason_tag ?? null,
      note: note ?? null,
    })
  })

  return NextResponse.json({ ok: true, status: newStatus })
}
