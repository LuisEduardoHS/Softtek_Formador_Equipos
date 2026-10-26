import { SearchX } from "lucide-react"
import Button from "../ui/Button"
import { EmptyState } from "../ui/Feedback"

export default function CandidatesEmptyState({ available, reason, onRefresh }) {
  return <EmptyState icon={SearchX} title={available ? "Aún no hay candidatos recomendados" : "No hay vacantes utilizables"}
    actions={<Button variant="secondary" onClick={onRefresh}>Actualizar candidatos</Button>}>
    {available
      ? "Solo se muestran personas con recomendaciones activadas, perfil no pausado y datos permitidos para estas vacantes. Pide a quienes quieran participar que revisen y confirmen su perfil y activen Recomendaciones. Las habilidades ocultas o sin confirmar no acreditan requisitos; integrantes y solicitudes pendientes se excluyen. Puedes actualizar después de esos cambios."
      : reason || "Revisa la capacidad y los roles del proyecto antes de buscar candidatos."}
  </EmptyState>
}
