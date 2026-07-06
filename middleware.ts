import NextAuth from 'next-auth'
import { authConfig } from './auth.config'

// auth.config만 import — jose DecompressionStream Edge 오류 방지
export const { auth: middleware } = NextAuth(authConfig)

export const config = {
  matcher: [
    // /auth/*, /api/auth/*, Next 내부 자원, favicon 제외한 전부
    '/((?!auth|api/auth|_next/static|_next/image|favicon.ico).*)',
  ],
}
