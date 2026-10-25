import Button from "./Button"

const STATES = {
  listo: ["Análisis listo", "Los datos revisados y su representación para recomendaciones están actualizados."],
  pendiente_embedding: ["Datos confirmados; análisis pendiente", "Tus datos están guardados. Puedes reintentar el análisis; las recomendaciones pueden usar la información que confirmaste."],
  interpretando: ["Revisión pendiente", "Revisa tus datos o vuelve a interpretarlos antes de confirmar."],
  interpretacion_pendiente: ["Interpretación pendiente", "El servicio no completó la interpretación. Puedes revisar los datos manualmente o volver a intentarlo."],
  pendiente_revision: ["Requiere tu revisión", "Revisa y confirma los datos actuales para usarlos en las recomendaciones."],
  obsoleto: ["Los datos cambiaron", "Confirma los cambios antes de volver a generar el análisis."],
}

export default function AIStatus({ state, onRetry, onReview, busy = false, disabled = false }) {
  const [title, description] = STATES[state] ?? STATES.pendiente_revision
  return <section aria-label="Estado del análisis" className="rounded-xl border border-ai-line bg-ai-soft p-4">
    <p role="status" className="font-semibold">{busy ? "Procesando… Tus datos están guardados." : title}</p>
    <p className="mt-1 text-sm text-ink-2">{description}</p>
    {disabled && <p className="mt-1 text-sm text-ink-2">Guarda o descarta los cambios antes de continuar.</p>}
    {state === "pendiente_embedding" && onRetry && <Button className="mt-3" variant="secondary" disabled={busy || disabled} onClick={onRetry}>
      {busy ? "Reintentando…" : "Reintentar análisis"}
    </Button>}
    {!["listo", "pendiente_embedding"].includes(state) && onReview && <Button className="mt-3" disabled={busy || disabled} onClick={onReview}>
      Revisar y confirmar datos
    </Button>}
  </section>
}
