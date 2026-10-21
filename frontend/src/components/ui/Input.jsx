import { useId } from "react"
import { inputCls } from "../../lib/ui"

/**
 * Campo de texto con etiqueta visible, ayuda y error.
 * Acepta cualquier prop de <input> (name, type, required, value…).
 */
export default function Input({ label, hint, error, optional, trailing, className = "", ...props }) {
  const id = useId()
  const msgId = `${id}-msg`
  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={id} className="text-sm font-semibold text-ink">
          {label} {optional && <span className="font-normal text-ink-2">(opcional)</span>}
        </label>
      )}
      <div className="relative">
        <input
          id={id}
          aria-invalid={!!error}
          aria-describedby={error || hint ? msgId : undefined}
          className={`${inputCls(error)} ${trailing ? "pr-11" : ""} ${className}`}
          {...props}
        />
        {trailing && <div className="absolute inset-y-0 right-0 flex items-center">{trailing}</div>}
      </div>
      {(error || hint) && (
        <p id={msgId} className={`text-xs ${error ? "text-danger" : "text-ink-2"}`} role={error ? "alert" : undefined}>
          {error || hint}
        </p>
      )}
    </div>
  )
}
