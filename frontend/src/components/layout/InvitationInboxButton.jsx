import { Link } from "react-router-dom"
import { Mail } from "lucide-react"
import useAsync from "../../hooks/useAsync"
import { countPendingInvitations } from "../../lib/invitations"
import { obtenerInvitaciones } from "../../services/api"

export function InvitationInboxButton({ count }) {
  const label = count > 0 ? `Invitaciones, ${count} pendientes` : "Invitaciones"

  return (
    <Link
      to="/invitaciones"
      aria-label={label}
      title={label}
      className="relative grid size-11 shrink-0 place-items-center rounded-lg border border-line bg-surface text-ink transition-colors hover:bg-surface-2"
    >
      <Mail aria-hidden="true" className="size-5" />
      {count === 1 ? (
        <span aria-hidden="true" className="absolute -top-0.5 -right-0.5 size-3 rounded-full border-2 border-canvas bg-danger" />
      ) : count > 1 ? (
        <span aria-hidden="true" className="absolute -top-2 -right-2 grid min-h-5 min-w-5 place-items-center rounded-full border-2 border-canvas bg-danger px-1 text-[10px] leading-none font-bold text-white">
          {count}
        </span>
      ) : null}
    </Link>
  )
}

export default function HomeInvitationInbox() {
  const invitations = useAsync(obtenerInvitaciones)
  const count = countPendingInvitations(invitations.data ?? [])
  return <InvitationInboxButton count={count} />
}
