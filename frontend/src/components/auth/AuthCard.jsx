import { useState } from "react"
import { Eye, EyeOff } from "lucide-react"
import Card from "../ui/Card"
import Input from "../ui/Input"
import Button from "../ui/Button"

const EMAIL_VALIDATION = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function PasswordToggle({ show, onToggle, label }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-label={show ? `Ocultar ${label}` : `Mostrar ${label}`}
      className="grid size-11 cursor-pointer place-items-center text-ink-2 hover:text-ink"
    >
      {show ? <EyeOff aria-hidden="true" className="size-4" /> : <Eye aria-hidden="true" className="size-4" />}
    </button>
  )
}

export default function AuthCard({ systemName = "Complementa", initialMode = "login", onSignIn, onSignUp, loading = false }) {
  const [errors, setErrors] = useState({})
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isSignUp, setIsSignUp] = useState(initialMode === "signup")

  const handleLoginSubmit = (event) => {
    event.preventDefault()
    const formData = new FormData(event.target)
    const email = String(formData.get("email") ?? "").trim()
    const password = String(formData.get("password") ?? "")
    const errs = {}
    if (!EMAIL_VALIDATION.test(email)) errs.email = "Ingresa un correo válido."
    if (password.length < 8) errs.password = "La contraseña debe tener al menos 8 caracteres."
    setErrors(errs)
    if (Object.keys(errs).length) return
    onSignIn?.({ email, password })
  }

  const handleRegisterSubmit = (event) => {
    event.preventDefault()
    const formData = new FormData(event.target)
    const nombre = String(formData.get("nombre") ?? "").trim()
    const email = String(formData.get("email") ?? "").trim()
    const carrera = String(formData.get("carrera") ?? "").trim()
    const estado = String(formData.get("estado_geografico") ?? "").trim()
    const municipio = String(formData.get("municipio") ?? "").trim()
    const password = String(formData.get("password") ?? "")
    const confirmPassword = String(formData.get("confirmPassword") ?? "")

    const errs = {}
    if (!nombre) errs.nombre = "Escribe tu nombre completo."
    if (!EMAIL_VALIDATION.test(email)) errs.email = "Ingresa un correo válido."
    if (!carrera) errs.carrera = "Selecciona o escribe tu carrera."
    if (password.length < 8) errs.password = "La contraseña debe tener al menos 8 caracteres."
    if (password !== confirmPassword) errs.confirmPassword = "Las contraseñas no coinciden."

    setErrors(errs)
    if (Object.keys(errs).length) return

    onSignUp?.({
      nombre,
      correo: email,
      carrera,
      estado_geografico: estado || undefined,
      municipio: municipio || undefined,
      password,
    })
  }

  const loginTitle = isSignUp ? "Crear cuenta" : "Inicia sesión"

  return (
    <Card className="w-full max-w-md animate-scale-in p-6 shadow-pop sm:p-10">
      <p className="mb-2 text-center text-label font-semibold tracking-[0.18em] text-ink-2 uppercase">Bienvenido a {systemName}</p>
      <h1 className="mb-8 text-center text-h1 font-bold text-ink">{loginTitle}</h1>

      <form className="flex flex-col gap-4" onSubmit={isSignUp ? handleRegisterSubmit : handleLoginSubmit} noValidate>
        {isSignUp && (
          <>
            <Input
              label="Nombre completo"
              name="nombre"
              type="text"
              autoComplete="name"
              placeholder="Tu nombre completo"
              error={errors.nombre}
              required
            />
            <Input
              label="Correo electrónico"
              name="email"
              type="email"
              autoComplete="email"
              placeholder="nombre@ejemplo.com"
              error={errors.email}
              required
            />
            <Input
              label="Carrera"
              name="carrera"
              type="text"
              autoComplete="organization-title"
              placeholder="Ej. Ingeniería en Sistemas"
              error={errors.carrera}
              required
            />
            <div className="grid gap-4 sm:grid-cols-2">
              <Input
                label="Estado"
                name="estado_geografico"
                type="text"
                optional
                placeholder="Ej. Jalisco"
              />
              <Input
                label="Municipio"
                name="municipio"
                type="text"
                optional
                placeholder="Ej. Guadalajara"
              />
            </div>
            <Input
              label="Contraseña"
              name="password"
              type={showPassword ? "text" : "password"}
              autoComplete="new-password"
              error={errors.password}
              required
              trailing={<PasswordToggle show={showPassword} onToggle={() => setShowPassword((s) => !s)} label="contraseña" />}
            />
            <Input
              label="Confirmar contraseña"
              name="confirmPassword"
              type={showConfirmPassword ? "text" : "password"}
              autoComplete="new-password"
              error={errors.confirmPassword}
              required
              trailing={<PasswordToggle show={showConfirmPassword} onToggle={() => setShowConfirmPassword((s) => !s)} label="confirmación de contraseña" />}
            />
          </>
        )}

        {!isSignUp && (
          <>
            <Input
              label="Correo electrónico"
              name="email"
              type="email"
              autoComplete="email"
              placeholder="nombre@ejemplo.com"
              error={errors.email}
              required
            />
            <Input
              label="Contraseña"
              name="password"
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              error={errors.password}
              required
              trailing={<PasswordToggle show={showPassword} onToggle={() => setShowPassword((s) => !s)} label="contraseña" />}
            />

            <button type="button" className="-mt-1 self-start text-sm font-medium text-primary hover:underline">
              ¿Olvidaste tu contraseña?
            </button>
          </>
        )}

        <Button type="submit" size="lg" className="w-full" disabled={loading}>
          {loading ? (isSignUp ? "Creando cuenta…" : "Un momento…") : isSignUp ? "Crear mi cuenta" : "Entrar"}
        </Button>

        <p className="mt-4 text-center text-sm text-ink-2">{isSignUp ? "¿Ya tienes cuenta?" : "¿Aún no tienes cuenta?"}</p>
        <Button
          type="button"
          variant="secondary"
          size="lg"
          className="w-full"
          onClick={() => {
            setErrors({})
            setIsSignUp((s) => !s)
          }}
        >
          {isSignUp ? "Iniciar sesión" : "Crear mi cuenta"}
        </Button>
      </form>
    </Card>
  )
}
