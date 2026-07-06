import { notFound } from 'next/navigation'
import { promises as fs } from 'fs'
import path from 'path'
import { remark } from 'remark'
import remarkGfm from 'remark-gfm'
import remarkHtml from 'remark-html'
import MarkdownRenderer from '@/components/MarkdownRenderer'

const SECTORS = ['power_equipment', 'ai_semis'] as const
type Sector = typeof SECTORS[number]

const SECTOR_META: Record<Sector, { label: string; description: string }> = {
  power_equipment: {
    label: '전력기기',
    description: '변압기·HVDC·ESS·전력망 인프라 섹터 리서치 wiki',
  },
  ai_semis: {
    label: 'AI 반도체',
    description: 'GPU·HBM·CoWoS·AI 가속기·데이터센터 칩 섹터 리서치 wiki',
  },
}

export async function generateStaticParams() {
  return SECTORS.map((sector) => ({ sector }))
}

type Params = { params: Promise<{ sector: string }> }

export default async function WikiPage({ params }: Params) {
  const { sector } = await params

  if (!SECTORS.includes(sector as Sector)) notFound()

  const meta = SECTOR_META[sector as Sector]
  const wikiPath = path.join(process.cwd(), 'kb', 'wiki', `${sector}.md`)

  let html = ''
  let isEmpty = false

  try {
    let raw = await fs.readFile(wikiPath, 'utf-8')

    // frontmatter 제거 (--- ... --- 블록)
    raw = raw.replace(/^---[\s\S]*?---\n/, '')

    const result = await remark().use(remarkGfm).use(remarkHtml).process(raw)
    html = String(result)
  } catch {
    isEmpty = true
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      {/* 헤더 */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <a href="/" className="text-xs text-neutral-600 hover:text-neutral-400 transition-colors">
            Research Wiki
          </a>
          <span className="text-neutral-700">/</span>
          <span className="text-xs text-neutral-400">{meta.label}</span>
        </div>
        <h1 className="text-xl font-semibold text-white">{meta.label}</h1>
        <p className="text-sm text-neutral-500 mt-1">{meta.description}</p>
      </div>

      {/* 콘텐츠 */}
      {isEmpty ? (
        <div className="py-16 text-center">
          <p className="text-sm text-neutral-500">
            아직 wiki가 생성되지 않았습니다.
          </p>
          <p className="text-xs text-neutral-600 mt-2">
            충분한 claims가 수집되면 자동 생성됩니다
            (신규 claims 5건 누적 또는 주 1회).
          </p>
          <code className="text-xs text-neutral-700 mt-4 block">
            python3 knowledge/generate_wiki.py --sector {sector} --force
          </code>
        </div>
      ) : (
        <MarkdownRenderer html={html} />
      )}
    </div>
  )
}
