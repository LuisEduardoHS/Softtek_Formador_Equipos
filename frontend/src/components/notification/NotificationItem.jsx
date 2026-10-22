import { Link } from "react-router-dom"
import { Cpu, Mail, Users } from "lucide-react"

const GRUPOS = {
  ia: { Icon: Cpu, cls: "bg-ai-soft text-ai-ink border border-ai-line" },
  invitaciones: { Icon: Mail, cls: "bg-surface-2 text-ink" },
  equipo: { Icon: Users, cls: "bg-success-soft text-success-ink" },
}

export default function NotificationItem({ notification }) {
  const { grupo, texto, fecha, accion } = notification
  const { Icon, cls } = GRUPOS[grupo]
  return (
    <li className="relative flex animate-fade-up items-start gap-3 rounded-xl bg-surface p-4 transition-colors">
      <span className={`grid size-10 shrink-0 place-items-center rounded-full ${cls}`}>
        <Icon aria-hidden="true" className="size-5" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-sm text-ink">{texto}</p>
        {fecha && <p className="mt-0.5 text-xs text-ink-2">{new Intl.DateTimeFormat("es-MX", { dateStyle: "medium", timeStyle: "short" }).format(new Date(fecha))}</p>}
        <Link
          to={accion.to}
          className="mt-2 inline-flex min-h-9 items-center rounded-lg border border-line bg-surface px-3 text-sm font-semibold text-ink transition-colors hover:bg-surface-2"
        >
          {accion.label}
        </Link>
      </div>
    </li>
  )
}
