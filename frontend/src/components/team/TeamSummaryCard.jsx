import { Link } from "react-router-dom"
import { ChevronRight } from "lucide-react"
import { AvatarGroup } from "../ui/Avatar"
import SkillChip from "../ui/SkillChip"
import { coverage } from "../../lib/projects"

// Barra segmentada de cobertura: cubiertos (verde) vs. faltantes (ámbar).
export function CoverageBar({ cubiertos, total }) {
  return (
    <div>
      <div
        className="flex h-2 gap-0.5 overflow-hidden rounded-full"
        role="img"
        aria-label={`${cubiertos} de ${total} roles cubiertos`}
      >
        {Array.from({ length: total }, (_, i) => (
          <span
            key={i}
            className={`flex-1 transition-colors duration-500 ${i < cubiertos ? "bg-success" : "bg-warn/60"}`}
          />
        ))}
      </div>
      <p className="mt-1.5 flex justify-between text-xs text-ink-2">
        <span>
          <span className="font-semibold text-success-ink">{cubiertos} cubiertos</span>
          {total - cubiertos > 0 && (
            <>
              {" · "}
              <span className="font-semibold text-warn-ink">{total - cubiertos} por cubrir</span>
            </>
          )}
        </span>
      </p>
    </div>
  )
}

export default function TeamSummaryCard({ team, project }) {
  const { cubiertos, total, pendientes } = coverage(project)
  const miembros = team.miembros.map((member) => member.nombre)

  return (
    <Link
      to={`/equipos/${team.id}`}
      className="group block rounded-xl border border-line bg-surface p-4 transition-all hover:border-ink/20 hover:shadow-card"
    >
      <div className="flex items-center gap-3">
        <div className="min-w-0 flex-1">
          <p className="truncate font-semibold text-ink">{team.nombre}</p>
          <p className="truncate text-xs text-ink-2">{project.titulo}</p>
        </div>
        <AvatarGroup names={miembros} size="xs" />
        <ChevronRight aria-hidden="true" className="size-4 text-ink-2 transition-transform group-hover:translate-x-0.5" />
      </div>
      <div className="mt-3">
        <CoverageBar cubiertos={cubiertos} total={total} />
      </div>
      {pendientes.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {pendientes.map((r) => (
            <SkillChip key={r.id} variant="needed">
              {r.nombre}
            </SkillChip>
          ))}
        </div>
      )}
    </Link>
  )
}
