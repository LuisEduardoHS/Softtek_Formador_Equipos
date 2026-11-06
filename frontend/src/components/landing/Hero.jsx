import { Link } from "react-router-dom"
import { ArrowRight } from "lucide-react"
import Button from "../ui/Button"
import { LocalProcessing } from "../ui/AIBadge"
import RecommendationCard from "../recommendation/RecommendationCard"
import { mockMatch } from "../../data/mockProfiles"

export default function Hero({ onGetStarted }) {
  return (
    <section className="relative isolate overflow-hidden">
      {/* Manchas de color animadas al fondo */}
      <div aria-hidden="true" className="pointer-events-none absolute inset-x-0 -inset-y-8 -z-10">
        <span className="absolute -top-24 -left-16 size-80 animate-blob rounded-full bg-accent/25 blur-3xl will-change-transform" />
        <span className="absolute top-20 -right-24 size-96 animate-blob rounded-full bg-accent-2/20 blur-3xl will-change-transform [animation-delay:-5s]" />
        <span className="absolute -bottom-24 left-1/3 size-72 animate-blob rounded-full bg-primary/20 blur-3xl will-change-transform [animation-delay:-9s]" />
        <span className="absolute inset-0 bg-[radial-gradient(var(--line)_1px,transparent_1px)] bg-size-[22px_22px] mask-[radial-gradient(ellipse_at_center,black_30%,transparent_75%)]" />
      </div>

      <div className="mx-auto grid max-w-6xl items-center gap-12 px-4 pt-12 pb-20 sm:px-8 lg:grid-cols-[1.1fr_1fr] lg:pt-20">
        <div>
         
         
          <h1 className="animate-fade-up text-[2.25rem] leading-[1.1] font-extrabold tracking-tight text-ink [animation-delay:100ms] sm:text-[3.25rem]">
            Forma equipos donde cada quien aporta <span className="text-gradient">algo distinto</span>.
          </h1>
          <p className="mt-5 max-w-xl animate-fade-up text-lg text-ink-2 [animation-delay:200ms]">
            Cuéntanos qué sabes hacer y qué quieres aprender. Te recomendamos compañeros de cualquier carrera que complementan tus fortalezas y te
            explicamos por qué.
          </p>
          <div className="mt-8 flex animate-fade-up flex-wrap gap-3 [animation-delay:300ms]">
            <Button size="lg" onClick={onGetStarted} className="group">
              Crear mi perfil <ArrowRight aria-hidden="true" className="size-4 transition-transform duration-200 group-hover:translate-x-1" />
            </Button>
            <Button size="lg" variant="secondary" as={Link} to="/auth">
              Ya tengo cuenta
            </Button>
          </div>
          <LocalProcessing className="mt-6 animate-fade-in [animation-delay:450ms]" />
        </div>

        {/* Ejemplo visual de una recomendación */}
        <div className="group/ejemplo relative animate-scale-in [animation-delay:250ms]" role="img" aria-label="Ejemplo de recomendación: Ana Torres cubriría Diseño de interfaces">
          <div aria-hidden="true" className="absolute inset-6 -z-10 rounded-3xl bg-linear-to-br from-accent/35 via-accent-2/25 to-primary/35 blur-2xl" />
          <div className="pointer-events-none mx-auto max-w-sm animate-float select-none group-hover/ejemplo:[animation-play-state:paused]" aria-hidden="true">
            <RecommendationCard student={mockMatch.student} rol={mockMatch.rol} rec={mockMatch.rec} />
          </div>
         
        </div>
      </div>
    </section>
  )
}
