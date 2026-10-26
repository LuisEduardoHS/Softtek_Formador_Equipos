import { SearchX } from "lucide-react"
import Button from "../ui/Button"
import { EmptyState } from "../ui/Feedback"

export default function CandidatesEmptyState({ available, reason, onRefresh }) {
  return <EmptyState icon={SearchX} title={available ? "Aún no hay candidatos recomendados" : "No hay vacantes utilizables"}
    actions={<Button variant="secondary" onClick={onRefresh}>Actualizar candidatos</Button>}>
    {available
      ? "Análisis listo describe el proyecto; no activa automáticamente los perfiles de otras personas. Pide a quienes quieran participar que confirmen su perfil y activen Recomendaciones en su propia cuenta: Perfil → Editar → Privacidad → Activar recomendaciones → Guardar cambios. Deben mantener el perfil sin pausa y permitir las habilidades que quieran compartir. Las habilidades ocultas o sin confirmar no acreditan requisitos; integrantes y solicitudes pendientes se excluyen. Después pulsa Actualizar candidatos."
      : reason || "Revisa la capacidad y los roles del proyecto antes de buscar candidatos."}
  </EmptyState>
}
