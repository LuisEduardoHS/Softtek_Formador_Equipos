import { Check, Clock, X } from "lucide-react"
import Avatar from "../ui/Avatar"
import Button from "../ui/Button"

const ESTADOS = {
  pendiente: { label: "Pendiente", cls: "border-warn-line bg-warn-soft text-warn-ink", Icon: Clock },
  aceptada: { label: "Aceptada", cls: "border-success-line bg-success-soft text-success-ink", Icon: Check },
  rechazada: { label: "Rechazada", cls: "border-line bg-surface-2 text-ink-2", Icon: X },
  expirada: { label: "Expirada", cls: "border-line bg-surface-2 text-ink-2 border-dashed", Icon: Clock },
}

export function StatusBadge({ estado }) {
  const { label, cls, Icon } = ESTADOS[estado]
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-semibold ${cls}`}>
      <Icon aria-hidden="true" className="size-3" strokeWidth={2.5} />
      {label}
    </span>
  )
}

/**
 * Invitación recibida o enviada. Las recibidas pendientes muestran
 * acciones rápidas para aceptar o rechazar.
 */
export default function InvitationItem({ invitation, person, project, onRespond, busy = false, compact = false }) {
  const { tipo, estado, rol, mensaje } = invitation
  const recibida = tipo === "recibida"
  const canRespond = recibida && estado === "pendiente" && onRespond

  return (
    <li className="flex animate-fade-up flex-col gap-3 rounded-xl border border-line bg-surface p-4 transition-colors">
      <div className="flex items-start gap-3">
        <Avatar name={person.nombre} size="sm" />
        <div className="min-w-0 flex-1">
          <p className="text-sm text-ink">
            {recibida ? (
              <>
                <span className="font-semibold">{person.nombre}</span> te invitó a{" "}
                <span className="font-semibold">{project.titulo}</span>
              </>
            ) : (
              <>
                Invitaste a <span className="font-semibold">{person.nombre}</span> a{" "}
                <span className="font-semibold">{project.titulo}</span>
              </>
            )}
          </p>
          <p className="mt-0.5 text-xs text-ink-2">Rol: {rol}</p>
        </div>
        {!canRespond && <StatusBadge estado={estado} />}
      </div>
      {mensaje && !compact && <p className="rounded-lg bg-surface-2 p-3 text-sm text-ink-2 italic">“{mensaje}”</p>}
      {canRespond && (
        <div className="flex gap-2">
          <Button size="sm" className="flex-1" disabled={busy} onClick={() => onRespond("aceptada")}>
            <Check aria-hidden="true" className="size-4" /> Aceptar
          </Button>
          <Button size="sm" variant="secondary" className="flex-1" disabled={busy} onClick={() => onRespond("rechazada")}>
            Rechazar
          </Button>
        </div>
      )}
    </li>
  )
}
