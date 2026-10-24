import { useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react'
import { t } from '../i18n'
import type { ChatMessage, Citation, Lang } from '../types'

interface Props {
  lang: Lang
  messages: ChatMessage[]
  busy: boolean
  onSend: (text: string) => void
}

// Turn "[1]" markers into links to the matching citation.
function renderAnswer(text: string, citations: Citation[] = [], msgIndex: number): ReactNode[] {
  return text.split(/(\[\d+\])/g).map((part, i) => {
    const m = part.match(/^\[(\d+)\]$/)
    const c = m && citations.find((x) => x.n === Number(m[1]))
    if (!c) return part
    return (
      <a key={i} className="cite" href={`#cite-${msgIndex}-${c.n}`} title={c.title}>
        {c.n}
      </a>
    )
  })
}

export function Chat({ lang, messages, busy, onSend }: Props) {
  const [draft, setDraft] = useState('')
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), [messages, busy])

  const submit = (e: FormEvent) => {
    e.preventDefault()
    if (!draft.trim() || busy) return
    onSend(draft.trim())
    setDraft('')
  }

  return (
    <section className="panel chat" aria-labelledby="chat-title">
      <h2 id="chat-title">{t('chatTitle', lang)}</h2>
      <div className="messages" aria-live="polite">
        {messages.length === 0 && (
          <div className="examples">
            {t('examples', lang).map((q) => (
              <button key={q} type="button" className="chip" onClick={() => onSend(q)} disabled={busy}>
                {q}
              </button>
            ))}
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}${m.error ? ' error' : ''}`}>
            {m.notice && <p className="notice">{m.notice}</p>}
            <p>{m.role === 'assistant' ? renderAnswer(m.content, m.citations, i) : m.content}</p>
            {m.citations && m.citations.length > 0 && (
              <details className="sources">
                <summary>
                  {t('sources', lang)} ({m.citations.length})
                </summary>
                <ol>
                  {m.citations.map((c) => (
                    <li key={c.n} id={`cite-${i}-${c.n}`} value={c.n}>
                      <a href={c.url} target="_blank" rel="noreferrer">
                        {c.title}
                      </a>
                      {c.section !== c.title && <span className="section"> · {c.section}</span>}
                      <blockquote lang="de">{c.excerpt}…</blockquote>
                    </li>
                  ))}
                </ol>
              </details>
            )}
          </div>
        ))}
        {busy && <div className="msg assistant pending">{t('thinking', lang)}</div>}
        <div ref={endRef} />
      </div>
      <form className="composer" onSubmit={submit}>
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={t('placeholder', lang)}
          maxLength={1000}
          aria-label={t('placeholder', lang)}
        />
        <button type="submit" disabled={busy || !draft.trim()}>
          {t('send', lang)}
        </button>
      </form>
    </section>
  )
}
