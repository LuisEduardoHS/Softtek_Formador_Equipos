import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { ArrowLeft } from "lucide-react"
import GlowBackground from "../components/layout/GlowBackground"
import AuthCard from "../components/auth/AuthCard"
import { Logo } from "../components/layout/AppLayout"
import { LocalProcessing } from "../components/ui/AIBadge"
import { iniciarSesion, registrarUsuario } from "../services/api"

export default function AuthPage({ initialMode = "login" }) {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState("")

  // Recibe { email, password } desde AuthCard
  const signIn = async ({ email, password }) => {
    setLoading(true)
    setErrorMsg("")

    try {
      const data = await iniciarSesion({ correo: email, password })
      localStorage.setItem("usuario", JSON.stringify(data.usuario))
      navigate("/inicio")
    } catch (error) {
      console.error("Error de conexión:", error)
      setErrorMsg(error.message || "No se pudo conectar con el servidor backend.")
    } finally {
      setLoading(false)
    }
  }

  const signUp = async ({ nombre, correo, carrera, estado_geografico, municipio, password }) => {
    setLoading(true)
    setErrorMsg("")

    try {
      const data = await registrarUsuario({
        nombre,
        correo,
        carrera,
        estado_geografico,
        municipio,
        password,
      })

      localStorage.setItem("usuario", JSON.stringify(data.usuario))
      navigate("/profile")
    } catch (error) {
      console.error("Error al registrar usuario:", error)
      setErrorMsg(error.message || "No se pudo crear la cuenta.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <GlowBackground>
      <header className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-4 sm:px-8">
        <Logo to="/" />
        <Link
          to="/"
          className="inline-flex min-h-9 items-center gap-1 text-sm font-medium text-ink-2 hover:text-ink"
        >
          <ArrowLeft aria-hidden="true" className="size-4" /> Volver
        </Link>
      </header>
      <main className="flex flex-1 flex-col items-center justify-center gap-6 px-4 py-10">
        {errorMsg && (
          <div className="w-full max-w-md rounded-lg border border-red-500/20 bg-red-500/10 p-3 text-center text-sm font-medium text-red-500">
            {errorMsg}
          </div>
        )}
        <AuthCard
          loading={loading}
          initialMode={initialMode}
          onSignIn={signIn}
          onSignUp={signUp}
        />
        <LocalProcessing />
      </main>
    </GlowBackground>
  )
}