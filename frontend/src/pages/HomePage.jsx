import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { ArrowRight, Compass, Inbox, Plus, UserPen, Users } from "lucide-react"
import Button from "../components/ui/Button"
import Card from "../components/ui/Card"
import SkillChip from "../components/ui/SkillChip"
import { LocalProcessing } from "../components/ui/AIBadge"
import { CardSkeleton, EmptyState, ErrorState, Skeleton } from "../components/ui/Feedback"
import { useToast } from "../components/ui/Toast"
import Carousel, { CarouselItem } from "../components/ui/Carousel"
import RecommendationCard from "../components/recommendation/RecommendationCard"
import ProjectCard, { RoleDots } from "../components/project/ProjectCard"
import InvitationItem from "../components/invite/InvitationItem"
import InviteModal from "../components/invite/InviteModal"
import TeamSummaryCard from "../components/team/TeamSummaryCard"
import StudentSearch from "../components/search/StudentSearch"
import useAsync from "../hooks/useAsync"
import {
  enviarRetroalimentacion,
  obtenerEquipos,
  obtenerInvitaciones,
  obtenerRecomendaciones,
  responderInvitacion,
} from "../services/api"
import { currentUser, pendingInviteIds, projectById, studentById } from "../data/mockData"
import { coverage, firstName } from "../lib/projects"

function greeting() {
  const h = new Date().getHours()
  if (h < 12) return "Buenos días"
  if (h < 19) return "Buenas tardes"
  return "Buenas noches"
}

function SectionHeader({ title, desc, action, id }) {
  return (
    <div className="mb-4 flex flex-wrap items-end justify-between gap-2">
      <div>
        <h2 id={id} className="text-h2 font-semibold text-ink">
          {title}
        </h2>
        {desc && <p className="text-sm text-ink-2">{desc}</p>}
      </div>
      {action}
    </div>
  )
}

/* ------------------------- Perfil completo ------------------------- */

function ProfileProgress({ value }) {
  const r = 22
  const c = 2 * Math.PI * r
  return (
    <Card className="flex items-center gap-4 p-4 sm:p-5">
      <div className="relative grid size-14 shrink-0 place-items-center">
        <svg viewBox="0 0 52 52" className="size-14 -rotate-90" aria-hidden="true">
          <circle cx="26" cy="26" r={r} fill="none" strokeWidth="5" className="stroke-surface-2" />
          <circle
            cx="26"
            cy="26"
            r={r}
            fill="none"
            strokeWidth="5"
            strokeLinecap="round"
            strokeDasharray={c}
            strokeDashoffset={c * (1 - value / 100)}
            className="stroke-success transition-[stroke-dashoffset] duration-700"
          />
        </svg>
        <span className="absolute text-xs font-bold">{value}%</span>
      </div>
      <div className="min-w-0 flex-1">
        <p className="font-semibold text-ink">Tu perfil está casi listo</p>
        <p className="text-sm text-ink-2">
          Agrega un enlace de contacto para que tu futuro equipo pueda escribirte.
        </p>
      </div>
      <Button variant="secondary" size="sm" as={Link} to="/perfil" className="shrink-0">
        <UserPen aria-hidden="true" className="size-4" />
        <span className="hidden sm:inline">Completar</span>
      </Button>
    </Card>
  )
}

/* -------------------------- Arranque en frío -------------------------- */

function ColdStart() {
  return (
    <EmptyState
      icon={Compass}
      title="Estamos conociéndote"
      actions={
        <>
          <Button as={Link} to="/perfil">
            <UserPen aria-hidden="true" className="size-4" /> Completar perfil
          </Button>
          <Button variant="secondary" as={Link} to="/proyectos">
            Explorar proyectos
          </Button>
          <Button variant="ghost" as={Link} to="/proyectos/nuevo">
            <Plus aria-hidden="true" className="size-4" /> Crear uno
          </Button>
        </>
      }
    >
      Aún no tenemos recomendaciones para ti. Mientras más nos cuentes de lo que sabes hacer, mejores compañeros
      podremos sugerirte. También puedes explorar proyectos abiertos o crear el tuyo.
    </EmptyState>
  )
}

/* ------------------------- Recomendado para ti ------------------------- */

function Recommendations() {
  const navigate = useNavigate()
  const recs = useAsync(obtenerRecomendaciones)
  const [tab, setTab] = useState("companeros")
  const [inviteTarget, setInviteTarget] = useState(null)
  const [invited, setInvited] = useState(() => pendingInviteIds("p1"))

  if (recs.loading) {
    return (
      <div className="flex gap-4 overflow-hidden" aria-busy="true">
        <span className="sr-only">Cargando recomendaciones…</span>
        {[0, 1, 2].map((i) => (
          <CardSkeleton key={i} className="w-[85%] max-w-[360px] shrink-0 sm:w-[340px]" />
        ))}
      </div>
    )
  }
  if (recs.status === "error") {
    return <ErrorState message="No pudimos cargar tus recomendaciones." onRetry={recs.reload} />
  }

  const { companeros, proyectos } = recs.data
  if (!companeros.length && !proyectos.length) return <ColdStart />

  // Las recomendaciones de compañeros se muestran en el contexto de tu proyecto
  const project = companeros.length ? projectById(companeros[0].projectId) : null
  const { pendientes } = project ? coverage(project) : { pendientes: [] }

  const tabs = [
    { id: "companeros", label: "Compañeros", count: companeros.length },
    { id: "proyectos", label: "Proyectos", count: proyectos.length },
  ]

  return (
    <>
      <div role="tablist" aria-label="Tipo de recomendación" className="mb-4 inline-flex rounded-lg bg-surface-2 p-1">
        {tabs.map((t) => (
          <button
            key={t.id}
            role="tab"
            type="button"
            aria-selected={tab === t.id}
            onClick={() => setTab(t.id)}
            className={`min-h-9 cursor-pointer rounded-md px-4 text-sm font-semibold transition-all ${
              tab === t.id ? "bg-surface text-ink shadow-card" : "text-ink-2 hover:text-ink"
            }`}
          >
            {t.label} <span className="font-normal text-ink-2">{t.count}</span>
          </button>
        ))}
      </div>

      {tab === "companeros" && project && (
        <div key="c" className="animate-fade-in" role="tabpanel">
          <div className="mb-4 flex flex-col gap-2 rounded-xl border border-line bg-surface p-3 sm:flex-row sm:items-center sm:gap-4">
            <p className="text-sm">
              Para <Link to={`/proyectos/${project.id}`} className="font-semibold text-ink hover:text-primary hover:underline">{project.titulo}</Link>
            </p>
            <RoleDots roles={project.roles} />
            <div className="flex flex-wrap gap-1.5 sm:ml-auto">
              {pendientes.map((r) => (
                <SkillChip key={r.id} variant="needed">
                  {r.nombre}
                </SkillChip>
              ))}
            </div>
          </div>
          <Carousel label="Compañeros recomendados">
            {companeros.map((rec) => {
              const student = studentById(rec.studentId)
              const rol = project.roles.find((r) => r.id === rec.rolId)
              return (
                <CarouselItem key={rec.id}>
                  <RecommendationCard
                    student={student}
                    rol={rol}
                    rec={rec}
                    invited={invited.has(student.id)}
                    onInvite={() => setInviteTarget({ student, rol })}
                    onViewProfile={() => navigate(`/perfil/${student.id}`)}
                    onFeedback={(v) => enviarRetroalimentacion(rec.id, { util: v === "util" })}
                    onDismiss={(motivo) => enviarRetroalimentacion(rec.id, { util: false, motivo })}
                    className="h-full"
                  />
                </CarouselItem>
              )
            })}
          </Carousel>
        </div>
      )}

      {tab === "proyectos" && (
        <div key="p" className="animate-fade-in" role="tabpanel">
          <Carousel label="Proyectos recomendados">
            {proyectos.map((s) => (
              <CarouselItem key={s.projectId}>
                <ProjectCard project={projectById(s.projectId)} suggestion={s} className="h-full" />
              </CarouselItem>
            ))}
          </Carousel>
        </div>
      )}

      <InviteModal
        open={!!inviteTarget}
        onClose={() => setInviteTarget(null)}
        student={inviteTarget?.student}
        rol={inviteTarget?.rol}
        project={project}
        onSent={(s) => setInvited((prev) => new Set(prev).add(s.id))}
      />
    </>
  )
}

/* ------------------------ Invitaciones pendientes ------------------------ */

function PendingInvitations() {
  const toast = useToast()
  const inv = useAsync(obtenerInvitaciones)
  const [busy, setBusy] = useState(null)

  const respond = async (invitation, estado) => {
    setBusy(invitation.id)
    try {
      await responderInvitacion(invitation.id, estado)
      inv.setData((list) => list.map((i) => (i.id === invitation.id ? { ...i, estado } : i)))
      const project = projectById(invitation.projectId)
      toast(estado === "aceptada" ? `¡Te uniste a «${project.titulo}»!` : "Rechazaste la invitación.", estado === "aceptada" ? "success" : "info")
    } catch {
      toast("No pudimos registrar tu respuesta. Inténtalo de nuevo.", "error")
    } finally {
      setBusy(null)
    }
  }

  let body
  if (inv.loading) {
    body = (
      <div className="space-y-2">
        <Skeleton className="h-28 w-full rounded-xl" />
        <Skeleton className="h-28 w-full rounded-xl" />
      </div>
    )
  } else if (inv.status === "error") {
    body = <ErrorState message="No pudimos cargar tus invitaciones." onRetry={inv.reload} />
  } else {
    const pendientes = inv.data.filter((i) => i.tipo === "recibida" && i.estado === "pendiente")
    const respondidas = inv.data.filter((i) => i.tipo === "recibida" && i.estado === "aceptada")
    body =
      pendientes.length === 0 && respondidas.length === 0 ? (
        <EmptyState icon={Inbox} title="Sin invitaciones por ahora" className="py-8">
          Cuando alguien quiera sumarte a su equipo, aparecerá aquí.
        </EmptyState>
      ) : (
        <ul className="space-y-2">
          {[...pendientes, ...respondidas].map((i) => (
            <InvitationItem
              key={i.id}
              invitation={i}
              person={studentById(i.deId)}
              project={projectById(i.projectId)}
              busy={busy === i.id}
              onRespond={(estado) => respond(i, estado)}
              compact
            />
          ))}
        </ul>
      )
  }

  return (
    <section aria-labelledby="inv-title">
      <SectionHeader
        id="inv-title"
        title="Invitaciones"
        action={
          <Link to="/invitaciones" className="text-sm font-semibold text-primary hover:underline">
            Ver todas
          </Link>
        }
      />
      {body}
    </section>
  )
}

/* ------------------------------ Mis equipos ------------------------------ */

function MyTeams() {
  const teams = useAsync(obtenerEquipos)
  let body
  if (teams.loading) {
    body = <Skeleton className="h-32 w-full rounded-xl" />
  } else if (teams.status === "error") {
    body = <ErrorState message="No pudimos cargar tus equipos." onRetry={teams.reload} />
  } else if (teams.data.length === 0) {
    body = (
      <EmptyState icon={Users} title="Aún no estás en un equipo" className="py-8">
        Acepta una invitación o crea un proyecto para empezar.
      </EmptyState>
    )
  } else {
    body = (
      <div className="space-y-2">
        {teams.data.map((t) => (
          <TeamSummaryCard key={t.id} team={t} project={projectById(t.projectId)} />
        ))}
      </div>
    )
  }
  return (
    <section aria-labelledby="teams-title">
      <SectionHeader
        id="teams-title"
        title="Mis equipos"
        action={
          <Link to="/equipos" className="text-sm font-semibold text-primary hover:underline">
            Ver todos
          </Link>
        }
      />
      {body}
    </section>
  )
}

/* -------------------------------- Página -------------------------------- */

export default function HomePage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-8 sm:py-10">
      <header className="mb-6 flex animate-fade-up flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-h1 font-bold text-ink">
            {greeting()}, {firstName(currentUser.nombre)}
          </h1>
          <p className="mt-1 text-ink-2">Esto es lo que encontramos para ti hoy.</p>
        </div>
        <Button as={Link} to="/proyectos/nuevo" className="hidden lg:inline-flex">
          <Plus aria-hidden="true" className="size-4" /> Crear proyecto
        </Button>
      </header>

      <div className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="min-w-0 space-y-10">
          <div className="animate-fade-up [animation-delay:60ms]">
            <ProfileProgress value={currentUser.perfilCompleto} />
          </div>

          <section aria-labelledby="rec-title" className="animate-fade-up [animation-delay:120ms]">
            <SectionHeader
              id="rec-title"
              title="Recomendado para ti"
              desc="Personas y proyectos que complementan lo que tú ya sabes hacer."
              action={<LocalProcessing />}
            />
            <Recommendations />
          </section>

          <section aria-labelledby="search-title" className="animate-fade-up [animation-delay:180ms]">
            <SectionHeader
              id="search-title"
              title="¿Buscas a alguien en particular?"
              desc="Busca por nombre o habilidad y filtra por carrera, horario o semestre."
            />
            <StudentSearch />
          </section>
        </div>

        <aside className="animate-fade-up space-y-10 [animation-delay:150ms]">
          <PendingInvitations />
          <MyTeams />
          <Link
            to="/proyectos"
            className="group flex items-center justify-between rounded-xl border border-dashed border-line p-4 text-sm text-ink-2 transition-colors hover:border-primary hover:text-primary"
          >
            Explorar todos los proyectos abiertos
            <ArrowRight aria-hidden="true" className="size-4 transition-transform group-hover:translate-x-0.5" />
          </Link>
        </aside>
      </div>
    </div>
  )
}
