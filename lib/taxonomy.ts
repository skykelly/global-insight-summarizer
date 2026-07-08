// lib/taxonomy.ts — configs/taxonomy.yaml 로더 (TS 쪽).
// Python의 knowledge/taxonomy.py와 대칭. 섹터·컨셉의 단일 진실은 configs/taxonomy.yaml —
// 하드코딩 금지. nodejs 런타임 전용(fs 사용) — edge 런타임에서는 호출 금지.

import { readFileSync } from 'fs'
import path from 'path'
import yaml from 'js-yaml'

export type Sector = {
  id: string
  rank_seed: number
  name: string
  name_en: string
  description: string
  active: boolean
  legacy_alias?: string
}

export type Concept = {
  id: string
  canonical_name: string
  aliases?: string[]
  definition: string
  related_sectors: string[]
}

type TaxonomyFile = { sectors: Sector[]; concepts: Concept[] }

let _cache: TaxonomyFile | null = null

function load(): TaxonomyFile {
  if (_cache) return _cache
  const filePath = path.join(process.cwd(), 'configs', 'taxonomy.yaml')
  _cache = yaml.load(readFileSync(filePath, 'utf-8')) as TaxonomyFile
  return _cache
}

export function allSectors(): Sector[] {
  return load().sectors
}

export function activeSectors(): Sector[] {
  return allSectors().filter((s) => s.active)
}

export function sectorIds(activeOnly = false): string[] {
  return (activeOnly ? activeSectors() : allSectors()).map((s) => s.id)
}

export function sectorLabel(sectorId: string): string {
  return allSectors().find((s) => s.id === sectorId)?.name ?? sectorId
}

export function allConcepts(): Concept[] {
  return load().concepts
}

/** 자연어 질의에서 섹터 힌트를 찾는다 — 2-pass 매칭:
 * 1차: id·legacy_alias 정확 매칭(가장 신뢰도 높음, 예: "ai_semis" → semi)
 * 2차: 섹터명 하위 토큰 매칭(예: "전력망 전망 알려줘" → "전력망·에너지 안보"의 "전력망")
 *   - 한글 토큰은 2자 이상, 순수 영문 토큰(AI 등 범용 약어로 여러 섹터에 걸침)은 3자 이상만 후보. */
export function detectSectorHint(query: string): string | null {
  const q = query.toLowerCase()

  for (const s of allSectors()) {
    const idLike = [s.id, s.legacy_alias].filter(Boolean) as string[]
    if (idLike.some((c) => q.includes(c.toLowerCase()))) return s.id
  }

  for (const s of allSectors()) {
    const nameTokens = s.name
      .split(/[·\s]+/)
      .filter((t) => (/^[a-zA-Z]+$/.test(t) ? t.length >= 3 : t.length >= 2))
    if (nameTokens.some((c) => q.includes(c.toLowerCase()))) return s.id
  }

  return null
}
