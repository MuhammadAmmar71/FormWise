import type { ChatMessage, Citation, Lang } from './types'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export interface ChatReply {
  answer: string
  citations: Citation[]
  lang: Lang
  route: string
  pii_warning: string | null
}

export async function sendChat(
  message: string,
  lang: Lang,
  history: ChatMessage[],
  fieldId?: string,
): Promise<ChatReply> {
  const res = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      lang,
      field_id: fieldId ?? null,
      history: history.filter((m) => !m.error).slice(-6).map(({ role, content }) => ({ role, content })),
    }),
  })
  if (res.status === 429) throw new Error('rate_limited')
  if (!res.ok) throw new Error('unavailable')
  return res.json()
}
