import type { Lang } from './types'

const strings = {
  appTitle: { en: 'FormWise', de: 'FormWise' },
  tagline: {
    en: 'Understand and fill in the German residence registration, explained from official sources.',
    de: 'Die Anmeldung einer Wohnung verstehen und ausfüllen – erklärt anhand offizieller Quellen.',
  },
  banner: {
    en: 'Unofficial student project – not legal advice and not affiliated with any authority. Do not enter real personal data.',
    de: 'Inoffizielles Studierendenprojekt – keine Rechtsberatung und keiner Behörde zugehörig. Bitte keine echten persönlichen Daten eingeben.',
  },
  chatTitle: { en: 'Ask a question', de: 'Frage stellen' },
  placeholder: { en: 'e.g. How long do I have to register?', de: 'z. B. Wie lange habe ich Zeit für die Anmeldung?' },
  send: { en: 'Send', de: 'Senden' },
  thinking: { en: 'Looking it up in the official sources…', de: 'Suche in den offiziellen Quellen…' },
  sources: { en: 'Sources', de: 'Quellen' },
  rateLimited: {
    en: 'Too many questions in a short time – please wait a minute.',
    de: 'Zu viele Fragen in kurzer Zeit – bitte warten Sie eine Minute.',
  },
  unavailable: {
    en: 'The assistant is unavailable right now (the free server may be waking up). Please try again in a moment.',
    de: 'Der Assistent ist gerade nicht erreichbar (der kostenlose Server startet evtl. noch). Bitte gleich erneut versuchen.',
  },
  formTitle: { en: 'Form walkthrough', de: 'Formular Schritt für Schritt' },
  demoFill: { en: 'Fill with demo data', de: 'Mit Demodaten füllen' },
  clear: { en: 'Clear', de: 'Leeren' },
  demoNotice: {
    en: 'Practice only: entries stay in your browser and are never sent anywhere. Use invented data.',
    de: 'Nur zum Üben: Eingaben bleiben in Ihrem Browser und werden nirgendwohin gesendet. Nutzen Sie erfundene Daten.',
  },
  why: { en: 'Why is this asked?', de: 'Warum wird das gefragt?' },
  askField: { en: 'Ask about this field', de: 'Zu diesem Feld fragen' },
  askFieldPrompt: { en: 'What should I enter here, and why?', de: 'Was trage ich hier ein und warum?' },
  back: { en: 'Back', de: 'Zurück' },
  next: { en: 'Next', de: 'Weiter' },
  checklist: { en: 'What to bring', de: 'Was Sie mitbringen müssen' },
  step: { en: 'Step', de: 'Schritt' },
  of: { en: 'of', de: 'von' },
  footer: {
    en: 'Inspired by research on conversational agents for administrative form-filling at Universität Koblenz. Not endorsed by the university.',
    de: 'Inspiriert von Forschung zu Conversational Agents für das Ausfüllen von Verwaltungsformularen an der Universität Koblenz. Nicht von der Universität unterstützt.',
  },
  examples: {
    en: ['How long do I have to register?', 'What is a Wohnungsgeberbestätigung?', 'I only stay 2 months – do I need to register?'],
    de: ['Wie lange habe ich Zeit für die Anmeldung?', 'Was ist eine Wohnungsgeberbestätigung?', 'Ersetzt der Mietvertrag die Bestätigung des Vermieters?'],
  },
} satisfies Record<string, Record<Lang, string | string[]>>

export type Key = keyof typeof strings

export function t<K extends Key>(key: K, lang: Lang): (typeof strings)[K][Lang] {
  return strings[key][lang]
}
