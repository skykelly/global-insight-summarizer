import { NextRequest, NextResponse } from 'next/server'

// next-auth를 import하지 않음 — jose 호환성 문제 우회
// JWT 검증은 각 route/page의 auth() 콜에서 수행
export function middleware(req: NextRequest) {
  // next-auth v5 및 v4 양쪽 쿠키명 모두 확인
  const session =
    req.cookies.get('__Secure-authjs.session-token') ??  // v5 HTTPS
    req.cookies.get('authjs.session-token') ??            // v5 HTTP
    req.cookies.get('__Secure-next-auth.session-token') ?? // v4 HTTPS
    req.cookies.get('next-auth.session-token')             // v4 HTTP

  if (!session) {
    const url = req.nextUrl.clone()
    url.pathname = '/auth/signin'
    url.searchParams.set('callbackUrl', req.nextUrl.pathname)
    return NextResponse.redirect(url)
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    '/((?!auth|api/auth|_next/static|_next/image|favicon.ico).*)',
  ],
}
