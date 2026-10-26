import { Link } from "react-router-dom"
import Button from "../ui/Button"

export default function RecommendationConsentStatus({ consent, paused = false, onEnable, disabled = false, busy = false }) {
  if (consent === true && !paused) return null
  return <section role="status" className="rounded-xl border border-warn-line bg-warn-soft p-4 text-sm">
    <h2 className="font-semibold text-warn-ink">{consent === true ? "Tu perfil está en pausa" : "No apareces en recomendaciones"}</h2>
    {consent !== true && <p className="mt-1">Las recomendaciones están desactivadas. Aunque tu análisis esté listo, no aparecerás como candidato ni recibirás proyectos recomendados. Activarlas permite usar los datos confirmados que hayas decidido compartir.</p>}
    {paused && <p className="mt-1">Para volver a aparecer, desactiva «Pausar mi perfil» en Perfil → Editar → Privacidad y guarda. Activar el consentimiento no quita la pausa.</p>}
    <p className="mt-2 text-ink-2">Este permiso aplica solo a tu cuenta. Cada participante debe activarlo en su propio perfil.</p>
    {consent !== true && (onEnable
      ? <div className="mt-3"><Button disabled={disabled || busy} onClick={onEnable}>{busy ? "Guardando…" : "Activar y guardar recomendaciones"}</Button>
        {disabled && !busy && <p className="mt-2">Guarda o descarta tus cambios pendientes antes de usar esta acción.</p>}</div>
      : <Button as={Link} to="/perfil" variant="secondary" className="mt-3">Configurar recomendaciones en mi perfil</Button>)}
  </section>
}
