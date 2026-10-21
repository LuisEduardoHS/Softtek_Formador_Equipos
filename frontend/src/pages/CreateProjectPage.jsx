import { useEffect, useId, useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { ArrowLeft, ArrowRight, CircleAlert, CircleCheck, Minus, Plus, Rocket, Trash2 } from "lucide-react"
import Button from "../components/ui/Button"
import Card from "../components/ui/Card"
import ProgressSteps from "../components/ui/ProgressSteps"
import TagEditor from "../components/ui/TagEditor"
import AIBadge, { LocalProcessing } from "../components/ui/AIBadge"
import { AILoading, ErrorState, Skeleton } from "../components/ui/Feedback"
import { Field, Segmented } from "../components/ui/Controls"
import { useToast } from "../components/ui/Toast"
import { interpretarProyecto } from "../services/api"
import { inputCls } from "../lib/ui"

const STEPS = ["Describe tu proyecto", "Roles necesarios"]

/* ----------------------------- Paso 1 ----------------------------- */

function Stepper({ value, onChange, min = 2, max = 8, id }) {
  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        aria-label="Quitar un integrante"
        onClick={() => onChange(Math.max(min, value - 1))}
        disabled={value <= min}
        className="grid size-11 cursor-pointer place-items-center rounded-lg border border-line bg-surface hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-40"
      >
        <Minus aria-hidden="true" className="size-4" />
      </button>
      <output id={id} aria-live="polite" className="w-10 text-center text-h2 font-semibold">
        {value}
      </output>
      <button
        type="button"
        aria-label="Agregar un integrante"
        onClick={() => onChange(Math.min(max, value + 1))}
        disabled={value >= max}
        className="grid size-11 cursor-pointer place-items-center rounded-lg border border-line bg-surface hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-40"
      >
        <Plus aria-hidden="true" className="size-4" />
      </button>
    </div>
  )
}

function DetailsStep({ form, set, errors }) {
  const ids = { t: useId(), d: useId(), m: useId(), n: useId(), f: useId() }
  return (
    <Card className="space-y-6 p-5 sm:p-7">
      <Field id={ids.t} label="Título del proyecto" error={errors.titulo}>
        <input
          id={ids.t}
          value={form.titulo}
          onChange={(e) => set("titulo", e.target.value)}
          placeholder="Ej.: App de seguimiento de hábitos saludables"
          aria-invalid={!!errors.titulo}
          aria-describedby={errors.titulo ? `${ids.t}-msg` : undefined}
          className={inputCls(errors.titulo)}
        />
      </Field>

      <Field
        id={ids.d}
        label="Descripción"
        hint="Cuenta qué quieren lograr y qué tipo de trabajo implica. La IA lo usará para proponer los roles."
        error={errors.descripcion}
      >
        <textarea
          id={ids.d}
          rows={5}
          value={form.descripcion}
          onChange={(e) => set("descripcion", e.target.value)}
          placeholder="Ej.: Queremos crear una app móvil para que estudiantes registren sus horas de sueño y actividad física, con recordatorios y un panel semanal."
          aria-invalid={!!errors.descripcion}
          aria-describedby={`${ids.d}-msg`}
          className={`${inputCls(errors.descripcion)} resize-y py-3`}
        />
      </Field>

      <div className="grid gap-6 sm:grid-cols-2">
        <div>
          <p className="mb-1.5 text-sm font-semibold">Tipo de proyecto</p>
          <Segmented
            label="Tipo de proyecto"
            value={form.tipo}
            onChange={(v) => set("tipo", v)}
            options={[
              ["academico", "Académico"],
              ["personal", "Personal"],
            ]}
          />
        </div>
        <Field id={ids.m} label="Materia" optional>
          <input
            id={ids.m}
            value={form.materia}
            onChange={(e) => set("materia", e.target.value)}
            placeholder="Ej.: Ingeniería de Software"
            disabled={form.tipo === "personal"}
            className={`${inputCls()} disabled:bg-surface-2 disabled:opacity-60`}
          />
        </Field>
        <div>
          <label htmlFor={ids.n} className="mb-1.5 block text-sm font-semibold">
            Número de integrantes
          </label>
          <Stepper id={ids.n} value={form.integrantes} onChange={(v) => set("integrantes", v)} />
          <p className="mt-1 text-xs text-ink-2">Incluyéndote a ti.</p>
        </div>
        <Field id={ids.f} label="Fecha límite" optional>
          <input id={ids.f} type="date" value={form.fechaLimite} onChange={(e) => set("fechaLimite", e.target.value)} className={inputCls()} />
        </Field>
      </div>
    </Card>
  )
}

/* ----------------------------- Paso 2 ----------------------------- */

function RoleCard({ role, index, onChange, onRemove }) {
  const nameId = useId()
  return (
    <li
      style={{ animationDelay: `${index * 60}ms` }}
      className={`animate-fade-up rounded-2xl border bg-surface p-4 shadow-card transition-colors sm:p-5 ${
        role.indispensable ? "border-ink/25" : "border-line"
      }`}
    >
      <div className="flex items-start gap-2">
        <div className="min-w-0 flex-1">
          <label htmlFor={nameId} className="sr-only">
            Nombre del rol
          </label>
          <input
            id={nameId}
            value={role.nombre}
            onChange={(e) => onChange({ ...role, nombre: e.target.value })}
            placeholder="Nombre del rol"
            className="w-full rounded-lg border border-transparent bg-transparent px-2 py-1.5 text-h3 font-semibold text-ink outline-none hover:border-line focus:border-primary focus:ring-3 focus:ring-primary/15"
          />
        </div>
        <button
          type="button"
          onClick={onRemove}
          aria-label={`Quitar rol ${role.nombre}`}
          className="grid size-10 shrink-0 cursor-pointer place-items-center rounded-lg text-ink-2 transition-colors hover:bg-danger-soft hover:text-danger"
        >
          <Trash2 aria-hidden="true" className="size-4" />
        </button>
      </div>

      <div className="mt-3 px-2">
        <p className="mb-2 text-label font-semibold tracking-wide text-ink-2 uppercase">Habilidades que necesita</p>
        <TagEditor
          items={role.habilidades}
          onChange={(h) => onChange({ ...role, habilidades: h })}
          variant="needed"
          placeholder="Agregar habilidad"
        />
      </div>

      <label className="mt-4 flex min-h-11 cursor-pointer items-center gap-3 rounded-lg px-2 hover:bg-surface-2">
        <input
          type="checkbox"
          checked={role.indispensable}
          onChange={(e) => onChange({ ...role, indispensable: e.target.checked })}
          className="size-5 cursor-pointer rounded accent-primary"
        />
        <span className="text-sm">
          <span className="font-semibold">Indispensable</span>
          <span className="text-ink-2"> · priorizaremos encontrar a alguien para este rol</span>
        </span>
      </label>
    </li>
  )
}

function RolesStep({ form, roles, setRoles }) {
  const [state, setState] = useState(roles ? "ready" : "loading")
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    if (roles) return
    let alive = true
    interpretarProyecto(form).then(
      (res) => {
        if (!alive) return
        setRoles(res.roles.map((r, i) => ({ ...r, id: `n${i}` })))
        setState("ready")
      },
      () => alive && setState("error"),
    )
    return () => {
      alive = false
    }
  }, [attempt, roles, form, setRoles])

  if (state === "loading") {
    return (
      <div className="space-y-4" aria-busy="true">
        <AILoading text="La IA está identificando los roles que necesita tu proyecto…" />
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} className="h-40 w-full rounded-2xl" />
        ))}
      </div>
    )
  }
  if (state === "error") {
    return (
      <ErrorState
        message="No pudimos proponer los roles. Puedes reintentar o agregarlos tú."
        onRetry={() => {
          setState("loading")
          setAttempt((a) => a + 1)
        }}
      />
    )
  }

  const update = (idx, r) => setRoles(roles.map((x, i) => (i === idx ? r : x)))
  const remove = (idx) => setRoles(roles.filter((_, i) => i !== idx))
  const add = () => setRoles([...roles, { id: `n${Date.now()}`, nombre: "Nuevo rol", habilidades: [], indispensable: false }])
  const otros = form.integrantes - 1 // tú ya ocupas un lugar

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-2 rounded-xl border border-ai-line bg-ai-soft p-4 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm">
          <span className="font-semibold text-ai-ink">Estos son los roles que creemos que necesitas.</span> Renómbralos, quítalos o agrega
          otros. Marca cuáles son indispensables.
        </p>
        <LocalProcessing className="shrink-0" />
      </div>

      {roles.length > otros + 1 && (
        <p className="flex items-start gap-2 rounded-xl border border-warn-line bg-warn-soft p-3 text-sm text-ink">
          <CircleAlert aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-warn-ink" />
          Tienes {roles.length} roles para {form.integrantes} integrantes. Está bien si alguien cubre más de uno; solo tenlo en cuenta.
        </p>
      )}

      <ul className="space-y-3">
        {roles.map((r, i) => (
          <RoleCard key={r.id} role={r} index={i} onChange={(nr) => update(i, nr)} onRemove={() => remove(i)} />
        ))}
      </ul>

      <button
        type="button"
        onClick={add}
        className="flex min-h-14 w-full cursor-pointer items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-line text-sm font-semibold text-ink-2 transition-colors hover:border-primary hover:text-primary"
      >
        <Plus aria-hidden="true" className="size-4" /> Agregar rol
      </button>
    </div>
  )
}

/* ------------------------------ Página ------------------------------ */

const EMPTY = { titulo: "", descripcion: "", tipo: "academico", materia: "", integrantes: 4, fechaLimite: "" }

export default function CreateProjectPage() {
  const navigate = useNavigate()
  const toast = useToast()
  const [step, setStep] = useState(0)
  const [form, setForm] = useState(EMPTY)
  const [roles, setRoles] = useState(null)
  const [analyzedFor, setAnalyzedFor] = useState(null)
  const [errors, setErrors] = useState({})
  const [published, setPublished] = useState(false)

  const set = (k, v) => {
    setForm((f) => ({ ...f, [k]: v }))
    if (errors[k]) setErrors((e) => ({ ...e, [k]: undefined }))
  }

  const next = () => {
    const e = {}
    if (form.titulo.trim().length < 4) e.titulo = "Ponle un título a tu proyecto."
    if (form.descripcion.trim().length < 30) e.descripcion = "Cuéntanos un poco más (al menos un par de frases) para proponer buenos roles."
    setErrors(e)
    if (Object.keys(e).length) return
    const key = `${form.titulo}|${form.descripcion}|${form.integrantes}`
    if (key !== analyzedFor) {
      setRoles(null)
      setAnalyzedFor(key)
    }
    setStep(1)
    window.scrollTo({ top: 0, behavior: "smooth" })
  }

  const publish = () => {
    // TODO(backend): POST /proyectos con { ...form, roles }
    setPublished(true)
    toast("¡Proyecto publicado! Ya estamos buscando candidatos.")
  }

  const validRoles = roles?.filter((r) => r.nombre.trim()).length > 0

  if (published) {
    return (
      <div className="mx-auto flex max-w-xl animate-scale-in flex-col items-center px-4 py-20 text-center">
        <span className="grid size-20 animate-pop place-items-center rounded-full bg-success-soft">
          <Rocket aria-hidden="true" className="size-9 text-success" />
        </span>
        <h1 className="mt-6 text-h1 font-bold">¡Tu proyecto está publicado!</h1>
        <p className="mt-2 text-ink-2">
          La IA ya está buscando personas que cubran los {roles.length} roles. Te avisaremos en cuanto haya candidatos.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-2">
          {/* TODO(backend): navegar al id real del proyecto creado */}
          <Button size="lg" onClick={() => navigate("/proyectos/p1")}>
            Ver candidatos <ArrowRight aria-hidden="true" className="size-4" />
          </Button>
          <Button size="lg" variant="secondary" as={Link} to="/inicio">
            Ir al inicio
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-6 pb-32 sm:px-8 sm:py-10 lg:pb-32">
      <Link to="/proyectos" className="mb-4 inline-flex min-h-9 items-center gap-1 text-sm font-medium text-ink-2 hover:text-ink">
        <ArrowLeft aria-hidden="true" className="size-4" /> Proyectos
      </Link>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-h1 font-bold">Crear proyecto</h1>
        {step === 1 && <AIBadge label="Roles propuestos por IA" />}
      </div>
      <div className="mb-8">
        <ProgressSteps steps={STEPS} current={step} />
      </div>

      <div key={step} className="animate-fade-up">
        {step === 0 ? <DetailsStep form={form} set={set} errors={errors} /> : <RolesStep form={form} roles={roles} setRoles={setRoles} />}
      </div>

      {/* Acciones fijas (sobre la barra inferior en móvil) */}
      <div className="fixed inset-x-0 bottom-[calc(3.5rem+env(safe-area-inset-bottom))] z-20 border-t border-line bg-surface/95 backdrop-blur lg:bottom-0 lg:left-[260px]">
        <div className="mx-auto flex max-w-3xl items-center justify-between gap-3 px-4 py-3 sm:px-8">
          {step === 0 ? (
            <Button variant="ghost" as={Link} to="/proyectos">
              Cancelar
            </Button>
          ) : (
            <Button variant="ghost" onClick={() => setStep(0)}>
              <ArrowLeft aria-hidden="true" className="size-4" /> Atrás
            </Button>
          )}
          {step === 0 ? (
            <Button onClick={next} className="min-w-36">
              Continuar <ArrowRight aria-hidden="true" className="size-4" />
            </Button>
          ) : (
            <Button onClick={publish} disabled={!validRoles} className="min-w-36">
              <CircleCheck aria-hidden="true" className="size-4" /> Publicar
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
