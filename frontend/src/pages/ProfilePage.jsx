import { useId, useState, useEffect } from "react"
import { Link, useNavigate, useParams } from "react-router-dom"
import { ArrowLeft, Eye, Lock, PauseCircle, Pencil, RefreshCw, Send, UserX } from "lucide-react"
import Button from "../components/ui/Button"
import Card from "../components/ui/Card"
import TagEditor from "../components/ui/TagEditor"
import AvailabilityGrid from "../components/ui/AvailabilityGrid"
import { EmptyState, Skeleton } from "../components/ui/Feedback"
import { Field, LevelPicker, Segmented, Switch } from "../components/ui/Controls"
import { useToast } from "../components/ui/Toast"
import PublicProfile from "../components/profile/PublicProfile"
import InviteModal from "../components/invite/InviteModal"
import { confirmarPerfil, guardarPerfil, obtenerPerfil, obtenerPerfilUsuario, obtenerProyectos } from "../services/api"
import { inputCls } from "../lib/ui"
import { getSessionUser } from "../lib/session"

// Estructura por defecto para evitar errores si la base de datos devuelve nulos en cuentas nuevas
const PERFIL_DEFAULT = {
  carrera: "",
  semestre: 1,
  fortalezas: [],
  reforzar: [],
  intereses: [],
  disponibilidad: [],
  grupoExterno: "",
  visibilidad: { fortalezas: true, intereses: true, disponibilidad: true, reforzar: false, correo: false },
  pausado: false,
  consentimiento_recomendaciones: false,
}

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

const AI_FIELDS = ["fortalezas", "reforzar", "intereses", "disponibilidad"]

function EditProfile({ perfil, setPerfil, dirty, aiDirty, onSave, onDiscard }) {
  const ids = { c: useId(), s: useId(), g: useId(), e: useId() }
  const set = (k) => (v) => setPerfil((p) => ({ ...p, [k]: v }))
  const setVis = (k) => (v) => setPerfil((p) => ({ ...p, visibilidad: { ...p.visibilidad, [k]: v } }))

  const setFortalezas = (names) =>
    setPerfil((p) => ({
      ...p,
      fortalezas: names.map((n) => ({
        nombre: n,
        nivel: p.fortalezas.find((f) => f.nombre === n)?.nivel ?? null,
      })),
    }))

  return (
    <div className="space-y-4">
      {perfil.pausado && (
        <div className="flex animate-fade-up items-start gap-3 rounded-xl border border-warn-line bg-warn-soft p-4 text-sm">
          <PauseCircle aria-hidden="true" className="mt-0.5 size-5 shrink-0 text-warn-ink" />
          <p>
            <span className="font-semibold">Tu perfil está en pausa.</span> No aparecerás en recomendaciones de otras personas, pero conservas tus equipos e invitaciones.
          </p>
        </div>
      )}

      {aiDirty && (
        <div role="status" className="flex animate-fade-up items-center gap-3 rounded-xl border border-ai-line bg-ai-soft p-4 text-sm text-ink">
          <RefreshCw aria-hidden="true" className="size-4 shrink-0 text-ai-ink" />
          Confirmaremos los datos que cambiaste y actualizaremos su vector si Ollama está disponible.
        </div>
      )}

      <Section title="Información básica">
        <div className="grid gap-4 sm:grid-cols-[1fr_140px]">
          <Field id={ids.c} label="Carrera">
            <input id={ids.c} value={perfil.carrera || ""} onChange={(e) => set("carrera")(e.target.value)} className={inputCls()} />
          </Field>
          <Field id={ids.s} label="Semestre">
            <select id={ids.s} value={perfil.semestre || 1} onChange={(e) => set("semestre")(Number(e.target.value))} className={`${inputCls()} cursor-pointer`}>
              {Array.from({ length: 12 }, (_, i) => i + 1).map((n) => (
                <option key={n} value={n}>{n}.º</option>
              ))}
            </select>
          </Field>
        </div>
      </Section>

      <Section title="Fortalezas" desc="Pulsa una etiqueta para corregirla e indica tu nivel.">
        <TagEditor
          items={(perfil.fortalezas || []).map((f) => f.nombre)}
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

      <Section title="Quiero reforzar" desc="Estas áreas no se consideran habilidades adquiridas." badge={<span className="inline-flex items-center gap-1 rounded-full border border-line px-2 py-0.5 text-xs font-medium text-ink-2"><Lock className="size-3" /> {perfil.visibilidad?.reforzar ? "Visible" : "Privado"}</span>}>
        <TagEditor items={perfil.reforzar || []} onChange={set("reforzar")} variant="private" placeholder="Agregar, p. ej. Hablar en público" />
      </Section>

      <Section title="Intereses">
        <TagEditor items={perfil.intereses || []} onChange={set("intereses")} placeholder="Agregar interés" />
      </Section>

      <Section title="Disponibilidad" desc="Toca los bloques en los que sueles estar libre.">
        <AvailabilityGrid value={perfil.disponibilidad || []} onChange={set("disponibilidad")} />
      </Section>

      <Section title="Contacto" desc="Solo lo verán los integrantes de tus equipos.">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field id={ids.e} label="Correo institucional" hint="Lo tomamos de tu cuenta universitaria.">
            <input id={ids.e} value={perfil.correo || ""} readOnly className={`${inputCls()} bg-surface-2 text-ink-2`} />
          </Field>
          <Field id={ids.g} label="Enlace a grupo externo" optional hint="Por ejemplo, tu usuario de Discord o un enlace de WhatsApp.">
            <input id={ids.g} value={perfil.grupoExterno || ""} onChange={(e) => set("grupoExterno")(e.target.value)} placeholder="https://…" className={inputCls()} />
          </Field>
        </div>
      </Section>

      <Section title="Privacidad" desc="Decide qué ven las demás personas.">
        <div className="divide-y divide-line">
          <Switch label="Mostrar mis fortalezas" checked={perfil.visibilidad?.fortalezas ?? true} onChange={setVis("fortalezas")} />
          <Switch label="Mostrar mis intereses" checked={perfil.visibilidad?.intereses ?? true} onChange={setVis("intereses")} />
          <Switch label="Mostrar mi disponibilidad" checked={perfil.visibilidad?.disponibilidad ?? true} onChange={setVis("disponibilidad")} />
          <Switch label="Mostrar «Quiero reforzar»" description="Privado por defecto." checked={perfil.visibilidad?.reforzar ?? false} onChange={setVis("reforzar")} />
          <Switch label="Compartir mi correo con mis equipos" checked={perfil.visibilidad?.correo ?? false} onChange={setVis("correo")} />
          <Switch label="Pausar mi perfil" checked={perfil.pausado ?? false} onChange={set("pausado")} />
          <Switch label="Activar recomendaciones" description="Permite sugerir tu perfil a organizadores y mostrarte proyectos." checked={perfil.consentimiento_recomendaciones ?? false} onChange={set("consentimiento_recomendaciones")} />
        </div>
      </Section>

      {dirty && (
        <div className="fixed inset-x-0 bottom-[calc(3.5rem+env(safe-area-inset-bottom))] z-20 animate-fade-up border-t border-line bg-surface/95 backdrop-blur lg:bottom-0 lg:left-[260px]">
          <div className="mx-auto flex max-w-4xl items-center justify-between gap-3 px-4 py-3 sm:px-8">
            <p className="text-sm text-ink-2">Tienes cambios sin guardar</p>
            <div className="flex gap-2">
              <Button variant="ghost" onClick={onDiscard}>Descartar</Button>
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
  const [loading, setLoading] = useState(true)
  const [saved, setSaved] = useState(null)
  const [perfil, setPerfil] = useState(null)
  const [mode, setMode] = useState("editar")

  useEffect(() => {
    obtenerPerfil()
      .then((data) => {
        const perfilCompleto = { ...PERFIL_DEFAULT, ...data }
        setSaved(perfilCompleto)
        setPerfil(perfilCompleto)
        setLoading(false)
      })
      .catch((err) => {
        console.error("Error cargando perfil:", err)
        toast("No pudimos cargar tu perfil de la base de datos.", "error")
        setLoading(false)
      })
  }, [toast])

  if (loading) return <div className="p-8"><Skeleton className="h-64 w-full rounded-xl" /></div>

  const dirty = JSON.stringify(perfil) !== JSON.stringify(saved)
  const aiDirty = AI_FIELDS.some((k) => JSON.stringify(perfil[k]) !== JSON.stringify(saved[k]))

  const save = async () => {
    try {
      let actualizado
      if (aiDirty) {
        const confirmado = await confirmarPerfil({
          nombre: perfil.nombre, carrera: perfil.carrera, fortalezas: perfil.fortalezas,
          reforzar: perfil.reforzar, intereses: perfil.intereses,
          experiencia: perfil.experiencia ?? [], resumen_publico: perfil.resumen_publico ?? "",
          disponibilidad: perfil.disponibilidad, visibilidad: perfil.visibilidad,
          pausado: perfil.pausado, consentimiento_recomendaciones: perfil.consentimiento_recomendaciones,
        })
        actualizado = await guardarPerfil({ ...confirmado, semestre: perfil.semestre,
          grupoExterno: perfil.grupoExterno })
      } else actualizado = await guardarPerfil(perfil)
      setSaved(actualizado)
      setPerfil(actualizado)
      toast(aiDirty ? "Perfil confirmado; recomendaciones disponibles según tus permisos." : "Perfil guardado en base de datos.", "success")
    } catch (error) {
      console.error(error)
      toast(error.message || "Error al guardar el perfil.", "error")
    }
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
            ["editar", <span key="e" className="flex items-center gap-1.5"><Pencil className="size-4" /> Editar</span>],
            ["publica", <span key="p" className="flex items-center gap-1.5"><Eye className="size-4" /> Ver como otros me ven</span>],
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
  const [student, setStudent] = useState(null)
  const [loading, setLoading] = useState(true)
  const [inviting, setInviting] = useState(false)
  const [projects, setProjects] = useState([])
  const [projectsLoading, setProjectsLoading] = useState(true)
  const [projectsError, setProjectsError] = useState(false)
  const [projectId, setProjectId] = useState("")
  const [roleId, setRoleId] = useState("")
  
  useEffect(() => {
    obtenerPerfilUsuario(id)
      .then((data) => {
        setStudent({ ...PERFIL_DEFAULT, ...data })
        setLoading(false)
      })
      .catch((error) => {
        console.error("No se pudo cargar el perfil:", error)
        setLoading(false)
      })
  }, [id])

  useEffect(() => {
    let usuarioLocal = {}
    try {
      usuarioLocal = JSON.parse(localStorage.getItem("usuario") || "{}")
    } catch (error) {
      console.error("No se pudo leer el usuario de la sesión:", error)
    }

    let active = true
    obtenerProyectos()
      .then((allProjects) => {
        if (!active) return
        const propios = allProjects.filter(
          (project) => String(project.creadorId) === String(usuarioLocal.id_usuario),
        )
        setProjects(propios)
        setProjectId(propios[0]?.id ?? "")
      })
      .catch((error) => {
        console.error("No se pudieron cargar tus eventos:", error)
        if (active) setProjectsError(true)
      })
      .finally(() => active && setProjectsLoading(false))

    return () => {
      active = false
    }
  }, [])

  const selectedProject = projects.find((project) => project.id === projectId)
  const openRoles = selectedProject?.roles.filter((role) => !role.cubiertoPor) ?? []
  const availableRoles = openRoles.length > 0 ? openRoles : selectedProject?.roles ?? []
  const selectedRole = availableRoles.find((role) => role.id === roleId) ?? availableRoles[0]

  if (loading) return <div className="p-8"><Skeleton className="h-64 w-full rounded-xl" /></div>

  if (!student) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10 sm:px-8">
        <EmptyState icon={UserX} title="No encontramos este perfil en la Base de Datos" actions={<Button variant="secondary" onClick={() => navigate(-1)}>Volver</Button>}>
          Puede que la persona haya pausado o eliminado su perfil.
        </EmptyState>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-6 sm:px-8 sm:py-10">
      <button type="button" onClick={() => navigate(-1)} className="mb-4 inline-flex min-h-9 items-center gap-1 text-sm font-medium text-ink-2 hover:text-ink">
        <ArrowLeft className="size-4" /> Volver
      </button>
      <div className="animate-fade-up">
        <PublicProfile student={student} />
        <section className="mt-4 flex flex-col gap-4 rounded-2xl border border-line bg-surface p-4 sm:flex-row sm:items-end">
          <div className="min-w-0 flex-1 space-y-3">
            <label htmlFor="profile-invite-project" className="block text-sm font-semibold">Invitar a uno de tus eventos</label>
            {projectsError ? (
              <p role="alert" className="text-sm text-danger">No pudimos cargar tus eventos.</p>
            ) : projectsLoading ? (
              <Skeleton className="h-11 w-full" />
            ) : projects.length === 0 ? (
              <div>
                <p className="text-sm text-ink-2">Primero crea un evento para poder enviar una invitación.</p>
                <Button variant="secondary" as={Link} to="/proyectos/nuevo" className="mt-2">Crear evento</Button>
              </div>
            ) : (
              <>
                <select
                  id="profile-invite-project"
                  value={projectId}
                  onChange={(event) => {
                    setProjectId(event.target.value)
                    setRoleId("")
                  }}
                  className="min-h-11 w-full rounded-lg border border-line bg-surface px-3 text-sm text-ink"
                >
                  {projects.map((project) => <option key={project.id} value={project.id}>{project.titulo}</option>)}
                </select>
                {availableRoles.length > 0 && (
                  <select
                    aria-label="Rol propuesto"
                    value={selectedRole?.id ?? ""}
                    onChange={(event) => setRoleId(event.target.value)}
                    className="min-h-11 w-full rounded-lg border border-line bg-surface px-3 text-sm text-ink"
                  >
                    {availableRoles.map((role) => <option key={role.id} value={role.id}>{role.nombre}</option>)}
                  </select>
                )}
              </>
            )}
          </div>
          <Button
            onClick={() => setInviting(true)}
            disabled={projectsLoading || projectsError || projects.length === 0}
          >
            <Send aria-hidden="true" className="size-4" /> Invitar
          </Button>
        </section>
        <InviteModal
          open={inviting}
          onClose={() => setInviting(false)}
          student={student}
          project={selectedProject}
          rol={selectedRole ?? { id: "participante", nombre: "Participante" }}
        />
      </div>
    </div>
  )
}

export default function ProfilePage() {
  const { id } = useParams()
  const usuarioGuardado = getSessionUser()
  const isMe = !id || String(id) === String(usuarioGuardado.id_usuario)

  if (isMe) return <MyProfile />
  return <OtherProfile key={id} id={id} />
}
