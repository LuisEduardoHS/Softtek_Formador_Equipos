import { useState } from "react"
import Card from "../ui/Card"
import Button from "../ui/Button"
import TagEditor from "../ui/TagEditor"
import AIStatus from "../ui/AIStatus"
import { confirmarProyecto, interpretarProyecto, reintentarEmbeddingProyecto } from "../../services/api"

function manualRequirements(project) {
  return { categoria: project.tipo, titulo_normalizado: project.titulo, resumen: "",
    roles_buscados: project.roles.map((r) => r.nombre),
    habilidades_obligatorias: [...new Set(project.roles.filter((r) => r.indispensable).flatMap((r) => r.habilidades))],
    habilidades_deseables: [...new Set(project.roles.filter((r) => !r.indispensable).flatMap((r) => r.habilidades))],
    intereses_relacionados: [], restricciones_explicitas: [] }
}

export default function ProjectAIReview({ project, onSaved }) {
  const [editing, setEditing] = useState(false)
  const [requirements, setRequirements] = useState(() => project.requirements ?? manualRequirements(project))
  const [busy, setBusy] = useState(false)
  const [reviewed, setReviewed] = useState(false)
  const [error, setError] = useState("")

  const perform = async (work) => {
    setBusy(true)
    setError("")
    try { await work() } catch (err) { setError(err.message || "No pudimos completar el análisis.") }
    finally { setBusy(false) }
  }
  const interpret = () => perform(async () => {
    const result = await interpretarProyecto(project)
    setRequirements({ ...result.requisitos, roles_buscados: project.roles.map((r) => r.nombre) })
    setReviewed(false)
  })
  const update = (key, items) => {
    setRequirements((current) => ({ ...current, [key]: items }))
    setReviewed(false)
  }
  return <div className="space-y-3">
    <AIStatus state={project.estado_ia} busy={busy} onReview={() => setEditing(true)}
      onRetry={() => perform(async () => { await reintentarEmbeddingProyecto(project.id); onSaved() })} />
    {editing && <Card className="p-5"><fieldset disabled={busy} className="space-y-5">
      <h2 className="text-h3 font-semibold">Revisa los requisitos actuales</h2>
      <p className="text-sm text-ink-2">Las sugerencias necesitan tu confirmación. Corrige las habilidades, intereses y condiciones; los roles corresponden a la edición actual del proyecto.</p>
      <p className="text-sm">Roles: {project.roles.map((r) => r.nombre).join(", ") || "Sin roles definidos"}</p>
      <Button variant="secondary" disabled={busy} onClick={interpret}>Interpretar descripción actual con IA</Button>
      {[["habilidades_obligatorias", "Habilidades obligatorias"], ["habilidades_deseables", "Habilidades deseables"],
        ["intereses_relacionados", "Intereses relacionados"], ["restricciones_explicitas", "Condiciones de participación"]].map(([key, label]) =>
        <div key={key}><p className="mb-2 text-sm font-semibold">{label}</p>
          <TagEditor items={requirements[key] ?? []} onChange={(items) => update(key, items)} placeholder={`Agregar ${label.toLowerCase()}`} />
        </div>)}
      <label className="flex items-start gap-2 text-sm"><input type="checkbox" checked={reviewed} disabled={busy}
        onChange={(event) => setReviewed(event.target.checked)} />He revisado estos requisitos y confirmo que corresponden al proyecto actual.</label>
      <div className="flex gap-2">
        <Button disabled={!reviewed || busy} onClick={() => perform(async () => {
          await confirmarProyecto(project, requirements)
          onSaved()
        })}>{busy ? "Guardando…" : "Confirmar y generar análisis"}</Button>
        <Button variant="ghost" disabled={busy} onClick={() => setEditing(false)}>Cancelar</Button>
      </div>
    </fieldset></Card>}
    {error && <p role="alert" className="rounded-lg bg-danger-soft p-3 text-sm text-danger">{error}</p>}
  </div>
}
