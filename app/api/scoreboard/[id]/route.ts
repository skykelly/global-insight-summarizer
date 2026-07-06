import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { claims } from '@/db/schema'
import { eq } from 'drizzle-orm'
import { auth } from '@/auth'

type Params = { params: Promise<{ id: string }> }

const VALID_OUTCOMES = ['hit', 'miss', 'partial', 'open'] as const
type Outcome = typeof VALID_OUTCOMES[number]

export async function PATCH(req: NextRequest, { params }: Params) {
  const session = await auth()
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const { id } = await params
  const { outcome } = await req.json() as { outcome: Outcome | null }

  if (outcome !== null && !VALID_OUTCOMES.includes(outcome as Outcome)) {
    return NextResponse.json({ error: 'Invalid outcome' }, { status: 400 })
  }

  const [updated] = await db
    .update(claims)
    .set({ outcome: outcome ?? null })
    .where(eq(claims.id, id))
    .returning({ id: claims.id, outcome: claims.outcome })

  if (!updated) return NextResponse.json({ error: 'Not found' }, { status: 404 })

  return NextResponse.json({ ok: true, outcome: updated.outcome })
}
