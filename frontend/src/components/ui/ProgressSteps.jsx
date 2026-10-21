import { Check } from "lucide-react"

/** Barra de progreso por pasos. `current` empieza en 0. */
export default function ProgressSteps({ steps, current }) {
  const pct = ((current + 1) / steps.length) * 100
  return (
    <div>
      <p className="mb-2 text-sm text-ink-2 sm:hidden">
        Paso {current + 1} de {steps.length} · <span className="font-semibold text-ink">{steps[current]}</span>
      </p>
      <div
        className="h-1.5 overflow-hidden rounded-full bg-surface-2"
        role="progressbar"
        aria-valuemin={1}
        aria-valuemax={steps.length}
        aria-valuenow={current + 1}
        aria-valuetext={`Paso ${current + 1} de ${steps.length}: ${steps[current]}`}
      >
        <div className="h-full rounded-full bg-primary transition-[width] duration-500 ease-out" style={{ width: `${pct}%` }} />
      </div>
      <ol className="mt-3 hidden gap-4 sm:flex">
        {steps.map((s, i) => {
          const done = i < current
          const active = i === current
          return (
            <li key={s} className="flex flex-1 items-center gap-2 text-sm" aria-current={active ? "step" : undefined}>
              <span
                className={`grid size-6 shrink-0 place-items-center rounded-full text-xs font-bold transition-colors ${
                  done ? "bg-success text-white" : active ? "bg-primary text-white" : "bg-surface-2 text-ink-2"
                }`}
              >
                {done ? <Check aria-hidden="true" className="size-3.5" strokeWidth={3} /> : i + 1}
              </span>
              <span className={active ? "font-semibold text-ink" : "text-ink-2"}>{s}</span>
            </li>
          )
        })}
      </ol>
    </div>
  )
}
