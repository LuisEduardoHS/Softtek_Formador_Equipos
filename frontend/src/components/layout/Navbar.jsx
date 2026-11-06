import { useState } from "react"
import { Link } from "react-router-dom"
import Button from "../ui/Button"
import { Logo } from "./AppLayout"

const LINKS = [
  ["#como-funciona", "Cómo funciona"],
  ["#estudiantes", "Estudiantes"],
  ["#por-que", "Por qué complementar"],
  ["#para-quien", "Para quién es"],
]

/** Barra superior de la landing. En móvil, el menú de dos líneas abre los enlaces. */
export default function Navbar({ onGetStarted }) {
  const [open, setOpen] = useState(false)

  return (
    <header className="sticky top-0 z-30 animate-fade-in border-b border-line/70 bg-canvas/75 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-8">
        <Logo to="/" />

        <nav aria-label="Secciones" className="hidden items-center gap-6 text-sm font-medium text-ink-2 lg:flex">
          {LINKS.map(([href, label]) => (
            <a key={href} href={href} className="relative py-1 transition-colors after:absolute after:inset-x-0 after:-bottom-0.5 after:h-0.5 after:origin-left after:scale-x-0 after:rounded-full after:bg-linear-to-r after:from-primary after:to-accent after:transition-transform after:duration-300 hover:text-ink hover:after:scale-x-100">
              {label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <Button variant="ghost" as={Link} to="/auth" className="max-sm:hidden">
            Iniciar sesión
          </Button>
          <Button onClick={onGetStarted}>Crear mi perfil</Button>
          <button
            type="button"
            onClick={() => setOpen((o) => !o)}
            aria-expanded={open}
            aria-controls="menu-movil"
            aria-label={open ? "Cerrar menú" : "Abrir menú"}
            className="grid size-11 cursor-pointer place-items-center rounded-lg hover:bg-surface-2 lg:hidden"
          >
            <span className="flex w-5 flex-col gap-1.5" aria-hidden="true">
              <span className={`h-0.5 w-full rounded bg-ink transition-transform duration-200 ${open ? "translate-y-1 rotate-45" : ""}`} />
              <span className={`h-0.5 w-full rounded bg-ink transition-transform duration-200 ${open ? "-translate-y-1 -rotate-45" : ""}`} />
            </span>
          </button>
        </div>
      </div>

      {open && (
        <nav id="menu-movil" aria-label="Secciones" className="animate-fade-up border-t border-line bg-surface px-4 py-2 lg:hidden">
          <ul>
            {LINKS.map(([href, label]) => (
              <li key={href}>
                <a href={href} onClick={() => setOpen(false)} className="flex min-h-11 items-center text-sm font-medium text-ink">
                  {label}
                </a>
              </li>
            ))}
            <li className="sm:hidden">
              <Link to="/auth" className="flex min-h-11 items-center text-sm font-semibold text-primary">
                Iniciar sesión
              </Link>
            </li>
          </ul>
        </nav>
      )}
    </header>
  )
}
