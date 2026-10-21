import { Link } from "react-router-dom"
import { ArrowRight, CalendarDays, Users } from "lucide-react"
import Card from "../ui/Card"
import { AIPanel } from "../ui/AIBadge"
import { ComplementLevel } from "../recommendation/RecommendationCard"
import { coverage, formatDate } from "../../lib/projects"

export function TypeBadge({ tipo }) {
  return (
    <span className="rounded-md bg-surface-2 px-2 py-0.5 text-xs font-medium text-ink-2">
      {tipo === "academico" ? "Académico" : "Personal"}
    </span>
  )
}

// Mini indicador de roles: un segmento por rol, verde si está cubierto, ámbar si falta.
export function RoleDots({ roles }) {
  const { cubiertos, total } = coverage({ roles })
  return (
    <div className="flex items-center gap-2">
      <div className="flex gap-1" aria-hidden="true">
        {roles.map((r) => (
          <span key={r.id} className={`h-1.5 w-5 rounded-full ${r.cubiertoPor ? "bg-success" : "bg-warn"}`} />
        ))}
      </div>
      <span className="text-xs text-ink-2">
        {cubiertos} de {total} roles cubiertos
      </span>
    </div>
  )
}

/**
 * Tarjeta de proyecto. Si recibe `suggestion` muestra el rol que el usuario
 * cubriría y la explicación de la IA.
 */
export default function ProjectCard({ project, suggestion, className = "" }) {
  const rol = suggestion && project.roles.find((r) => r.id === suggestion.rolId)
  return (
    <Card interactive className={`relative flex flex-col gap-4 p-5 ${className}`}>
      <div className="flex items-start justify-between gap-3">
        <TypeBadge tipo={project.tipo} />
        {suggestion && <ComplementLevel nivel={suggestion.nivel} />}
      </div>
      <div>
        <h3 className="line-clamp-2 text-h3 font-semibold text-ink">{project.titulo}</h3>
        <p className="mt-1 line-clamp-2 text-sm text-ink-2">{project.descripcion}</p>
      </div>
      {rol && (
        <p className="flex flex-wrap items-center gap-2 text-sm text-ink-2">
          Podrías cubrir
          <span className="rounded-md bg-ink px-2 py-0.5 text-xs font-semibold text-canvas">{rol.nombre}</span>
        </p>
      )}
      <RoleDots roles={project.roles} />
      {suggestion && (
        <AIPanel title="Por qué te lo sugerimos">
          <p className="line-clamp-2">{suggestion.porQue}</p>
        </AIPanel>
      )}
      <div className="mt-auto flex items-center justify-between gap-3 border-t border-line pt-4 text-xs text-ink-2">
        <span className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            <Users aria-hidden="true" className="size-3.5" /> {project.integrantes}
          </span>
          {project.fechaLimite && (
            <span className="flex items-center gap-1">
              <CalendarDays aria-hidden="true" className="size-3.5" /> {formatDate(project.fechaLimite)}
            </span>
          )}
        </span>
        <Link
          to={`/proyectos/${project.id}`}
          className="flex min-h-9 items-center gap-1 rounded-md px-1 text-sm font-semibold text-primary after:absolute after:inset-0 hover:underline"
        >
          Ver proyecto <ArrowRight aria-hidden="true" className="size-4" />
        </Link>
      </div>
    </Card>
  )
}
