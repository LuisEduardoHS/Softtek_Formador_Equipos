import { useId, useState } from "react"
import { Pencil, Plus } from "lucide-react"
import SkillChip from "./SkillChip"

/**
 * Lista de etiquetas editable: agregar, quitar y corregir (clic en el texto).
 * - items: string[]
 * - renderExtra(item, index): contenido adicional por etiqueta (p. ej. nivel)
 */
export default function TagEditor({ items, onChange, variant = "neutral", addLabel = "Agregar", placeholder = "Escribe y pulsa Enter", renderExtra, layout = "wrap" }) {
  const inputId = useId()
  const [draft, setDraft] = useState("")
  const [editing, setEditing] = useState(null)
  const [editValue, setEditValue] = useState("")

  const add = () => {
    const v = draft.trim()
    if (v && !items.some((i) => i.toLowerCase() === v.toLowerCase())) onChange([...items, v])
    setDraft("")
  }
  const remove = (idx) => onChange(items.filter((_, i) => i !== idx))
  const startEdit = (idx) => {
    setEditing(idx)
    setEditValue(items[idx])
  }
  const commitEdit = () => {
    const v = editValue.trim()
    if (v) onChange(items.map((it, i) => (i === editing ? v : it)))
    setEditing(null)
  }

  return (
    <div className="space-y-3">
      <ul className={layout === "rows" ? "space-y-2" : "flex flex-wrap gap-2"}>
        {items.map((item, idx) => (
          <li key={`${item}-${idx}`} className={`animate-scale-in ${layout === "rows" ? "flex flex-wrap items-center justify-between gap-2" : ""}`}>
            {editing === idx ? (
              <input
                autoFocus
                aria-label={`Corregir ${item}`}
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                onBlur={commitEdit}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault()
                    commitEdit()
                  }
                  if (e.key === "Escape") setEditing(null)
                }}
                className="min-h-8 rounded-full border border-primary bg-surface px-3 text-xs font-medium outline-none ring-3 ring-primary/15"
              />
            ) : (
              <SkillChip variant={variant} label={item} onRemove={() => remove(idx)}>
                <button
                  type="button"
                  onClick={() => startEdit(idx)}
                  className="group inline-flex cursor-text items-center gap-1"
                  aria-label={`${item}. Pulsa para corregir`}
                >
                  {item}
                  <Pencil aria-hidden="true" className="size-3 opacity-0 transition-opacity group-hover:opacity-60 group-focus-visible:opacity-60" />
                </button>
              </SkillChip>
            )}
            {renderExtra?.(item, idx)}
          </li>
        ))}
      </ul>
      <div className="flex gap-2">
        <label htmlFor={inputId} className="sr-only">
          {addLabel}
        </label>
        <input
          id={inputId}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault()
              add()
            }
          }}
          placeholder={placeholder}
          className="min-h-11 min-w-0 flex-1 rounded-lg border border-line bg-surface px-3 text-sm outline-none placeholder:text-ink-2 focus:border-primary focus:ring-3 focus:ring-primary/15"
        />
        <button
          type="button"
          onClick={add}
          disabled={!draft.trim()}
          className="flex min-h-11 cursor-pointer items-center gap-1 rounded-lg border border-line px-3 text-sm font-semibold text-ink transition-colors hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Plus aria-hidden="true" className="size-4" /> {addLabel}
        </button>
      </div>
    </div>
  )
}
