'use client'
import { signIn } from 'next-auth/react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useState, Suspense } from 'react'

function SignInForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const callbackUrl = searchParams.get('callbackUrl') || '/'

  const [error, setError] = useState(false)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = new FormData(e.currentTarget)
    setLoading(true)
    setError(false)

    const result = await signIn('credentials', {
      email:    fd.get('email'),
      password: fd.get('password'),
      redirect: false,
    })

    setLoading(false)

    if (result?.ok) {
      router.push(callbackUrl)
      router.refresh()
    } else {
      setError(true)
    }
  }

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-8 shadow-2xl">
          <h1 className="text-white text-xl font-semibold mb-1">Research Wiki</h1>
          <p className="text-neutral-500 text-sm mb-8">관리자 로그인</p>

          {error && (
            <p className="text-red-400 text-sm bg-red-950/40 border border-red-900 rounded-lg px-4 py-3 mb-6">
              이메일 또는 패스워드가 올바르지 않습니다.
            </p>
          )}

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div>
              <label className="block text-xs text-neutral-400 mb-1.5">이메일</label>
              <input
                name="email"
                type="email"
                required
                autoComplete="email"
                className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2.5 text-sm text-white placeholder-neutral-600 focus:outline-none focus:border-neutral-500 focus:ring-1 focus:ring-neutral-500"
              />
            </div>
            <div>
              <label className="block text-xs text-neutral-400 mb-1.5">패스워드</label>
              <input
                name="password"
                type="password"
                required
                autoComplete="current-password"
                className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2.5 text-sm text-white placeholder-neutral-600 focus:outline-none focus:border-neutral-500 focus:ring-1 focus:ring-neutral-500"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="mt-2 w-full bg-accent-600 hover:bg-accent-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg py-2.5 transition-colors"
            >
              {loading ? '로그인 중…' : '로그인'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

export default function SignInPage() {
  return (
    <Suspense>
      <SignInForm />
    </Suspense>
  )
}
