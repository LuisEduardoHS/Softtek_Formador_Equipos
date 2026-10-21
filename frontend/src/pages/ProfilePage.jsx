import { useId, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { ArrowLeft, Eye, Lock, PauseCircle, Pencil, RefreshCw, Send, UserX } from "lucide-react"
import Button from "../components/ui/Button"
import Card from "../components/ui/Card"
import TagEditor from "../components/ui/TagEditor"
import AvailabilityGrid from "../components/ui/AvailabilityGrid"
import { EmptyState } from "../components/ui/Feedback"
import { Field, LevelPicker, Segmented, Switch } from "../components/ui/Controls"
import { useToast } from "../components/ui/Toast"
import PublicProfile from "../components/profile/PublicProfile"
import InviteModal from "../components/invite/InviteModal"
import { currentUser, pendingInviteIds, projects, studentById } from "../data/mockData"
import { coverage } from "../lib/projects"
import { inputCls } from "../lib/ui"

/* ------------------------------ Edición ------------------------------ */

function Section({ title, desc, badge, children }) {
  return (
    <Card className="p-5 sm:p-6">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 className="text-h3 font-semibold">{title}</h2>
          {desc && <p className="text-sm text-ink-2">{desc}</p>}
        </div>
        {badge}
      </div>
      {children}
    </Card>
  )
}

// Campos que alimentan a la IA: si cambian, se recalculan las recomendaciones
const AI_FIELDS = ["fortalezas", "reforzar", "intereses", "disponibilidad"]

function EditProfile({ perfil, setPerfil, dirty, aiDirty, onSave, onDiscard }) {
  const ids = { c: useId(), s: useId(), g: useId(), e: useId() }
  const set = (k) => (v) => setPerfil((p) => ({ ...p, [k]: v }))
  const setVis = (k) => (v) => setPerfil((p) => ({ ...p, visibilidad: { ...p.visibilidad, [k]: v } }))

  const setFortalezas = (names) =>
    setPerfil((p) => ({
      ...p,
      fortalezas: names.map((n, i) => ({
        nombre: n,
        nivel: p.fortalezas.find((f) => f.nombre === n)?.nivel ?? (names.length === p.fortalezas.length ? p.fortalezas[i].nivel : "intermedio"),
      })),
    }))

  return (
    <div className="space-y-4">
      {perfil.pausado && (
        <div className="flex animate-fade-up items-start gap-3 rounded-xl border border-warn-line bg-warn-soft p-4 text-sm">
          <PauseCircle aria-hidden="true" className="mt-0.5 size-5 shrink-0 text-warn-ink" />
          <p>
            <span className="font-semibold">Tu perfil está en pausa.</span> No aparecerás en recomendaciones de otras personas, pero conservas tus
            equipos e invitaciones.
          </p>
        </div>
      )}

      {aiDirty && (
        <div role="status" className="flex animate-fade-up items-center gap-3 rounded-xl border border-ai-line bg-ai-soft p-4 text-sm text-ink">
          <RefreshCw aria-hidden="true" className="size-4 shrink-0 text-ai-ink" />
          Actualizaremos tus recomendaciones con estos cambios al guardar.
        </div>
      )}

      <Section title="Información básica">
        <div className="grid gap-4 sm:grid-cols-[1fr_140px]">
          <Field id={ids.c} label="Carrera">
            <input id={ids.c} value={perfil.carrera} onChange={(e) => set("carrera")(e.target.value)} className={inputCls()} />
          </Field>
          <Field id={ids.s} label="Semestre">
            <select id={ids.s} value={perfil.semestre} onChange={(e) => set("semestre")(Number(e.target.value))} className={`${inputCls()} cursor-pointer`}>
              {Array.from({ length: 12 }, (_, i) => i + 1).map((n) => (
                <option key={n} value={n}>
                  {n}.º
                </option>
              ))}
            </select>
          </Field>
        </div>
      </Section>

      <Section title="Fortalezas" desc="Pulsa una etiqueta para corregirla e indica tu nivel.">
        <TagEditor
          items={perfil.fortalezas.map((f) => f.nombre)}
          onChange={setFortalezas}
          layout="rows"
          placeholder="Agregar fortaleza"
          renderExtra={(name, idx) => (
            <LevelPicker
              name={name}
              value={perfil.fortalezas[idx]?.nivel}
              onChange={(n) => setPerfil((p) => ({ ...p, fortalezas: p.fortalezas.map((f, i) => (i === idx ? { ...f, nivel: n } : f)) }))}
            />
          )}
        />
      </Section>

      <Section
        title="Quiero reforzar"
        desc="La IA lo usa para encontrar quién te complementa."
        badge={
          <span className="inline-flex items-center gap-1 rounded-full border border-line px-2 py-0.5 text-xs font-medium text-ink-2">
            <Lock aria-hidden="true" className="size-3" /> {perfil.visibilidad.reforzar ? "Visible" : "Privado"}
          </span>
        }
      >
        <TagEditor items={perfil.reforzar} onChange={set("reforzar")} variant="private" placeholder="Agregar, p. ej. Hablar en público" />
      </Section>

      <Section title="Intereses">
        <TagEditor items={perfil.intereses} onChange={set("intereses")} placeholder="Agregar interés" />
      </Section>

      <Section title="Disponibilidad" desc="Toca los bloques en los que sueles estar libre.">
        <AvailabilityGrid value={perfil.disponibilidad} onChange={set("disponibilidad")} />
      </Section>

      <Section title="Contacto" desc="Solo lo verán los integrantes de tus equipos.">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field id={ids.e} label="Correo institucional" hint="Lo tomamos de tu cuenta universitaria.">
            <input id={ids.e} value={perfil.correo} readOnly className={`${inputCls()} bg-surface-2 text-ink-2`} />
          </Field>
          <Field id={ids.g} label="Enlace a grupo externo" optional hint="Por ejemplo, tu usuario de Discord o un enlace de WhatsApp.">
            <input
              id={ids.g}
              value={perfil.grupoExterno}
              onChange={(e) => set("grupoExterno")(e.target.value)}
              placeholder="https://…"
              className={inputCls()}
            />
          </Field>
        </div>
      </Section>

      <Section title="Privacidad" desc="Decide qué ven las demás personas. La IA siempre puede usar tu perfil para recomendarte, salvo que lo pauses.">
        <div className="divide-y divide-line">
          <Switch label="Mostrar mis fortalezas" checked={perfil.visibilidad.fortalezas} onChange={setVis("fortalezas")} />
          <Switch label="Mostrar mis intereses" checked={perfil.visibilidad.intereses} onChange={setVis("intereses")} />
          <Switch label="Mostrar mi disponibilidad" checked={perfil.visibilidad.disponibilidad} onChange={setVis("disponibilidad")} />
          <Switch
            label="Mostrar «Quiero reforzar»"
            description="Privado por defecto. Si lo muestras, otras personas podrán ofrecerte ayuda."
            checked={perfil.visibilidad.reforzar}
            onChange={setVis("reforzar")}
          />
          <Switch label="Compartir mi correo con mis equipos" checked={perfil.visibilidad.correo} onChange={setVis("correo")} />
          <Switch
            label="Pausar mi perfil"
            description="No aparecerás en recomendaciones mientras esté en pausa."
            checked={perfil.pausado}
            onChange={set("pausado")}
          />
        </div>
      </Section>

      {/* Barra de guardado: aparece solo con cambios */}
      {dirty && (
        <div className="fixed inset-x-0 bottom-[calc(3.5rem+env(safe-area-inset-bottom))] z-20 animate-fade-up border-t border-line bg-surface/95 backdrop-blur lg:bottom-0 lg:left-[260px]">
          <div className="mx-auto flex max-w-4xl items-center justify-between gap-3 px-4 py-3 sm:px-8">
            <p className="text-sm text-ink-2">Tienes cambios sin guardar</p>
            <div className="flex gap-2">
              <Button variant="ghost" onClick={onDiscard}>
                Descartar
              </Button>
              <Button onClick={onSave}>Guardar cambios</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

/* --------------------------- Mi perfil (/perfil) --------------------------- */

function MyProfile() {
  const toast = useToast()
  const [saved, setSaved] = useState(currentUser)
  const [perfil, setPerfil] = useState(currentUser)
  const [mode, setMode] = useState("editar")

  const dirty = JSON.stringify(perfil) !== JSON.stringify(saved)
  const aiDirty = AI_FIELDS.some((k) => JSON.stringify(perfil[k]) !== JSON.stringify(saved[k]))

  const save = () => {
    // TODO(backend): PUT /perfil/me
    setSaved(perfil)
    toast(aiDirty ? "Perfil guardado. Estamos actualizando tus recomendaciones." : "Perfil guardado")
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-6 pb-32 sm:px-8 sm:py-10">
      <header className="mb-6 flex animate-fade-up flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-h1 font-bold">Mi perfil</h1>
          <p className="mt-1 text-ink-2">Tú decides qué se muestra y qué usa la IA.</p>
        </div>
        <Segmented
          label="Modo de vista"
          value={mode}
          onChange={setMode}
          options={[
            [
              "editar",
              <span key="e" className="flex items-center gap-1.5">
                <Pencil aria-hidden="true" className="size-4" /> Editar
              </span>,
            ],
            [
              "publica",
              <span key="p" className="flex items-center gap-1.5">
                <Eye aria-hidden="true" className="size-4" /> Ver como otros me ven
              </span>,
            ],
          ]}
        />
      </header>

      <div key={mode} className="animate-fade-in">
        {mode === "editar" ? (
          <EditProfile perfil={perfil} setPerfil={setPerfil} dirty={dirty} aiDirty={aiDirty} onSave={save} onDiscard={() => setPerfil(saved)} />
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-ink-2">Así ven tu perfil las demás personas{dirty && " (incluye cambios sin guardar)"}.</p>
            <PublicProfile student={perfil} preview />
          </div>
        )}
      </div>
    </div>
  )
}

/* ------------------------ Perfil de otra persona ------------------------ */

function OtherProfile({ id }) {
  const navigate = useNavigate()
  const student = studentById(id)
  const [inviting, setInviting] = useState(false)
  // Proyecto propio con roles pendientes donde podría encajar
  const project = projects.find((p) => p.creadorId === currentUser.id && coverage(p).pendientes.length)
  const rol =
    project &&
    (coverage(project).pendientes.find((r) => r.habilidades.some((h) => student?.fortalezas.some((f) => f.nombre === h))) ?? coverage(project).pendientes[0])
  const [invited, setInvited] = useState(() => (project ? pendingInviteIds(project.id).has(id) : false))

  if (!student) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10 sm:px-8">
        <EmptyState icon={UserX} title="No encontramos este perfil" actions={<Button variant="secondary" onClick={() => navigate(-1)}>Volver</Button>}>
          Puede que la persona haya pausado o eliminado su perfil.
        </EmptyState>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-6 sm:px-8 sm:py-10">
      <button
        type="button"
        onClick={() => navigate(-1)}
        className="mb-4 inline-flex min-h-9 cursor-pointer items-center gap-1 text-sm font-medium text-ink-2 hover:text-ink"
      >
        <ArrowLeft aria-hidden="true" className="size-4" /> Volver
      </button>
      <div className="animate-fade-up">
        <PublicProfile
          student={student}
          actions={
            project && (
              <Button onClick={() => setInviting(true)} disabled={invited}>
                <Send aria-hidden="true" className="size-4" /> {invited ? "Invitación enviada" : "Invitar a un proyecto"}
              </Button>
            )
          }
        />
      </div>
      {project && (
        <InviteModal open={inviting} onClose={() => setInviting(false)} student={student} project={project} rol={rol} onSent={() => setInvited(true)} />
      )}
    </div>
  )
}

export default function ProfilePage() {
  const { id } = useParams()
  if (!id || id === currentUser.id) return <MyProfile />
  return <OtherProfile key={id} id={id} />
}
