import { useId, useState } from "react"
import { Camera, Lock } from "lucide-react"
import Card from "../ui/Card"
import Input from "../ui/Input"
import Avatar from "../ui/Avatar"

const PREGUNTAS = [
  {
    key: "fortalezas",
    label: "¿En qué eres bueno?",
    hint: "Habilidades, herramientas o cosas que otros te piden ayuda para hacer.",
    placeholder: "Ej.: Se me da bien programar en Python y explicar temas a otros. También organizo bien la información en hojas de cálculo.",
    required: true,
  },
  {
    key: "reforzar",
    label: "¿Qué te gustaría reforzar?",
    hint: "Lo que quieres aprender o practicar trabajando en equipo. Solo lo usa la IA para encontrar coincidencias; nadie más lo ve.",
    placeholder: "Ej.: Me gustaría aprender a diseñar interfaces y perderle el miedo a presentar frente a un grupo.",
    privado: true,
  },
  {
    key: "intereses",
    label: "¿Qué temas te interesan?",
    hint: "Áreas o causas en las que te gustaría que fueran tus proyectos.",
    placeholder: "Ej.: Salud digital, educación, sostenibilidad y videojuegos.",
  },
]

function TextQuestion({ q, value, onChange, error }) {
  const id = useId()
  return (
    <div>
      <div className="mb-1 flex flex-wrap items-center gap-2">
        <label htmlFor={id} className="text-h3 font-semibold text-ink">
          {q.label}
          {q.required && <span className="sr-only"> (obligatorio)</span>}
        </label>
        {q.privado && (
          <span className="inline-flex items-center gap-1 rounded-full border border-line px-2 py-0.5 text-xs font-medium text-ink-2">
            <Lock aria-hidden="true" className="size-3" /> Privado
          </span>
        )}
      </div>
      <p id={`${id}-hint`} className="mb-2 text-sm text-ink-2">
        {q.hint}
      </p>
      <textarea
        id={id}
        name={q.key}
        rows={4}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={q.placeholder}
        aria-describedby={`${id}-hint${error ? ` ${id}-err` : ""}`}
        aria-invalid={!!error}
        className={`w-full resize-y rounded-xl border bg-surface p-4 text-body text-ink transition-shadow outline-none placeholder:text-ink-2/80 focus:ring-3 ${
          error ? "border-danger focus:ring-danger/15" : "border-line focus:border-primary focus:ring-primary/15"
        }`}
      />
      <div className="mt-1 flex justify-between gap-2 text-xs">
        <span id={`${id}-err`} className="text-danger" role={error ? "alert" : undefined}>
          {error}
        </span>
        <span className="text-ink-2">{value.length} caracteres</span>
      </div>
    </div>
  )
}

/**
 * Formulario de configuración de perfil (paso 1 del onboarding):
 * nombre, foto, idiomas y las tres preguntas en texto libre.
 * values: { nombre, foto (File|null), idiomas, fortalezas, reforzar, intereses }
 */
export default function ProfileSetupForm({ values, onChange, errors = {} }) {
  const photoId = useId()
  const [preview, setPreview] = useState(null)
  const set = (k) => (v) => onChange({ ...values, [k]: v })

  const pickPhoto = (file) => {
    if (preview) URL.revokeObjectURL(preview)
    setPreview(file ? URL.createObjectURL(file) : null)
    set("foto")(file)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-h1 font-bold">Configura tu perfil</h1>
        <p className="mt-1 text-ink-2">
          No necesitas formato especial: escribe como si se lo contaras a un compañero. La IA lo organiza por ti y podrás revisarlo antes de guardar.
        </p>
      </div>

      <Card className="p-5 sm:p-6">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start">
          <label htmlFor={photoId} className="group relative mx-auto cursor-pointer self-center rounded-full sm:mx-0 sm:self-start">
            <Avatar name={values.nombre || "Tú"} src={values.foto ? (preview ?? undefined) : undefined} size="xl" />
            <span className="absolute -right-1 -bottom-1 grid size-8 place-items-center rounded-full border border-line bg-surface text-ink-2 shadow-card transition-colors group-hover:text-primary">
              <Camera aria-hidden="true" className="size-4" />
            </span>
            <span className="sr-only">{values.foto ? "Cambiar foto de perfil" : "Subir foto de perfil (opcional)"}</span>
            <input
              id={photoId}
              type="file"
              name="photo"
              accept="image/*"
              className="sr-only"
              onChange={(e) => pickPhoto(e.target.files?.[0] ?? null)}
            />
          </label>
          <div className="grid flex-1 gap-4">
            <Input
              label="Nombre"
              name="name"
              value={values.nombre}
              onChange={(e) => set("nombre")(e.target.value)}
              placeholder="¿Cómo te llamas?"
              autoComplete="name"
              error={errors.nombre}
              required
            />
            <Input
              label="Idiomas que hablas"
              name="languages"
              optional
              value={values.idiomas}
              onChange={(e) => set("idiomas")(e.target.value)}
              placeholder="Ej.: Español, inglés"
            />
          </div>
        </div>
      </Card>

      <Card className="space-y-8 p-5 sm:p-6">
        {PREGUNTAS.map((q) => (
          <TextQuestion key={q.key} q={q} value={values[q.key]} onChange={set(q.key)} error={errors[q.key]} />
        ))}
      </Card>
    </div>
  )
}
