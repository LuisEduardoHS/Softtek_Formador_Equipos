import { Check, CircleDashed, Send } from "lucide-react"
import Avatar from "../ui/Avatar"
import SkillChip from "../ui/SkillChip"
import { studentById } from "../../data/mockData"
import { firstName } from "../../lib/projects"

/**
 * Mapa de cobertura de roles: cada rol aparece como cubierto (verde, con
 * el integrante) o pendiente (ámbar, con las habilidades que necesita).
 * - invitedByRole: { [rolId]: nombre } invitaciones enviadas aún sin respuesta
 */
export default function RoleCoverage({ roles, invitedByRole = {}, highlightRolId }) {
  return (
    <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      {roles.map((r, i) => {
        const member = r.cubiertoPor
          ? studentById(String(r.cubiertoPor)) ?? {
              id: String(r.cubiertoPor),
              nombre: "Integrante",
              carrera: "",
            }
          : null
        const invited = invitedByRole[r.id]
        return (
          <li
            key={r.id}
            style={{ animationDelay: `${i * 50}ms` }}
            className={`relative flex animate-fade-up flex-col gap-3 rounded-xl border p-4 ${
              member ? "border-success-line bg-success-soft/60" : "border-dashed border-warn-line bg-warn-soft/50"
            } ${highlightRolId === r.id ? "ring-2 ring-primary ring-offset-2 ring-offset-canvas" : ""}`}
          >
            <div className="flex items-start justify-between gap-2">
              <p className="font-semibold text-ink">{r.nombre}</p>
              {member ? (
                <span className="flex shrink-0 items-center gap-1 text-xs font-semibold text-success-ink">
                  <Check aria-hidden="true" className="size-3.5" strokeWidth={3} /> Cubierto
                </span>
              ) : (
                <span className="flex shrink-0 items-center gap-1 text-xs font-semibold text-warn-ink">
                  <CircleDashed aria-hidden="true" className="size-3.5" strokeWidth={2.5} /> Pendiente
                </span>
              )}
            </div>

            {member ? (
              <div className="flex items-center gap-2">
                <Avatar name={member.nombre} size="sm" />
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-ink">
                    {member.id === "u0" ? "Tú" : member.nombre}
                  </p>
                  <p className="truncate text-xs text-ink-2">{member.carrera}</p>
                </div>
              </div>
            ) : (
              <div className="flex flex-wrap gap-1.5">
                {r.habilidades.map((h) => (
                  <SkillChip key={h} variant="needed">
                    {h}
                  </SkillChip>
                ))}
              </div>
            )}

            {(r.indispensable || invited) && (
              <div className="flex flex-wrap items-center gap-2 text-xs">
                {r.indispensable && (
                  <span className="rounded-md bg-ink/5 px-1.5 py-0.5 font-semibold text-ink-2">Indispensable</span>
                )}
                {invited && !member && (
                  <span className="flex items-center gap-1 text-ink-2">
                    <Send aria-hidden="true" className="size-3" /> Invitaste a {firstName(invited)}
                  </span>
                )}
              </div>
            )}
          </li>
        )
      })}
    </ul>
  )
}
