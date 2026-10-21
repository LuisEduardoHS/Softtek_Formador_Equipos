import { useId } from "react"
import { NIVELES } from "../../lib/ui"

/** Interruptor accesible (role="switch"). */
export function Switch({ checked, onChange, label, description, disabled = false }) {
  const id = useId()
  return (
    <div className="flex items-start justify-between gap-4 py-3">
      <div className="min-w-0">
        <label htmlFor={id} className="block text-sm font-semibold text-ink">
          {label}
        </label>
        {description && <p className="mt-0.5 text-sm text-ink-2">{description}</p>}
      </div>
      <button
        id={id}
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={`relative mt-0.5 inline-flex h-7 w-12 shrink-0 cursor-pointer items-center rounded-full transition-colors duration-200 disabled:cursor-not-allowed disabled:opacity-50 ${
          checked ? "bg-primary" : "bg-line"
        }`}
      >
        <span
          aria-hidden="true"
          className={`inline-block size-5 rounded-full bg-white shadow-card transition-transform duration-200 ${
            checked ? "translate-x-6" : "translate-x-1"
          }`}
        />
      </button>
    </div>
  )
}

/** Control segmentado (radio group visual). options: [[valor, etiqueta]] */
export function Segmented({ value, onChange, options, label, size = "md" }) {
  return (
    <div role="radiogroup" aria-label={label} className="inline-flex rounded-lg bg-surface-2 p-1">
      {options.map(([v, l]) => (
        <button
          key={v}
          type="button"
          role="radio"
          aria-checked={value === v}
          onClick={() => onChange(v)}
          className={`cursor-pointer rounded-md font-semibold transition-all ${size === "sm" ? "min-h-8 px-2.5 text-xs" : "min-h-9 px-4 text-sm"} ${
            value === v ? "bg-surface text-ink shadow-card" : "text-ink-2 hover:text-ink"
          }`}
        >
          {l}
        </button>
      ))}
    </div>
  )
}

export function LevelPicker({ value, onChange, name }) {
  return <Segmented value={value} onChange={onChange} options={NIVELES} label={`Nivel en ${name}`} size="sm" />
}

/** Pestañas simples con contador opcional. tabs: [{ id, label, count }] */
export function Tabs({ tabs, value, onChange, label }) {
  return (
    <div role="tablist" aria-label={label} className="flex gap-1 overflow-x-auto border-b border-line">
      {tabs.map((t) => (
        <button
          key={t.id}
          role="tab"
          type="button"
          aria-selected={value === t.id}
          onClick={() => onChange(t.id)}
          className={`-mb-px flex min-h-11 shrink-0 cursor-pointer items-center gap-2 border-b-2 px-3 text-sm font-semibold transition-colors ${
            value === t.id ? "border-primary text-ink" : "border-transparent text-ink-2 hover:text-ink"
          }`}
        >
          {t.label}
          {t.count != null && (
            <span className={`rounded-full px-1.5 text-xs ${value === t.id ? "bg-primary text-white" : "bg-surface-2 text-ink-2"}`}>{t.count}</span>
          )}
        </button>
      ))}
    </div>
  )
}

/** Campo de texto con etiqueta, ayuda y error. */
export function Field({ label, hint, error, optional, children, id }) {
  return (
    <div>
      <label htmlFor={id} className="mb-1.5 block text-sm font-semibold text-ink">
        {label} {optional && <span className="font-normal text-ink-2">(opcional)</span>}
      </label>
      {children}
      {(error || hint) && (
        <p id={`${id}-msg`} className={`mt-1 text-xs ${error ? "text-danger" : "text-ink-2"}`} role={error ? "alert" : undefined}>
          {error || hint}
        </p>
      )}
    </div>
  )
}
