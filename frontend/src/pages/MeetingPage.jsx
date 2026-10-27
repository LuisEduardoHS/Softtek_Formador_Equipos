import { Link } from "react-router-dom"
import Card from "../components/ui/Card"
import Button from "../components/ui/Button"

export default function MeetingPage() {
  return <div className="mx-auto max-w-lg px-4 py-12">
    <Card className="space-y-4 p-6">
      <h1 className="text-h2 font-bold">Reuniones no disponibles</h1>
      <p role="status" className="text-ink-2">La programación de reuniones no forma parte de este MVP. No se envían ni se guardan propuestas desde esta página.</p>
      <Button as={Link} to="/equipos" variant="secondary">Ver mis equipos</Button>
    </Card>
  </div>
}
