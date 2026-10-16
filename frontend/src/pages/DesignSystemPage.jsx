import { useState } from "react"
import { Bell, FolderKanban, Home, Moon, Plus, Sun, Trash2, UserRound, Users } from "lucide-react"
import Button from "../components/ui/Button"
import Card from "../components/ui/Card"
import SkillChip from "../components/ui/SkillChip"
import Avatar, { AvatarGroup } from "../components/ui/Avatar"
import AIBadge, { AIPanel, LocalProcessing } from "../components/ui/AIBadge"
import RecommendationCard from "../components/recommendation/RecommendationCard"
import { projects, recommendations, studentById } from "../data/mockData"

const PALETTE = [
  { name: "Fondo", token: "canvas", hex: "#F8FAFC", use: "60 % · fondo general", cls: "bg-canvas" },
  { name: "Tinta", token: "ink", hex: "#0F172A", use: "30 % · estructura y texto", cls: "bg-ink" },
  { name: "Acento", token: "primary", hex: "#2563EB", use: "10 % · CTA, enlaces", cls: "bg-primary" },
  { name: "Cubierto", token: "success", hex: "#10B981 / #047857", use: "Coincide, aceptado", cls: "bg-success" },
  { name: "Pendiente", token: "warn", hex: "#F59E0B / #B45309", use: "Falta cubrir", cls: "bg-warn" },
  { name: "Error", token: "danger", hex: "#DC2626", use: "Errores, destructivo", cls: "bg-danger" },
  { name: "IA", token: "ai-soft", hex: "#EFF6FF · #BFDBFE · #1D4ED8", use: "Bloques generados por IA", cls: "bg-ai-soft border border-ai-line" },
  { name: "Superficie", token: "surface", hex: "#FFFFFF · borde #E2E8F0", use: "Tarjetas", cls: "bg-surface border border-line" },
  { name: "Secundario", token: "ink-2", hex: "#64748B", use: "Texto secundario", cls: "bg-ink-2" },
]

const TYPE = [
  { cls: "text-display font-extrabold", label: "Display · 40/46 · ExtraBold", sample: "Equipos que se complementan" },
  { cls: "text-h1 font-bold", label: "H1 · 28/36 · Bold", sample: "Recomendado para ti" },
  { cls: "text-h2 font-semibold", label: "H2 · 20/28 · Semibold", sample: "Mapa de cobertura de roles" },
  { cls: "text-h3 font-semibold", label: "H3 · 16/24 · Semibold", sample: "Ana Torres" },
  { cls: "text-body", label: "Cuerpo · 15/24 · Regular", sample: "Cada integrante aporta algo distinto al proyecto." },
  { cls: "text-sm text-ink-2", label: "Secundario · 14/20", sample: "Diseño Gráfico · 5.º semestre" },
  { cls: "text-label font-semibold uppercase tracking-wide text-ink-2", label: "Etiqueta · 12/16 · Semibold", sample: "Aporta" },
]

const NAV = [
  { icon: Home, label: "Inicio", children: ["Recomendado para ti", "Invitaciones pendientes", "Resumen de equipos", "Búsqueda con filtros"] },
  { icon: FolderKanban, label: "Proyectos", children: ["Explorar", "Mis proyectos", "Detalle de proyecto", "Crear proyecto (2 pasos)"] },
  { icon: Users, label: "Mis equipos", children: ["Vista de equipo", "Invitaciones enviadas / recibidas"] },
  { icon: Bell, label: "Notificaciones", badge: 3, children: ["Oportunidades de la IA", "Invitaciones", "Actualizaciones de equipo"] },
  { icon: UserRound, label: "Perfil", children: ["Vista pública", "Edición", "Privacidad"] },
]

function Section({ title, desc, children }) {
  return (
    <section className="animate-fade-up space-y-4">
      <div>
        <h2 className="text-h2 font-semibold">{title}</h2>
        {desc && <p className="text-sm text-ink-2">{desc}</p>}
      </div>
      {children}
    </section>
  )
}

export default function DesignSystemPage() {
  const [dark, setDark] = useState(() => document.documentElement.classList.contains("dark"))
  const toggleDark = () => {
    document.documentElement.classList.toggle("dark")
    setDark((d) => !d)
  }

  const p1 = projects[0]
  const cards = recommendations.slice(0, 2).map((rec) => ({
    rec,
    student: studentById(rec.studentId),
    rol: p1.roles.find((r) => r.id === rec.rolId),
  }))

  return (
    <div className="mx-auto max-w-6xl space-y-14 px-4 py-10 sm:px-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-label font-semibold tracking-wide text-primary uppercase">Complementa · v0.1</p>
          <h1 className="text-h1 font-bold sm:text-display sm:font-extrabold">Sistema de diseño</h1>
          <p className="mt-1 max-w-xl text-ink-2">
            Base visual para formar equipos complementarios: limpia, clara y con la IA presente de forma discreta.
          </p>
        </div>
        <Button variant="secondary" onClick={toggleDark} aria-pressed={dark}>
          {dark ? <Sun aria-hidden="true" className="size-4" /> : <Moon aria-hidden="true" className="size-4" />}
          {dark ? "Modo claro" : "Modo oscuro"}
        </Button>
      </header>

      <Section title="Paleta" desc="Regla 60-30-10. El azul se reserva para acciones clave; verde y ámbar comunican cobertura.">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {PALETTE.map((c) => (
            <Card key={c.token} className="overflow-hidden">
              <div className={`h-16 ${c.cls}`} />
              <div className="space-y-0.5 p-3">
                <p className="text-sm font-semibold">{c.name}</p>
                <p className="font-mono text-[11px] text-ink-2">{c.hex}</p>
                <p className="text-xs text-ink-2">{c.use}</p>
              </div>
            </Card>
          ))}
        </div>
      </Section>

      <Section title="Tipografía" desc="Plus Jakarta Sans. Escala corta para mantener jerarquía clara.">
        <Card className="divide-y divide-line">
          {TYPE.map((t) => (
            <div key={t.label} className="flex flex-col gap-1 p-4 sm:flex-row sm:items-baseline sm:gap-6">
              <span className="w-56 shrink-0 font-mono text-xs text-ink-2">{t.label}</span>
              <span className={t.cls}>{t.sample}</span>
            </div>
          ))}
        </Card>
      </Section>

      <Section title="Espaciado, radios y sombras" desc="Múltiplos de 4/8 px · 8 px en controles · 12–16 px en tarjetas.">
        <div className="grid gap-4 md:grid-cols-3">
          <Card className="p-5">
            <p className="mb-3 text-sm font-semibold">Espaciado</p>
            <div className="space-y-2">
              {[4, 8, 12, 16, 24, 32, 48].map((s) => (
                <div key={s} className="flex items-center gap-3 text-xs text-ink-2">
                  <span className="w-8 font-mono">{s}</span>
                  <span className="h-2 rounded-sm bg-primary/70" style={{ width: s * 2 }} />
                </div>
              ))}
            </div>
          </Card>
          <Card className="p-5">
            <p className="mb-3 text-sm font-semibold">Radios</p>
            <div className="flex items-end gap-4">
              {[
                ["8 px", "rounded-lg"],
                ["12 px", "rounded-xl"],
                ["16 px", "rounded-2xl"],
                ["Píldora", "rounded-full"],
              ].map(([l, r]) => (
                <div key={l} className="text-center">
                  <div className={`size-14 border-2 border-ink/20 bg-surface-2 ${r}`} />
                  <p className="mt-1 text-xs text-ink-2">{l}</p>
                </div>
              ))}
            </div>
          </Card>
          <Card className="p-5">
            <p className="mb-3 text-sm font-semibold">Sombras</p>
            <div className="flex gap-4">
              <div className="grid h-20 flex-1 place-items-center rounded-xl bg-surface text-xs text-ink-2 shadow-card">Nivel 1 · tarjeta</div>
              <div className="grid h-20 flex-1 place-items-center rounded-xl bg-surface text-xs text-ink-2 shadow-pop">Nivel 2 · flotante</div>
            </div>
          </Card>
        </div>
      </Section>

      <Section title="Botones" desc="Altura mínima de 44 px. Un solo botón primario por zona.">
        <Card className="space-y-4 p-5">
          <div className="flex flex-wrap items-center gap-3">
            <Button>
              <Plus aria-hidden="true" className="size-4" /> Crear proyecto
            </Button>
            <Button variant="secondary">Ver perfil</Button>
            <Button variant="ghost">Descartar</Button>
            <Button variant="danger">
              <Trash2 aria-hidden="true" className="size-4" /> Eliminar proyecto
            </Button>
            <Button disabled>Deshabilitado</Button>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Button size="sm">Pequeño</Button>
            <Button size="md">Mediano</Button>
            <Button size="lg">Grande</Button>
          </div>
        </Card>
      </Section>

      <Section title="SkillChips" desc="Cada variante lleva ícono o texto, no solo color.">
        <Card className="grid gap-4 p-5 sm:grid-cols-2">
          {[
            ["neutral", "Neutra · habilidad general", "Redacción"],
            ["match", "Coincidente · cubre una necesidad", "Diseño de interfaces"],
            ["needed", "Necesaria · nadie la cubre aún", "Programación backend"],
            ["private", "Privada · solo la ve la IA", "Hablar en público"],
          ].map(([v, d, s]) => (
            <div key={v} className="flex items-center justify-between gap-3">
              <span className="text-sm text-ink-2">{d}</span>
              <SkillChip variant={v}>{s}</SkillChip>
            </div>
          ))}
          <div className="flex items-center justify-between gap-3">
            <span className="text-sm text-ink-2">Con nivel y editable</span>
            <SkillChip level="avanzado" onRemove={() => {}}>
              Python
            </SkillChip>
          </div>
        </Card>
      </Section>

      <Section title="Elementos de IA" desc="Un único estilo azul tenue para todo lo generado por IA: reconocible, nunca llamativo.">
        <div className="grid gap-4 md:grid-cols-2">
          <Card className="space-y-3 p-5">
            <div className="flex flex-wrap items-center gap-3">
              <AIBadge />
              <AIBadge label="Roles propuestos por IA" />
            </div>
            <LocalProcessing />
            <div className="flex items-center gap-3">
              <AvatarGroup names={["Ana Torres", "Diego Ramírez", "Camila Ortega", "Sofía Hernández", "Luis Medina"]} />
              <Avatar name="Mariana López" size="lg" />
            </div>
          </Card>
          <AIPanel title="A tu equipo le falta alguien de gestión de proyectos" className="self-start">
            Sofía Hernández y otras 2 personas podrían cubrirlo y coinciden con sus horarios.{" "}
            <a href="#" className="font-semibold text-primary underline-offset-2 hover:underline">
              Ver sugerencias
            </a>
          </AIPanel>
        </div>
      </Section>

      <Section title="Tarjeta de recomendación" desc="Compacta para listas y carruseles; expandida para el detalle del proyecto.">
        <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,380px)_1fr]">
          <RecommendationCard {...cards[0]} variant="compact" />
          <RecommendationCard {...cards[1]} project={p1} variant="expanded" />
        </div>
      </Section>

      <Section title="Mapa de navegación" desc="Barra lateral en escritorio, barra inferior en móvil. «Crear proyecto» siempre accesible.">
        <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
          <Card className="p-5">
            <ol className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <li className="rounded-xl border border-dashed border-line p-4 text-sm sm:col-span-2 lg:col-span-3">
                <span className="font-semibold">Público:</span>{" "}
                <span className="text-ink-2">Landing → Iniciar sesión (correo institucional) → Onboarding 3 pasos → Inicio</span>
              </li>
              {NAV.map(({ icon: Icon, label, badge, children }) => (
                <li key={label} className="rounded-xl bg-surface-2 p-4">
                  <p className="mb-2 flex items-center gap-2 font-semibold">
                    <Icon aria-hidden="true" className="size-4 text-ink-2" />
                    {label}
                    {badge && <span className="rounded-full bg-primary px-1.5 text-[11px] font-bold text-white">{badge}</span>}
                  </p>
                  <ul className="space-y-1 text-sm text-ink-2">
                    {children.map((c) => (
                      <li key={c}>· {c}</li>
                    ))}
                  </ul>
                </li>
              ))}
              <li className="rounded-xl border border-primary/30 bg-primary-soft p-4">
                <p className="flex items-center gap-2 font-semibold text-primary">
                  <Plus aria-hidden="true" className="size-4" /> Crear proyecto
                </p>
                <p className="mt-1 text-sm text-ink-2">Acción global: botón en la barra lateral y botón central en móvil.</p>
              </li>
            </ol>
          </Card>

          {/* Vista previa barra inferior móvil */}
          <div className="mx-auto w-full max-w-[320px]">
            <div className="overflow-hidden rounded-[28px] border-4 border-ink/80 bg-canvas shadow-pop">
              <div className="h-56 space-y-2 p-4">
                <div className="h-4 w-2/3 rounded bg-surface-2" />
                <div className="h-20 rounded-xl border border-line bg-surface" />
                <div className="h-20 rounded-xl border border-line bg-surface" />
              </div>
              <nav aria-label="Vista previa móvil" className="grid grid-cols-5 border-t border-line bg-surface px-1 pb-2 pt-1">
                {[
                  [Home, "Inicio", true],
                  [FolderKanban, "Proyectos"],
                  [Plus, "Crear"],
                  [Users, "Equipos"],
                  [Bell, "Avisos"],
                ].map(([Icon, l, active]) =>
                  l === "Crear" ? (
                    <span key={l} className="-mt-5 grid place-items-center">
                      <span className="grid size-12 place-items-center rounded-full bg-primary text-white shadow-pop">
                        <Icon aria-hidden="true" className="size-5" />
                      </span>
                    </span>
                  ) : (
                    <span key={l} className={`flex flex-col items-center gap-0.5 py-1 text-[10px] font-medium ${active ? "text-primary" : "text-ink-2"}`}>
                      <Icon aria-hidden="true" className="size-5" />
                      {l}
                    </span>
                  ),
                )}
              </nav>
            </div>
            <p className="mt-2 text-center text-xs text-ink-2">Perfil se abre desde el avatar del encabezado móvil.</p>
          </div>
        </div>
      </Section>
    </div>
  )
}
