// app/wiki/page.tsx — /wiki 단독 접근 시 Antenna 위키 화면으로.
import { redirect } from 'next/navigation'

export default function WikiIndexPage() {
  redirect('/observatory?nav=wiki')
}
