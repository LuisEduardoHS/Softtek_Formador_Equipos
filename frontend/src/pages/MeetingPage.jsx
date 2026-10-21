import { useNavigate } from "react-router-dom"
import ScheduleMeetingModal from "../components/meeting/ScheduleMeetingModal"
import { useToast } from "../components/ui/Toast"

export default function MeetingPage() {
  const navigate = useNavigate()
  const toast = useToast()

  return (
    <div className="relative flex min-h-[calc(100dvh-3.5rem)] items-start justify-center overflow-hidden px-4 py-8 sm:items-center lg:min-h-dvh">
      {/* Brillos del diseño de Figma */}
      <div aria-hidden="true" className="pointer-events-none absolute inset-0">
        <span className="absolute -top-40 -left-40 size-[26rem] rounded-full bg-primary/10 blur-[110px] dark:bg-primary/25" />
        <span className="absolute -right-40 -bottom-40 size-[26rem] rounded-full bg-primary/10 blur-[110px] dark:bg-primary/25" />
      </div>
      <div className="relative w-full max-w-lg">
        <ScheduleMeetingModal
          inline
          name="Equipo Hábitos"
          role="App de seguimiento de hábitos saludables"
          suggestion={{ label: "Martes por la tarde: coinciden todos los integrantes.", dia: 2, hora: "16:00" }}
          onSend={() => {
            // TODO(backend): POST /equipos/{id}/reuniones
            toast("Propuesta enviada al equipo")
            navigate("/equipos/t1")
          }}
          onCancel={() => navigate(-1)}
        />
      </div>
    </div>
  )
}
