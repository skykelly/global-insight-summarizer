'use client'

export default function Error({
  error, reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-24 text-center">
      <h1 className="text-2xl font-semibold text-white mb-2">문제가 발생했습니다</h1>
      <p className="text-sm text-neutral-500 mb-6">{error.message || '알 수 없는 오류가 발생했습니다.'}</p>
      <button
        onClick={reset}
        className="text-sm bg-accent-600 hover:bg-accent-700 text-white px-4 py-2 rounded-lg transition-colors"
      >
        다시 시도
      </button>
    </div>
  )
}
