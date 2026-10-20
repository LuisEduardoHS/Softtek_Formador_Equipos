import { Link, NavLink, Outlet } from "react-router-dom"
import { Bell, FolderKanban, Home, Plus, UserRound, Users } from "lucide-react"
import Avatar from "../ui/Avatar"
import { notifications } from "../../data/mockData"

const NAV = [
  { to: "/inicio", label: "Inicio", icon: Home },
  { to: "/proyectos", label: "Proyectos", icon: FolderKanban },
  { to: "/equipos", label: "Mis equipos", short: "Equipos", icon: Users },
  { to: "/notificaciones", label: "Notificaciones", short: "Avisos", icon: Bell, badge: true },
  { to: "/perfil", label: "Perfil", icon: UserRound },
]

const unread = notifications.filter((n) => !n.leida).length

function getSessionUser() {
  try {
    return JSON.parse(localStorage.getItem("usuario") || "{}")
  } catch (error) {
    console.error("No se pudo leer el usuario de la sesión:", error)
    return {}
  }
}

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

function Badge({ count }) {
  if (!count) return null
  return (
    <span className="grid h-5 min-w-5 place-items-center rounded-full bg-primary px-1 text-[11px] font-bold text-white">
      {count}
      <span className="sr-only"> sin leer</span>
    </span>
  )
}

export default function AppLayout() {
  const usuario = getSessionUser()
  const nombre = usuario.nombre || "Usuario"
  const detalle = usuario.carrera || usuario.correo || ""

  return (
    <div className="min-h-dvh lg:grid lg:grid-cols-[260px_1fr]">
      <a href="#contenido" className="sr-only z-50 rounded-lg bg-primary px-4 py-2 text-white focus:not-sr-only focus:fixed focus:top-3 focus:left-3">
        Saltar al contenido
      </a>

      {/* Barra lateral (escritorio) */}
      <aside className="sticky top-0 hidden h-dvh flex-col gap-6 border-r border-line bg-surface px-4 py-6 lg:flex">
        <Logo className="px-2" />
        <Link
          to="/proyectos/nuevo"
          className="flex min-h-11 items-center justify-center gap-2 rounded-lg bg-primary px-4 text-sm font-semibold text-white shadow-card transition-all hover:bg-primary-hover active:scale-[0.98]"
        >
          <Plus aria-hidden="true" className="size-4" /> Crear proyecto
        </Link>
        <nav aria-label="Principal">
          <ul className="space-y-1">
            {NAV.map(({ to, label, icon: Icon, badge }) => (
              <li key={to}>
                <NavLink
                  to={to}
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
                      {badge && <Badge count={unread} />}
                    </>
                  )}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
        <Link
          to="/perfil"
          className="mt-auto flex items-center gap-3 rounded-xl border border-line p-3 transition-colors hover:bg-surface-2"
        >
          <Avatar name={nombre} size="sm" />
          <span className="min-w-0">
            <span className="block truncate text-sm font-semibold text-ink">{nombre}</span>
            {detalle && <span className="block truncate text-xs text-ink-2">{detalle}</span>}
          </span>
        </Link>
      </aside>

      {/* Encabezado (móvil) */}
      <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-line bg-surface/90 px-4 backdrop-blur lg:hidden">
        <Logo />
        <Link to="/perfil" aria-label="Mi perfil" className="rounded-full">
          <Avatar name={nombre} size="sm" />
        </Link>
      </header>

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
          {NAV.slice(2, 4).map((item) => (
            <BottomItem key={item.to} {...item} />
          ))}
        </ul>
      </nav>
    </div>
  )
}

function BottomItem({ to, label, short, icon: Icon, badge }) {
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
          {badge && unread > 0 && (
            <span className="absolute -top-1.5 -right-2.5 grid h-4 min-w-4 place-items-center rounded-full bg-primary px-1 text-[10px] font-bold text-white ring-2 ring-surface">
              {unread}
            </span>
          )}
        </span>
        {short ?? label}
      </NavLink>
    </li>
  )
}
