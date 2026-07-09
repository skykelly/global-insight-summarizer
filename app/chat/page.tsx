// app/chat/page.tsx — Antenna UI의 챗 화면으로 리다이렉트.
// (구 RAG 챗 UI는 Antenna 디자인으로 교체됨. 백엔드 /api/chat 은 유지 — 데이터 배선 단계에서 재사용.)
import { redirect } from 'next/navigation'

export default function ChatPage() {
  redirect('/observatory?nav=chat')
}
