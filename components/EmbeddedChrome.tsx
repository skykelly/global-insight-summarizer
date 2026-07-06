'use client'
import { useEffect } from 'react'

export default function EmbeddedChrome() {
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    document.body.toggleAttribute('data-embedded', params.get('popup') === '1')
  }, [])
  return null
}
