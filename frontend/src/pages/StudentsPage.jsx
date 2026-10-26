import { useEffect, useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { MapPin, SearchX, Send, Users } from "lucide-react"
import Avatar from "../components/ui/Avatar"
import Button from "../components/ui/Button"
import SkillChip from "../components/ui/SkillChip"
import PublicProfile from "../components/profile/PublicProfile"
import InviteModal from "../components/invite/InviteModal"
import { EmptyState, ErrorState, Skeleton } from "../components/ui/Feedback"
import { SearchBar } from "../components/search/StudentSearch"
import { obtenerEstudiantes, obtenerProyectos } from "../services/api"
import { availableRoles as usableRoles } from "../lib/contracts"

function getUsuarioActual() {
  try {
    return JSON.parse(localStorage.getItem("usuario") || "{}")
  } catch (error) {
    console.error("No se pudo leer el usuario de la sesión:", error)
    return {}
  }
}

export default function StudentsPage() {
  const usuario = getUsuarioActual()
  const [query, setQuery] = useState("")
  const [students, setStudents] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [loadingStudents, setLoadingStudents] = useState(true)
  const [studentsError, setStudentsError] = useState(false)
  const [studentsAttempt, setStudentsAttempt] = useState(0)
  const [projects, setProjects] = useState([])
  const [loadingProjects, setLoadingProjects] = useState(true)
  const [projectsError, setProjectsError] = useState(false)
  const [projectId, setProjectId] = useState("")
  const [roleId, setRoleId] = useState("")
  const [inviteOpen, setInviteOpen] = useState(false)

  useEffect(() => {
    let active = true
    const timer = setTimeout(() => {
      setLoadingStudents(true)
      obtenerEstudiantes({ q: query, excludeId: usuario.id_usuario })
        .then((results) => {
          if (!active) return
          setStudents(results)
          setSelectedId((previous) =>
            results.some((student) => student.id === previous) ? previous : results[0]?.id ?? null,
          )
          setStudentsError(false)
        })
        .catch((error) => {
          console.error("No se pudieron cargar los perfiles:", error)
          if (active) setStudentsError(true)
        })
        .finally(() => active && setLoadingStudents(false))
    }, 200)

    return () => {
      active = false
      clearTimeout(timer)
    }
  }, [query, usuario.id_usuario, studentsAttempt])

  useEffect(() => {
    let active = true
    obtenerProyectos()
      .then((allProjects) => {
        if (!active) return
        const ownProjects = allProjects.filter(
          (project) => String(project.creadorId) === String(usuario.id_usuario),
        )
        setProjects(ownProjects)
        setProjectId((current) =>
          ownProjects.some((project) => project.id === current) ? current : ownProjects[0]?.id ?? "",
        )
        setProjectsError(false)
      })
      .catch((error) => {
        console.error("No se pudieron cargar tus eventos:", error)
        if (active) setProjectsError(true)
      })
      .finally(() => active && setLoadingProjects(false))
    return () => {
      active = false
    }
  }, [usuario.id_usuario])

  const selectedStudent = students.find((student) => student.id === selectedId)
  const selectedProject = projects.find((project) => project.id === projectId)
  const availableRoles = useMemo(() => {
    if (!selectedProject) return []
    return usableRoles(selectedProject)
  }, [selectedProject])
  const selectedRole = availableRoles.find((role) => role.id === roleId) ?? availableRoles[0]

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-8 sm:py-10">
      <header className="mb-6">
        <p className="text-label font-semibold tracking-[0.16em] text-primary uppercase">Comunidad</p>
        <h1 className="mt-1 text-h1 font-bold">Encuentra personas para tu equipo</h1>
        <p className="mt-1 text-ink-2">Explora perfiles de estudiantes y descubre quién puede complementar tu proyecto.</p>
      </header>

      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <section aria-label="Directorio de estudiantes">
          <div className="mb-4 flex items-center justify-between gap-3">
            <h2 className="text-h3 font-semibold">Estudiantes registrados</h2>
            {!loadingStudents && !studentsError && (
              <span className="text-sm text-ink-2">{students.length} perfiles</span>
            )}
          </div>
          <div className="mb-4">
            <SearchBar value={query} onChange={setQuery} placeholder="Nombre, carrera o habilidad confirmada visible" />
          </div>

          {loadingStudents ? (
            <div className="space-y-3" aria-busy="true">
              {[0, 1, 2].map((item) => <Skeleton key={item} className="h-36 rounded-2xl" />)}
            </div>
          ) : studentsError ? (
            <ErrorState
              message="No pudimos cargar los perfiles. Comprueba la conexión e inténtalo de nuevo."
              onRetry={() => setStudentsAttempt((attempt) => attempt + 1)}
            />
          ) : students.length === 0 ? (
            <EmptyState icon={SearchX} title="No encontramos estudiantes">
              Prueba con otro nombre, carrera o habilidad confirmada visible.
            </EmptyState>
          ) : (
            <ul className="space-y-3">
              {students.map((student) => {
                const active = student.id === selectedId
                return (
                  <li key={student.id}>
                    <button
                      type="button"
                      onClick={() => setSelectedId(student.id)}
                      aria-pressed={active}
                      className={`w-full cursor-pointer rounded-2xl border bg-surface p-4 text-left shadow-card transition-colors hover:border-primary/60 ${
                        active ? "border-primary ring-2 ring-primary/10" : "border-line"
                      }`}
                    >
                      <span className="flex items-start gap-3">
                        <Avatar name={student.nombre} size="md" />
                        <span className="min-w-0 flex-1">
                          <span className="block truncate font-semibold text-ink">{student.nombre}</span>
                          <span className="mt-0.5 block truncate text-sm text-ink-2">{student.carrera || "Carrera no especificada"}</span>
                          {(student.municipio || student.estado_geografico) && (
                            <span className="mt-1 flex items-center gap-1 text-xs text-ink-2">
                              <MapPin aria-hidden="true" className="size-3.5" />
                              {[student.municipio, student.estado_geografico].filter(Boolean).join(", ")}
                            </span>
                          )}
                        </span>
                      </span>
                      {student.fortalezas.length > 0 ? (
                        <span className="mt-3 flex flex-wrap gap-1.5">
                          {student.fortalezas.slice(0, 4).map((skill) => (
                            <SkillChip key={skill.nombre}>{skill.nombre}</SkillChip>
                          ))}
                          {student.fortalezas.length > 4 && (
                            <span className="self-center text-xs text-ink-2">+{student.fortalezas.length - 4}</span>
                          )}
                        </span>
                      ) : (
                        <span className="mt-3 block text-xs text-ink-2">Aún no agrega fortalezas a su perfil.</span>
                      )}
                    </button>
                  </li>
                )
              })}
            </ul>
          )}
        </section>

        <section className="lg:sticky lg:top-6" aria-label="Perfil seleccionado">
          {selectedStudent ? (
            <>
              <PublicProfile student={selectedStudent} />
              <div className="mt-4 flex flex-col gap-3 rounded-2xl border border-line bg-surface p-4 sm:flex-row sm:items-end">
                <div className="min-w-0 flex-1 space-y-3">
                  <label className="block text-sm font-semibold" htmlFor="invite-project">
                    Invitar a uno de tus eventos
                  </label>
                  {projectsError ? (
                    <p role="alert" className="text-sm text-danger">No pudimos cargar tus eventos.</p>
                  ) : loadingProjects ? (
                    <Skeleton className="h-11 w-full" />
                  ) : projects.length === 0 ? (
                    <div>
                      <p className="text-sm text-ink-2">Primero crea un evento para poder enviar una invitación.</p>
                      <Button variant="secondary" as={Link} to="/proyectos/nuevo" className="mt-2">
                        Crear evento
                      </Button>
                    </div>
                  ) : (
                    <>
                      <select
                        id="invite-project"
                        value={projectId}
                        onChange={(event) => {
                          setProjectId(event.target.value)
                          setRoleId("")
                        }}
                        className="min-h-11 w-full rounded-lg border border-line bg-surface px-3 text-sm text-ink"
                      >
                        {projects.map((project) => <option key={project.id} value={project.id}>{project.titulo}</option>)}
                      </select>
                      {availableRoles.length > 0 && (
                        <select
                          aria-label="Rol propuesto"
                          value={selectedRole?.id ?? ""}
                          onChange={(event) => setRoleId(event.target.value)}
                          className="min-h-11 w-full rounded-lg border border-line bg-surface px-3 text-sm text-ink"
                        >
                          {availableRoles.map((role) => <option key={role.id} value={role.id}>{role.nombre}</option>)}
                        </select>
                      )}
                    </>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button
                    onClick={() => setInviteOpen(true)}
                    disabled={loadingProjects || !selectedRole || projectsError}
                  >
                    <Send aria-hidden="true" className="size-4" /> Invitar
                  </Button>
                  {selectedProject && !selectedRole && <p role="status" className="text-sm text-ink-2">{selectedProject.motivo_no_disponible || "No hay vacantes utilizables."}</p>}
                  <Button variant="secondary" as={Link} to={`/perfil/${selectedStudent.id}`}>
                    Ver perfil completo
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <EmptyState icon={Users} title="Selecciona un perfil">
              Elige una persona del directorio para ver su perfil completo.
            </EmptyState>
          )}
        </section>
      </div>

      <InviteModal
        open={inviteOpen}
        onClose={() => setInviteOpen(false)}
        student={selectedStudent}
        project={selectedProject}
        rol={selectedRole ?? { id: "participante", nombre: "Participante" }}
      />
    </div>
  )
}
