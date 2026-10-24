export type Lang = 'en' | 'de'
export type Localized = Record<Lang, string>

export interface Field {
  id: string
  label: Localized
  help: Localized
  sources: string[]
  demo: string
}

export interface FormSchema {
  id: string
  title: Localized
  note: Localized
  groups: { id: string; label: Localized; fields: Field[] }[]
  checklist: (Localized & { sources: string[] })[]
  sources: Record<string, { title: string; url: string }>
}

export interface Citation {
  n: number
  title: string
  section: string
  url: string
  excerpt: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  notice?: string
  error?: boolean
}
