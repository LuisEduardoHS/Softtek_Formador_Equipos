import { useEffect, useState } from "react"
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom"
import { Bell, FolderKanban, Home, LogOut, Menu, Plus, UserRound, Users, UsersRound, X } from "lucide-react"
import Avatar from "../ui/Avatar"
import Button from "../ui/Button"
import { getSessionUser } from "../../lib/session"
import HomeInvitationInbox from "./InvitationInboxButton"

const NAV = [
  { to: "/inicio", label: "Inicio", icon: Home },
  { to: "/proyectos", label: "Proyectos", icon: FolderKanban },
  { to: "/estudiantes", label: "Estudiantes", short: "Personas", icon: UsersRound },
  { to: "/equipos", label: "Mis equipos", short: "Equipos", icon: Users },
  { to: "/notificaciones", label: "Notificaciones", short: "Avisos", icon: Bell },
  { to: "/perfil", label: "Perfil", icon: UserRound },
]

export function Logo({ to = "/inicio", className = "" }) {
  return (
    <Link to={to} className={`flex items-center gap-2 font-bold text-ink ${className}`}>
      <span aria-hidden="true" className="grid size-8 place-items-center rounded-lg bg-ink text-canvas">
        {/* Dos piezas distintas que encajan: la idea de complementariedad */}
        <svg viewBox="0 0 20 20" className="size-4" fill="currentColor">
          <path d="M3 3h7v7H3z" opacity=".55" />
          <path d="M10 10h7v7h-7zM10 3h7v7h-7z" />
        </svg>
      </span>
      Complementa
    </Link>
  )
}

export default function AppLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)
  const usuario = getSessionUser()
  const nombre = usuario.nombre || "Usuario"
  const detalle = usuario.carrera || usuario.correo || ""

  useEffect(() => {
    if (!menuOpen) return undefined
    const closeOnEscape = (event) => {
      if (event.key === "Escape") setMenuOpen(false)
    }
    window.addEventListener("keydown", closeOnEscape)
    return () => window.removeEventListener("keydown", closeOnEscape)
  }, [menuOpen])

  function cerrarSesion() {
    sessionStorage.removeItem("access_token")
    sessionStorage.removeItem("usuario")
    navigate("/", { replace: true })
  }

  return (
    <div className="min-h-dvh">
      <a href="#contenido" className="sr-only z-50 rounded-lg bg-primary px-4 py-2 text-white focus:not-sr-only focus:fixed focus:top-3 focus:left-3">
        Saltar al contenido
      </a>

      <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-line bg-surface/90 px-4 backdrop-blur">
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setMenuOpen((open) => !open)}
            aria-label={menuOpen ? "Cerrar menú" : "Abrir menú"}
            aria-expanded={menuOpen}
            aria-controls="navigation-drawer"
            className="px-2"
          >
            <Menu aria-hidden="true" className="size-5" />
          </Button>
          <Logo />
        </div>
        <div className="flex items-center gap-2">
          {location.pathname === "/inicio" && <HomeInvitationInbox />}
          <Link to="/perfil" aria-label="Mi perfil" className="rounded-full">
            <Avatar name={nombre} size="sm" />
          </Link>
        </div>
      </header>

      {menuOpen && (
        <>
          <button
            type="button"
            aria-label="Cerrar menú"
            onClick={() => setMenuOpen(false)}
            className="fixed inset-0 z-40 cursor-default bg-ink/40"
          />
          <aside
            id="navigation-drawer"
            aria-label="Menú principal"
            className="fixed inset-y-0 left-0 z-50 flex w-[min(20rem,85vw)] flex-col gap-6 overflow-y-auto border-r border-line bg-surface px-4 py-6 pb-24 shadow-pop"
          >
            <div className="flex items-center justify-between px-2">
              <Logo />
              <Button variant="ghost" size="sm" onClick={() => setMenuOpen(false)} aria-label="Cerrar menú">
                <X aria-hidden="true" className="size-5" />
              </Button>
            </div>
            <Link
              to="/proyectos/nuevo"
              onClick={() => setMenuOpen(false)}
              className="flex min-h-11 items-center justify-center gap-2 rounded-lg bg-primary px-4 text-sm font-semibold text-white shadow-card transition-all hover:bg-primary-hover active:scale-[0.98]"
            >
              <Plus aria-hidden="true" className="size-4" /> Crear proyecto
            </Link>
            <nav aria-label="Principal">
              <ul className="space-y-1">
                {NAV.map(({ to, label, icon: Icon }) => (
                  <li key={to}>
                    <NavLink
                      to={to}
                      onClick={() => setMenuOpen(false)}
                      className={({ isActive }) =>
                        `flex min-h-11 items-center gap-3 rounded-lg px-3 text-sm font-medium transition-colors ${
                          isActive ? "bg-surface-2 text-ink" : "text-ink-2 hover:bg-surface-2/70 hover:text-ink"
                        }`
                      }
                    >
                      {({ isActive }) => (
                        <>
                          <Icon aria-hidden="true" className={`size-5 ${isActive ? "text-primary" : ""}`} />
                          <span className="flex-1">{label}</span>
                        </>
                      )}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </nav>
            <Link
              to="/perfil"
              onClick={() => setMenuOpen(false)}
              className="mt-auto flex items-center gap-3 rounded-xl border border-line p-3 transition-colors hover:bg-surface-2"
            >
              <Avatar name={nombre} size="sm" />
              <span className="min-w-0">
                <span className="block truncate text-sm font-semibold text-ink">{nombre}</span>
                {detalle && <span className="block truncate text-xs text-ink-2">{detalle}</span>}
              </span>
            </Link>
            <Button variant="ghost" onClick={cerrarSesion} className="w-full justify-start">
              <LogOut aria-hidden="true" className="size-4" />
              Cerrar sesión
            </Button>
          </aside>
        </>
      )}

      <main id="contenido" className="min-w-0 pb-28 lg:pb-0">
        <Outlet />
      </main>

      {/* Barra inferior (móvil) */}
      <nav
        aria-label="Principal"
        className="fixed inset-x-0 bottom-0 z-30 border-t border-line bg-surface/95 pb-[env(safe-area-inset-bottom)] backdrop-blur lg:hidden"
      >
        <ul className="mx-auto grid max-w-md grid-cols-5 px-1">
          {NAV.slice(0, 2).map((item) => (
            <BottomItem key={item.to} {...item} />
          ))}
          <li className="grid place-items-center">
            <Link
              to="/proyectos/nuevo"
              aria-label="Crear proyecto"
              className="-mt-6 grid size-14 place-items-center rounded-full bg-primary text-white shadow-pop transition-transform active:scale-95"
            >
              <Plus aria-hidden="true" className="size-6" />
            </Link>
          </li>
          {[NAV[2], NAV[4]].map((item) => (
            <BottomItem key={item.to} {...item} />
          ))}
        </ul>
      </nav>
    </div>
  )
}

function BottomItem({ to, label, short, icon: Icon }) {
  return (
    <li>
      <NavLink
        to={to}
        className={({ isActive }) =>
          `relative flex min-h-14 flex-col items-center justify-center gap-0.5 text-[11px] font-medium transition-colors ${
            isActive ? "text-primary" : "text-ink-2"
          }`
        }
      >
        <span className="relative">
          <Icon aria-hidden="true" className="size-5" />
        </span>
        {short ?? label}
      </NavLink>
    </li>
  )
}
