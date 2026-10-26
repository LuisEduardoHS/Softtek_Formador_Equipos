import { useId, useState } from "react"
import { CircleCheck, Send } from "lucide-react"
import Modal from "../ui/Modal"
import Button from "../ui/Button"
import Avatar from "../ui/Avatar"
import { useToast } from "../ui/Toast"
import { enviarInvitacion } from "../../services/api"

function mensajeSugerido(student, project, rol) {
  const nombre = student.nombre.split(" ")[0]
  return `¡Hola ${nombre}! Estoy formando un equipo para «${project.titulo}» y quisiera invitarte para conversar sobre el rol ${rol.nombre}. ¿Te gustaría participar?`
}

/**
 * Modal para invitar a alguien a un proyecto con una plantilla editable.
 */
export default function InviteModal(props) {
  if (!props.open || !props.student) return null
  // La key reinicia el formulario cada vez que se invita a otra persona
  return <InviteDialog key={`${props.student.id}-${props.rol?.id}`} {...props} />
}

function InviteDialog({ open, onClose, student, project, rol, onSent }) {
  const toast = useToast()
  const fieldId = useId()
  const [mensaje, setMensaje] = useState(() => mensajeSugerido(student, project, rol))
  const [status, setStatus] = useState("idle") // idle | sending | sent | error
  const [errorMessage, setErrorMessage] = useState("")

  const submit = async (e) => {
    e.preventDefault()
    setStatus("sending")
    setErrorMessage("")
    try {
      await enviarInvitacion({ paraId: student.id, projectId: project.id, rol: rol.nombre, mensaje })
      setStatus("sent")
      onSent?.(student)
      toast(`Invitación enviada a ${student.nombre}`)
      setTimeout(onClose, 1100)
    } catch (error) {
      console.error("No se pudo enviar la invitación:", error)
      setErrorMessage(error.message || "No pudimos enviar la invitación. Inténtalo de nuevo.")
      setStatus("error")
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Invitar al proyecto"
      description={project.titulo}
      footer={
        status !== "sent" && (
          <>
            <Button variant="secondary" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" form={`${fieldId}-form`} disabled={status === "sending" || !mensaje.trim()}>
              <Send aria-hidden="true" className="size-4" />
              {status === "sending" ? "Enviando…" : "Enviar invitación"}
            </Button>
          </>
        )
      }
    >
      {status === "sent" ? (
        <div className="flex animate-scale-in flex-col items-center py-6 text-center">
          <CircleCheck aria-hidden="true" className="size-14 animate-pop text-success" />
          <p className="mt-3 text-h3 font-semibold">¡Invitación enviada!</p>
          <p className="text-sm text-ink-2">Te avisaremos cuando {student.nombre.split(" ")[0]} responda.</p>
        </div>
      ) : (
        <form id={`${fieldId}-form`} onSubmit={submit} className="space-y-4">
          <div className="flex items-center gap-3 rounded-xl bg-surface-2 p-3">
            <Avatar name={student.nombre} />
            <div className="min-w-0 flex-1">
              <p className="truncate font-semibold">{student.nombre}</p>
              <p className="truncate text-sm text-ink-2">
                Para el rol <span className="font-medium text-ink">{rol.nombre}</span>
              </p>
            </div>
          </div>

          <div>
            <div className="mb-1.5 flex items-center justify-between gap-2">
              <label htmlFor={fieldId} className="text-sm font-semibold">
                Mensaje <span className="font-normal text-ink-2">(opcional)</span>
              </label>
              <span className="text-xs text-ink-2">Plantilla editable</span>
            </div>
            <textarea
              id={fieldId}
              rows={5}
              value={mensaje}
              onChange={(e) => setMensaje(e.target.value)}
              className="w-full resize-y rounded-lg border border-line bg-surface p-3 text-sm text-ink transition-shadow outline-none focus:border-primary focus:ring-3 focus:ring-primary/15"
            />
            <p className="mt-1 text-xs text-ink-2">Puedes editarlo; así sabrá por qué pensaste en esta persona.</p>
          </div>

          {status === "error" && (
            <p role="alert" className="text-sm text-danger">
              {errorMessage}
            </p>
          )}
        </form>
      )}
    </Modal>
  )
}
