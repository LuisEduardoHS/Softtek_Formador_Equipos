import { CircleAlert, Cpu, RotateCw } from "lucide-react"
import Button from "./Button"

export function Skeleton({ className = "" }) {
  return <div aria-hidden="true" className={`animate-pulse rounded-lg bg-surface-2 ${className}`} />
}

// Esqueleto de una tarjeta de recomendación compacta
export function CardSkeleton({ className = "" }) {
  return (
    <div className={`space-y-4 rounded-2xl border border-line bg-surface p-5 ${className}`}>
      <div className="flex items-center gap-3">
        <Skeleton className="size-10 rounded-full" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-3 w-3/4" />
        </div>
      </div>
      <div className="flex gap-2">
        <Skeleton className="h-6 w-20 rounded-full" />
        <Skeleton className="h-6 w-24 rounded-full" />
        <Skeleton className="h-6 w-16 rounded-full" />
      </div>
      <Skeleton className="h-14 w-full rounded-xl" />
      <Skeleton className="h-11 w-full" />
    </div>
  )
}

// Estado de carga cuando la IA está trabajando
export function AILoading({ text = "La IA está analizando…", className = "" }) {
  return (
    <div role="status" className={`flex items-center gap-3 rounded-xl border border-ai-line bg-ai-soft p-4 text-sm text-ai-ink ${className}`}>
      <span className="relative grid size-8 place-items-center">
        <span className="absolute inset-0 animate-ping rounded-full bg-ai-line/60" />
        <Cpu aria-hidden="true" className="relative size-4" />
      </span>
      <span className="font-medium">{text}</span>
    </div>
  )
}

export function EmptyState({ icon: Icon, title, children, actions, className = "" }) {
  return (
    <div className={`flex animate-fade-up flex-col items-center rounded-2xl border border-dashed border-line px-6 py-10 text-center ${className}`}>
      {Icon && (
        <span className="mb-4 grid size-12 place-items-center rounded-full bg-surface-2 text-ink-2">
          <Icon aria-hidden="true" className="size-6" />
        </span>
      )}
      <h3 className="text-h3 font-semibold text-ink">{title}</h3>
      {children && <p className="mt-1 max-w-md text-sm text-ink-2">{children}</p>}
      {actions && <div className="mt-5 flex flex-wrap justify-center gap-2">{actions}</div>}
    </div>
  )
}

export function ErrorState({ message = "Algo salió mal al cargar esta sección.", onRetry, className = "" }) {
  return (
    <div role="alert" className={`flex flex-wrap items-center gap-3 rounded-2xl border border-danger/30 bg-danger-soft p-4 ${className}`}>
      <CircleAlert aria-hidden="true" className="size-5 shrink-0 text-danger" />
      <p className="flex-1 text-sm text-ink">{message}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          <RotateCw aria-hidden="true" className="size-4" /> Reintentar
        </Button>
      )}
    </div>
  )
}
