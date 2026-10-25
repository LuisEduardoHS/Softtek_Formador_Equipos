import { useCallback, useId, useMemo, useState } from "react"
import { Link, useNavigate, useParams } from "react-router-dom"
import { ArrowLeft, CalendarDays, CircleCheck, FileQuestion, Hand, Pencil, Plus, SearchX, Trash2, Users } from "lucide-react"
import Avatar from "../components/ui/Avatar"
import Button from "../components/ui/Button"
import Card from "../components/ui/Card"
import Modal from "../components/ui/Modal"
import { Segmented } from "../components/ui/Controls"
import { LocalProcessing } from "../components/ui/AIBadge"
import { AILoading, CardSkeleton, EmptyState, ErrorState, Skeleton } from "../components/ui/Feedback"
import { useToast } from "../components/ui/Toast"
import ProjectAIReview from "../components/project/ProjectAIReview"
import RoleCoverage from "../components/project/RoleCoverage"
import { TypeBadge } from "../components/project/ProjectCard"
import { CoverageBar } from "../components/team/TeamSummaryCard"
import InviteModal from "../components/invite/InviteModal"
import useAsync from "../hooks/useAsync"
import { actualizarProyecto, obtenerCandidatos, obtenerInvitaciones, obtenerProyecto, solicitarUnirse } from "../services/api"
import { coverage, formatDate } from "../lib/projects"
import { getSessionUser } from "../lib/session"
import { inputCls } from "../lib/ui"

/* ------------------------------ Encabezado ------------------------------ */

function ProjectHeader({ project, action }) {
  const creador = {
    id: String(project.creadorId),
    nombre: project.creadorNombre || "Creador del evento",
    carrera: "",
  }
  const nombreCreador = project.creadorNombre || creador.nombre
  const usuarioLocal = getSessionUser()
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
            <Avatar name={esActual ? usuarioLocal.nombre || nombreCreador : nombreCreador} size="xs" />
            Creado por <span className="font-medium text-ink">{esActual ? "ti" : nombreCreador}</span>
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
  const [invited, setInvited] = useState(new Set())
  const [selectedRoles, setSelectedRoles] = useState({})
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
  return (
    <div className="space-y-4">
      {cands.data.length === 0 && <EmptyState icon={SearchX} title="Aún no hay candidatos recomendados">
        Se mostrarán perfiles con consentimiento y evidencia confirmada cuando haya coincidencias elegibles.
      </EmptyState>}
      {cands.data.map((rec) => <Card key={rec.candidate_id} className="p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 className="font-semibold">Persona #{rec.candidate_id}</h3>
            <p className="text-xs text-ink-2">{rec.eligibility === "needs_review" ? "Requiere revisión" : "Elegible"} · {rec.evidence_group === "insufficient_evidence" ? "Evidencia insuficiente" : "Evidencia confirmada"}</p>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => navigate(`/perfil/${rec.candidate_id}`)}>Ver perfil</Button>
            {pendientes.length > 0 && !invited.has(rec.candidate_id) && <>
              <select aria-label={`Rol para persona ${rec.candidate_id}`}
                value={selectedRoles[rec.candidate_id] ?? pendientes[0].id}
                onChange={(event) => setSelectedRoles((prev) => ({ ...prev, [rec.candidate_id]: event.target.value }))}
                className="rounded-lg border border-line bg-surface px-2 text-sm">
                {pendientes.map((rol) => <option key={rol.id} value={rol.id}>{rol.nombre}</option>)}
              </select>
              <Button onClick={() => setTarget({ student: { id: String(rec.candidate_id), nombre: `Persona ${rec.candidate_id}` },
                rol: pendientes.find((rol) => String(rol.id) === String(selectedRoles[rec.candidate_id] ?? pendientes[0].id)) })}>Invitar</Button>
            </>}
          </div>
        </div>
        {rec.explanation.strengths.map((fact, i) => <p key={`s${i}`} className="mt-2 text-sm text-ink">{fact}</p>)}
        {rec.explanation.gaps.map((fact, i) => <p key={`g${i}`} className="mt-2 text-sm text-warn-ink">{fact}</p>)}
        {rec.explanation.unknowns.map((fact, i) => <p key={`u${i}`} className="mt-2 text-sm text-ink-2">{fact}</p>)}
      </Card>)}

      <InviteModal
        open={!!target}
        onClose={() => setTarget(null)}
        student={target?.student}
        rol={target?.rol}
        project={project}
        onSent={(s) => { setInvited((prev) => new Set(prev).add(Number(s.id))); cands.reload() }}
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
    } catch (error) {
      toast(error.message || "No pudimos enviar tu solicitud. Inténtalo de nuevo.", "error")
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
                <span className="flex-1 text-sm font-medium">
                  <span className="block">{r.nombre}</span>
                  {r.habilidades.length > 0 && (
                    <span className="mt-0.5 block text-xs font-normal text-ink-2">
                      Habilidades: {r.habilidades.join(", ")}
                    </span>
                  )}
                </span>
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

function EditProjectModal({ project, onClose, onSaved }) {
  const roleIdPrefix = useId()
  const [tipo, setTipo] = useState(project.tipo)
  const [integrantes, setIntegrantes] = useState(project.integrantes)
  const [fechaLimite, setFechaLimite] = useState(project.fechaLimite || "")
  const [descripcion, setDescripcion] = useState(project.descripcion)
  const [roles, setRoles] = useState(() => project.roles.map((role) => ({ ...role, habilidades: [...role.habilidades] })))
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")

  const updateRole = (roleId, changes) => {
    setRoles((current) => current.map((role) => (
      role.id === roleId ? { ...role, ...changes } : role
    )))
  }

  const addRole = () => {
    setRoles((current) => [
      ...current,
      {
        id: `${roleIdPrefix}-${Date.now()}-${current.length}`,
        nombre: "",
        habilidades: [],
        indispensable: false,
        cubiertoPor: null,
      },
    ])
  }

  const submit = async (event) => {
    event.preventDefault()
    if (roles.some((role) => !role.nombre.trim())) {
      setError("Escribe un nombre para cada rol antes de guardar.")
      return
    }
    setSaving(true)
    setError("")
    try {
      const updated = await actualizarProyecto(project.id, {
        tipo,
        materia: project.materia,
        descripcion,
        fuente_revision: project.fuente_revision,
        integrantes,
        fechaLimite,
        roles,
      })
      onSaved(updated)
    } catch (saveError) {
      setError(saveError.message || "No pudimos guardar los cambios.")
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open
      onClose={onClose}
      title="Editar proyecto"
      description={project.titulo}
      size="lg"
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={saving}>Cancelar</Button>
          <Button type="submit" form="edit-project-form" disabled={saving || roles.length === 0}>
            {saving ? "Guardando…" : "Guardar cambios"}
          </Button>
        </>
      }
    >
      <form id="edit-project-form" onSubmit={submit} className="space-y-6">
        <p className="rounded-lg bg-ai-soft p-3 text-sm">Al guardar tendrás que revisar y confirmar los requisitos actualizados antes de volver a usar el análisis de IA.</p>
        <label className="block text-sm font-semibold">Descripción
          <textarea value={descripcion} onChange={(event) => setDescripcion(event.target.value)} rows={4} className={`${inputCls()} mt-2 w-full`} />
        </label>
        <div>
          <p className="mb-2 text-sm font-semibold">Tipo de proyecto</p>
          <Segmented
            label="Tipo de proyecto"
            value={tipo}
            onChange={setTipo}
            options={[
              ["academico", "Académico"],
              ["personal", "Personal"],
              ["deportivo", "Deportivo"],
              ["videojuegos", "Videojuegos"],
              ["general", "General"],
            ]}
          />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="edit-project-members" className="mb-1.5 block text-sm font-semibold">
              Número de integrantes
            </label>
            <input
              id="edit-project-members"
              type="number"
              min="2"
              max="8"
              required
              value={integrantes}
              onChange={(event) => setIntegrantes(Number(event.target.value))}
              className={inputCls()}
            />
            <p className="mt-1 text-xs text-ink-2">Incluyéndote a ti. De 2 a 8 integrantes.</p>
          </div>
          <div>
            <label htmlFor="edit-project-deadline" className="mb-1.5 block text-sm font-semibold">
              Fecha límite <span className="font-normal text-ink-2">(opcional)</span>
            </label>
            <input
              id="edit-project-deadline"
              type="date"
              value={fechaLimite}
              onChange={(event) => setFechaLimite(event.target.value)}
              className={inputCls()}
            />
          </div>
        </div>

        <section aria-labelledby="edit-project-roles" className="space-y-2">
          <div>
            <h3 id="edit-project-roles" className="text-sm font-semibold">Roles necesarios</h3>
            <p className="text-xs text-ink-2">Puedes quitar roles que ya no necesites. Los que tienen integrantes no se pueden eliminar.</p>
          </div>
          <ul className="space-y-2">
            {roles.map((role) => (
              <li key={role.id} className="flex items-start gap-3 rounded-lg border border-line p-3">
                <div className="min-w-0 flex-1 space-y-2">
                  <label className="block">
                    <span className="sr-only">Nombre del rol</span>
                    <input
                      value={role.nombre}
                      onChange={(event) => updateRole(role.id, { nombre: event.target.value })}
                      disabled={role.ocupados > 0 || Boolean(role.cubiertoPor)}
                      placeholder="Nombre del rol"
                      className={`${inputCls()} disabled:bg-surface-2 disabled:opacity-70`}
                    />
                  </label>
                  <label className="block">
                    <span className="sr-only">Habilidades requeridas, separadas por comas</span>
                    <input
                      value={role.habilidades.join(", ")}
                      onChange={(event) => updateRole(role.id, {
                        habilidades: event.target.value.split(",").map((item) => item.trim()).filter(Boolean),
                      })}
                      placeholder="Habilidades requeridas, separadas por comas"
                      className={inputCls()}
                    />
                  </label>
                  {role.cubiertoPor && <p className="text-xs text-ink-2">Este rol ya tiene integrante.</p>}
                </div>
                <button
                  type="button"
                  aria-label={`Quitar rol ${role.nombre}`}
                  disabled={role.ocupados > 0 || Boolean(role.cubiertoPor) || roles.length === 1}
                  onClick={() => setRoles((current) => current.filter((item) => item.id !== role.id))}
                  className="grid size-10 shrink-0 cursor-pointer place-items-center rounded-lg text-ink-2 hover:bg-danger-soft hover:text-danger disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <Trash2 aria-hidden="true" className="size-4" />
                </button>
              </li>
            ))}
          </ul>
          <Button type="button" variant="secondary" onClick={addRole}>
            <Plus aria-hidden="true" className="size-4" /> Agregar rol
          </Button>
        </section>
        {error && <p role="alert" className="rounded-lg border border-danger/30 bg-danger-soft p-3 text-sm text-danger">{error}</p>}
      </form>
    </Modal>
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
  const sentInvitations = useAsync(obtenerInvitaciones)
  const [joinOpen, setJoinOpen] = useState(false)
  const [requestedRol, setRequestedRol] = useState(null)
  const [editOpen, setEditOpen] = useState(false)
  const toast = useToast()

  const invitedByRole = useMemo(() => {
    if (!project) return {}
    const map = {}
    const pendingInvitations = sentInvitations.data ?? []
    pendingInvitations
      .filter((i) => String(i.projectId) === String(project.id) && i.tipo === "enviada" && i.estado === "pendiente")
      .forEach((i) => {
        const rol = project.roles.find((r) => r.nombre === i.rol)
        if (rol) map[rol.id] = i.destinatario?.nombre ?? `Persona ${i.paraId}`
      })
    return map
  }, [project, sentInvitations.data])

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

  const usuarioLocal = getSessionUser()
  const usuarioId = usuarioLocal.id_usuario
  const esDueno = usuarioId !== undefined && String(project.creadorId) === String(usuarioId)
  const esIntegrante = project.soy_integrante
  const { cubiertos, total, pendientes } = coverage(project)

  const pendingApplication = (sentInvitations.data ?? []).find((item) =>
    String(item.projectId) === String(project.id) && item.estado === "pendiente" &&
    item.tipo === "enviada" && item.tipoSolicitud === "unirse")
  let action
  if (esDueno) {
    action = (
      <Button variant="secondary" onClick={() => setEditOpen(true)}>
        <Pencil aria-hidden="true" className="size-4" /> Editar proyecto
      </Button>
    )
  } else if (esIntegrante) {
    action = (
      <Button as={Link} to="/equipos" variant="secondary">
        <Users aria-hidden="true" className="size-4" /> Ver mi equipo
      </Button>
    )
  } else if (pendientes.length > 0 && project.cupos_disponibles > 0 && project.estado === "Abierto") {
    action = requestedRol || pendingApplication ? (
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
        {esDueno && <ProjectAIReview key={`${project.id}-${project.fuente_revision}-${project.estado_ia}`} project={project} onSaved={reload} />}
        {!esDueno && !project.requisitos_confirmados && <p role="status" className="rounded-lg bg-ai-soft p-4 text-sm">El creador está revisando los requisitos actuales. El análisis anterior ya no se utiliza.</p>}

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

        {esDueno && project.requisitos_confirmados && (
          <section aria-labelledby="cand-title" className="animate-fade-up [animation-delay:180ms]">
            <div className="mb-5 flex flex-wrap items-end justify-between gap-2">
              <div>
                <h2 id="cand-title" className="text-h2 font-semibold">
                  Candidatos recomendados
                </h2>
                <p className="text-sm text-ink-2">Revisa la evidencia y elige un rol disponible antes de invitar.</p>
              </div>
              <LocalProcessing />
            </div>
            <Candidates key={`${project.id}-${project.fuente_revision}-${project.estado_ia}`} project={project} />
          </section>
        )}
      </div>

      {joinOpen && (
        <JoinModal
          open
          onClose={() => setJoinOpen(false)}
          project={project}
          defaultRolId={null}
          onSent={setRequestedRol}
        />
      )}
      {editOpen && (
        <EditProjectModal
          project={project}
          onClose={() => setEditOpen(false)}
          onSaved={() => {
            setEditOpen(false)
            toast("Cambios guardados. Revisa y confirma los requisitos actualizados.")
            reload()
          }}
        />
      )}
    </div>
  )
}
