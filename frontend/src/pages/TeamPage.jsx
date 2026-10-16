import { useState } from "react"
import { Link, useParams } from "react-router-dom"
import ScheduleMeetingModal from "../components/meeting/ScheduleMeetingModal"
import { ArrowLeft, ArrowRight, CalendarClock, Check, Copy, ExternalLink, EyeOff, Link2, Mail, UserPlus } from "lucide-react"
import Avatar, { AvatarGroup } from "../components/ui/Avatar"
import Button from "../components/ui/Button"
import Card from "../components/ui/Card"
import Modal from "../components/ui/Modal"
import SkillChip from "../components/ui/SkillChip"
import { AIPanel } from "../components/ui/AIBadge"
import { EmptyState } from "../components/ui/Feedback"
import { Field } from "../components/ui/Controls"
import { useToast } from "../components/ui/Toast"
import TeamCoverageChart from "../components/team/TeamCoverageChart"
import { CoverageBar } from "../components/team/TeamSummaryCard"
import { currentUser, projectById, studentById, teams } from "../data/mockData"
import { coverage } from "../lib/projects"
import { inputCls } from "../lib/ui"

function CopyButton({ text, label }) {
  const toast = useToast()
  const [done, setDone] = useState(false)
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text)
      setDone(true)
      toast(`${label} copiado`)
      setTimeout(() => setDone(false), 1500)
    } catch {
      toast("No pudimos copiar. Selecciónalo manualmente.", "error")
    }
  }
  return (
    <button
      type="button"
      onClick={copy}
      aria-label={`Copiar ${label.toLowerCase()}`}
      className="grid size-9 shrink-0 cursor-pointer place-items-center rounded-lg text-ink-2 transition-colors hover:bg-surface-2 hover:text-ink"
    >
      {done ? <Check aria-hidden="true" className="size-4 animate-pop text-success" /> : <Copy aria-hidden="true" className="size-4" />}
    </button>
  )
}

function MemberCard({ member, rol, esYo }) {
  const necesarias = new Set(rol.habilidades)
  const aporta = member.fortalezas ?? []
  const visible = member.correoVisible !== false
  return (
    <li className="flex flex-col gap-4 rounded-2xl border border-line bg-surface p-5 shadow-card">
      <div className="flex items-start gap-3">
        <Avatar name={member.nombre} size="md" />
        <div className="min-w-0 flex-1">
          <p className="truncate font-semibold">
            {member.nombre} {esYo && <span className="font-normal text-ink-2">(tú)</span>}
          </p>
          <p className="truncate text-sm text-ink-2">
            {member.carrera} · {member.semestre}.º
          </p>
        </div>
      </div>
      <p className="flex flex-wrap items-center gap-2 text-sm text-ink-2">
        Rol
        <span className="rounded-md bg-ink px-2 py-0.5 text-xs font-semibold text-canvas">{rol.nombre}</span>
      </p>
      <div>
        <p className="mb-2 text-label font-semibold tracking-wide text-ink-2 uppercase">Aporta</p>
        <ul className="flex flex-wrap gap-1.5">
          {aporta.map((f) => (
            <li key={f.nombre}>
              <SkillChip variant={necesarias.has(f.nombre) ? "match" : "neutral"}>{f.nombre}</SkillChip>
            </li>
          ))}
        </ul>
      </div>
      <div className="mt-auto border-t border-line pt-3">
        {visible ? (
          <div className="flex items-center gap-2 text-sm">
            <Mail aria-hidden="true" className="size-4 shrink-0 text-ink-2" />
            <a href={`mailto:${member.correo}`} className="min-w-0 flex-1 truncate text-primary hover:underline">
              {member.correo}
            </a>
            <CopyButton text={member.correo} label="Correo" />
          </div>
        ) : (
          <p className="flex items-center gap-2 text-sm text-ink-2">
            <EyeOff aria-hidden="true" className="size-4" /> Prefirió no compartir su correo
          </p>
        )}
      </div>
    </li>
  )
}

function GroupLinkModal({ open, onClose, value, onSave }) {
  const [link, setLink] = useState(value)
  const valid = !link || /^https?:\/\/\S+$/.test(link)
  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Enlace al grupo del equipo"
      description="Comparte el grupo externo donde se organizan (WhatsApp, Discord, Teams…)."
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button disabled={!valid} onClick={() => onSave(link)}>
            Guardar
          </Button>
        </>
      }
    >
      <Field id="group-link" label="Enlace" error={!valid ? "Escribe un enlace que empiece con https://" : null}>
        <input id="group-link" value={link} onChange={(e) => setLink(e.target.value)} placeholder="https://chat.whatsapp.com/…" className={inputCls(!valid)} />
      </Field>
    </Modal>
  )
}

export default function TeamPage() {
  const { id } = useParams()
  const toast = useToast()
  const team = teams.find((t) => t.id === id)
  const [enlace, setEnlace] = useState(team?.enlaceGrupo ?? "")
  const [editLink, setEditLink] = useState(false)
  const [meeting, setMeeting] = useState(false)

  if (!team) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10 sm:px-8">
        <EmptyState
          title="No encontramos este equipo"
          actions={
            <Button variant="secondary" as={Link} to="/equipos">
              Ver mis equipos
            </Button>
          }
        />
      </div>
    )
  }

  const project = projectById(team.projectId)
  const { cubiertos, total, pendientes } = coverage(project)
  const miembros = project.roles.filter((r) => r.cubiertoPor).map((r) => ({ rol: r, member: studentById(r.cubiertoPor) }))
  const esDueno = project.creadorId === currentUser.id
  const faltaIndispensable = pendientes.find((r) => r.indispensable) ?? pendientes[0]
  const correos = miembros.filter(({ member }) => member.correoVisible !== false).map(({ member }) => member.correo)

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-8 sm:py-10">
      <Link to="/equipos" className="mb-4 inline-flex min-h-9 items-center gap-1 text-sm font-medium text-ink-2 hover:text-ink">
        <ArrowLeft aria-hidden="true" className="size-4" /> Mis equipos
      </Link>

      <Card className="mb-8 animate-fade-up p-5 sm:p-7">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="min-w-0">
            <h1 className="text-h1 font-bold">{team.nombre}</h1>
            <Link to={`/proyectos/${project.id}`} className="mt-1 inline-flex items-center gap-1 text-sm text-ink-2 hover:text-primary hover:underline">
              {project.titulo} <ArrowRight aria-hidden="true" className="size-3.5" />
            </Link>
          </div>
          <div className="flex items-center gap-4">
            <AvatarGroup names={miembros.map((m) => m.member.nombre)} size="md" />
            <div className="w-44">
              <CoverageBar cubiertos={cubiertos} total={total} />
            </div>
          </div>
        </div>
        <div className="mt-5 border-t border-line pt-4">
          <Button variant="secondary" onClick={() => setMeeting(true)}>
            <CalendarClock aria-hidden="true" className="size-4" /> Proponer reunión
          </Button>
        </div>
      </Card>

      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div className="min-w-0 space-y-10">
          {/* Cobertura */}
          <section aria-labelledby="cov" className="animate-fade-up [animation-delay:60ms]">
            <h2 id="cov" className="mb-4 text-h2 font-semibold">
              Cobertura de habilidades
            </h2>
            <Card className="space-y-5 p-5 sm:p-6">
              <TeamCoverageChart roles={project.roles} />
              {faltaIndispensable && (
                <AIPanel title="Sugerencia">
                  <p>
                    A tu equipo le falta alguien de <strong className="font-semibold">{faltaIndispensable.nombre.toLowerCase()}</strong>.{" "}
                    <Link to={`/proyectos/${project.id}`} className="font-semibold text-primary hover:underline">
                      Ver sugerencias
                    </Link>
                  </p>
                </AIPanel>
              )}
            </Card>
          </section>

          {/* Integrantes */}
          <section aria-labelledby="mem" className="animate-fade-up [animation-delay:120ms]">
            <div className="mb-4 flex items-end justify-between gap-2">
              <h2 id="mem" className="text-h2 font-semibold">
                Integrantes <span className="font-normal text-ink-2">({miembros.length})</span>
              </h2>
              {esDueno && pendientes.length > 0 && (
                <Button variant="secondary" size="sm" as={Link} to={`/proyectos/${project.id}`}>
                  <UserPlus aria-hidden="true" className="size-4" /> Invitar
                </Button>
              )}
            </div>
            <ul className="grid gap-4 md:grid-cols-2">
              {miembros.map(({ rol, member }) => (
                <MemberCard key={rol.id} rol={rol} member={member} esYo={member.id === currentUser.id} />
              ))}
              {pendientes.map((r) => (
                <li key={r.id} className="flex min-h-40 flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-warn-line bg-warn-soft/40 p-5 text-center">
                  <SkillChip variant="needed">{r.nombre}</SkillChip>
                  <p className="text-sm text-ink-2">Lugar disponible</p>
                </li>
              ))}
            </ul>
          </section>
        </div>

        {/* Contacto */}
        <aside className="animate-fade-up space-y-4 [animation-delay:150ms]">
          <h2 className="text-h2 font-semibold">Cómo contactarse</h2>
          <Card className="space-y-4 p-5">
            <div>
              <p className="mb-2 text-sm font-semibold">Grupo del equipo</p>
              {enlace ? (
                <div className="flex items-center gap-2 rounded-lg bg-surface-2 p-2 pl-3">
                  <Link2 aria-hidden="true" className="size-4 shrink-0 text-ink-2" />
                  <a href={enlace} target="_blank" rel="noreferrer" className="min-w-0 flex-1 truncate text-sm text-primary hover:underline">
                    {enlace.replace(/^https?:\/\//, "")}
                  </a>
                  <ExternalLink aria-hidden="true" className="size-4 shrink-0 text-ink-2" />
                </div>
              ) : (
                <p className="text-sm text-ink-2">Aún no hay un enlace de grupo.</p>
              )}
              <Button variant="ghost" size="sm" className="mt-2 -ml-2" onClick={() => setEditLink(true)}>
                {enlace ? "Cambiar enlace" : "+ Agregar enlace"}
              </Button>
            </div>
            <div className="border-t border-line pt-4">
              <p className="mb-2 text-sm font-semibold">Correos compartidos</p>
              <div className="flex items-center gap-2">
                <p className="min-w-0 flex-1 text-sm text-ink-2">
                  {correos.length} de {miembros.length} integrantes compartieron su correo institucional.
                </p>
                <CopyButton text={correos.join(", ")} label="Correos" />
              </div>
            </div>
          </Card>
          <p className="text-xs text-ink-2">
            Cada integrante decide qué datos de contacto comparte desde su configuración de privacidad.
          </p>
        </aside>
      </div>

      {meeting && (
        <ScheduleMeetingModal
          name={team.nombre}
          role={project.titulo}
          suggestion={{ label: "Martes por la tarde: coinciden todos los integrantes.", dia: 2, hora: "16:00" }}
          onCancel={() => setMeeting(false)}
          onSend={() => {
            // TODO(backend): POST /equipos/{id}/reuniones
            setMeeting(false)
            toast("Propuesta enviada al equipo")
          }}
        />
      )}

      {editLink && (
        <GroupLinkModal
          open
          value={enlace}
          onClose={() => setEditLink(false)}
          onSave={(v) => {
            // TODO(backend): PATCH /equipos/{id} { enlace_grupo }
            setEnlace(v)
            setEditLink(false)
            toast("Enlace del grupo actualizado")
          }}
        />
      )}
    </div>
  )
}
