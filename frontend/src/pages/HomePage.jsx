import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { ArrowRight, Compass, FolderOpen, Plus, UserPen, Users } from "lucide-react"
import Button from "../components/ui/Button"
import Card from "../components/ui/Card"
import { LocalProcessing } from "../components/ui/AIBadge"
import { CardSkeleton, EmptyState, ErrorState, Skeleton } from "../components/ui/Feedback"
import Carousel, { CarouselItem } from "../components/ui/Carousel"
import SkillChip from "../components/ui/SkillChip"
import TeamSummaryCard from "../components/team/TeamSummaryCard"
import StudentSearch from "../components/search/StudentSearch"
import RecommendationConsentStatus from "../components/profile/RecommendationConsentStatus"
import useAsync from "../hooks/useAsync"
import {
  obtenerEquipos,
  obtenerPerfil,
  obtenerProyectos,
  obtenerRecomendaciones,
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

export function ProfileProgress({ value, status }) {
  if (status === "success" && value === 100) return null

  const r = 22
  const c = 2 * Math.PI * r
  const progress = value ?? 0
  const message = status === "loading"
    ? "Calculando el avance de tu perfil…"
    : status === "error"
      ? "No pudimos calcular el avance de tu perfil."
      : progress === 100
        ? "¡Tu perfil está completo!"
        : progress >= 60
          ? "Tu perfil está casi listo"
          : "Completa tu perfil"

  return (
    <Card className="flex animate-scale-in items-center gap-4 border-primary/20 bg-linear-to-r from-primary-soft to-surface p-4 sm:p-5">
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
            strokeDashoffset={c * (1 - progress / 100)}
            className="stroke-primary transition-[stroke-dashoffset] duration-1000 ease-out"
          />
        </svg>
        <span className="absolute text-xs font-bold">{value === null ? "—" : `${value}%`}</span>
      </div>
      <div className="min-w-0 flex-1">
        <p className="font-semibold text-ink">{message}</p>
        <p className="text-sm text-ink-2">
          {status === "success"
            ? "Revisa los campos de tu perfil y confirma la información que quieras compartir."
            : status === "loading"
              ? "Estamos revisando los datos que has completado."
              : "Vuelve a cargar la página para intentarlo de nuevo."}
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

// Aviso compacto: cuando aún no hay recomendaciones, no debe ocupar el lugar de los proyectos reales.
function RecsNotice({ locked }) {
  return (
    <Card className="flex animate-fade-up flex-col gap-4 border-dashed p-4 sm:flex-row sm:items-center sm:p-5">
      <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-primary-soft text-primary">
        <Compass aria-hidden="true" className="size-5" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="font-semibold text-ink">
          {locked ? "Activa las recomendaciones" : "Aún no hay recomendaciones para tu perfil"}
        </p>
        <p className="text-sm text-ink-2">
          {locked
            ? "Confirma tu perfil y acepta las recomendaciones para ver proyectos que complementan lo que sabes."
            : "Mientras tanto, explora los proyectos publicados o completa tu perfil para mejorar las sugerencias."}
        </p>
      </div>
      <Button variant="secondary" size="sm" as={Link} to="/perfil" className="shrink-0 self-start sm:self-center">
        <UserPen aria-hidden="true" className="size-4" /> {locked ? "Ir a mi perfil" : "Completar perfil"}
      </Button>
    </Card>
  )
}

/* ------------------------- Recomendado para ti ------------------------- */

function Recommendations({ onState }) {
  const [proyectos, setProyectos] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let active = true
    Promise.all([obtenerRecomendaciones(), obtenerProyectos()])
      .then(([resultado, eventos]) => {
        if (!active) return
        const byId = new Map(eventos.map((evento) => [evento.id, evento]))
        setProyectos(resultado.proyectos.map((rec) => ({ ...rec, proyecto: byId.get(String(rec.event_id)) })))
        setLoading(false)
        onState?.(resultado.proyectos.length ? "ready" : "empty")
      })
      .catch((err) => {
        if (!active) return
        setError(err)
        setLoading(false)
        onState?.(err.status === 403 ? "locked" : "error")
      })
    return () => { active = false }
  }, [onState])

  if (loading) {
    return (
      <div className="flex gap-4 overflow-hidden" aria-busy="true">
        <span className="sr-only">Cargando recomendaciones…</span>
        {[0, 1, 2].map((i) => (
          <CardSkeleton key={i} className="w-[85%] max-w-90 shrink-0 sm:w-85" />
        ))}
      </div>
    )
  }

  if (error) {
    return error.status === 403
      ? <RecsNotice locked />
      : <ErrorState message="No pudimos cargar las recomendaciones." />
  }

  if (!proyectos.length) return <RecsNotice />

  return (
    <>
      <div className="animate-fade-in" role="tabpanel">
        <Carousel label="Proyectos recomendados">
          {proyectos.map(({ proyecto, ...rec }, i) => (
            <CarouselItem key={rec.event_id}>
              <Card interactive className="group flex h-full animate-fade-up flex-col justify-between p-6 shadow-sm" style={{ animationDelay: `${i * 90}ms` }}>
                <div>
                  <div className="flex items-center justify-between gap-2">
                    <span className="rounded-md bg-primary/10 px-2.5 py-1 text-xs font-semibold text-primary uppercase tracking-wider">
                      {proyecto?.tipo || "Proyecto"}
                    </span>
                    <span className="text-xs text-ink-2">{rec.eligibility === "needs_review" ? "Requiere revisión" : "Elegible por evidencias"}</span>
                  </div>
                  <h3 className="mt-3 text-lg font-bold text-ink">{proyecto?.titulo || `Proyecto ${rec.event_id}`}</h3>
                  <p className="mt-1 text-xs text-ink-2">{proyecto?.acepta_participacion ? "Con vacantes de rol" : proyecto?.motivo_no_disponible || "Disponibilidad por verificar"}</p>
                  <p className="mt-2 line-clamp-3 text-sm text-ink-2">{rec.explanation.strengths[0] || rec.explanation.unknowns[0] || "Revisa los requisitos del proyecto."}</p>
                </div>

                <div className="mt-6 pt-4 border-t border-line flex items-center justify-between">
                  <span className="text-xs text-ink-2">
                    {rec.evidence_group === "insufficient_evidence" ? "Evidencia insuficiente" : "Basado en hechos confirmados"}
                  </span>
                  <Link
                    to={`/proyectos/${rec.event_id}`}
                    className="inline-flex items-center gap-1 text-xs font-semibold text-primary hover:underline"
                  >
                    Ver detalle <ArrowRight className="size-3 transition-transform duration-200 group-hover:translate-x-1" />
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

/* ----------------------- Proyectos en la plataforma ----------------------- */

const TIPO = { academico: "Académico", personal: "Personal" }

function ProjectsFeed() {
  const proyectos = useAsync(obtenerProyectos)

  if (proyectos.loading) {
    return (
      <div className="flex gap-4 overflow-hidden" aria-busy="true">
        <span className="sr-only">Cargando proyectos…</span>
        {[0, 1].map((i) => (
          <CardSkeleton key={i} className="w-[85%] max-w-90 shrink-0 sm:w-85" />
        ))}
      </div>
    )
  }

  if (proyectos.status === "error") {
    return <ErrorState message="No pudimos cargar los proyectos." onRetry={proyectos.reload} />
  }

  if (!proyectos.data.length) {
    return (
      <EmptyState
        icon={FolderOpen}
        title="Todavía no hay proyectos publicados"
        actions={
          <Button as={Link} to="/proyectos/nuevo">
            <Plus aria-hidden="true" className="size-4" /> Crear el primero
          </Button>
        }
      >
        Publica tu idea y la plataforma te ayudará a encontrar a quienes la complementan.
      </EmptyState>
    )
  }

  return (
    <Carousel label="Proyectos en la plataforma">
      {proyectos.data.map((p, i) => {
        const buscan = (p.roles_disponibles.length ? p.roles_disponibles : p.roles.filter((r) => !r.cubiertoPor))
          .map((r) => r.nombre)
          .filter(Boolean)
        return (
          <CarouselItem key={p.id}>
            <Card
              interactive
              className="group flex h-full animate-fade-up flex-col justify-between p-6"
              style={{ animationDelay: `${i * 90}ms` }}
            >
              <div>
                <div className="flex items-center justify-between gap-2">
                  <span className="rounded-md bg-primary-soft px-2.5 py-1 text-xs font-semibold tracking-wider text-primary uppercase">
                    {TIPO[p.tipo] ?? "Proyecto"}
                  </span>
                  {p.acepta_participacion ? (
                    <span className="inline-flex items-center gap-1.5 text-xs font-medium text-success-ink">
                      <span className="size-1.5 rounded-full bg-success" aria-hidden="true" />
                      {p.cupos_disponibles > 0
                        ? `${p.cupos_disponibles} ${p.cupos_disponibles === 1 ? "lugar disponible" : "lugares disponibles"}`
                        : "Acepta participantes"}
                    </span>
                  ) : (
                    <span className="text-xs text-ink-2">{p.soy_integrante ? "Ya participas" : "Sin vacantes"}</span>
                  )}
                </div>
                <h3 className="mt-3 line-clamp-2 text-lg font-bold text-ink">{p.titulo}</h3>
                {p.creadorNombre && <p className="mt-0.5 text-xs text-ink-2">Publicado por {p.creadorNombre}</p>}
                {p.descripcion && <p className="mt-2 line-clamp-2 text-sm text-ink-2">{p.descripcion}</p>}
                {buscan.length > 0 && (
                  <ul className="mt-4 flex flex-wrap gap-1.5" aria-label="Roles que buscan">
                    {buscan.slice(0, 3).map((nombre) => (
                      <li key={nombre}>
                        <SkillChip variant="needed">{nombre}</SkillChip>
                      </li>
                    ))}
                    {buscan.length > 3 && <li className="self-center text-xs text-ink-2">+{buscan.length - 3}</li>}
                  </ul>
                )}
              </div>

              <div className="mt-6 flex items-center justify-end border-t border-line pt-4">
                <Link
                  to={`/proyectos/${p.id}`}
                  className="inline-flex items-center gap-1 text-xs font-semibold text-primary hover:underline"
                >
                  Ver detalle <ArrowRight aria-hidden="true" className="size-3 transition-transform duration-200 group-hover:translate-x-1" />
                </Link>
              </div>
            </Card>
          </CarouselItem>
        )
      })}
    </Carousel>
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
  
  const nombreReal = perfilQuery.data?.nombre || usuarioGuardado.nombre || "Estudiante"
  const progresoReal = perfilQuery.status === "success" ? perfilQuery.data.perfilCompleto : null
  const [recsState, setRecsState] = useState("loading")
  const feedFirst = recsState === "empty" || recsState === "locked"

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-8 sm:py-10">
      <header className="mb-6 flex animate-fade-up flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-h1 font-bold text-ink">
            {greeting()}, {firstName(nombreReal)}
          </h1>
          <p className="mt-1 text-ink-2">Esto es lo que encontramos para ti hoy en la plataforma.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button as={Link} to="/proyectos/nuevo" className="max-lg:hidden">
            <Plus aria-hidden="true" className="size-4" /> Crear proyecto
          </Button>
        </div>
      </header>

      <section
        aria-labelledby="search-title"
        className="mb-10 animate-fade-up [animation-delay:60ms]"
      >
        <SectionHeader
          id="search-title"
          title="¿Buscas a alguien en particular?"
          desc="Busca por nombre o habilidad y filtra por carrera, horario o semestre."
        />
        <StudentSearch />
      </section>

      <div className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="flex min-w-0 flex-col gap-10">
          <div className="order-1 animate-fade-up [animation-delay:60ms]">
            <ProfileProgress value={progresoReal} status={perfilQuery.status} />
            {perfilQuery.status === "success" && <div className="mt-3"><RecommendationConsentStatus
              consent={perfilQuery.data.consentimiento_recomendaciones} paused={perfilQuery.data.pausado} /></div>}
          </div>

          <section aria-labelledby="rec-title" className={`animate-fade-up [animation-delay:120ms] ${feedFirst ? "order-3" : "order-2"}`}>
            <SectionHeader
              id="rec-title"
              title="Recomendados para ti"
              desc="Proyectos donde tu perfil complementa lo que el equipo necesita"
              action={<LocalProcessing />}
            />
            <Recommendations onState={setRecsState} />
          </section>

          <section aria-labelledby="feed-title" className={`animate-fade-up [animation-delay:180ms] ${feedFirst ? "order-2" : "order-3"}`}>
            <SectionHeader
              id="feed-title"
              title="Proyectos en la plataforma"
              desc="Ideas que tus compañeros ya publicaron y están formando equipo"
              action={
                <Link to="/proyectos" className="text-sm font-semibold text-primary hover:underline">
                  Ver todos
                </Link>
              }
            />
            <ProjectsFeed />
          </section>

        </div>

        <aside className="animate-fade-up space-y-10 [animation-delay:150ms]">
          <MyTeams />
          <Link
            to="/proyectos"
            className="group flex items-center justify-between rounded-xl border border-dashed border-line p-4 text-sm text-ink-2 transition-all duration-300 hover:-translate-y-0.5 hover:border-primary hover:bg-primary-soft hover:text-primary"
          >
            Explorar todos los proyectos abiertos
            <ArrowRight aria-hidden="true" className="size-4 transition-transform group-hover:translate-x-1" />
          </Link>
        </aside>
      </div>
    </div>
  )
}
