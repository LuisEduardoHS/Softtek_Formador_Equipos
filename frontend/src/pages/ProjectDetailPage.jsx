import { useCallback, useId, useMemo, useState } from "react"
import { Link, useNavigate, useParams } from "react-router-dom"
import { ArrowLeft, CalendarDays, CircleCheck, FileQuestion, Hand, Pencil, SearchX, Users } from "lucide-react"
import Avatar from "../components/ui/Avatar"
import Button from "../components/ui/Button"
import Card from "../components/ui/Card"
import Modal from "../components/ui/Modal"
import SkillChip from "../components/ui/SkillChip"
import { AIPanel, LocalProcessing } from "../components/ui/AIBadge"
import { AILoading, CardSkeleton, EmptyState, ErrorState, Skeleton } from "../components/ui/Feedback"
import { useToast } from "../components/ui/Toast"
import RecommendationCard from "../components/recommendation/RecommendationCard"
import RoleCoverage from "../components/project/RoleCoverage"
import { TypeBadge } from "../components/project/ProjectCard"
import { CoverageBar } from "../components/team/TeamSummaryCard"
import InviteModal from "../components/invite/InviteModal"
import useAsync from "../hooks/useAsync"
import { enviarRetroalimentacion, obtenerCandidatos, obtenerProyecto, solicitarUnirse } from "../services/api"
import { currentUser, invitations, projectSuggestions, studentById, teams } from "../data/mockData"
import { coverage, formatDate } from "../lib/projects"

/* ------------------------------ Encabezado ------------------------------ */

function ProjectHeader({ project, action }) {
  const creador = studentById(project.creadorId) ?? {
    id: String(project.creadorId),
    nombre: `Usuario ${project.creadorId}`,
    carrera: "",
  }
  const usuarioLocal = JSON.parse(localStorage.getItem("usuario") || "{}")
  const esActual = usuarioLocal.id_usuario !== undefined && String(creador.id) === String(usuarioLocal.id_usuario)
  return (
    <Card className="animate-fade-up p-5 sm:p-7">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0 flex-1">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <TypeBadge tipo={project.tipo} />
            {project.materia && <span className="text-xs text-ink-2">{project.materia}</span>}
          </div>
          <h1 className="text-h1 font-bold text-ink">{project.titulo}</h1>
          <div className="mt-3 flex items-center gap-2 text-sm text-ink-2">
            <Avatar name={creador.nombre} size="xs" />
            Creado por <span className="font-medium text-ink">{esActual ? "ti" : creador.nombre}</span>
            · {formatDate(project.creado, { day: "numeric", month: "long" })}
          </div>
          <p className="mt-4 max-w-2xl text-ink">{project.descripcion}</p>
          <dl className="mt-5 flex flex-wrap gap-x-6 gap-y-2 text-sm">
            <div className="flex items-center gap-1.5">
              <Users aria-hidden="true" className="size-4 text-ink-2" />
              <dt className="sr-only">Integrantes</dt>
              <dd>{project.integrantes} integrantes</dd>
            </div>
            {project.fechaLimite && (
              <div className="flex items-center gap-1.5">
                <CalendarDays aria-hidden="true" className="size-4 text-ink-2" />
                <dt className="text-ink-2">Fecha límite:</dt>
                <dd className="font-medium">{formatDate(project.fechaLimite, { day: "numeric", month: "long", year: "numeric" })}</dd>
              </div>
            )}
          </dl>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">{action}</div>
      </div>
    </Card>
  )
}

/* ------------------------- Candidatos (dueño) ------------------------- */

function Candidates({ project }) {
  const navigate = useNavigate()
  const fetchCandidates = useCallback(() => obtenerCandidatos(project.id), [project.id])
  const cands = useAsync(fetchCandidates)
  const [target, setTarget] = useState(null)
  const [invited, setInvited] = useState(
    () => new Set(invitations.filter((i) => i.projectId === project.id && i.tipo === "enviada" && i.estado === "pendiente").map((i) => i.paraId)),
  )
  const { pendientes } = coverage(project)

  if (cands.loading) {
    return (
      <div className="space-y-4" aria-busy="true">
        <AILoading text="La IA está buscando a quién le falta a tu equipo…" />
        <CardSkeleton />
      </div>
    )
  }
  if (cands.status === "error") return <ErrorState message="No pudimos cargar los candidatos." onRetry={cands.reload} />
  if (pendientes.length === 0) {
    return (
      <EmptyState icon={CircleCheck} title="¡Todos los roles están cubiertos!">
        Tu equipo está completo. Ya pueden empezar a trabajar.
      </EmptyState>
    )
  }

  return (
    <div className="space-y-10">
      {pendientes.map((rol) => {
        const lista = cands.data.filter((c) => c.rolId === rol.id)
        return (
          <section key={rol.id} aria-labelledby={`rol-${rol.id}`}>
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <h3 id={`rol-${rol.id}`} className="text-h3 font-semibold">
                Para <span className="text-warn-ink">{rol.nombre}</span>
              </h3>
              {rol.indispensable && (
                <span className="rounded-md bg-ink/5 px-1.5 py-0.5 text-xs font-semibold text-ink-2">Indispensable</span>
              )}
              <span className="text-sm text-ink-2">
                · {lista.length} {lista.length === 1 ? "candidato" : "candidatos"}
              </span>
            </div>
            {lista.length === 0 ? (
              <EmptyState icon={SearchX} title="Aún no encontramos a nadie para este rol" className="py-8">
                Te avisaremos en cuanto alguien con este perfil esté disponible. Mientras, puedes buscar manualmente desde Inicio.
              </EmptyState>
            ) : (
              <div className="space-y-4">
                {lista.map((rec) => {
                  const student = studentById(rec.studentId)
                  return (
                    <RecommendationCard
                      key={rec.id}
                      variant="expanded"
                      student={student}
                      rol={rol}
                      rec={rec}
                      project={project}
                      invited={invited.has(student.id)}
                      onInvite={() => setTarget({ student, rol })}
                      onViewProfile={() => navigate(`/perfil/${student.id}`)}
                      onFeedback={(v) => enviarRetroalimentacion(rec.id, { util: v === "util" })}
                      onDismiss={(motivo) => enviarRetroalimentacion(rec.id, { util: false, motivo })}
                    />
                  )
                })}
              </div>
            )}
          </section>
        )
      })}

      <InviteModal
        open={!!target}
        onClose={() => setTarget(null)}
        student={target?.student}
        rol={target?.rol}
        project={project}
        onSent={(s) => setInvited((prev) => new Set(prev).add(s.id))}
      />
    </div>
  )
}

/* ---------------------- Solicitar unirme (no dueño) ---------------------- */

function JoinModal({ open, onClose, project, defaultRolId, onSent }) {
  const toast = useToast()
  const msgId = useId()
  const pendientes = coverage(project).pendientes
  const [rolId, setRolId] = useState(defaultRolId ?? pendientes[0]?.id)
  const [mensaje, setMensaje] = useState("")
  const [sending, setSending] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setSending(true)
    try {
      await solicitarUnirse(project.id, { rolId, mensaje })
      toast("Solicitud enviada. Te avisaremos cuando respondan.")
      onSent(rolId)
      onClose()
    } catch {
      toast("No pudimos enviar tu solicitud. Inténtalo de nuevo.", "error")
    } finally {
      setSending(false)
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Solicitar unirme"
      description={project.titulo}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" form="join-form" disabled={sending || !rolId}>
            {sending ? "Enviando…" : "Enviar solicitud"}
          </Button>
        </>
      }
    >
      <form id="join-form" onSubmit={submit} className="space-y-5">
        <fieldset>
          <legend className="mb-2 text-sm font-semibold">¿Qué rol te gustaría cubrir?</legend>
          <div className="space-y-2">
            {pendientes.map((r) => (
              <label
                key={r.id}
                className={`flex min-h-11 cursor-pointer items-center gap-3 rounded-lg border p-3 transition-colors ${
                  rolId === r.id ? "border-primary bg-primary-soft" : "border-line hover:bg-surface-2"
                }`}
              >
                <input
                  type="radio"
                  name="rol"
                  value={r.id}
                  checked={rolId === r.id}
                  onChange={() => setRolId(r.id)}
                  className="size-4 accent-primary"
                />
                <span className="flex-1 text-sm font-medium">{r.nombre}</span>
                {r.id === defaultRolId && <span className="text-xs font-semibold text-ai-ink">Sugerido para ti</span>}
              </label>
            ))}
          </div>
        </fieldset>
        <div>
          <label htmlFor={msgId} className="mb-1.5 block text-sm font-semibold">
            Mensaje <span className="font-normal text-ink-2">(opcional)</span>
          </label>
          <textarea
            id={msgId}
            rows={4}
            value={mensaje}
            onChange={(e) => setMensaje(e.target.value)}
            placeholder="Cuéntales brevemente qué te gustaría aportar."
            className="w-full resize-y rounded-lg border border-line bg-surface p-3 text-sm outline-none placeholder:text-ink-2 focus:border-primary focus:ring-3 focus:ring-primary/15"
          />
        </div>
      </form>
    </Modal>
  )
}

function YourFit({ project, suggestion }) {
  const rol = project.roles.find((r) => r.id === suggestion.rolId)
  const mias = new Set(currentUser.fortalezas.map((f) => f.nombre))
  return (
    <AIPanel title={`Podrías cubrir «${rol.nombre}»`}>
      <p>{suggestion.porQue}</p>
      <div className="mt-3 flex flex-wrap gap-1.5">
        {rol.habilidades.map((h) => (
          <SkillChip key={h} variant={mias.has(h) ? "match" : "needed"}>
            {h}
          </SkillChip>
        ))}
      </div>
    </AIPanel>
  )
}

/* -------------------------------- Página -------------------------------- */

// La key reinicia todo el estado al navegar de un proyecto a otro
export default function ProjectDetailRoute() {
  const { id } = useParams()
  return <ProjectDetailPage key={id} id={id} />
}

function ProjectDetailPage({ id }) {
  const fetchProject = useCallback(() => obtenerProyecto(id), [id])
  const { status, data: project, error, reload } = useAsync(fetchProject)
  const [joinOpen, setJoinOpen] = useState(false)
  const [requestedRol, setRequestedRol] = useState(null)

  const invitedByRole = useMemo(() => {
    if (!project) return {}
    const map = {}
    invitations
      .filter((i) => i.projectId === project.id && i.tipo === "enviada" && i.estado === "pendiente")
      .forEach((i) => {
        const rol = project.roles.find((r) => r.nombre === i.rol)
        if (rol) map[rol.id] = studentById(i.paraId).nombre
      })
    return map
  }, [project])

  const back = (
    <Link to="/proyectos" className="mb-4 inline-flex min-h-9 items-center gap-1 text-sm font-medium text-ink-2 hover:text-ink">
      <ArrowLeft aria-hidden="true" className="size-4" /> Proyectos
    </Link>
  )

  if (status === "loading") {
    return (
      <div className="mx-auto max-w-6xl space-y-6 px-4 py-6 sm:px-8 sm:py-10" aria-busy="true">
        {back}
        <Skeleton className="h-56 w-full rounded-2xl" />
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-32 rounded-xl" />
          ))}
        </div>
      </div>
    )
  }

  if (status === "error") {
    return (
      <div className="mx-auto max-w-3xl px-4 py-6 sm:px-8 sm:py-10">
        {back}
        {error.status === 404 ? (
          <EmptyState
            icon={FileQuestion}
            title="No encontramos este proyecto"
            actions={
              <Button as={Link} to="/proyectos" variant="secondary">
                Ver proyectos
              </Button>
            }
          >
            Puede que se haya cerrado o que el enlace esté incompleto.
          </EmptyState>
        ) : (
          <ErrorState message="No pudimos cargar el proyecto." onRetry={reload} />
        )}
      </div>
    )
  }

  const usuarioLocal = JSON.parse(localStorage.getItem("usuario") || "{}")
  const usuarioId = usuarioLocal.id_usuario
  const esDueno = usuarioId !== undefined && String(project.creadorId) === String(usuarioId)
  const esIntegrante = usuarioId !== undefined && project.roles.some((r) => String(r.cubiertoPor) === String(usuarioId))
  const team = teams.find((t) => t.projectId === project.id)
  const suggestion = projectSuggestions.find((s) => s.projectId === project.id)
  const { cubiertos, total, pendientes } = coverage(project)

  let action
  if (esDueno) {
    action = (
      <Button variant="secondary">
        <Pencil aria-hidden="true" className="size-4" /> Editar proyecto
      </Button>
    )
  } else if (esIntegrante) {
    action = (
      <Button as={Link} to={team ? `/equipos/${team.id}` : "/equipos"} variant="secondary">
        <Users aria-hidden="true" className="size-4" /> Ver mi equipo
      </Button>
    )
  } else if (pendientes.length > 0) {
    action = requestedRol ? (
      <Button disabled className="animate-scale-in">
        <CircleCheck aria-hidden="true" className="size-4" /> Solicitud enviada
      </Button>
    ) : (
      <Button onClick={() => setJoinOpen(true)} className="w-full sm:w-auto">
        <Hand aria-hidden="true" className="size-4" /> Solicitar unirme
      </Button>
    )
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-8 sm:py-10">
      {back}
      <div className="space-y-10">
        <ProjectHeader project={project} action={action} />

        {!esDueno && !esIntegrante && suggestion && (
          <div className="animate-fade-up [animation-delay:80ms]">
            <YourFit project={project} suggestion={suggestion} />
          </div>
        )}

        <section aria-labelledby="cov-title" className="animate-fade-up [animation-delay:120ms]">
          <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h2 id="cov-title" className="text-h2 font-semibold">
                Mapa de cobertura de roles
              </h2>
              <p className="text-sm text-ink-2">Qué aporta ya cada integrante y qué falta cubrir.</p>
            </div>
            <div className="w-full sm:w-64">
              <CoverageBar cubiertos={cubiertos} total={total} />
            </div>
          </div>
          <RoleCoverage roles={project.roles} invitedByRole={esDueno ? invitedByRole : {}} highlightRolId={requestedRol} />
        </section>

        {esDueno && (
          <section aria-labelledby="cand-title" className="animate-fade-up [animation-delay:180ms]">
            <div className="mb-5 flex flex-wrap items-end justify-between gap-2">
              <div>
                <h2 id="cand-title" className="text-h2 font-semibold">
                  Candidatos recomendados
                </h2>
                <p className="text-sm text-ink-2">Agrupados por el rol pendiente que cubrirían.</p>
              </div>
              <LocalProcessing />
            </div>
            <Candidates project={project} />
          </section>
        )}
      </div>

      {joinOpen && (
        <JoinModal
          open
          onClose={() => setJoinOpen(false)}
          project={project}
          defaultRolId={suggestion?.rolId}
          onSent={setRequestedRol}
        />
      )}
    </div>
  )
}
