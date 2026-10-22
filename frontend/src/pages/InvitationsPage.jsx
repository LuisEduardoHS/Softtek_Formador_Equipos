import { useState } from "react"
import { Inbox, Send } from "lucide-react"
import { Tabs } from "../components/ui/Controls"
import { EmptyState, ErrorState, Skeleton } from "../components/ui/Feedback"
import { useToast } from "../components/ui/Toast"
import InvitationItem from "../components/invite/InvitationItem"
import useAsync from "../hooks/useAsync"
import { obtenerInvitaciones, responderInvitacion } from "../services/api"

const FILTROS = [
  ["todas", "Todas"],
  ["pendiente", "Pendientes"],
  ["aceptada", "Aceptadas"],
  ["rechazada", "Rechazadas"],
  ["expirada", "Expiradas"],
]

export default function InvitationsPage() {
  const toast = useToast()
  const inv = useAsync(obtenerInvitaciones)
  const [tab, setTab] = useState("recibida")
  const [filtro, setFiltro] = useState("todas")
  const [busy, setBusy] = useState(null)

  const respond = async (i, estado) => {
    setBusy(i.id)
    try {
      const result = await responderInvitacion(i.id, estado)
      inv.setData((list) => list.map((x) => (x.id === i.id ? { ...x, estado: result.estado } : x)))
      toast(estado === "aceptada" ? `¡Te uniste a «${i.proyecto?.titulo || "tu equipo"}»!` : "Rechazaste la invitación.", estado === "aceptada" ? "success" : "info")
    } catch {
      toast("No pudimos registrar tu respuesta.", "error")
    } finally {
      setBusy(null)
    }
  }

  const all = inv.data ?? []
  const deTipo = all.filter((i) => i.tipo === tab)
  const list = deTipo.filter((i) => filtro === "todas" || i.estado === filtro)
  const pendientes = (t) => all.filter((i) => i.tipo === t && i.estado === "pendiente").length

  return (
    <div className="mx-auto max-w-3xl px-4 py-6 sm:px-8 sm:py-10">
      <header className="mb-6 animate-fade-up">
        <h1 className="text-h1 font-bold">Invitaciones</h1>
        <p className="mt-1 text-ink-2">Las que te enviaron y las que tú enviaste, con su estado.</p>
      </header>

      <Tabs
        label="Tipo de invitación"
        value={tab}
        onChange={(t) => {
          setTab(t)
          setFiltro("todas")
        }}
        tabs={[
          { id: "recibida", label: "Recibidas", count: inv.data ? pendientes("recibida") || undefined : undefined },
          { id: "enviada", label: "Enviadas", count: inv.data ? pendientes("enviada") || undefined : undefined },
        ]}
      />

      <div className="my-4 flex gap-2 overflow-x-auto pb-1" role="group" aria-label="Filtrar por estado">
        {FILTROS.map(([v, l]) => (
          <button
            key={v}
            type="button"
            aria-pressed={filtro === v}
            onClick={() => setFiltro(v)}
            className={`min-h-9 shrink-0 cursor-pointer rounded-full border px-3 text-sm font-medium transition-colors ${
              filtro === v ? "border-ink bg-ink text-canvas" : "border-line bg-surface text-ink-2 hover:text-ink"
            }`}
          >
            {l}
          </button>
        ))}
      </div>

      {inv.loading ? (
        <div className="space-y-2">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-28 w-full rounded-xl" />
          ))}
        </div>
      ) : inv.status === "error" ? (
        <ErrorState message="No pudimos cargar tus invitaciones." onRetry={inv.reload} />
      ) : list.length === 0 ? (
        <EmptyState icon={tab === "recibida" ? Inbox : Send} title={filtro === "todas" ? "Nada por aquí todavía" : "No hay invitaciones con este estado"}>
          {tab === "recibida"
            ? "Cuando alguien quiera sumarte a su equipo, lo verás aquí."
            : "Invita a personas desde las recomendaciones de tus proyectos."}
        </EmptyState>
      ) : (
        <ul className="space-y-3">
          {list.map((i) => (
            <InvitationItem
              key={i.id}
              invitation={i}
              person={i.tipo === "recibida" ? i.remitente : i.destinatario}
              project={i.proyecto}
              busy={busy === i.id}
              onRespond={(estado) => respond(i, estado)}
            />
          ))}
        </ul>
      )}
    </div>
  )
}
