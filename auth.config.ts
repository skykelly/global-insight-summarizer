import type { NextAuthConfig } from 'next-auth'

// Edge Runtime에서 실행 가능한 최소 설정 (Credentials provider 제외)
// middleware.ts가 이 파일만 import → jose DecompressionStream 오류 방지
export const authConfig: NextAuthConfig = {
  pages: { signIn: '/auth/signin' },
  session: { strategy: 'jwt' },
  callbacks: {
    authorized({ auth, request: { nextUrl } }) {
      if (auth?.user) return true
      const signinUrl = new URL('/auth/signin', nextUrl)
      signinUrl.searchParams.set('callbackUrl', nextUrl.pathname)
      return Response.redirect(signinUrl)
    },
  },
  providers: [],  // Credentials는 auth.ts에만 — Edge 비호환
}
