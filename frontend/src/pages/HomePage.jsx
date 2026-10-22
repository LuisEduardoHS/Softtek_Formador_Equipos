import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { ArrowRight, Compass, Inbox, Plus, UserPen, Users } from "lucide-react"
import Button from "../components/ui/Button"
import Card from "../components/ui/Card"
import { LocalProcessing } from "../components/ui/AIBadge"
import { CardSkeleton, EmptyState, ErrorState, Skeleton } from "../components/ui/Feedback"
import { useToast } from "../components/ui/Toast"
import Carousel, { CarouselItem } from "../components/ui/Carousel"
import InvitationItem from "../components/invite/InvitationItem"
import TeamSummaryCard from "../components/team/TeamSummaryCard"
import StudentSearch from "../components/search/StudentSearch"
import useAsync from "../hooks/useAsync"
import {
  obtenerEquipos,
  obtenerInvitaciones,
  responderInvitacion,
  obtenerPerfil,
} from "../services/api"
import { firstName } from "../lib/projects"
import { getSessionUser } from "../lib/session"

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

function ProfileProgress({ value = 75 }) {
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
          Agrega tus habilidades y tecnologías para que la IA encuentre tu equipo ideal.
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
      title="Aún no hay proyectos o recomendaciones"
      actions={
        <>
          <Button as={Link} to="/perfil">
            <UserPen aria-hidden="true" className="size-4" /> Completar perfil
          </Button>
          <Button variant="ghost" as={Link} to="/proyectos/nuevo">
            <Plus aria-hidden="true" className="size-4" /> Crear un proyecto
          </Button>
        </>
      }
    >
      Actualmente no hay proyectos publicados en tu universidad. ¡Sé el primero en crear una convocatoria o completa tu perfil!
    </EmptyState>
  )
}

/* ------------------------- Recomendado para ti ------------------------- */

function Recommendations() {
  const [proyectos, setProyectos] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [tab, setTab] = useState("proyectos")

  useEffect(() => {
    fetch("http://127.0.0.1:8000/eventos/")
      .then((res) => {
        if (!res.ok) throw new Error("Error en la API")
        return res.json()
      })
      .then((data) => {
        setProyectos(data)
        setLoading(false)
      })
      .catch((err) => {
        console.error("Error al obtener eventos:", err)
        setError(true)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className="flex gap-4 overflow-hidden" aria-busy="true">
        <span className="sr-only">Cargando proyectos desde MySQL…</span>
        {[0, 1, 2].map((i) => (
          <CardSkeleton key={i} className="w-[85%] max-w-[360px] shrink-0 sm:w-[340px]" />
        ))}
      </div>
    )
  }

  if (error) {
    return <ErrorState message="No pudimos conectar con la base de datos de eventos." />
  }

  if (!proyectos.length) return <ColdStart />

  const tabs = [
    { id: "proyectos", label: "Proyectos en MySQL", count: proyectos.length }
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
            className="min-h-9 cursor-pointer rounded-md bg-surface px-4 text-sm font-semibold text-ink shadow-card"
          >
            {t.label} <span className="font-normal text-ink-2">{t.count}</span>
          </button>
        ))}
      </div>

      <div className="animate-fade-in" role="tabpanel">
        <Carousel label="Proyectos en tu Universidad">
          {proyectos.map((evento) => (
            <CarouselItem key={evento.id_evento}>
              <Card className="flex h-full flex-col justify-between p-6 shadow-sm">
                <div>
                  <div className="flex items-center justify-between gap-2">
                    <span className="rounded-md bg-primary/10 px-2.5 py-1 text-xs font-semibold text-primary uppercase tracking-wider">
                      {evento.categoria_principal}
                    </span>
                    <span className="text-xs text-ink-2">{evento.estado}</span>
                  </div>
                  <h3 className="mt-3 text-lg font-bold text-ink">{evento.titulo}</h3>
                  <p className="mt-2 line-clamp-3 text-sm text-ink-2">{evento.descripcion_libre}</p>
                </div>

                <div className="mt-6 pt-4 border-t border-line flex items-center justify-between">
                  <span className="text-xs text-ink-2">
                    {evento.detalles_especificos?.modalidad || "Presencial"}
                  </span>
                  <Link
                    to={`/proyectos/${evento.id_evento}`}
                    className="inline-flex items-center gap-1 text-xs font-semibold text-primary hover:underline"
                  >
                    Ver detalle <ArrowRight className="size-3" />
                  </Link>
                </div>
              </Card>
            </CarouselItem>
          ))}
        </Carousel>
      </div>
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
      const result = await responderInvitacion(invitation.id, estado)
      inv.setData((list) => list.map((i) => (i.id === invitation.id ? { ...i, estado: result.estado } : i)))
      toast(estado === "aceptada" ? `¡Te uniste al proyecto!` : "Rechazaste la invitación.", estado === "aceptada" ? "success" : "info")
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
      </div>
    )
  } else if (inv.status === "error") {
    body = <ErrorState message="No pudimos cargar tus invitaciones." onRetry={inv.reload} />
  } else {
    const pendientes = inv.data.filter((i) => i.tipo === "recibida" && i.estado === "pendiente")
    body =
      pendientes.length === 0 ? (
        <EmptyState icon={Inbox} title="Sin invitaciones por ahora" className="py-8">
          Cuando alguien quiera sumarte a su equipo, aparecerá aquí.
        </EmptyState>
      ) : (
        <ul className="space-y-2">
          {pendientes.map((i) => (
            <InvitationItem
              key={i.id}
              invitation={i}
              person={i.remitente}
              project={i.proyecto}
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
          <TeamSummaryCard key={t.id} team={t} project={t.proyecto} />
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
  const perfilQuery = useAsync(obtenerPerfil)
  const usuarioGuardado = getSessionUser()
  
  const nombreReal = usuarioGuardado.nombre || perfilQuery.data?.nombre || "Estudiante"
  const progresoReal = perfilQuery.data?.perfilCompleto || 20

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-8 sm:py-10">
      <header className="mb-6 flex animate-fade-up flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-h1 font-bold text-ink">
            {greeting()}, {firstName(nombreReal)}
          </h1>
          <p className="mt-1 text-ink-2">Esto es lo que encontramos para ti hoy en la plataforma.</p>
        </div>
        <Button as={Link} to="/proyectos/nuevo" className="hidden lg:inline-flex">
          <Plus aria-hidden="true" className="size-4" /> Crear proyecto
        </Button>
      </header>

      <div className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="min-w-0 space-y-10">
          <div className="animate-fade-up [animation-delay:60ms]">
            <ProfileProgress value={progresoReal} />
          </div>

          <section aria-labelledby="rec-title" className="animate-fade-up [animation-delay:120ms]">
            <SectionHeader
              id="rec-title"
              title="Convocatorias Abiertas"
              desc="Proyectos y eventos registrados en MySQL para formar equipo."
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