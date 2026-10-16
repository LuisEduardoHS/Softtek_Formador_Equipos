import { useEffect, useId, useState } from "react"
import { Link } from "react-router-dom"
import { Search, SearchX, SlidersHorizontal, X } from "lucide-react"
import Avatar from "../ui/Avatar"
import Button from "../ui/Button"
import SkillChip from "../ui/SkillChip"
import { EmptyState, ErrorState, Skeleton } from "../ui/Feedback"
import { buscarEstudiantes } from "../../services/api"
import { FRANJAS, FRANJAS_LABEL, filtros } from "../../data/mockData"

export function SearchBar({ value, onChange, placeholder = "Buscar por nombre o habilidad", label = "Buscar estudiantes" }) {
  const id = useId()
  return (
    <div className="relative flex-1">
      <label htmlFor={id} className="sr-only">
        {label}
      </label>
      <Search aria-hidden="true" className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-ink-2" />
      <input
        id={id}
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="min-h-11 w-full rounded-lg border border-line bg-surface pr-3 pl-9 text-sm text-ink transition-shadow outline-none placeholder:text-ink-2 focus:border-primary focus:ring-3 focus:ring-primary/15"
      />
    </div>
  )
}

function Select({ label, value, onChange, options }) {
  const id = useId()
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-xs font-semibold text-ink-2">
        {label}
      </label>
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="min-h-11 cursor-pointer rounded-lg border border-line bg-surface px-3 text-sm text-ink outline-none focus:border-primary focus:ring-3 focus:ring-primary/15"
      >
        <option value="">Todas</option>
        {options.map(([v, l]) => (
          <option key={v} value={v}>
            {l}
          </option>
        ))}
      </select>
    </div>
  )
}

const EMPTY = { carrera: "", habilidad: "", disponibilidad: "", semestre: "" }

export function FilterPanel({ value, onChange }) {
  const set = (k) => (v) => onChange({ ...value, [k]: v })
  return (
    <div className="grid animate-fade-up gap-3 rounded-xl border border-line bg-surface-2/60 p-4 sm:grid-cols-2 lg:grid-cols-4">
      <Select label="Carrera" value={value.carrera} onChange={set("carrera")} options={filtros.carreras.map((c) => [c, c])} />
      <Select label="Habilidad" value={value.habilidad} onChange={set("habilidad")} options={filtros.habilidades.map((h) => [h, h])} />
      <Select
        label="Disponibilidad"
        value={value.disponibilidad}
        onChange={set("disponibilidad")}
        options={FRANJAS.map((f) => [f, FRANJAS_LABEL[f]])}
      />
      <Select label="Semestre" value={value.semestre} onChange={set("semestre")} options={filtros.semestres.map((s) => [s, `${s}.º`])} />
    </div>
  )
}

/** Búsqueda manual (secundaria) con filtros. */
export default function StudentSearch() {
  const [q, setQ] = useState("")
  const [f, setF] = useState(EMPTY)
  const [open, setOpen] = useState(false)
  const [state, setState] = useState({ status: "idle", data: [] })
  const activos = Object.values(f).filter(Boolean).length
  const hasQuery = Boolean(q.trim() || activos)

  useEffect(() => {
    if (!hasQuery) return
    let alive = true
    const t = setTimeout(() => {
      setState((s) => ({ ...s, status: "loading" }))
      buscarEstudiantes({ q, ...f }).then(
        (data) => alive && setState({ status: "success", data }),
        () => alive && setState({ status: "error", data: [] }),
      )
    }, 250)
    return () => {
      alive = false
      clearTimeout(t)
    }
  }, [q, f, hasQuery])

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <SearchBar value={q} onChange={setQ} />
        <Button variant="secondary" onClick={() => setOpen((o) => !o)} aria-expanded={open} aria-label="Filtros">
          <SlidersHorizontal aria-hidden="true" className="size-4" />
          <span className="hidden sm:inline">Filtros</span>
          {activos > 0 && <span className="grid size-5 place-items-center rounded-full bg-primary text-[11px] text-white">{activos}</span>}
        </Button>
      </div>

      {open && <FilterPanel value={f} onChange={setF} />}

      {activos > 0 && (
        <button
          type="button"
          onClick={() => setF(EMPTY)}
          className="flex cursor-pointer items-center gap-1 text-sm font-medium text-primary hover:underline"
        >
          <X aria-hidden="true" className="size-4" /> Limpiar filtros
        </button>
      )}

      {hasQuery &&
        (state.status === "loading" || state.status === "idle" ? (
          <div className="space-y-2">
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} className="h-16 w-full rounded-xl" />
            ))}
          </div>
        ) : state.status === "error" ? (
          <ErrorState message="No pudimos completar la búsqueda." onRetry={() => setF({ ...f })} />
        ) : state.data.length === 0 ? (
          <EmptyState icon={SearchX} title="Sin resultados">
            Prueba con otra habilidad o quita algún filtro.
          </EmptyState>
        ) : (
          <ul className="divide-y divide-line rounded-xl border border-line bg-surface">
            {state.data.map((s) => (
              <li key={s.id} className="flex animate-fade-in items-center gap-3 p-3">
                <Avatar name={s.nombre} size="sm" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold">{s.nombre}</p>
                  <p className="truncate text-xs text-ink-2">
                    {s.carrera} · {s.semestre}.º
                  </p>
                </div>
                <div className="hidden flex-wrap justify-end gap-1 md:flex">
                  {s.fortalezas.slice(0, 2).map((h) => (
                    <SkillChip key={h.nombre}>{h.nombre}</SkillChip>
                  ))}
                </div>
                <Button variant="ghost" size="sm" as={Link} to={`/perfil/${s.id}`}>
                  Ver perfil
                </Button>
              </li>
            ))}
          </ul>
        ))}
    </div>
  )
}
