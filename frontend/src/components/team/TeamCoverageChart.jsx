import { Check, CircleDashed } from "lucide-react"

/**
 * Gráfico de cobertura de habilidades del equipo: anillo cubiertas vs.
 * faltantes y, al lado, el detalle de cada habilidad.
 * - coverage: requisitos y declaraciones confirmadas calculados por el backend.
 */
export default function TeamCoverageChart({ coverage }) {
  const { cubiertas = [], por_acreditar: faltantes = [], total = 0, estado = "desconocida" } = coverage ?? {}
  const unknown = estado !== "conocida" || total === 0
  const r = 42
  const c = 2 * Math.PI * r
  const frac = total ? cubiertas.length / total : 0
  const gap = total && faltantes.length && cubiertas.length ? 4 : 0

  return (
    <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-start">
      <figure className="relative grid size-36 shrink-0 place-items-center">
        <svg viewBox="0 0 100 100" className="size-36 -rotate-90" aria-hidden="true">
          <circle cx="50" cy="50" r={r} fill="none" strokeWidth="12" className="stroke-warn/50" />
          <circle
            cx="50"
            cy="50"
            r={r}
            fill="none"
            strokeWidth="12"
            strokeDasharray={`${Math.max(c * frac - gap, 0)} ${c}`}
            className="stroke-success transition-[stroke-dasharray] duration-700 ease-out"
          />
        </svg>
        <figcaption className="absolute text-center">
          <span className="block text-h1 font-bold">
            {total ? `${cubiertas.length}/${total}` : "—"}
          </span>
          <span className="text-xs text-ink-2">{unknown ? "Desconocida" : "habilidades"}</span>
        </figcaption>
        <span className="sr-only">
          {unknown ? "No se puede determinar la cobertura completa." : `${cubiertas.length} de ${total} habilidades cubiertas`}
        </span>
      </figure>

      <div className="grid w-full flex-1 gap-5 sm:grid-cols-2">
        <div>
          <p className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-success-ink">
            <Check aria-hidden="true" className="size-4" strokeWidth={3} /> Cubiertas ({cubiertas.length})
          </p>
          <ul className="flex flex-wrap gap-1.5">
            {cubiertas.map((h) => (
              <li key={h} className="rounded-full border border-success-line bg-success-soft px-2.5 py-1 text-xs font-medium text-success-ink">
                {h}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-warn-ink">
            <CircleDashed aria-hidden="true" className="size-4" strokeWidth={2.5} /> Por acreditar ({faltantes.length})
          </p>
          {faltantes.length ? (
            <ul className="flex flex-wrap gap-1.5">
              {faltantes.map((h) => (
                <li key={h} className="rounded-full border border-warn-line bg-warn-soft px-2.5 py-1 text-xs font-medium text-warn-ink">
                  {h}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-ink-2">{unknown ? "Cobertura desconocida: faltan requisitos confirmados o perfiles con habilidades visibles y confirmadas." : "Las habilidades requeridas tienen evidencia confirmada en el equipo."}</p>
          )}
        </div>
      </div>
      {unknown && total > 0 && <p className="text-xs text-ink-2">La información no visible o sin confirmar impide verificar toda la cobertura.</p>}
    </div>
  )
}
