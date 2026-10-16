import { useEffect, useId, useRef } from "react"
import { X } from "lucide-react"

/**
 * Modal accesible: cierra con Esc o clic fuera, atrapa el foco y lo
 * devuelve al elemento que lo abrió. En móvil se muestra como hoja inferior.
 */
export default function Modal({ open, onClose, title, description, children, footer, size = "md" }) {
  const ref = useRef(null)
  const titleId = useId()
  // Ref para no reiniciar el efecto (y robar el foco) si onClose cambia en cada render
  const onCloseRef = useRef(onClose)
  useEffect(() => {
    onCloseRef.current = onClose
  })

  useEffect(() => {
    if (!open) return
    const prev = document.activeElement
    const node = ref.current
    const focusables = () =>
      node.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])')
    focusables()[0]?.focus()

    const onKey = (e) => {
      if (e.key === "Escape") onCloseRef.current()
      if (e.key === "Tab") {
        const els = [...focusables()]
        const first = els[0]
        const last = els.at(-1)
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault()
          last.focus()
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault()
          first.focus()
        }
      }
    }
    document.addEventListener("keydown", onKey)
    document.body.style.overflow = "hidden"
    return () => {
      document.removeEventListener("keydown", onKey)
      document.body.style.overflow = ""
      prev?.focus?.()
    }
  }, [open])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-40 flex items-end justify-center sm:items-center sm:p-6">
      <div className="absolute inset-0 animate-fade-in bg-ink/40 backdrop-blur-[2px]" onClick={onClose} aria-hidden="true" />
      <div
        ref={ref}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className={`relative flex max-h-[92vh] w-full animate-fade-up flex-col rounded-t-2xl border border-line bg-surface shadow-pop sm:animate-scale-in sm:rounded-2xl ${
          size === "lg" ? "sm:max-w-2xl" : "sm:max-w-lg"
        }`}
      >
        <header className="flex items-start gap-3 border-b border-line p-5">
          <div className="flex-1">
            <h2 id={titleId} className="text-h2 font-semibold text-ink">
              {title}
            </h2>
            {description && <p className="mt-0.5 text-sm text-ink-2">{description}</p>}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar"
            className="-mt-1 -mr-1 grid size-10 cursor-pointer place-items-center rounded-lg text-ink-2 hover:bg-surface-2 hover:text-ink"
          >
            <X aria-hidden="true" className="size-5" />
          </button>
        </header>
        <div className="overflow-y-auto p-5">{children}</div>
        {footer && <footer className="flex flex-wrap justify-end gap-2 border-t border-line p-4">{footer}</footer>}
      </div>
    </div>
  )
}
