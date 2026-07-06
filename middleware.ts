import { auth } from './auth'
import { NextResponse } from 'next/server'

// D8 / HANDOVER §1: 개인 도구 — 전체 잠금(본인 계정 전용).
// 인증 경로·정적 자원만 예외, 나머지 전 라우트는 로그인 필수.
export default auth((req) => {
  if (!req.auth) {
    const url = req.nextUrl.clone()
    url.pathname = '/auth/signin'
    url.searchParams.set('callbackUrl', req.nextUrl.pathname)
    return NextResponse.redirect(url)
  }
})

export const config = {
  matcher: [
    // /auth/*, /api/auth/*, Next 내부 자원, favicon 제외한 전부
    '/((?!auth|api/auth|_next/static|_next/image|favicon.ico).*)',
  ],
}
