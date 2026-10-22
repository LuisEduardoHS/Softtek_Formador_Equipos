import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { ArrowLeft, ArrowRight, CalendarDays, Check, CircleCheck, Lock, Pencil } from "lucide-react"
import Button from "../components/ui/Button"
import Card from "../components/ui/Card"
import ProgressSteps from "../components/ui/ProgressSteps"
import AvailabilityGrid from "../components/ui/AvailabilityGrid"
import TagEditor from "../components/ui/TagEditor"
import { LevelPicker } from "../components/ui/Controls"
import AIBadge, { LocalProcessing } from "../components/ui/AIBadge"
import { AILoading, ErrorState, Skeleton } from "../components/ui/Feedback"
import { useToast } from "../components/ui/Toast"
import { Logo } from "../components/layout/AppLayout"
import ProfileSetupForm from "../components/profile/ProfileSetupForm"
import { confirmarPerfil, interpretarPerfil } from "../services/api"
import { DIAS, DIAS_LABEL, FRANJAS, FRANJAS_LABEL } from "../data/mockData"
import { getSessionUser } from "../lib/session"

const STEPS = ["Cuéntanos de ti", "Tu disponibilidad", "Revisa tu perfil"]

/* ------------------------ Paso 2: disponibilidad ------------------------ */

const PRESETS = [
  { label: "Todas las tardes", blocks: DIAS.filter((d) => d !== "sab").map((d) => `${d}-tarde`) },
  { label: "Todas las mañanas", blocks: DIAS.filter((d) => d !== "sab").map((d) => `${d}-manana`) },
  { label: "Fines de semana", blocks: FRANJAS.map((f) => `sab-${f}`) },
]

function AvailabilityStep({ value, onChange, error }) {
  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-h3 font-semibold">¿Cuándo puedes reunirte con tu equipo?</h2>
        <p className="text-sm text-ink-2">Toca los bloques en los que normalmente estás libre. Podrás cambiarlos cuando quieras.</p>
      </div>
      <div className="flex flex-wrap gap-2">
        {PRESETS.map((p) => (
          <button
            key={p.label}
            type="button"
            onClick={() => onChange([...new Set([...value, ...p.blocks])])}
            className="min-h-9 cursor-pointer rounded-full border border-line bg-surface px-3 text-sm font-medium text-ink transition-colors hover:border-primary hover:text-primary"
          >
            + {p.label}
          </button>
        ))}
        {value.length > 0 && (
          <button type="button" onClick={() => onChange([])} className="min-h-9 cursor-pointer px-2 text-sm text-ink-2 hover:text-ink hover:underline">
            Limpiar
          </button>
        )}
      </div>
      <AvailabilityGrid value={value} onChange={onChange} />
      <p className={`text-sm ${error ? "text-danger" : "text-ink-2"}`} role={error ? "alert" : "status"}>
        {error || (
          <>
            <span className="font-semibold text-ink">{value.length}</span> {value.length === 1 ? "bloque seleccionado" : "bloques seleccionados"}
          </>
        )}
      </p>
    </div>
  )
}

/* -------------------------- Paso 3: revisión -------------------------- */

const ANALYSIS_MESSAGES = ["Leyendo tus respuestas…", "Identificando tus habilidades…", "Organizando tu perfil…"]
function ReviewBlock({ title, desc, badge, children }) {
  return (
    <Card className="animate-fade-up p-5">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="text-h3 font-semibold">{title}</h3>
          {desc && <p className="text-sm text-ink-2">{desc}</p>}
        </div>
        {badge}
      </div>
      {children}
    </Card>
  )
}

function summarize(blocks) {
  return DIAS.map((d) => {
    const fr = FRANJAS.filter((f) => blocks.includes(`${d}-${f}`)).map((f) => FRANJAS_LABEL[f].toLowerCase())
    return fr.length ? `${DIAS_LABEL[d]}: ${fr.join(", ")}` : null
  }).filter(Boolean)
}

function ReviewStep({ textos, disponibilidad, perfil, setPerfil, onEditAvailability }) {
  const [state, setState] = useState(perfil ? "ready" : "loading")
  const [msg, setMsg] = useState(0)
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    if (perfil) return
    let alive = true
    const timer = setInterval(() => setMsg((m) => Math.min(m + 1, ANALYSIS_MESSAGES.length - 1)), 750)
    interpretarPerfil(textos)
      .then((p) => {
        if (!alive) return
        setPerfil(p)
        setState("ready")
      })
      .catch(() => alive && setState("error"))
      .finally(() => clearInterval(timer))
    return () => {
      alive = false
      clearInterval(timer)
    }
  }, [attempt, perfil, textos, setPerfil])

  if (state === "loading") {
    return (
      <div className="space-y-4" aria-busy="true">
        <AILoading text={`La IA está analizando tu perfil… ${ANALYSIS_MESSAGES[msg]}`} />
        <LocalProcessing />
        <Button variant="secondary" onClick={() => {
          setPerfil({ fortalezas: [], reforzar: [], intereses: [], experiencia: [], resumen_publico: "" })
          setState("ready")
        }}>Revisar manualmente</Button>
        {[0, 1, 2].map((i) => (
          <div key={i} className="space-y-3 rounded-2xl border border-line bg-surface p-5">
            <Skeleton className="h-5 w-40" />
            <div className="flex gap-2">
              <Skeleton className="h-7 w-24 rounded-full" />
              <Skeleton className="h-7 w-32 rounded-full" />
              <Skeleton className="h-7 w-20 rounded-full" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (state === "error") {
    return (
      <div className="space-y-3">
        <ErrorState message="No pudimos analizar tu perfil. Tus respuestas siguen guardadas."
          onRetry={() => { setState("loading"); setMsg(0); setAttempt((a) => a + 1) }} />
        <Button variant="secondary" onClick={() => {
          setPerfil({ fortalezas: [], reforzar: [], intereses: [], experiencia: [], resumen_publico: "" })
          setState("ready")
        }}>Revisar manualmente</Button>
      </div>
    )
  }

  const set = (k) => (v) => setPerfil((p) => ({ ...p, [k]: v }))
  const fortalezaNames = perfil.fortalezas.map((f) => f.nombre)

  const setFortalezas = (names) =>
    setPerfil((p) => ({
      ...p,
      fortalezas: names.map((n, i) => ({
        nombre: n,
        nivel:
          p.fortalezas.find((f) => f.nombre === n)?.nivel ??
          (names.length === p.fortalezas.length ? p.fortalezas[i].nivel : null),
      })),
    }))

  const setNivel = (idx, nivel) =>
    setPerfil((p) => ({ ...p, fortalezas: p.fortalezas.map((f, i) => (i === idx ? { ...f, nivel } : f)) }))

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-2 rounded-xl border border-ai-line bg-ai-soft p-4 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-ink">
          <span className="font-semibold text-ai-ink">{perfil.origen === "ia_sin_confirmar" ? "Así entendimos tu perfil." : "Revisa tu perfil."}</span> Revisa, corrige lo que no encaje y confirma. Nada se
          publica hasta que lo hagas.
        </p>
        <LocalProcessing className="shrink-0" />
      </div>

      <ReviewBlock title="Fortalezas" desc="Indica tu nivel en cada una. Pulsa una etiqueta para corregirla." badge={perfil.origen === "ia_sin_confirmar" ? <AIBadge label="Interpretado por IA" /> : null}>
        <TagEditor
          items={fortalezaNames}
          onChange={setFortalezas}
          addLabel="Agregar"
          placeholder="Agregar fortaleza, p. ej. SQL"
          layout="rows"
          renderExtra={(name, idx) => (
            <LevelPicker name={name} value={perfil.fortalezas[idx]?.nivel} onChange={(n) => setNivel(idx, n)} />
          )}
        />
      </ReviewBlock>

      <ReviewBlock
        title="Quiero reforzar"
        desc="La IA lo usa para encontrar quién te puede complementar."
        badge={
          <span className="inline-flex items-center gap-1 rounded-full border border-line px-2 py-0.5 text-xs font-medium text-ink-2">
            <Lock aria-hidden="true" className="size-3" /> Privado · solo tú lo ves
          </span>
        }
      >
        <TagEditor items={perfil.reforzar} onChange={set("reforzar")} variant="private" placeholder="Agregar, p. ej. Hablar en público" />
      </ReviewBlock>

      <ReviewBlock title="Intereses" desc="Temas en los que te gustaría trabajar." badge={perfil.origen === "ia_sin_confirmar" ? <AIBadge label="Interpretado por IA" /> : null}>
        <TagEditor items={perfil.intereses} onChange={set("intereses")} placeholder="Agregar, p. ej. Fintech" />
      </ReviewBlock>

      <ReviewBlock title="Experiencia" desc="Conserva solo experiencias que hayas tenido.">
        <TagEditor items={perfil.experiencia ?? []} onChange={set("experiencia")} placeholder="Agregar experiencia real" />
      </ReviewBlock>

      <ReviewBlock title="Resumen público" desc="Comprueba que el texto sea fiel a tu perfil.">
        <textarea rows={3} value={perfil.resumen_publico ?? ""}
          onChange={(event) => set("resumen_publico")(event.target.value)}
          className="w-full rounded-lg border border-line bg-surface p-3 text-sm" />
      </ReviewBlock>

      <ReviewBlock
        title="Disponibilidad"
        badge={
          <Button variant="ghost" size="sm" onClick={onEditAvailability}>
            <Pencil aria-hidden="true" className="size-4" /> Editar
          </Button>
        }
      >
        <ul className="flex flex-wrap gap-2">
          {summarize(disponibilidad).map((s) => (
            <li key={s} className="flex items-center gap-1.5 rounded-lg bg-surface-2 px-3 py-1.5 text-sm">
              <CalendarDays aria-hidden="true" className="size-4 text-ink-2" /> {s}
            </li>
          ))}
        </ul>
      </ReviewBlock>
    </div>
  )
}

/* --------------------------- Pantalla de éxito --------------------------- */

function Done() {
  const navigate = useNavigate()
  return (
    <div className="flex animate-scale-in flex-col items-center py-16 text-center">
      <span className="grid size-20 animate-pop place-items-center rounded-full bg-success-soft">
        <CircleCheck aria-hidden="true" className="size-10 text-success" />
      </span>
      <h1 className="mt-6 text-h1 font-bold">¡Tu perfil está listo!</h1>
      <p className="mt-2 max-w-md text-ink-2">
        Tu perfil confirmado está guardado. Ya puedes explorar personas y proyectos.
      </p>
      <div className="mt-8 flex flex-wrap justify-center gap-2">
        <Button size="lg" onClick={() => navigate("/match")}>
          Explorar <ArrowRight aria-hidden="true" className="size-4" />
        </Button>
        <Button size="lg" variant="secondary" onClick={() => navigate("/inicio")}>
          Ir al inicio
        </Button>
      </div>
    </div>
  )
}

/* -------------------------------- Página -------------------------------- */

export default function ProfileSetupPage() {
  const toast = useToast()
  const [step, setStep] = useState(0)
  const [textos, setTextos] = useState({ nombre: "", foto: null, idiomas: "", fortalezas: "", reforzar: "", intereses: "" })
  const [disponibilidad, setDisponibilidad] = useState([])
  const [perfil, setPerfil] = useState(null)
  const [analyzedFor, setAnalyzedFor] = useState(null)
  const [errors, setErrors] = useState({})
  const [done, setDone] = useState(false)
  const [saving, setSaving] = useState(false)

  const go = (n) => {
    setStep(n)
    window.scrollTo({ top: 0, behavior: "smooth" })
  }

  const next = () => {
    if (step === 0) {
      const e = {}
      if (!textos.nombre.trim()) e.nombre = "Escribe tu nombre."
      if (textos.fortalezas.trim().length < 15) e.fortalezas = "Cuéntanos un poco más (al menos una frase) para que la IA pueda entenderte."
      if (Object.keys(e).length) {
        setErrors(e)
        return
      }
      // Solo se vuelve a interpretar si los textos cambiaron
      const key = JSON.stringify([textos.fortalezas, textos.reforzar, textos.intereses])
      if (key !== analyzedFor) {
        setPerfil(null)
        setAnalyzedFor(key)
      }
    }
    if (step === 1 && disponibilidad.length === 0) {
      setErrors({ disponibilidad: "Elige al menos un bloque para poder coincidir con tu equipo." })
      return
    }
    setErrors({})
    go(step + 1)
  }

  const confirm = async () => {
    const usuarioLocal = getSessionUser()
    const datosPerfil = {
      nombre: textos.nombre.trim(),
      carrera: usuarioLocal.carrera || "",
      fortalezas: perfil.fortalezas,
      reforzar: perfil.reforzar,
      intereses: perfil.intereses,
      experiencia: perfil.experiencia ?? [],
      resumen_publico: perfil.resumen_publico ?? "",
      disponibilidad,
      visibilidad: { fortalezas: true, intereses: true, disponibilidad: true, reforzar: false, correo: false },
      pausado: false,
    }

    setSaving(true)
    try {
      const guardado = await confirmarPerfil(datosPerfil)
      localStorage.setItem("usuario", JSON.stringify({
        ...usuarioLocal,
        nombre: guardado.nombre,
        carrera: guardado.carrera,
      }))
      toast("Perfil guardado")
      setDone(true)
    } catch (error) {
      console.error("No se pudo guardar el perfil:", error)
      toast(error.message || "No se pudo guardar tu perfil.", "error")
    } finally {
      setSaving(false)
    }
  }

  const updateTextos = (v) => {
    setTextos(v)
    if (Object.keys(errors).length) setErrors({})
  }

  return (
    <div className="min-h-dvh bg-canvas">
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex h-14 max-w-3xl items-center justify-between px-4 sm:px-8">
          <Logo />
          {!done && <span className="text-sm text-ink-2">Crear mi perfil</span>}
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-4 pt-6 pb-32 sm:px-8 sm:pt-10">
        {done ? (
          <Done />
        ) : (
          <>
            <div className="mb-8">
              <ProgressSteps steps={STEPS} current={step} />
            </div>

            <div key={step} className="animate-fade-up">
              {step === 0 && <ProfileSetupForm values={textos} onChange={updateTextos} errors={errors} />}

              {step === 1 && (
                <Card className="p-3 sm:p-6">
                  <AvailabilityStep
                    value={disponibilidad}
                    onChange={(v) => {
                      setDisponibilidad(v)
                      if (errors.disponibilidad) setErrors({})
                    }}
                    error={errors.disponibilidad}
                  />
                </Card>
              )}

              {step === 2 && (
                <div className="space-y-6">
                  <div>
                    <h1 className="text-h1 font-bold">Revisa tu perfil</h1>
                    <p className="mt-1 text-ink-2">Tú decides qué queda. Todo se puede editar más adelante desde tu perfil.</p>
                  </div>
                  <ReviewStep
                    textos={textos}
                    disponibilidad={disponibilidad}
                    perfil={perfil}
                    setPerfil={setPerfil}
                    onEditAvailability={() => go(1)}
                  />
                </div>
              )}
            </div>
          </>
        )}
      </main>

      {/* Navegación entre pasos: fija abajo para alcanzarla con el pulgar */}
      {!done && (
        <div className="fixed inset-x-0 bottom-0 z-20 border-t border-line bg-surface/95 pb-[env(safe-area-inset-bottom)] backdrop-blur">
          <div className="mx-auto flex max-w-3xl items-center justify-between gap-3 px-4 py-3 sm:px-8">
            <Button variant="ghost" onClick={() => go(step - 1)} disabled={step === 0} className={step === 0 ? "invisible" : ""}>
              <ArrowLeft aria-hidden="true" className="size-4" /> Atrás
            </Button>
            {step < 2 ? (
              <Button onClick={next} className="min-w-36">
                Continuar <ArrowRight aria-hidden="true" className="size-4" />
              </Button>
            ) : (
              <Button onClick={confirm} disabled={saving || !perfil || perfil.fortalezas.length === 0} className="min-w-36">
                <Check aria-hidden="true" className="size-4" /> {saving ? "Guardando…" : "Confirmar perfil"}
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
