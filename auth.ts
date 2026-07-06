import NextAuth from 'next-auth'
import Credentials from 'next-auth/providers/credentials'

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    Credentials({
      credentials: {
        email:    { label: 'Email',    type: 'email'    },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        if (
          credentials?.email    === process.env.AUTH_ADMIN_EMAIL &&
          credentials?.password === process.env.AUTH_ADMIN_PASSWORD
        ) {
          return { id: '1', email: credentials.email as string, name: 'Admin' }
        }
        return null
      },
    }),
  ],
  session: { strategy: 'jwt' },
  pages: { signIn: '/auth/signin' },
})
