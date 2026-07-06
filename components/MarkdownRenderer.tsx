'use client'

export default function MarkdownRenderer({ html }: { html: string }) {
  return (
    <div
      className="prose prose-invert prose-sm max-w-none
        prose-headings:text-white prose-headings:font-semibold
        prose-p:text-neutral-300 prose-p:leading-relaxed
        prose-a:text-accent-400 prose-a:no-underline hover:prose-a:underline
        prose-strong:text-white prose-code:text-accent-300 prose-code:bg-neutral-800 prose-code:px-1 prose-code:rounded
        prose-pre:bg-neutral-900 prose-pre:border prose-pre:border-neutral-800
        prose-blockquote:border-neutral-700 prose-blockquote:text-neutral-400
        prose-hr:border-neutral-800
        prose-img:rounded-xl prose-img:border prose-img:border-neutral-800
        prose-table:text-sm prose-th:text-neutral-300 prose-td:text-neutral-400"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}
