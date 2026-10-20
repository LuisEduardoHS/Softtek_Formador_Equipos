/**
 * Capa de servicios.
 *
 * Por ahora todas las funciones devuelven datos simulados con una latencia
 * artificial. Cada una indica con `TODO(backend)` el endpoint sugerido de
 * FastAPI que debe reemplazarla. Para conectar el backend:
 *   1. Define VITE_API_URL en .env (p. ej. http://localhost:8000)
 *   2. Sustituye el cuerpo simulado por `return request("/ruta", {...})`
 */
import {
  currentUser,
  invitations,
  projectSuggestions,
  projects,
  recommendations,
  students,
  teams,
} from "../data/mockData"

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000"

// Cliente HTTP listo para usarse cuando exista el backend.
// eslint-disable-next-line no-unused-vars
async function request(path, { method = "GET", body } = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) throw new Error(`Error ${res.status} en ${path}`)
  return res.json()
}

// Simulación: latencia y, para la demo, fallos forzados con ?estado=error
const delay = (ms = 600) => new Promise((r) => setTimeout(r, ms))
const demoState = () => new URLSearchParams(window.location.search).get("estado")
async function mock(data, ms) {
  await delay(ms)
  if (demoState() === "error") throw new Error("No pudimos conectar con el servidor.")
  return structuredClone(data)
}

/* ---------------------------- Perfil ---------------------------- */

export function obtenerPerfil() {
  // TODO(backend): GET /perfil/me
  return mock(currentUser, 400)
}

/**
 * Envía los textos libres del onboarding y devuelve el perfil estructurado.
 * TODO(backend): POST /ia/interpretar-perfil  { fortalezas, reforzar, intereses }
 *   → Llama + embeddings Nomic → { fortalezas:[{nombre,nivel}], reforzar:[], intereses:[] }
 */
export function interpretarPerfil(textos) {
  void textos
  return mock(
    {
      fortalezas: currentUser.fortalezas,
      reforzar: currentUser.reforzar,
      intereses: currentUser.intereses,
    },
    2200,
  )
}

/* --------------------------- Proyectos -------------------------- */

export function obtenerProyectos() {
  // TODO(backend): GET /proyectos
  return mock(projects)
}

/** TODO(backend): GET /proyectos/{id} */
export async function obtenerProyecto(id) {
  const project = projects.find((p) => p.id === id)
  const data = await mock(project ?? null, 600)
  if (!data) throw Object.assign(new Error("Proyecto no encontrado"), { status: 404 })
  return data
}

/** TODO(backend): POST /proyectos/{id}/solicitudes  { rol_id, mensaje } */
export function solicitarUnirse(projectId, { rolId, mensaje }) {
  return mock({ id: `s${Date.now()}`, projectId, rolId, mensaje, estado: "pendiente" }, 700)
}

/**
 * TODO(backend): POST /ia/interpretar-proyecto  { titulo, descripcion, integrantes }
 *   → { roles: [{ nombre, habilidades[], indispensable }] }
 */
export function interpretarProyecto(proyecto) {
  void proyecto
  return mock(
    {
      roles: [
        { nombre: "Programación backend", habilidades: ["Backend", "Bases de datos"], indispensable: true },
        { nombre: "Diseño de interfaces", habilidades: ["Diseño de interfaces", "Figma"], indispensable: true },
        { nombre: "Bases de datos", habilidades: ["SQL", "Modelado de datos"], indispensable: false },
        { nombre: "Gestión de proyectos", habilidades: ["Gestión de proyectos", "Scrum"], indispensable: false },
      ],
    },
    2000,
  )
}

/* ------------------------ Recomendaciones ----------------------- */

/**
 * TODO(backend): GET /recomendaciones?proyecto_id=
 *   → compañeros y proyectos sugeridos con { nivel, aporta, bloquesComunes, porQue }
 * Con ?estado=vacio se simula el arranque en frío (sin recomendaciones).
 */
export function obtenerRecomendaciones() {
  const vacio = demoState() === "vacio"
  return mock(
    {
      companeros: vacio ? [] : recommendations,
      proyectos: vacio ? [] : projectSuggestions,
    },
    900,
  )
}

/**
 * Candidatos para los roles pendientes de un proyecto propio.
 * TODO(backend): GET /proyectos/{id}/candidatos
 */
export function obtenerCandidatos(projectId) {
  return mock(demoState() === "vacio" ? [] : recommendations.filter((r) => r.projectId === projectId), 1100)
}

/** TODO(backend): POST /recomendaciones/{id}/retroalimentacion  { util: bool, motivo? } */
export function enviarRetroalimentacion(recomendacionId, datos) {
  void recomendacionId, datos
  return mock({ ok: true }, 250)
}

/* ------------------------- Invitaciones ------------------------- */

export function obtenerInvitaciones() {
  // TODO(backend): GET /invitaciones
  return mock(demoState() === "vacio" ? [] : invitations, 700)
}

/** TODO(backend): POST /invitaciones  { para_id, proyecto_id, rol, mensaje } */
export function enviarInvitacion({ paraId, projectId, rol, mensaje }) {
  return mock({ id: `i${Date.now()}`, tipo: "enviada", deId: currentUser.id, paraId, projectId, rol, mensaje, estado: "pendiente" }, 700)
}

/** TODO(backend): PATCH /invitaciones/{id}  { estado: "aceptada" | "rechazada" } */
export function responderInvitacion(id, estado) {
  return mock({ id, estado }, 500)
}

/* ---------------------------- Equipos --------------------------- */

export function obtenerEquipos() {
  // TODO(backend): GET /equipos/mios
  return mock(demoState() === "vacio" ? [] : teams, 800)
}

/* ---------------------------- Búsqueda -------------------------- */

/** TODO(backend): GET /estudiantes?q=&carrera=&habilidad=&disponibilidad=&semestre= */
export function buscarEstudiantes({ q = "", carrera, habilidad, disponibilidad, semestre } = {}) {
  const t = q.trim().toLowerCase()
  const res = students.filter(
    (s) =>
      (!t || s.nombre.toLowerCase().includes(t) || s.fortalezas.some((f) => f.nombre.toLowerCase().includes(t))) &&
      (!carrera || s.carrera === carrera) &&
      (!habilidad || s.fortalezas.some((f) => f.nombre === habilidad)) &&
      (!disponibilidad || s.disponibilidad.some((b) => b.endsWith(disponibilidad))) &&
      (!semestre || s.semestre === Number(semestre)),
  )
  return mock(res, 450)
}
