import { useState } from "react"
import { BellOff, CheckCheck } from "lucide-react"
import Button from "../components/ui/Button"
import { EmptyState } from "../components/ui/Feedback"
import NotificationItem from "../components/notification/NotificationItem"
import { notifications as initial } from "../data/mockData"

const GROUPS = [
  ["ia", "Oportunidades de la IA"],
  ["invitaciones", "Invitaciones"],
  ["equipo", "Actualizaciones de equipo"],
]

// TODO(backend): GET /notificaciones y PATCH /notificaciones/{id} { leida: true }
export default function NotificationsPage() {
  const [items, setItems] = useState(() => (new URLSearchParams(window.location.search).get("estado") === "vacio" ? [] : initial))
  const unread = items.filter((n) => !n.leida).length

  const markRead = (id) => setItems((list) => list.map((n) => (id == null || n.id === id ? { ...n, leida: true } : n)))

  return (
    <div className="mx-auto max-w-3xl px-4 py-6 sm:px-8 sm:py-10">
      <header className="mb-8 flex animate-fade-up flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-h1 font-bold">Notificaciones</h1>
          <p className="mt-1 text-ink-2" aria-live="polite">
            {unread ? `Tienes ${unread} sin leer.` : "Estás al día."}
          </p>
        </div>
        {unread > 0 && (
          <Button variant="secondary" size="sm" onClick={() => markRead(null)}>
            <CheckCheck aria-hidden="true" className="size-4" /> Marcar todo como leído
          </Button>
        )}
      </header>

      {items.length === 0 ? (
        <EmptyState icon={BellOff} title="Sin notificaciones">
          Te avisaremos cuando la IA encuentre una oportunidad o alguien responda a tus invitaciones.
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
                    <NotificationItem key={n.id} notification={n} onOpen={() => markRead(n.id)} />
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
