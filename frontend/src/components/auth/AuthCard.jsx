import { useState } from "react"
import { Eye, EyeOff } from "lucide-react"
import Card from "../ui/Card"
import Input from "../ui/Input"
import Button from "../ui/Button"

// Validación visual del dominio institucional (ajustar al dominio real)
const DOMINIO = /@[\w.-]+\.edu(\.mx)?$/i

function GoogleIcon() {
  return (
    <svg viewBox="0 0 24 24" className="size-4" aria-hidden="true">
      <path fill="#4285F4" d="M22.6 12.2c0-.8-.1-1.5-.2-2.2H12v4.2h5.9a5 5 0 0 1-2.2 3.3v2.7h3.6c2.1-1.9 3.3-4.8 3.3-8z" />
      <path fill="#34A853" d="M12 23c3 0 5.5-1 7.3-2.7l-3.6-2.8c-1 .7-2.2 1.1-3.7 1.1-2.9 0-5.3-1.9-6.2-4.5H2.1v2.8A11 11 0 0 0 12 23z" />
      <path fill="#FBBC05" d="M5.8 14.1a6.6 6.6 0 0 1 0-4.2V7.1H2.1a11 11 0 0 0 0 9.8z" />
      <path fill="#EA4335" d="M12 5.4c1.6 0 3 .6 4.2 1.6l3.1-3.1A11 11 0 0 0 2.1 7.1l3.7 2.8C6.7 7.3 9.1 5.4 12 5.4z" />
    </svg>
  )
}

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

export default function AuthCard({ systemName = "Complementa", onSignIn, onSignUp, onGoogle, loading = false }) {
  const [errors, setErrors] = useState({})
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isSignUp, setIsSignUp] = useState(false)

  const handleLoginSubmit = (event) => {
    event.preventDefault()
    const formData = new FormData(event.target)
    const email = String(formData.get("email") ?? "").trim()
    const password = String(formData.get("password") ?? "")
    const errs = {}
    if (!DOMINIO.test(email)) errs.email = "Usa tu correo institucional (termina en .edu.mx)."
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
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errs.email = "Ingresa un correo válido."
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
              placeholder="nombre.apellido@universidad.edu.mx"
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
              label="Correo institucional"
              name="email"
              type="email"
              autoComplete="email"
              placeholder="nombre.apellido@universidad.edu.mx"
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

        {!isSignUp && (
          <>
            <div className="my-1 flex items-center gap-4 text-sm text-ink-2">
              <span className="h-px flex-1 bg-line" />o<span className="h-px flex-1 bg-line" />
            </div>

            <Button type="button" variant="secondary" size="lg" className="w-full" onClick={onGoogle}>
              <GoogleIcon /> Continuar con Google institucional
            </Button>
          </>
        )}

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
