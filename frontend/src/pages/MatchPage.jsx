import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { ArrowLeft, ArrowRight, Compass } from "lucide-react"
import MatchCard from "../components/match/MatchCard"
import InviteModal from "../components/invite/InviteModal"
import Button from "../components/ui/Button"
import { LocalProcessing } from "../components/ui/AIBadge"
import { EmptyState } from "../components/ui/Feedback"
import { pendingInviteIds, projectById, recommendations, studentById } from "../data/mockData"

/**
 * Coincidencias una por una, a pantalla completa. Se llega aquí al terminar
 * de configurar el perfil o desde una notificación de la IA.
 */
export default function MatchPage() {
  const navigate = useNavigate()
  const [index, setIndex] = useState(0)
  const [inviting, setInviting] = useState(false)
  const [invited, setInvited] = useState(() => pendingInviteIds("p1"))

  const rec = recommendations[index]
  if (!rec) {
    return (
      <div className="mx-auto max-w-xl px-4 py-16">
        <EmptyState
          icon={Compass}
          title="Viste todas tus coincidencias"
          actions={
            <Button as={Link} to="/inicio">
              Ir al inicio
            </Button>
          }
        >
          Te avisaremos cuando la IA encuentre a alguien más que complemente tu equipo.
        </EmptyState>
      </div>
    )
  }

  const project = projectById(rec.projectId)
  const student = studentById(rec.studentId)
  const rol = project.roles.find((r) => r.id === rec.rolId)

  return (
    <div className="relative overflow-hidden">
      {/* Brillos del diseño de Figma, contenidos en la zona de la tarjeta */}
      <div aria-hidden="true" className="pointer-events-none absolute inset-0">
        <span className="absolute -top-32 left-1/2 size-[28rem] -translate-x-1/2 rounded-full bg-primary/10 blur-[110px] dark:bg-primary/25" />
      </div>

      <div className="relative mx-auto flex max-w-xl flex-col items-center px-4 py-8 sm:py-12">
        <p className="text-label font-semibold tracking-[0.18em] text-primary uppercase">Nueva coincidencia</p>
        <h1 className="mt-2 text-center text-h1 font-bold">Encontramos a alguien para tu equipo</h1>
        <p className="mt-1 text-center text-sm text-ink-2">
          Para{" "}
          <Link to={`/proyectos/${project.id}`} className="font-semibold text-ink hover:text-primary hover:underline">
            {project.titulo}
          </Link>
        </p>
        <LocalProcessing className="mt-3" />

        <div key={rec.id} className="mt-8 flex w-full justify-center">
          <MatchCard
            student={student}
            rol={rol}
            rec={rec}
            invited={invited.has(student.id)}
            onInvite={() => setInviting(true)}
            onGoToProfile={() => navigate(`/perfil/${student.id}`)}
          />
        </div>

        <div className="mt-6 flex w-full max-w-md items-center justify-between">
          <Button variant="ghost" onClick={() => setIndex((i) => i - 1)} disabled={index === 0}>
            <ArrowLeft aria-hidden="true" className="size-4" /> Anterior
          </Button>
          <span className="text-sm text-ink-2" aria-live="polite">
            {index + 1} de {recommendations.length}
          </span>
          <Button variant="ghost" onClick={() => setIndex((i) => i + 1)}>
            Siguiente <ArrowRight aria-hidden="true" className="size-4" />
          </Button>
        </div>
      </div>

      <InviteModal
        open={inviting}
        onClose={() => setInviting(false)}
        student={student}
        project={project}
        rol={rol}
        onSent={(s) => setInvited((prev) => new Set(prev).add(s.id))}
      />
    </div>
  )
}
