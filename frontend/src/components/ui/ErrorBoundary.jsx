import { Component } from "react"

export default class ErrorBoundary extends Component {
  state = { hasError: false }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error, info) {
    console.error("Error al mostrar esta sección:", error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <main className="grid min-h-dvh place-items-center bg-canvas px-4">
          <section role="alert" className="max-w-md rounded-2xl border border-danger/30 bg-surface p-6 text-center shadow-card">
            <h1 className="text-h2 font-bold text-ink">No pudimos mostrar esta página</h1>
            <p className="mt-2 text-sm text-ink-2">
              Ocurrió un error al cargar la sección. Puedes volver a intentarlo recargando la página.
            </p>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="mt-5 min-h-11 rounded-lg bg-primary px-4 text-sm font-semibold text-white hover:bg-primary-hover"
            >
              Recargar página
            </button>
          </section>
        </main>
      )
    }

    return this.props.children
  }
}
