import { useId, useState } from "react"
import { CalendarClock, Send } from "lucide-react"
import Modal from "../ui/Modal"
import Card from "../ui/Card"
import Input from "../ui/Input"
import Button from "../ui/Button"
import Avatar from "../ui/Avatar"
import { AIPanel } from "../ui/AIBadge"

const DURATIONS = [15, 30, 60]

// Próximo día de la semana (0 = domingo) en formato yyyy-mm-dd
function nextWeekday(day) {
  const d = new Date()
  d.setDate(d.getDate() + ((day + 7 - d.getDay()) % 7 || 7))
  return d.toISOString().slice(0, 10)
}

/**
 * Formulario para proponer una reunión del equipo (presencial o por el
 * grupo externo; la plataforma no tiene videollamadas).
 * - inline: se muestra como tarjeta en lugar de modal
 * - suggestion: { label, dia (0-6), hora } horario común sugerido por la IA
 */
function MeetingForm({ formId, name, role, suggestion, onSend, values, setValues }) {
  const set = (k) => (e) => setValues((v) => ({ ...v, [k]: e.target.value }))

  return (
    <form
      id={formId}
      className="flex flex-col gap-4"
      onSubmit={(event) => {
        event.preventDefault()
        onSend?.(values)
      }}
    >
      <div className="flex items-center gap-3 rounded-xl bg-surface-2 p-3">
        <Avatar name={name} />
        <div className="min-w-0">
          <p className="truncate font-semibold">{name}</p>
          <p className="truncate text-sm text-ink-2">{role}</p>
        </div>
      </div>

      {suggestion && (
        <AIPanel title="Horario en común">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span>{suggestion.label}</span>
            <button
              type="button"
              onClick={() => setValues((v) => ({ ...v, date: nextWeekday(suggestion.dia), time: suggestion.hora }))}
              className="min-h-9 cursor-pointer rounded-lg border border-ai-line bg-surface px-3 text-sm font-semibold text-ai-ink hover:bg-ai-soft"
            >
              Usar este horario
            </button>
          </div>
        </AIPanel>
      )}

      <Input label="Título de la reunión" name="title" value={values.title} onChange={set("title")} placeholder="Ej.: Arranque del proyecto" required />

      <div className="grid grid-cols-2 gap-3">
        <Input label="Fecha" name="date" type="date" value={values.date} onChange={set("date")} required />
        <Input label="Hora" name="time" type="time" value={values.time} onChange={set("time")} required />
      </div>

      <fieldset>
        <legend className="mb-1.5 text-sm font-semibold">Duración</legend>
        <div className="flex gap-2">
          {DURATIONS.map((option) => (
            <button
              key={option}
              type="button"
              aria-pressed={values.duration === option}
              onClick={() => setValues((v) => ({ ...v, duration: option }))}
              className={`min-h-11 flex-1 cursor-pointer rounded-lg border text-sm font-semibold transition-all ${
                values.duration === option ? "border-primary bg-primary-soft text-primary" : "border-line bg-surface text-ink hover:bg-surface-2"
              }`}
            >
              {option} min
            </button>
          ))}
        </div>
      </fieldset>

      <Input label="Lugar" name="place" optional value={values.place} onChange={set("place")} placeholder="Ej.: Biblioteca central, sala 3" />
    </form>
  )
}

export default function ScheduleMeetingModal({ open = true, inline = false, name, role, suggestion, onSend, onCancel }) {
  const formId = useId()
  const [values, setValues] = useState({ title: "", date: "", time: "", duration: 30, place: "" })
  const valid = values.title.trim() && values.date && values.time

  const actions = (
    <>
      <Button variant="secondary" onClick={onCancel}>
        Cancelar
      </Button>
      <Button type="submit" form={formId} disabled={!valid}>
        <Send aria-hidden="true" className="size-4" /> Enviar propuesta
      </Button>
    </>
  )
  const form = <MeetingForm formId={formId} name={name} role={role} suggestion={suggestion} onSend={onSend} values={values} setValues={setValues} />

  if (inline) {
    return (
      <Card className="w-full max-w-lg animate-scale-in shadow-pop">
        <header className="flex items-center gap-3 border-b border-line p-5">
          <span className="grid size-10 place-items-center rounded-xl bg-primary-soft text-primary">
            <CalendarClock aria-hidden="true" className="size-5" />
          </span>
          <div>
            <h1 className="text-h2 font-semibold">Proponer reunión</h1>
            <p className="text-sm text-ink-2">El equipo recibirá la propuesta como notificación.</p>
          </div>
        </header>
        <div className="p-5">{form}</div>
        <footer className="flex flex-wrap justify-end gap-2 border-t border-line p-4">{actions}</footer>
      </Card>
    )
  }

  return (
    <Modal open={open} onClose={onCancel} title="Proponer reunión" description="El equipo recibirá la propuesta como notificación." footer={actions}>
      {form}
    </Modal>
  )
}
