import { useState } from 'react'
import { form } from '../form'
import { t } from '../i18n'
import type { Lang } from '../types'

interface Props {
  lang: Lang
  busy: boolean
  onAskField: (fieldId: string) => void
}

const allFields = form.groups.flatMap((g) => g.fields)

export function FormWalkthrough({ lang, busy, onAskField }: Props) {
  // Practice values live only in component state: never persisted, never sent to the backend.
  const [values, setValues] = useState<Record<string, string>>({})
  const [step, setStep] = useState(0)
  const steps = form.groups.length + 1 // groups + final checklist
  const group = form.groups[step]

  return (
    <section className="panel walkthrough" aria-labelledby="form-title">
      <div className="walk-head">
        <h2 id="form-title">{t('formTitle', lang)}</h2>
        <div className="walk-actions">
          <button type="button" className="secondary" onClick={() => setValues(Object.fromEntries(allFields.map((f) => [f.id, f.demo])))}>
            {t('demoFill', lang)}
          </button>
          <button type="button" className="secondary" onClick={() => setValues({})}>
            {t('clear', lang)}
          </button>
        </div>
      </div>
      <p className="muted">{form.note[lang]}</p>
      <p className="demo-notice">{t('demoNotice', lang)}</p>

      <ol className="stepper" aria-label={t('step', lang)}>
        {[...form.groups.map((g) => g.label[lang]), t('checklist', lang)].map((label, i) => (
          <li key={label}>
            <button type="button" className={i === step ? 'active' : ''} aria-current={i === step ? 'step' : undefined} onClick={() => setStep(i)}>
              {i + 1}. {label}
            </button>
          </li>
        ))}
      </ol>

      {group ? (
        <div className="fields">
          {group.fields.map((f) => (
            <div key={f.id} className="field">
              <label htmlFor={`f-${f.id}`}>{f.label[lang]}</label>
              <input
                id={`f-${f.id}`}
                value={values[f.id] ?? ''}
                onChange={(e) => setValues((v) => ({ ...v, [f.id]: e.target.value }))}
                autoComplete="off"
                placeholder={f.demo}
              />
              <p className="help">{f.help[lang]}</p>
              <div className="field-foot">
                <details>
                  <summary>{t('why', lang)}</summary>
                  <ul>
                    {f.sources.map((s) => (
                      <li key={s}>
                        <a href={form.sources[s].url} target="_blank" rel="noreferrer">
                          {form.sources[s].title}
                        </a>
                      </li>
                    ))}
                  </ul>
                </details>
                <button type="button" className="link" disabled={busy} onClick={() => onAskField(f.id)}>
                  {t('askField', lang)} →
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <ul className="checklist">
          {form.checklist.map((item) => (
            <li key={item.en}>
              <span>{item[lang]}</span>
              <span className="refs">
                {item.sources.map((s) => (
                  <a key={s} href={form.sources[s].url} target="_blank" rel="noreferrer">
                    {form.sources[s].title.split(' – ')[0]}
                  </a>
                ))}
              </span>
            </li>
          ))}
        </ul>
      )}

      <div className="pager">
        <button type="button" className="secondary" disabled={step === 0} onClick={() => setStep(step - 1)}>
          ← {t('back', lang)}
        </button>
        <span className="muted">
          {t('step', lang)} {step + 1} {t('of', lang)} {steps}
        </span>
        <button type="button" disabled={step === steps - 1} onClick={() => setStep(step + 1)}>
          {t('next', lang)} →
        </button>
      </div>
    </section>
  )
}
