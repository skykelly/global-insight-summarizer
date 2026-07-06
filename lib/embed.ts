import OpenAI from 'openai'
import { and, eq } from 'drizzle-orm'
import { db } from './db'
import { knowledge_embeddings } from '@/db/schema'

const EMBED_MODEL = 'text-embedding-3-small'
const BATCH_SIZE = 20

export function chunkText(text: string, maxLen = 1200, overlap = 150): string[] {
  if (!text?.trim()) return []
  if (text.length <= maxLen) return [text]

  const chunks: string[] = []
  let start = 0
  while (start < text.length) {
    const end = Math.min(start + maxLen, text.length)
    chunks.push(text.slice(start, end))
    if (end >= text.length) break
    start = end - overlap
  }
  return chunks
}

export async function rebuildEmbeddings(
  refType: string,
  refId: string,
  chunks: string[]
): Promise<void> {
  await db.delete(knowledge_embeddings).where(
    and(
      eq(knowledge_embeddings.ref_type, refType),
      eq(knowledge_embeddings.ref_id, refId)
    )
  )

  if (chunks.length === 0) return

  const client = new OpenAI()
  const rows: {
    ref_type: string; ref_id: string; content: string
    embedding: number[]; metadata: Record<string, unknown>
  }[] = []

  for (let i = 0; i < chunks.length; i += BATCH_SIZE) {
    const batch = chunks.slice(i, i + BATCH_SIZE)
    const res = await client.embeddings.create({ model: EMBED_MODEL, input: batch })
    for (let j = 0; j < batch.length; j++) {
      rows.push({
        ref_type: refType,
        ref_id: refId,
        content: batch[j],
        embedding: res.data[j].embedding,
        metadata: {},
      })
    }
  }

  // Insert in batches of 50
  for (let i = 0; i < rows.length; i += 50) {
    await db.insert(knowledge_embeddings).values(rows.slice(i, i + 50))
  }
}
