'use client'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

export default function SearchBox({ className }: { className?: string }) {
  const router = useRouter()
  const [q, setQ] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const query = q.trim()
    router.push(query ? `/search?q=${encodeURIComponent(query)}` : '/search')
  }

  return (
    <form onSubmit={handleSubmit} className={className}>
      <input
        type="search"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="검색…"
        className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-3 py-1.5 text-sm text-white placeholder-neutral-600 focus:outline-none focus:border-neutral-600"
      />
    </form>
  )
}
