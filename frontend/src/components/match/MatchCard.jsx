import { CalendarCheck, Check, Send, UserRound } from "lucide-react"
import Avatar from "../ui/Avatar"
import Button from "../ui/Button"
import SkillChip from "../ui/SkillChip"
import { AIPanel } from "../ui/AIBadge"
import { ComplementLevel } from "../recommendation/RecommendationCard"

/**
 * Tarjeta destacada de una coincidencia: una persona a la vez, centrada.
 * - onInvite: acción principal (antes «Start chat»; aquí no hay chat interno)
 * - onGoToProfile: ver el perfil completo
 */
export default function MatchCard({ student, rol, rec, invited = false, onInvite, onGoToProfile }) {
  const necesarias = new Set(rol?.habilidades ?? [])
  return (
    <article className="w-full max-w-md animate-scale-in rounded-3xl border border-line bg-surface p-6 text-center shadow-pop sm:p-8">
      <Avatar name={student.nombre} size="xl" className="mx-auto ring-4 ring-surface-2" />
      <h2 className="mt-4 text-h2 font-bold text-ink">{student.nombre}</h2>
      <p className="text-sm text-ink-2">
        {student.carrera} · {student.semestre}.º semestre
      </p>

      <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
        {rol && (
          <span className="rounded-md bg-ink px-2 py-0.5 text-xs font-semibold text-canvas">Cubriría: {rol.nombre}</span>
        )}
        <ComplementLevel nivel={rec.nivel} />
      </div>

      <ul className="mt-5 flex flex-wrap justify-center gap-1.5">
        {rec.aporta.map((h) => (
          <li key={h}>
            <SkillChip variant={necesarias.has(h) ? "match" : "neutral"}>{h}</SkillChip>
          </li>
        ))}
      </ul>

      <p className="mt-4 flex items-center justify-center gap-2 text-sm text-ink">
        <CalendarCheck aria-hidden="true" className="size-4 text-success-ink" />
        Coinciden {rec.bloquesComunes} bloques por semana
      </p>

      <AIPanel title="Por qué te lo recomendamos" className="mt-5 text-left">
        {rec.porQue}
      </AIPanel>

      <div className="mt-6 grid gap-2 sm:grid-cols-2">
        <Button size="lg" onClick={onInvite} disabled={invited}>
          {invited ? <Check aria-hidden="true" className="size-4" /> : <Send aria-hidden="true" className="size-4" />}
          {invited ? "Invitación enviada" : "Invitar"}
        </Button>
        <Button size="lg" variant="secondary" onClick={onGoToProfile}>
          <UserRound aria-hidden="true" className="size-4" /> Ver perfil
        </Button>
      </div>
    </article>
  )
}
