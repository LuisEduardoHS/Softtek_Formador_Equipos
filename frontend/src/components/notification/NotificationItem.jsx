import { Link } from "react-router-dom"
import { Cpu, Mail, Users } from "lucide-react"

const GRUPOS = {
  ia: { label: "Oportunidades de la IA", Icon: Cpu, cls: "bg-ai-soft text-ai-ink border border-ai-line" },
  invitaciones: { label: "Invitaciones", Icon: Mail, cls: "bg-surface-2 text-ink" },
  equipo: { label: "Actualizaciones de equipo", Icon: Users, cls: "bg-success-soft text-success-ink" },
}

export default function NotificationItem({ notification, onOpen }) {
  const { grupo, texto, fecha, leida, accion } = notification
  const { Icon, cls } = GRUPOS[grupo]
  return (
    <li
      className={`relative flex animate-fade-up items-start gap-3 rounded-xl p-4 transition-colors ${
        leida ? "bg-surface" : "bg-primary-soft/60"
      }`}
    >
      <span className={`grid size-10 shrink-0 place-items-center rounded-full ${cls}`}>
        <Icon aria-hidden="true" className="size-5" />
      </span>
      <div className="min-w-0 flex-1">
        <p className={`text-sm ${leida ? "text-ink-2" : "font-medium text-ink"}`}>
          {!leida && <span className="sr-only">Sin leer: </span>}
          {texto}
        </p>
        <p className="mt-0.5 text-xs text-ink-2">{fecha}</p>
        <Link
          to={accion.to}
          onClick={onOpen}
          className="mt-2 inline-flex min-h-9 items-center rounded-lg border border-line bg-surface px-3 text-sm font-semibold text-ink transition-colors hover:bg-surface-2"
        >
          {accion.label}
        </Link>
      </div>
      {!leida && <span aria-hidden="true" className="mt-1.5 size-2.5 shrink-0 rounded-full bg-primary" />}
    </li>
  )
}
