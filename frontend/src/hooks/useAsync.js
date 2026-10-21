import { useCallback, useEffect, useState } from "react"

/**
 * Ejecuta una función asíncrona del servicio y expone su estado.
 * `fn` debe ser estable (función del módulo de servicios o memorizada).
 */
export default function useAsync(fn) {
  const [state, setState] = useState({ status: "loading", data: null, error: null })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let alive = true
    fn().then(
      (data) => alive && setState({ status: "success", data, error: null }),
      (error) => alive && setState({ status: "error", data: null, error }),
    )
    return () => {
      alive = false
    }
  }, [fn, attempt])

  const reload = useCallback(() => {
    setState({ status: "loading", data: null, error: null })
    setAttempt((n) => n + 1)
  }, [])

  // Permite actualizaciones optimistas sin recargar
  const setData = useCallback((updater) => {
    setState((s) => ({ ...s, data: typeof updater === "function" ? updater(s.data) : updater }))
  }, [])

  return { ...state, loading: state.status === "loading", reload, setData }
}
