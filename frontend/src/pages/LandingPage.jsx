import { useNavigate } from "react-router-dom"
import { ArrowRight, Check, Compass, Cpu, Lightbulb, ListChecks, PenLine, Puzzle, ServerCog, ShieldCheck, Sprout, UsersRound, X } from "lucide-react"
import Navbar from "../components/layout/Navbar"
import Hero from "../components/landing/Hero"
import SkillShowcase from "../components/landing/SkillShowcase"
import Button from "../components/ui/Button"
import Card from "../components/ui/Card"
import Avatar from "../components/ui/Avatar"
import Reveal from "../components/ui/Reveal"
import SkillChip from "../components/ui/SkillChip"
import { Logo } from "../components/layout/AppLayout"
import { mockProfiles } from "../data/mockProfiles"

const PASOS = [
  { Icon: PenLine, title: "Describe tus habilidades", text: "Escribe con tus palabras en qué eres bueno, qué quieres reforzar y cuándo puedes reunirte." },
  { Icon: Cpu, title: "La IA organiza tu perfil", text: "Convierte tu texto en un perfil claro. Tú lo revisas y corriges antes de guardarlo." },
  { Icon: Compass, title: "Recibe recomendaciones", text: "Te sugerimos personas y proyectos que complementan lo que sabes, con el porqué." },
  { Icon: UsersRound, title: "Forma tu equipo", text: "Invita, acepta y ve qué roles ya están cubiertos y cuáles faltan." },
]

// Promesas verificables del producto (no cifras inventadas)
const PILARES = [
  { Icon: ListChecks, value: "4 pasos", text: "para pasar de una idea a un equipo completo" },
  { Icon: ShieldCheck, value: "Tú confirmas", text: "la IA sugiere; nada se guarda sin tu revisión" },
  { Icon: ServerCog, value: "IA propia", text: "tu perfil se analiza en el servidor de la aplicación" },
]

const PERFILES = [
  {
    Icon: Lightbulb,
    title: "Tienes una idea",
    text: "Publica tu proyecto, define los roles que te faltan y recibe sugerencias de quién puede cubrirlos.",
  },
  {
    Icon: Puzzle,
    title: "Sabes hacer algo",
    text: "Describe tus habilidades y descubre proyectos donde lo que sabes es justo lo que el equipo necesita.",
  },
  {
    Icon: Sprout,
    title: "Quieres aprender",
    text: "Indica qué te gustaría reforzar y súmate a equipos donde aprendas junto a estudiantes de otras carreras.",
  },
]

function HowItWorks() {
  return (
    <section id="como-funciona" className="scroll-mt-20 border-y border-line bg-surface py-20">
      <div className="mx-auto max-w-6xl px-4 sm:px-8">
        <Reveal>
          <h2 className="text-center text-h1 font-bold">Cómo funciona</h2>
          <p className="mx-auto mt-2 max-w-xl text-center text-ink-2">Cuatro pasos, y la IA trabaja en segundo plano por ti.</p>
        </Reveal>
        <ol className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {PASOS.map(({ Icon, title, text }, i) => (
            <Reveal
              as="li"
              key={title}
              delay={i * 120}
              className="group relative rounded-2xl border border-line bg-canvas p-6 hover:-translate-y-1.5 hover:border-primary/40 hover:shadow-pop hover:shadow-primary/15"
            >
              <span className="absolute top-6 right-6 text-2xl font-extrabold text-ink-2/20 transition-colors duration-300 group-hover:text-primary/40" aria-hidden="true">
                0{i + 1}
              </span>
              <span className="grid size-11 place-items-center rounded-xl bg-linear-to-br from-primary to-accent text-white shadow-md shadow-primary/30 transition-transform duration-300 group-hover:scale-110 group-hover:-rotate-6">
                <Icon aria-hidden="true" className="size-5" />
              </span>
              <h3 className="mt-5 text-h3 font-semibold">
                <span className="sr-only">Paso {i + 1}: </span>
                {title}
              </h3>
              <p className="mt-1 text-sm text-ink-2">{text}</p>
            </Reveal>
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
      <Reveal className="mb-10 max-w-2xl">
        <h2 className="text-h1 font-bold">No juntamos gente parecida</h2>
        <p className="mt-2 text-ink-2">
          Un buen equipo no es el que tiene a los cuatro mejores programadores, sino el que cubre todo lo que el proyecto necesita.
        </p>
      </Reveal>
      <div className="grid gap-4 md:grid-cols-2">
        <Reveal from="left">
        <Card className="h-full p-6">
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
        </Reveal>
        <Reveal from="right" delay={150}>
        <Card className="h-full border-success-line p-6 shadow-pop ring-1 ring-success/20 transition-transform duration-300 hover:scale-[1.02]">
          <p className="mb-1 flex items-center gap-2 text-sm font-semibold text-success-ink">
            <Check aria-hidden="true" className="size-4" strokeWidth={3} /> Equipo complementario
          </p>
          <p className="mb-5 text-sm text-ink-2">Cada integrante aporta algo distinto. Todos los roles quedan cubiertos.</p>
          <ul className="space-y-2">
            {complementario.map(([n, h], i) => (
              <li key={n} className="flex animate-fade-up items-center gap-3" style={{ animationDelay: `${300 + i * 120}ms` }}>
                <Avatar name={n} size="sm" />
                <SkillChip variant="match">{h}</SkillChip>
              </li>
            ))}
          </ul>
          <p className="mt-5 text-sm font-semibold text-success-ink">4 de 4 roles cubiertos</p>
        </Card>
        </Reveal>
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

        <section aria-label="Lo que garantiza Complementa" className="bg-linear-to-br from-primary to-primary-hover py-16 text-white">
          <dl className="mx-auto grid max-w-5xl gap-10 px-4 text-center sm:grid-cols-3 sm:px-8">
            {PILARES.map(({ Icon, value, text }, i) => (
              <Reveal key={value} from="zoom" delay={i * 150} className="flex flex-col items-center">
                <span className="mb-3 grid size-12 place-items-center rounded-2xl bg-white/15 ring-1 ring-white/25">
                  <Icon aria-hidden="true" className="size-6" />
                </span>
                <dt className="text-[2rem] leading-tight font-extrabold tracking-tight">{value}</dt>
                <dd className="mt-1 max-w-56 text-sm text-white">{text}</dd>
              </Reveal>
            ))}
          </dl>
        </section>

        <section id="para-quien" className="mx-auto max-w-6xl scroll-mt-20 px-4 py-20 sm:px-8">
          <Reveal className="max-w-2xl">
            <h2 className="text-h1 font-bold">¿Para quién es Complementa?</h2>
            <p className="mt-2 text-ink-2">Llegues con una idea, con una habilidad o con ganas de aprender, hay un equipo que te necesita.</p>
          </Reveal>
          <ul className="mt-10 grid gap-4 md:grid-cols-3">
            {PERFILES.map(({ Icon, title, text }, i) => (
              <Reveal as="li" key={title} delay={i * 120}>
                <Card interactive className="group flex h-full flex-col p-6">
                  <span className="grid size-11 place-items-center rounded-xl bg-primary-soft text-primary transition-colors duration-300 group-hover:bg-primary group-hover:text-white">
                    <Icon aria-hidden="true" className="size-5" />
                  </span>
                  <h3 className="mt-5 text-h3 font-semibold text-ink">{title}</h3>
                  <p className="mt-1 text-sm text-ink-2">{text}</p>
                </Card>
              </Reveal>
            ))}
          </ul>
        </section>

        <section className="mx-auto max-w-6xl px-4 pb-20 sm:px-8">
          <Reveal from="zoom" className="flex flex-col items-center rounded-3xl border border-primary/20 bg-primary-soft px-6 py-14 text-center">
            <h2 className="text-h1 font-bold">Tu próximo equipo te está esperando</h2>
            <p className="mt-2 max-w-md text-ink-2">Solo necesitas tu correo institucional. Crear tu perfil toma unos 3 minutos.</p>
            <Button size="lg" className="group mt-8" onClick={getStarted}>
              Crear mi perfil <ArrowRight aria-hidden="true" className="size-4 transition-transform duration-200 group-hover:translate-x-1" />
            </Button>
          </Reveal>
        </section>
      </main>

      <footer className="border-t border-line">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-4 py-8 text-sm text-ink-2 sm:flex-row sm:px-8">
          <Logo to="/" />
          <p>Proyecto universitario · Los datos se procesan en el servidor configurado para esta aplicación.</p>
        </div>
      </footer>
    </div>
  )
}
