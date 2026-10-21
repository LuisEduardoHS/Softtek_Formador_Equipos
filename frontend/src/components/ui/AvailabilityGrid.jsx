import { Check } from "lucide-react"
import { DIAS, DIAS_LABEL, FRANJAS, FRANJAS_LABEL } from "../../data/mockData"

/**
 * Cuadrícula semanal de disponibilidad (días × mañana/tarde/noche).
 * - Editable: pasa `onChange` y cada bloque es un botón de 44 px.
 * - Comparación: pasa `compare` para resaltar en verde los bloques en común.
 */
export default function AvailabilityGrid({ value = [], onChange, compare, size = "md", className = "" }) {
  const selected = new Set(value)
  const other = compare ? new Set(compare) : null
  const editable = !!onChange
  const cell = size === "sm" ? "h-6" : "h-11"

  const toggle = (key) => {
    const next = new Set(selected)
    next.has(key) ? next.delete(key) : next.add(key)
    onChange([...next])
  }

  return (
    <div className={`overflow-x-auto ${className}`}>
      <table className="w-full border-separate border-spacing-1 text-xs">
        <caption className="sr-only">Disponibilidad semanal</caption>
        <thead>
          <tr>
            <th scope="col" className="w-12 sm:w-16" />
            {DIAS.map((d) => (
              <th key={d} scope="col" className="pb-1 text-center font-semibold text-ink-2">
                {DIAS_LABEL[d]}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {FRANJAS.map((f) => (
            <tr key={f}>
              <th scope="row" className="pr-1 text-left font-medium whitespace-nowrap text-ink-2">
                {FRANJAS_LABEL[f]}
              </th>
              {DIAS.map((d) => {
                const key = `${d}-${f}`
                const on = selected.has(key)
                const shared = on && other?.has(key)
                const label = `${DIAS_LABEL[d]} ${FRANJAS_LABEL[f].toLowerCase()}`
                const tone = shared
                  ? "bg-success text-white"
                  : on
                    ? other
                      ? "bg-surface-2 text-ink-2 ring-1 ring-line ring-inset"
                      : "bg-primary text-white"
                    : "bg-surface ring-1 ring-line ring-inset"

                return (
                  <td key={d} className="p-0">
                    {editable ? (
                      <button
                        type="button"
                        aria-pressed={on}
                        aria-label={label}
                        onClick={() => toggle(key)}
                        className={`grid w-full min-w-9 cursor-pointer sm:min-w-11 place-items-center rounded-lg transition-all duration-150 active:scale-95 ${cell} ${
                          on ? "bg-primary text-white shadow-card" : "bg-surface text-transparent ring-1 ring-line ring-inset hover:bg-primary-soft hover:text-primary/40"
                        }`}
                      >
                        <Check aria-hidden="true" className={`size-4 transition-transform ${on ? "scale-100" : "scale-75"}`} strokeWidth={3} />
                      </button>
                    ) : (
                      <span
                        className={`grid w-full min-w-6 place-items-center rounded-md ${cell} ${tone}`}
                        title={`${label}${on ? (shared ? " · en común" : " · disponible") : ""}`}
                      >
                        {shared && <Check aria-hidden="true" className="size-3" strokeWidth={3} />}
                        <span className="sr-only">
                          {label}: {on ? (shared ? "en común" : "disponible") : "no disponible"}
                        </span>
                      </span>
                    )}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
      {other && (
        <p className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-2">
          <span className="flex items-center gap-1.5">
            <span className="grid size-3 place-items-center rounded-sm bg-success" /> En común contigo
          </span>
          <span className="flex items-center gap-1.5">
            <span className="size-3 rounded-sm bg-surface-2 ring-1 ring-line" /> Solo esta persona
          </span>
        </p>
      )}
    </div>
  )
}
