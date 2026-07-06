import { remark } from 'remark'
import remarkGfm from 'remark-gfm'
import remarkHtml from 'remark-html'

export async function renderMarkdown(raw: string): Promise<string> {
  if (!raw) return ''
  const result = await remark()
    .use(remarkGfm)
    .use(remarkHtml, { sanitize: false })
    .process(raw)
  return result.toString()
}
