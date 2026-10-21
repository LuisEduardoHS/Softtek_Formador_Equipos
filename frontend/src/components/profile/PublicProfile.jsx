import { EyeOff, Lock, Mail } from "lucide-react"
import Avatar from "../ui/Avatar"
import Card from "../ui/Card"
import SkillChip from "../ui/SkillChip"
import AvailabilityGrid from "../ui/AvailabilityGrid"
import { currentUser } from "../../data/mockData"

const DEFAULT_VIS = { fortalezas: true, intereses: true, disponibilidad: true, reforzar: false, correo: true }

function Block({ title, children }) {
  return (
    <section>
      <h3 className="mb-3 text-label font-semibold tracking-wide text-ink-2 uppercase">{title}</h3>
      {children}
    </section>
  )
}

function Hidden({ children }) {
  return (
    <p className="flex items-center gap-2 rounded-lg border border-dashed border-line px-3 py-2 text-sm text-ink-2">
      <EyeOff aria-hidden="true" className="size-4" /> {children}
    </p>
  )
}

/**
 * Lo que otros ven de un perfil. Con `preview` (tu propio perfil) los bloques
 * ocultos aparecen indicados para que sepas qué no se muestra.
 */
export default function PublicProfile({ student, preview = false, actions }) {
  const vis = { ...DEFAULT_VIS, ...(student.visibilidad ?? {}), ...(student.correoVisible === false ? { correo: false } : {}) }
  const esOtro = student.id !== currentUser.id
  const intereses = new Set(currentUser.intereses)

  return (
    <Card className="overflow-hidden">
      <div className="h-20 border-b border-line bg-surface-2" aria-hidden="true" />
      <div className="px-5 pb-6 sm:px-7">
        <div className="-mt-10 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div className="flex items-end gap-4">
            <Avatar name={student.nombre} size="xl" ring />
            <div className="pb-1">
              <h2 className="text-h2 font-bold">{student.nombre}</h2>
              <p className="text-sm text-ink-2">
                {student.carrera} · {student.semestre}.º semestre
              </p>
            </div>
          </div>
          {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
        </div>

        {student.bio && (
          <section className="mt-6">
            <h3 className="mb-2 text-label font-semibold tracking-wide text-ink-2 uppercase">Acerca de mí</h3>
            <p className="whitespace-pre-wrap text-sm text-ink">{student.bio}</p>
          </section>
        )}

        <div className="mt-8 grid gap-8 md:grid-cols-2">
          <div className="space-y-8">
            <Block title="Fortalezas">
              {vis.fortalezas ? (
                student.fortalezas.length > 0 ? (
                  <ul className="flex flex-wrap gap-1.5">
                    {student.fortalezas.map((f) => (
                      <li key={f.nombre}>
                        <SkillChip level={f.nivel}>{f.nombre}</SkillChip>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-ink-2">Aún no agrega fortalezas a su perfil.</p>
                )
              ) : (
                <Hidden>Oculto para otras personas</Hidden>
              )}
            </Block>

            <Block title="Intereses">
              {vis.intereses ? (
                (student.intereses ?? []).length > 0 ? (
                  <ul className="flex flex-wrap gap-1.5">
                    {(student.intereses ?? []).map((i) => (
                      <li key={i}>
                        <SkillChip variant={esOtro && intereses.has(i) ? "match" : "neutral"}>{i}</SkillChip>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-ink-2">Aún no agrega intereses a su perfil.</p>
                )
              ) : (
                <Hidden>Oculto para otras personas</Hidden>
              )}
              {esOtro && vis.intereses && <p className="mt-2 text-xs text-ink-2">En verde, los intereses que compartes.</p>}
            </Block>

            {(preview || vis.reforzar) && (
              <Block title="Quiero reforzar">
                {vis.reforzar ? (
                  <ul className="flex flex-wrap gap-1.5">
                    {student.reforzar.map((r) => (
                      <li key={r}>
                        <SkillChip>{r}</SkillChip>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="flex items-center gap-2 rounded-lg border border-dashed border-line px-3 py-2 text-sm text-ink-2">
                    <Lock aria-hidden="true" className="size-4" /> Privado: nadie más lo ve. La IA lo usa para tus coincidencias.
                  </p>
                )}
              </Block>
            )}
          </div>

          <div className="space-y-8">
            <Block title="Disponibilidad">
              {vis.disponibilidad ? (
                student.disponibilidad.length > 0 ? (
                  <AvailabilityGrid value={student.disponibilidad} compare={esOtro ? currentUser.disponibilidad : undefined} size="sm" />
                ) : (
                  <p className="text-sm text-ink-2">Aún no indica su disponibilidad.</p>
                )
              ) : (
                <Hidden>Oculta para otras personas</Hidden>
              )}
            </Block>

            <Block title="Contacto">
              {vis.correo ? (
                <p className="flex items-center gap-2 text-sm">
                  <Mail aria-hidden="true" className="size-4 text-ink-2" />
                  <span className="truncate">{student.correo}</span>
                </p>
              ) : (
                <Hidden>Prefiere no compartir su correo</Hidden>
              )}
            </Block>
          </div>
        </div>
      </div>
    </Card>
  )
}
