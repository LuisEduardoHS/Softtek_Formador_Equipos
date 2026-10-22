import { BellOff } from "lucide-react"
import { EmptyState, ErrorState, Skeleton } from "../components/ui/Feedback"
import NotificationItem from "../components/notification/NotificationItem"
import useAsync from "../hooks/useAsync"
import { obtenerNotificaciones } from "../services/api"

const GROUPS = [
  ["ia", "Recomendaciones"],
  ["invitaciones", "Invitaciones"],
  ["equipo", "Actualizaciones de equipo"],
]

export default function NotificationsPage() {
  const notifications = useAsync(obtenerNotificaciones)
  const items = notifications.data ?? []

  return (
    <div className="mx-auto max-w-3xl px-4 py-6 sm:px-8 sm:py-10">
      <header className="mb-8 flex animate-fade-up flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-h1 font-bold">Notificaciones</h1>
          <p className="mt-1 text-ink-2">Invitaciones, recomendaciones y actividad real de tus equipos.</p>
        </div>
      </header>

      {notifications.loading ? (
        <div className="space-y-3" aria-busy="true">
          {[0, 1, 2].map((item) => <Skeleton key={item} className="h-28 w-full rounded-xl" />)}
        </div>
      ) : notifications.status === "error" ? (
        <ErrorState message="No pudimos cargar tus notificaciones reales." onRetry={notifications.reload} />
      ) : items.length === 0 ? (
        <EmptyState icon={BellOff} title="Sin notificaciones">
          Cuando recibas una invitación, haya una coincidencia para tus proyectos o alguien se una a tu equipo, aparecerá aquí.
        </EmptyState>
      ) : (
        <div className="space-y-8">
          {GROUPS.map(([key, label]) => {
            const list = items.filter((n) => n.grupo === key)
            if (!list.length) return null
            return (
              <section key={key} aria-labelledby={`g-${key}`}>
                <h2 id={`g-${key}`} className="mb-2 text-label font-semibold tracking-wide text-ink-2 uppercase">
                  {label}
                </h2>
                <ul className="divide-y divide-line overflow-hidden rounded-2xl border border-line bg-surface shadow-card">
                  {list.map((n) => (
                    <NotificationItem key={n.id} notification={n} />
                  ))}
                </ul>
              </section>
            )
          })}
        </div>
      )}
    </div>
  )
}
