// app/scoreboard/page.tsx — Antenna UI로 리다이렉트.
// 스코어보드는 Antenna 홈 대시보드(섹터 스코어보드 · Mention/Importance 2축)로 흡수됨.
import { redirect } from 'next/navigation'

export default function ScoreboardPage() {
  redirect('/observatory?nav=dash')
}
