import { eq, sql } from 'drizzle-orm'
import { db } from './db'
import { settings } from '@/db/schema'

export async function getSetting(key: string): Promise<string | null> {
  const [row] = await db.select().from(settings).where(eq(settings.key, key))
  return row?.value ?? null
}

export async function getSettingJson<T>(key: string, fallback: T): Promise<T> {
  try {
    const value = await getSetting(key)
    return value ? (JSON.parse(value) as T) : fallback
  } catch { return fallback }
}

export async function upsertSetting(key: string, value: string): Promise<void> {
  await db.insert(settings)
    .values({ key, value })
    .onConflictDoUpdate({ target: settings.key, set: { value, updated_at: sql`now()` } })
}
