'use client'
import { useMemo } from 'react'
import { diffLines } from '@/lib/diff'

export default function DiffView({ oldText, newText }: { oldText: string; newText: string }) {
  const lines = useMemo(() => diffLines(oldText, newText), [oldText, newText])
  const added = lines.filter((l) => l.type === 'add').length
  const removed = lines.filter((l) => l.type === 'remove').length

  if (added === 0 && removed === 0) {
    return <p className="text-sm text-neutral-600">현재 게시된 내용과 차이가 없습니다.</p>
  }

  return (
    <div>
      <p className="text-xs text-neutral-500 mb-2">
        게시된 내용 대비 <span className="text-emerald-500">+{added}</span>{' '}
        <span className="text-rose-500">-{removed}</span>
      </p>
      <pre className="text-xs font-mono whitespace-pre-wrap break-words leading-relaxed">
        {lines.map((line, i) => (
          <div
            key={i}
            className={
              line.type === 'add'
                ? 'bg-emerald-950/40 text-emerald-300'
                : line.type === 'remove'
                ? 'bg-rose-950/40 text-rose-300'
                : 'text-neutral-500'
            }
          >
            {line.type === 'add' ? '+ ' : line.type === 'remove' ? '- ' : '  '}
            {line.text || ' '}
          </div>
        ))}
      </pre>
    </div>
  )
}
