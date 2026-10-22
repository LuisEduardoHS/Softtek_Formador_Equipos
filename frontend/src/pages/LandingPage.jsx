import { useNavigate } from "react-router-dom"
import { ArrowRight, Check, Compass, Cpu, PenLine, Quote, UsersRound, X } from "lucide-react"
import Navbar from "../components/layout/Navbar"
import Hero from "../components/landing/Hero"
import SkillShowcase from "../components/landing/SkillShowcase"
import Button from "../components/ui/Button"
import Card from "../components/ui/Card"
import Avatar from "../components/ui/Avatar"
import SkillChip from "../components/ui/SkillChip"
import { Logo } from "../components/layout/AppLayout"
import { mockProfiles } from "../data/mockProfiles"
import { campusStats, testimonials } from "../data/mockData"

const PASOS = [
  { Icon: PenLine, title: "Describe tus habilidades", text: "Escribe con tus palabras en qué eres bueno, qué quieres reforzar y cuándo puedes reunirte." },
  { Icon: Cpu, title: "La IA organiza tu perfil", text: "Convierte tu texto en un perfil claro. Tú lo revisas y corriges antes de guardarlo." },
  { Icon: Compass, title: "Recibe recomendaciones", text: "Te sugerimos personas y proyectos que complementan lo que sabes, con el porqué." },
  { Icon: UsersRound, title: "Forma tu equipo", text: "Invita, acepta y ve qué roles ya están cubiertos y cuáles faltan." },
]

const NUM = new Intl.NumberFormat("es-MX")

function HowItWorks() {
  return (
    <section id="como-funciona" className="scroll-mt-20 border-y border-line bg-surface py-20">
      <div className="mx-auto max-w-6xl px-4 sm:px-8">
        <h2 className="text-center text-h1 font-bold">Cómo funciona</h2>
        <p className="mx-auto mt-2 max-w-xl text-center text-ink-2">Cuatro pasos, y la IA trabaja en segundo plano por ti.</p>
        <ol className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {PASOS.map(({ Icon, title, text }, i) => (
            <li key={title} className="relative rounded-2xl border border-line bg-canvas p-6">
              <span className="absolute top-6 right-6 text-sm font-bold text-ink-2/50" aria-hidden="true">
                0{i + 1}
              </span>
              <span className="grid size-11 place-items-center rounded-xl bg-ink text-canvas">
                <Icon aria-hidden="true" className="size-5" />
              </span>
              <h3 className="mt-5 text-h3 font-semibold">
                <span className="sr-only">Paso {i + 1}: </span>
                {title}
              </h3>
              <p className="mt-1 text-sm text-ink-2">{text}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  )
}

function Comparison() {
  const complementario = [
    ["Mariana", "Análisis de datos"],
    ["Ana", "Diseño de interfaces"],
    ["Diego", "Backend"],
    ["Camila", "Investigación de usuarios"],
  ]
  return (
    <section id="por-que" className="mx-auto max-w-6xl scroll-mt-20 px-4 py-20 sm:px-8">
      <div className="mb-10 max-w-2xl">
        <h2 className="text-h1 font-bold">No juntamos gente parecida</h2>
        <p className="mt-2 text-ink-2">
          Un buen equipo no es el que tiene a los cuatro mejores programadores, sino el que cubre todo lo que el proyecto necesita.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Card className="p-6">
          <p className="mb-1 flex items-center gap-2 text-sm font-semibold text-ink-2">
            <X aria-hidden="true" className="size-4" /> Equipo de gente parecida
          </p>
          <p className="mb-5 text-sm text-ink-2">Todos saben lo mismo; nadie cubre el diseño ni la investigación.</p>
          <ul className="space-y-2">
            {[1, 2, 3, 4].map((i) => (
              <li key={i} className="flex items-center gap-3">
                <span className="size-8 rounded-full bg-surface-2" aria-hidden="true" />
                <SkillChip>Python</SkillChip>
              </li>
            ))}
          </ul>
          <p className="mt-5 flex flex-wrap gap-1.5">
            <SkillChip variant="needed">Diseño</SkillChip>
            <SkillChip variant="needed">Backend</SkillChip>
            <SkillChip variant="needed">Investigación</SkillChip>
          </p>
        </Card>
        <Card className="border-success-line p-6 shadow-pop">
          <p className="mb-1 flex items-center gap-2 text-sm font-semibold text-success-ink">
            <Check aria-hidden="true" className="size-4" strokeWidth={3} /> Equipo complementario
          </p>
          <p className="mb-5 text-sm text-ink-2">Cada integrante aporta algo distinto. Todos los roles quedan cubiertos.</p>
          <ul className="space-y-2">
            {complementario.map(([n, h]) => (
              <li key={n} className="flex items-center gap-3">
                <Avatar name={n} size="sm" />
                <SkillChip variant="match">{h}</SkillChip>
              </li>
            ))}
          </ul>
          <p className="mt-5 text-sm font-semibold text-success-ink">4 de 4 roles cubiertos</p>
        </Card>
      </div>
    </section>
  )
}

export default function LandingPage() {
  const navigate = useNavigate()
  const getStarted = () => navigate("/registro")

  return (
    <div className="min-h-dvh bg-canvas">
      <Navbar onGetStarted={getStarted} />
      <main>
        <Hero onGetStarted={getStarted} />
        <HowItWorks />
        <div className="pt-20">
          <SkillShowcase profiles={mockProfiles} />
        </div>
        <Comparison />

        <section aria-label="Cifras del campus" className="bg-ink py-16 text-canvas">
          <dl className="mx-auto grid max-w-5xl gap-10 px-4 text-center sm:grid-cols-3 sm:px-8">
            {[
              [campusStats.estudiantes, "estudiantes con perfil"],
              [campusStats.equipos, "equipos formados"],
              [campusStats.carreras, "carreras participantes"],
            ].map(([n, l]) => (
              <div key={l} className="flex flex-col-reverse">
                <dt className="text-sm text-canvas/70">{l}</dt>
                <dd className="text-[2.75rem] font-extrabold tracking-tight">{NUM.format(n)}</dd>
              </div>
            ))}
          </dl>
        </section>

        <section id="testimonios" className="mx-auto max-w-6xl scroll-mt-20 px-4 py-20 sm:px-8">
          <h2 className="text-h1 font-bold">Lo que dicen otros estudiantes</h2>
          <ul className="mt-10 grid gap-4 md:grid-cols-3">
            {testimonials.map((t) => (
              <li key={t.nombre}>
                <Card as="figure" className="flex h-full flex-col p-6">
                  <Quote aria-hidden="true" className="size-6 text-primary/40" />
                  <blockquote className="mt-3 flex-1 text-ink">{t.texto}</blockquote>
                  <figcaption className="mt-6 flex items-center gap-3">
                    <Avatar name={t.nombre} size="sm" />
                    <span>
                      <span className="block text-sm font-semibold">{t.nombre}</span>
                      <span className="block text-xs text-ink-2">{t.carrera}</span>
                    </span>
                  </figcaption>
                </Card>
              </li>
            ))}
          </ul>
        </section>

        <section className="mx-auto max-w-6xl px-4 pb-20 sm:px-8">
          <div className="flex flex-col items-center rounded-3xl border border-line bg-surface px-6 py-14 text-center shadow-card">
            <h2 className="text-h1 font-bold">Tu próximo equipo te está esperando</h2>
            <p className="mt-2 max-w-md text-ink-2">Solo necesitas tu correo institucional. Crear tu perfil toma unos 3 minutos.</p>
            <Button size="lg" className="mt-8" onClick={getStarted}>
              Crear mi perfil <ArrowRight aria-hidden="true" className="size-4" />
            </Button>
          </div>
        </section>
      </main>

      <footer className="border-t border-line">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-4 py-8 text-sm text-ink-2 sm:flex-row sm:px-8">
          <Logo to="/" />
          <p>Proyecto universitario · Los datos se procesan en servidores de la universidad.</p>
        </div>
      </footer>
    </div>
  )
}
