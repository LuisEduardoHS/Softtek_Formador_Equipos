import { useCallback, useState } from "react"
import { Link } from "react-router-dom"
import { ArrowLeft, ArrowRight, Compass } from "lucide-react"
import Button from "../components/ui/Button"
import Card from "../components/ui/Card"
import { LocalProcessing } from "../components/ui/AIBadge"
import { EmptyState, ErrorState, CardSkeleton } from "../components/ui/Feedback"
import useAsync from "../hooks/useAsync"
import { obtenerProyectos, obtenerRecomendaciones } from "../services/api"

export default function MatchPage() {
  const load = useCallback(async () => {
    const [recommendations, projects] = await Promise.all([obtenerRecomendaciones(), obtenerProyectos()])
    const byId = new Map(projects.map((project) => [project.id, project]))
    return recommendations.proyectos.map((rec) => ({ ...rec, project: byId.get(String(rec.event_id)) }))
  }, [])
  const result = useAsync(load)
  const [index, setIndex] = useState(0)

  if (result.loading) return <div className="mx-auto max-w-xl px-4 py-12"><CardSkeleton /></div>
  if (result.status === "error") return <div className="mx-auto max-w-xl px-4 py-12">
    {result.error.status === 403
      ? <EmptyState icon={Compass} title="Activa las recomendaciones" actions={<Button as={Link} to="/perfil">Configurar recomendaciones en mi perfil</Button>}>Confirma tu perfil y activa el consentimiento desde Perfil → Editar → Privacidad. Cada persona decide sobre su propia cuenta.</EmptyState>
      : <ErrorState message="No pudimos cargar tus coincidencias." onRetry={result.reload} />}
  </div>
  if (!result.data.length) return <div className="mx-auto max-w-xl px-4 py-16">
    <EmptyState icon={Compass} title="Aún no hay coincidencias" actions={<Button as={Link} to="/inicio">Ir al inicio</Button>}>
      Aparecerán proyectos cuando existan hechos confirmados y elegibles.
    </EmptyState>
  </div>

  const rec = result.data[Math.min(index, result.data.length - 1)]
  return <div className="relative mx-auto flex max-w-xl flex-col items-center px-4 py-8 sm:py-12">
    <p className="text-label font-semibold tracking-[0.18em] text-primary uppercase">Coincidencia</p>
    <h1 className="mt-2 text-center text-h1 font-bold">Proyectos para ti</h1>
    <LocalProcessing className="mt-3" />
    <Card className="mt-8 w-full p-6">
      <p className="text-xs font-semibold text-ink-2">{rec.eligibility === "needs_review" ? "Requiere revisión" : "Elegible"} · {rec.evidence_group === "insufficient_evidence" ? "Evidencia insuficiente" : "Evidencia confirmada"}</p>
      <h2 className="mt-3 text-h2 font-semibold">{rec.project?.titulo || `Proyecto ${rec.event_id}`}</h2>
      <p className="mt-2 text-sm text-ink-2">{rec.explanation.strengths[0] || rec.explanation.unknowns[0] || "Revisa los requisitos del proyecto."}</p>
      {rec.explanation.gaps.length > 0 && <p className="mt-2 text-sm text-warn-ink">{rec.explanation.gaps[0]}</p>}
      <Button as={Link} to={`/proyectos/${rec.event_id}`} className="mt-5">Ver proyecto</Button>
    </Card>
    <div className="mt-6 flex w-full items-center justify-between">
      <Button variant="ghost" onClick={() => setIndex((i) => i - 1)} disabled={index === 0}><ArrowLeft className="size-4" /> Anterior</Button>
      <span className="text-sm text-ink-2">{index + 1} de {result.data.length}</span>
      <Button variant="ghost" onClick={() => setIndex((i) => i + 1)} disabled={index >= result.data.length - 1}>Siguiente <ArrowRight className="size-4" /></Button>
    </div>
  </div>
}
