import { createContext, useCallback, useContext, useState } from "react"
import { CircleAlert, CircleCheck, Info, X } from "lucide-react"

const ToastContext = createContext(null)

const TONES = {
  success: { Icon: CircleCheck, cls: "text-success-ink" },
  error: { Icon: CircleAlert, cls: "text-danger" },
  info: { Icon: Info, cls: "text-primary" },
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const dismiss = useCallback((id) => setToasts((t) => t.filter((x) => x.id !== id)), [])

  const toast = useCallback(
    (message, tone = "success") => {
      const id = crypto.randomUUID()
      setToasts((t) => [...t, { id, message, tone }])
      setTimeout(() => dismiss(id), 4000)
    },
    [dismiss],
  )

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div
        aria-live="polite"
        className="pointer-events-none fixed inset-x-4 bottom-24 z-50 flex flex-col items-center gap-2 lg:inset-x-auto lg:right-6 lg:bottom-6 lg:items-end"
      >
        {toasts.map(({ id, message, tone }) => {
          const { Icon, cls } = TONES[tone]
          return (
            <div
              key={id}
              role="status"
              className="pointer-events-auto flex w-full max-w-sm animate-fade-up items-start gap-3 rounded-xl border border-line bg-surface p-3 pr-2 shadow-pop"
            >
              <Icon aria-hidden="true" className={`mt-0.5 size-5 shrink-0 ${cls}`} />
              <p className="flex-1 text-sm text-ink">{message}</p>
              <button
                type="button"
                onClick={() => dismiss(id)}
                aria-label="Cerrar aviso"
                className="grid size-7 cursor-pointer place-items-center rounded-md text-ink-2 hover:bg-surface-2"
              >
                <X aria-hidden="true" className="size-4" />
              </button>
            </div>
          )
        })}
      </div>
    </ToastContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useToast() {
  return useContext(ToastContext)
}
