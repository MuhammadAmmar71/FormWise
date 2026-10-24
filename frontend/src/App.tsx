import { useEffect, useState } from 'react'
import { sendChat } from './api'
import { Chat } from './components/Chat'
import { FormWalkthrough } from './components/FormWalkthrough'
import { form } from './form'
import { t } from './i18n'
import type { ChatMessage, Lang } from './types'

function initialLang(): Lang {
  try {
    const saved = localStorage.getItem('lang')
    if (saved === 'en' || saved === 'de') return saved
  } catch {
    /* storage unavailable */
  }
  return navigator.language.startsWith('de') ? 'de' : 'en'
}

const fieldLabels = Object.fromEntries(form.groups.flatMap((g) => g.fields).map((f) => [f.id, f.label]))

export default function App() {
  const [lang, setLang] = useState<Lang>(initialLang)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    document.documentElement.lang = lang
    try {
      localStorage.setItem('lang', lang)
    } catch {
      /* storage unavailable */
    }
  }, [lang])

  async function ask(text: string, fieldId?: string) {
    const shown = fieldId ? `${fieldLabels[fieldId][lang]}: ${text}` : text
    const history = messages
    setMessages((m) => [...m, { role: 'user', content: shown }])
    setBusy(true)
    try {
      const reply = await sendChat(text, lang, history, fieldId)
      setMessages((m) => [
        ...m,
        { role: 'assistant', content: reply.answer, citations: reply.citations, notice: reply.pii_warning ?? undefined },
      ])
    } catch (err) {
      const key = err instanceof Error && err.message === 'rate_limited' ? 'rateLimited' : 'unavailable'
      setMessages((m) => [...m, { role: 'assistant', content: t(key, lang), error: true }])
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <div className="banner" role="note">
        {t('banner', lang)}
      </div>
      <header className="top">
        <div>
          <h1>{t('appTitle', lang)}</h1>
          <p className="muted">{t('tagline', lang)}</p>
        </div>
        <div className="lang-toggle" role="group" aria-label="Language">
          {(['en', 'de'] as const).map((l) => (
            <button key={l} type="button" className={l === lang ? 'active' : ''} aria-pressed={l === lang} onClick={() => setLang(l)}>
              {l.toUpperCase()}
            </button>
          ))}
        </div>
      </header>
      <main className="layout">
        <Chat lang={lang} messages={messages} busy={busy} onSend={(q) => ask(q)} />
        <FormWalkthrough lang={lang} busy={busy} onAskField={(id) => ask(t('askFieldPrompt', lang), id)} />
      </main>
      <footer className="muted">
        {t('footer', lang)} ·{' '}
        <a href="https://github.com/" id="repo-link">
          GitHub
        </a>
      </footer>
    </>
  )
}
