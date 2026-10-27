import { useEffect, useState } from "react"
import { obtenerPerfil } from "../services/api"

// Failed reads leave comparisons unavailable; never fall back to demo data.
export default function useAuthenticatedProfile(enabled = true) {
  const [profile, setProfile] = useState(null)
  useEffect(() => {
    if (!enabled || !sessionStorage.getItem("access_token")) return
    let active = true
    obtenerPerfil().then((value) => { if (active) setProfile(value) }).catch(() => {})
    return () => { active = false }
  }, [enabled])
  return profile
}
