import { useCallback } from "react"
import { Link, useParams } from "react-router-dom"
import { ArrowLeft, EyeOff, Mail } from "lucide-react"
import Avatar from "../components/ui/Avatar"
import Card from "../components/ui/Card"
import SkillChip from "../components/ui/SkillChip"
import TeamCoverageChart from "../components/team/TeamCoverageChart"
import { CoverageBar } from "../components/team/TeamSummaryCard"
import { EmptyState, ErrorState, Skeleton } from "../components/ui/Feedback"
import useAsync from "../hooks/useAsync"
import { obtenerEquipo } from "../services/api"
import { coverage } from "../lib/projects"
import { getSessionUser } from "../lib/session"

export default function TeamPage() {
  const { id } = useParams()
  const loadTeam = useCallback(() => obtenerEquipo(id), [id])
  const teamQuery = useAsync(loadTeam)
  const team = teamQuery.data

  if (teamQuery.loading) {
    return (
      <div className="mx-auto max-w-5xl space-y-4 px-4 py-10 sm:px-8" aria-busy="true">
        <Skeleton className="h-36 rounded-xl" />
        <Skeleton className="h-64 rounded-xl" />
      </div>
    )
  }

  if (teamQuery.status === "error") {
    return (
      <div className="mx-auto max-w-5xl px-4 py-10 sm:px-8">
        <ErrorState message="No pudimos cargar los datos reales del equipo." onRetry={teamQuery.reload} />
      </div>
    )
  }

  if (!team) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10 sm:px-8">
        <EmptyState title="No encontramos este equipo">
          <Link to="/equipos" className="font-semibold text-primary hover:underline">Ver mis equipos</Link>
        </EmptyState>
      </div>
    )
  }

  const project = team.proyecto
  const members = team.miembros
  const { cubiertos, total } = coverage(project)
  const usuario = getSessionUser()

  return (
    <div className="mx-auto max-w-5xl px-4 py-6 sm:px-8 sm:py-10">
      <Link to="/equipos" className="mb-4 inline-flex min-h-9 items-center gap-1 text-sm font-medium text-ink-2 hover:text-ink">
        <ArrowLeft aria-hidden="true" className="size-4" /> Mis equipos
      </Link>

      <Card className="mb-8 p-5 sm:p-7">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="min-w-0">
            <h1 className="text-h1 font-bold">{team.nombre}</h1>
            <Link to={`/proyectos/${project.id}`} className="mt-1 inline-flex text-sm text-ink-2 hover:text-primary hover:underline">
              Ver proyecto: {project.titulo}
            </Link>
          </div>
          <div className="w-full sm:w-52">
            <p className="mb-1 text-sm text-ink-2">{members.length} {members.length === 1 ? "integrante" : "integrantes"}</p>
            <CoverageBar cubiertos={cubiertos} total={total} />
          </div>
        </div>
      </Card>

      {(
        <section aria-labelledby="coverage-title" className="mb-8">
          <h2 id="coverage-title" className="mb-4 text-h2 font-semibold">Cobertura del equipo</h2>
          <Card className="p-5 sm:p-6">
            <TeamCoverageChart coverage={team.cobertura_habilidades} />
          </Card>
        </section>
      )}

      <section aria-labelledby="members-title">
        <h2 id="members-title" className="mb-4 text-h2 font-semibold">
          Participantes <span className="font-normal text-ink-2">({members.length})</span>
        </h2>
        {members.length === 0 ? (
          <EmptyState title="Aún no hay participantes registrados" />
        ) : (
          <ul className="grid gap-4 md:grid-cols-2">
            {members.map((member) => (
              <li key={member.id}>
                <Card className="flex h-full flex-col gap-4 p-5">
                  <div className="flex items-center gap-3">
                    <Avatar name={member.nombre} size="md" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-semibold">
                        {member.nombre}
                        {String(member.id) === String(usuario.id_usuario) && (
                          <span className="font-normal text-ink-2"> (tú)</span>
                        )}
                      </p>
                      <p className="truncate text-sm text-ink-2">{member.carrera}</p>
                    </div>
                  </div>
                  <p className="text-sm text-ink-2">
                    Rol: <span className="font-semibold text-ink">{member.rol}</span>
                  </p>
                  {member.fortalezas.length > 0 && (
                    <div>
                      <p className="mb-2 text-label font-semibold tracking-wide text-ink-2 uppercase">Habilidades</p>
                      <ul className="flex flex-wrap gap-1.5">
                        {member.fortalezas.map((fortaleza) => (
                          <li key={fortaleza.nombre}>
                            <SkillChip>{fortaleza.nombre}</SkillChip>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <div className="mt-auto border-t border-line pt-3">
                    {member.correo ? (
                      <a href={`mailto:${member.correo}`} className="flex items-center gap-2 text-sm text-primary hover:underline">
                        <Mail aria-hidden="true" className="size-4" />
                        <span className="truncate">{member.correo}</span>
                      </a>
                    ) : (
                      <p className="flex items-center gap-2 text-sm text-ink-2">
                        <EyeOff aria-hidden="true" className="size-4" /> No comparte su correo
                      </p>
                    )}
                  </div>
                </Card>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
