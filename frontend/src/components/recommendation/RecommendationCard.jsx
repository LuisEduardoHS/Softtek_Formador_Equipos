import { useState } from "react"
import { CalendarCheck, Check, Send, ThumbsDown, ThumbsUp, Undo2, UserRound, X } from "lucide-react"
import Avatar from "../ui/Avatar"
import AvailabilityGrid from "../ui/AvailabilityGrid"
import { confirmedComparison } from "../../lib/contracts"
import Button from "../ui/Button"
import SkillChip from "../ui/SkillChip"
import { AIPanel } from "../ui/AIBadge"

const NIVELES = {
  muy: { label: "Muy complementario", bars: 3 },
  comp: { label: "Complementario", bars: 2 },
}

const MOTIVOS = ["Horario", "Intereses", "Ya tengo equipo", "Otro"]

export function ComplementLevel({ nivel }) {
  const { label, bars } = NIVELES[nivel] ?? NIVELES.comp
  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-success-ink">
      <span aria-hidden="true" className="flex items-end gap-0.5">
        {[1, 2, 3].map((i) => (
          <span
            key={i}
            className={`w-1 rounded-sm ${i <= bars ? "bg-success" : "bg-line"}`}
            style={{ height: 4 + i * 3 }}
          />
        ))}
      </span>
      {label}
    </span>
  )
}

/**
 * Tarjeta de recomendación de compañero.
 * - student: { nombre, carrera, semestre }
 * - rol: { nombre, habilidades[] } rol pendiente que cubriría
 * - rec: { nivel, aporta[], bloquesComunes, porQue }
 * - project: opcional; en la versión expandida muestra qué roles cubre y cuáles siguen pendientes
 * - variant: "compact" (listas) | "expanded" (detalle)
 */
export default function RecommendationCard({
  student,
  viewer,
  rol,
  rec,
  project,
  variant = "compact",
  onInvite,
  onViewProfile,
  onDismiss,
  onFeedback,
  invited = false,
  className = "",
}) {
  const [dismissing, setDismissing] = useState(false)
  const [dismissed, setDismissed] = useState(null)
  const [feedback, setFeedback] = useState(null)
  const expanded = variant === "expanded"
  const necesarias = new Set(rol?.habilidades ?? [])
  const currentUser = confirmedComparison(viewer)
  const interesesComunes = (student.intereses ?? []).filter((i) => currentUser?.intereses?.includes(i))
  const commonBlocks = currentUser && Array.isArray(student.disponibilidad)
    ? student.disponibilidad.filter((block) => currentUser.disponibilidad?.includes(block)).length : null

  const sendFeedback = (value) => {
    const next = feedback === value ? null : value
    setFeedback(next)
    onFeedback?.(next)
  }

  const dismiss = (motivo) => {
    setDismissed(motivo)
    setDismissing(false)
    onDismiss?.(motivo)
  }

  if (dismissed) {
    return (
      <div
        className={`flex animate-fade-in items-center justify-between gap-3 rounded-2xl border border-dashed border-line bg-surface/60 px-4 py-3 text-sm text-ink-2 ${className}`}
      >
        <span>
          Descartaste a {student.nombre.split(" ")[0]}
          {dismissed !== "sin motivo" && <> · {dismissed}</>}. Lo tomaremos en cuenta.
        </span>
        <Button variant="ghost" size="sm" onClick={() => setDismissed(null)}>
          <Undo2 aria-hidden="true" className="size-4" /> Deshacer
        </Button>
      </div>
    )
  }

  return (
    <article
      className={`flex flex-col rounded-2xl border border-line bg-surface shadow-card transition-all duration-200 hover:shadow-pop ${
        expanded ? "gap-5 p-6" : "gap-4 p-5"
      } ${className}`}
    >
      {/* Encabezado */}
      <header className="flex items-start gap-3">
        <Avatar name={student.nombre} size={expanded ? "lg" : "md"} />
        <div className="min-w-0 flex-1">
          <h3 className={`truncate font-semibold text-ink ${expanded ? "text-h2" : "text-h3"}`}>{student.nombre}</h3>
          <p className="truncate text-sm text-ink-2">
            {student.carrera} · {student.semestre}.º semestre
          </p>
        </div>
      </header>

      {/* Rol que cubriría + nivel de complementariedad */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        {rol && (
          <p className="flex flex-wrap items-center gap-2 text-sm text-ink-2">
            Cubriría
            <span className="rounded-md bg-ink px-2 py-0.5 text-xs font-semibold text-canvas">{rol.nombre}</span>
          </p>
        )}
        <ComplementLevel nivel={rec.nivel} />
      </div>

      {/* Habilidades que aporta */}
      <div>
        <p className="mb-2 text-label font-semibold tracking-wide text-ink-2 uppercase">Aporta</p>
        <ul className="flex flex-wrap gap-1.5">
          {rec.aporta.map((h) => (
            <li key={h}>
              <SkillChip variant={necesarias.has(h) ? "match" : "neutral"}>{h}</SkillChip>
            </li>
          ))}
        </ul>
      </div>

      {commonBlocks !== null && <p className="flex items-center gap-2 text-sm text-ink">
        <CalendarCheck aria-hidden="true" className="size-4 text-success-ink" />
        Coinciden {commonBlocks} {commonBlocks === 1 ? "bloque" : "bloques"} por semana
      </p>}

      <AIPanel title="Por qué te lo recomendamos">
        <p className={expanded ? "" : "line-clamp-2"}>{rec.porQue}</p>
      </AIPanel>

      {/* Detalle solo en la versión expandida */}
      {expanded && (
        <div className="grid gap-5 md:grid-cols-2">
          {project && (
            <div>
              <p className="mb-2 text-label font-semibold tracking-wide text-ink-2 uppercase">En tu proyecto</p>
              <ul className="space-y-1.5">
                {project.roles
                  .filter((r) => !r.cubiertoPor)
                  .map((r) => {
                    const cubre = r.id === rol?.id
                    return (
                      <li
                        key={r.id}
                        className={`flex items-center justify-between gap-2 rounded-lg border px-3 py-2 text-sm ${
                          cubre ? "border-success-line bg-success-soft" : "border-line"
                        }`}
                      >
                        <span className={cubre ? "font-semibold text-ink" : "text-ink-2"}>{r.nombre}</span>
                        {cubre ? (
                          <span className="flex items-center gap-1 text-xs font-semibold text-success-ink">
                            <Check aria-hidden="true" className="size-3.5" strokeWidth={3} /> Lo cubre
                          </span>
                        ) : (
                          <span className="text-xs font-medium text-warn-ink">Sigue pendiente</span>
                        )}
                      </li>
                    )
                  })}
              </ul>
              {interesesComunes.length > 0 && (
                <div className="mt-4">
                  <p className="mb-2 text-label font-semibold tracking-wide text-ink-2 uppercase">Intereses en común</p>
                  <div className="flex flex-wrap gap-1.5">
                    {interesesComunes.map((i) => (
                      <SkillChip key={i}>{i}</SkillChip>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
          {student.disponibilidad && (
            <div>
              <p className="mb-2 text-label font-semibold tracking-wide text-ink-2 uppercase">Horarios</p>
              <AvailabilityGrid value={student.disponibilidad} compare={currentUser?.disponibilidad} size="sm" />
            </div>
          )}
        </div>
      )}

      {/* Motivo de descarte */}
      {dismissing && (
        <div className="animate-fade-up rounded-xl border border-line bg-surface-2 p-3" role="group" aria-label="Motivo para descartar">
          <p className="mb-2 text-sm font-medium text-ink">¿Por qué no te convence? (opcional)</p>
          <div className="flex flex-wrap gap-2">
            {MOTIVOS.map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => dismiss(m)}
                className="min-h-9 cursor-pointer rounded-full border border-line bg-surface px-3 text-sm text-ink transition-colors hover:border-primary hover:text-primary"
              >
                {m}
              </button>
            ))}
            <button
              type="button"
              onClick={() => dismiss("sin motivo")}
              className="min-h-9 cursor-pointer px-2 text-sm text-ink-2 underline-offset-2 hover:underline"
            >
              Omitir
            </button>
          </div>
        </div>
      )}

      {/* Acciones */}
      <footer className={`mt-auto flex flex-col gap-2 border-t border-line pt-4 ${expanded ? "sm:flex-row sm:items-center" : ""}`}>
        <div className="flex gap-2">
          <Button onClick={onInvite} disabled={invited} className={`flex-1 ${expanded ? "sm:flex-none" : ""}`}>
            {invited ? <Check aria-hidden="true" className="size-4" /> : <Send aria-hidden="true" className="size-4" />}
            {invited ? "Invitación enviada" : "Invitar"}
          </Button>
          <Button variant="secondary" onClick={onViewProfile} className={`flex-1 ${expanded ? "sm:flex-none" : ""}`}>
            <UserRound aria-hidden="true" className="size-4" />
            Ver perfil
          </Button>
        </div>

        <div className={`flex items-center justify-between gap-2 ${expanded ? "sm:flex-1" : ""}`}>
        <Button
          variant="ghost"
          onClick={() => setDismissing((v) => !v)}
          aria-expanded={dismissing}
          className="-ml-2"
        >
          <X aria-hidden="true" className="size-4" />
          Descartar
        </Button>

        <div className="flex items-center gap-1" role="group" aria-label="¿Te sirvió esta recomendación?">
          <span className="mr-1 hidden text-xs text-ink-2 sm:inline">¿Útil?</span>
          <FeedbackButton active={feedback === "util"} onClick={() => sendFeedback("util")} label="Útil">
            <ThumbsUp className="size-4" />
          </FeedbackButton>
          <FeedbackButton active={feedback === "no_util"} onClick={() => sendFeedback("no_util")} label="No útil">
            <ThumbsDown className="size-4" />
          </FeedbackButton>
        </div>
        </div>
      </footer>
    </article>
  )
}

function FeedbackButton({ active, onClick, label, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      aria-label={label}
      title={label}
      className={`grid size-9 cursor-pointer place-items-center rounded-lg transition-colors ${
        active ? "animate-pop bg-primary-soft text-primary" : "text-ink-2 hover:bg-surface-2 hover:text-ink"
      }`}
    >
      <span aria-hidden="true">{children}</span>
    </button>
  )
}
