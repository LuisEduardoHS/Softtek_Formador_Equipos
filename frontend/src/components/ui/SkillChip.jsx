import { Check, CircleDashed, Lock, X } from "lucide-react"

// Cada variante combina color + ícono + texto accesible: nunca solo color.
const VARIANTS = {
  neutral: { cls: "border-line bg-surface-2 text-ink", Icon: null, sr: "" },
  match: { cls: "border-success-line bg-success-soft text-success-ink", Icon: Check, sr: "Coincide con el proyecto: " },
  needed: { cls: "border-warn-line bg-warn-soft text-warn-ink", Icon: CircleDashed, sr: "Pendiente de cubrir: " },
  private: { cls: "border-line bg-surface text-ink-2 border-dashed", Icon: Lock, sr: "Privado: " },
}

const LEVELS = { basico: "Básico", intermedio: "Intermedio", avanzado: "Avanzado" }

// `label` se usa en el texto accesible de "Quitar" cuando children no es texto plano.
export default function SkillChip({ children, label, variant = "neutral", level, onRemove, className = "" }) {
  const { cls, Icon, sr } = VARIANTS[variant]
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium whitespace-nowrap ${cls} ${className}`}
    >
      {Icon && <Icon aria-hidden="true" className="size-3.5 shrink-0" strokeWidth={2.5} />}
      {sr && <span className="sr-only">{sr}</span>}
      {children}
      {level && <span className="opacity-70">· {LEVELS[level] ?? level}</span>}
      {onRemove && (
        <button
          type="button"
          onClick={onRemove}
          aria-label={`Quitar ${label ?? children}`}
          className="-mr-1 ml-0.5 grid size-5 cursor-pointer place-items-center rounded-full hover:bg-ink/10"
        >
          <X aria-hidden="true" className="size-3" />
        </button>
      )}
    </span>
  )
}
