// app/wiki/[sector]/page.tsx — Antenna UI의 섹터 위키로 리다이렉트.
// 구 섹터 id(power_equipment·ai_semis)를 Antenna 섹터 id로 매핑한다.
import { redirect } from 'next/navigation'

const SECTOR_MAP: Record<string, string> = {
  power_equipment: 'power',
  ai_semis: 'semi',
}

export default async function WikiSectorPage({
  params,
}: {
  params: Promise<{ sector: string }>
}) {
  const { sector } = await params
  const mapped = SECTOR_MAP[sector] ?? sector
  redirect(`/observatory?nav=wiki&sector=${mapped}`)
}
