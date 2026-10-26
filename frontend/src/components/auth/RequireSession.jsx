import { useEffect, useState } from "react"
import { Navigate, Outlet } from "react-router-dom"
import { verificarSesion } from "../../services/api"

export default function RequireSession() {
  const [state, setState] = useState(sessionStorage.getItem("access_token") ? "checking" : "denied")
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    if (state === "denied") return undefined
    let alive = true
    verificarSesion().then(
      (user) => {
        if (!alive) return
        sessionStorage.setItem("usuario", JSON.stringify(user))
        setState("ready")
      },
      (error) => {
        if (!alive) return
        if (error.status === 401 || error.status === 403) {
          sessionStorage.removeItem("access_token")
          sessionStorage.removeItem("usuario")
          setState("denied")
        } else setState("error")
      },
    )
    const expire = () => setState("denied")
    window.addEventListener("session-expired", expire)
    return () => { alive = false; window.removeEventListener("session-expired", expire) }
  }, [attempt])
  if (state === "denied") return <Navigate to="/auth" replace />
  if (state === "checking") return <div role="status" className="p-8 text-center">Verificando sesión…</div>
  if (state === "error") return <div role="alert" className="p-8 text-center">
    No pudimos verificar la sesión. <button type="button" className="underline" onClick={() => {
      setState("checking"); setAttempt((value) => value + 1)
    }}>Reintentar</button>
  </div>
  return <Outlet />
}
