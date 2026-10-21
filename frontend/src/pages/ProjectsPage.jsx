import { useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { FolderOpen, Plus, SearchX } from "lucide-react"
import Button from "../components/ui/Button"
import { Segmented, Tabs } from "../components/ui/Controls"
import { EmptyState, ErrorState, Skeleton } from "../components/ui/Feedback"
import ProjectCard from "../components/project/ProjectCard"
import { SearchBar } from "../components/search/StudentSearch"
import useAsync from "../hooks/useAsync"
import { obtenerProyectos } from "../services/api"

export default function ProjectsPage() {
  const { status, data, reload } = useAsync(obtenerProyectos)
  const usuarioLocal = JSON.parse(localStorage.getItem("usuario") || "{}")
  const [tab, setTab] = useState("explorar")
  const [q, setQ] = useState("")
  const [tipo, setTipo] = useState("todos")
  const [soloAbiertos, setSoloAbiertos] = useState(true)

  const { explorar, mios } = useMemo(() => {
    const all = data ?? []
    const tieneUsuario = usuarioLocal.id_usuario !== undefined && usuarioLocal.id_usuario !== null
    const esMio = (p) => tieneUsuario && String(p.creadorId) === String(usuarioLocal.id_usuario)
    return { explorar: all.filter((p) => !esMio(p)), mios: all.filter(esMio) }
  }, [data, usuarioLocal.id_usuario])

  const base = tab === "explorar" ? explorar : mios
  const t = q.trim().toLowerCase()
  const list = base.filter(
    (p) =>
      (!t || p.titulo.toLowerCase().includes(t) || p.roles.some((r) => r.nombre.toLowerCase().includes(t))) &&
      (tipo === "todos" || p.tipo === tipo) &&
      (tab === "mios" || !soloAbiertos || p.roles.length === 0 || p.roles.some((r) => !r.cubiertoPor)),
  )

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-8 sm:py-10">
      <header className="mb-6 flex animate-fade-up flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-h1 font-bold">Proyectos</h1>
          <p className="mt-1 text-ink-2">Encuentra un proyecto donde lo que sabes hacer sea justo lo que falta.</p>
        </div>
        <Button as={Link} to="/proyectos/nuevo">
          <Plus aria-hidden="true" className="size-4" /> Crear proyecto
        </Button>
      </header>

      <Tabs
        label="Proyectos"
        value={tab}
        onChange={setTab}
        tabs={[
          { id: "explorar", label: "Explorar", count: data ? explorar.length : undefined },
          { id: "mios", label: "Mis proyectos", count: data ? mios.length : undefined },
        ]}
      />

      <div className="my-5 flex flex-col gap-3 md:flex-row md:items-center">
        <SearchBar value={q} onChange={setQ} placeholder="Buscar por título o rol" label="Buscar proyectos" />
        <div className="flex flex-wrap items-center gap-3">
          <Segmented
            label="Tipo"
            value={tipo}
            onChange={setTipo}
            options={[
              ["todos", "Todos"],
              ["academico", "Académicos"],
              ["personal", "Personales"],
            ]}
          />
          {tab === "explorar" && (
            <label className="flex min-h-11 cursor-pointer items-center gap-2 text-sm text-ink">
              <input type="checkbox" checked={soloAbiertos} onChange={(e) => setSoloAbiertos(e.target.checked)} className="size-4 accent-primary" />
              Con roles abiertos
            </label>
          )}
        </div>
      </div>

      {status === "loading" ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-72 rounded-2xl" />
          ))}
        </div>
      ) : status === "error" ? (
        <ErrorState message="No pudimos cargar los proyectos." onRetry={reload} />
      ) : list.length === 0 ? (
        base.length === 0 && tab === "mios" ? (
          <EmptyState
            icon={FolderOpen}
            title="Todavía no tienes proyectos"
            actions={
              <Button as={Link} to="/proyectos/nuevo">
                <Plus aria-hidden="true" className="size-4" /> Crear proyecto
              </Button>
            }
          >
            Crea uno y te recomendaremos a las personas que lo complementen.
          </EmptyState>
        ) : (
          <EmptyState icon={SearchX} title="No hay proyectos con esos filtros">
            Prueba con otra palabra o quita algún filtro.
          </EmptyState>
        )
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {list.map((p, i) => (
            <li key={p.id} className="animate-fade-up" style={{ animationDelay: `${i * 50}ms` }}>
              <ProjectCard project={p} className="h-full" />
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
