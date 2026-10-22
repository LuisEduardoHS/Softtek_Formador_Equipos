import { Link } from "react-router-dom"
import { ArrowRight } from "lucide-react"
import Button from "../ui/Button"
import { LocalProcessing } from "../ui/AIBadge"
import RecommendationCard from "../recommendation/RecommendationCard"
import { mockMatch } from "../../data/mockProfiles"

export default function Hero({ onGetStarted }) {
  return (
    <section className="mx-auto grid max-w-6xl items-center gap-12 px-4 pt-12 pb-20 sm:px-8 lg:grid-cols-[1.1fr_1fr] lg:pt-20">
      <div className="animate-fade-up">
        <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-line bg-surface px-3 py-1 text-xs font-semibold text-ink-2">
          <span className="size-1.5 rounded-full bg-success" aria-hidden="true" /> Encuentra a tu equipo ideal
        </p>
        <h1 className="text-[2.25rem] leading-[1.1] font-extrabold tracking-tight text-ink sm:text-[3.25rem]">
          Forma equipos donde cada quien aporta <span className="text-primary">algo distinto</span>.
        </h1>
        <p className="mt-5 max-w-xl text-lg text-ink-2">
          Cuéntanos qué sabes hacer y qué quieres aprender. Te recomendamos compañeros de cualquier carrera que complementan tus fortalezas y te
          explicamos por qué.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Button size="lg" onClick={onGetStarted}>
            Crear mi perfil <ArrowRight aria-hidden="true" className="size-4" />
          </Button>
          <Button size="lg" variant="secondary" as={Link} to="/auth">
            Ya tengo cuenta
          </Button>
        </div>
        <LocalProcessing className="mt-6" />
      </div>

      {/* Ejemplo visual de una recomendación */}
      <div className="relative animate-fade-up [animation-delay:150ms]" role="img" aria-label="Ejemplo de recomendación: Ana Torres cubriría Diseño de interfaces">
        <div className="pointer-events-none mx-auto max-w-sm rotate-[0.6deg] select-none" aria-hidden="true">
          <RecommendationCard student={mockMatch.student} rol={mockMatch.rol} rec={mockMatch.rec} />
        </div>
      </div>
    </section>
  )
}
