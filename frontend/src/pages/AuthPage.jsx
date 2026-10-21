import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { ArrowLeft } from "lucide-react"
import GlowBackground from "../components/layout/GlowBackground"
import AuthCard from "../components/auth/AuthCard"
import { Logo } from "../components/layout/AppLayout"
import { LocalProcessing } from "../components/ui/AIBadge"

export default function AuthPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)

  // TODO(backend): POST /auth/login y flujo OAuth de Google institucional
  const signIn = () => {
    setLoading(true)
    setTimeout(() => navigate("/inicio"), 600)
  }

  return (
    <GlowBackground>
      <header className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-4 sm:px-8">
        <Logo to="/" />
        <Link to="/" className="inline-flex min-h-9 items-center gap-1 text-sm font-medium text-ink-2 hover:text-ink">
          <ArrowLeft aria-hidden="true" className="size-4" /> Volver
        </Link>
      </header>
      <main className="flex flex-1 flex-col items-center justify-center gap-6 px-4 py-10">
        <AuthCard loading={loading} onSignIn={signIn} onGoogle={signIn} onSignUp={() => navigate("/profile")} />
        <LocalProcessing />
      </main>
    </GlowBackground>
  )
}
