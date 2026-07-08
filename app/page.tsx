// app/page.tsx — 메인. Antenna UI(/observatory)로 리다이렉트.
import { redirect } from 'next/navigation'

export default function HomePage() {
  redirect('/observatory')
}
