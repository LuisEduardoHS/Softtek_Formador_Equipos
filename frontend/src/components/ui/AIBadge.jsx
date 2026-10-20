import { Cpu, ShieldCheck } from "lucide-react"

// Marca discreta para todo lo que genera la IA. Mismo estilo en toda la app.
export default function AIBadge({ label = "Sugerido por IA", className = "" }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md border border-ai-line bg-ai-soft px-1.5 py-0.5 text-[11px] font-semibold text-ai-ink ${className}`}
    >
      <Cpu aria-hidden="true" className="size-3" strokeWidth={2.25} />
      {label}
    </span>
  )
}

// Contenedor para bloques de texto generados por IA.
export function AIPanel({ title, children, className = "" }) {
  return (
    <div className={`rounded-xl border border-ai-line bg-ai-soft p-3 ${className}`}>
      {title && (
        <p className="mb-1 flex items-center gap-1.5 text-xs font-semibold text-ai-ink">
          <Cpu aria-hidden="true" className="size-3.5" strokeWidth={2.25} />
          {title}
        </p>
      )}
      <div className="text-sm text-ink">{children}</div>
    </div>
  )
}

// Indicador de confianza: el análisis ocurre en servidores de la universidad.
export function LocalProcessing({ className = "" }) {
  return (
    <p className={`inline-flex items-center gap-1.5 text-xs text-ink-2 ${className}`}>
      <ShieldCheck aria-hidden="true" className="size-3.5 text-success-ink" />
      Procesado de forma local en la universidad
    </p>
  )
}
