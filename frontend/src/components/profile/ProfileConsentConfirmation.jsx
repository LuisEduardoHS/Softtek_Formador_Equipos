import Button from "../ui/Button"
import Modal from "../ui/Modal"

export default function ProfileConsentConfirmation({ open, busy, onClose, onEnable, onKeepDisabled }) {
  return <Modal open={open} onClose={onClose} title="¿Quieres recibir recomendaciones y aparecer como candidato?"
    footer={<>
      <Button variant="secondary" disabled={busy} onClick={onKeepDisabled}>Guardar sin recomendaciones</Button>
      <Button disabled={busy} onClick={onEnable}>Activar recomendaciones y guardar perfil</Button>
    </>}>
    <p>Las recomendaciones están desactivadas. Si guardas así, no aparecerás como candidato para otros proyectos ni recibirás proyectos recomendados, aunque tu perfil tenga el análisis listo.</p>
    <p className="mt-3">Puedes activarlas para usar tus datos confirmados y permitidos en el directorio y las sugerencias, o continuar sin recomendaciones. Podrás cambiar esta decisión en Perfil → Editar → Privacidad.</p>
  </Modal>
}
