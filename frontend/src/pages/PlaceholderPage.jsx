import { Link } from "react-router-dom"
import { Hammer } from "lucide-react"
import Button from "../components/ui/Button"
import { EmptyState } from "../components/ui/Feedback"

// Pantalla temporal mientras se construye cada sección.
export default function PlaceholderPage({ title }) {
  return (
    <div className="mx-auto max-w-3xl px-4 py-10 sm:px-8">
      <h1 className="mb-6 text-h1 font-bold">{title}</h1>
      <EmptyState
        icon={Hammer}
        title="Esta sección está en construcción"
        actions={
          <Button as={Link} to="/inicio" variant="secondary">
            Volver al inicio
          </Button>
        }
      >
        Muy pronto podrás usarla.
      </EmptyState>
    </div>
  )
}
