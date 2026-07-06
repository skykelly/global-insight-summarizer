import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-24 text-center">
      <h1 className="text-2xl font-semibold text-white mb-2">페이지를 찾을 수 없습니다</h1>
      <p className="text-sm text-neutral-500 mb-6">요청하신 페이지가 존재하지 않거나 이동되었습니다.</p>
      <Link
        href="/"
        className="inline-block text-sm bg-accent-600 hover:bg-accent-700 text-white px-4 py-2 rounded-lg transition-colors"
      >
        홈으로
      </Link>
    </div>
  )
}
