/**
 * Capa de servicios conectada a FastAPI (MySQL).
 */

const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000"

// Cliente HTTP conectado a tu backend local
async function request(path, { method = "GET", body } = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  })
  
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Error ${res.status} en ${path}`);
  }
  return res.json();
}

// ============================================================================
// RUTAS CONECTADAS (Ya funcionan en FastAPI con MySQL)
// ============================================================================

/* ---------------------------- Perfil ---------------------------- */

export async function obtenerPerfil() {
  // Leemos el usuario activo del LocalStorage que se guardó en el Login
  const usuarioLocal = JSON.parse(localStorage.getItem("usuario") || "{}");
  if (!usuarioLocal.id_usuario) {
    throw new Error("No hay usuario autenticado.");
  }
  // Llamamos a tu endpoint existente GET /perfil/{id}
  return request(`/perfil/${usuarioLocal.id_usuario}`);
}

/* --------------------------- Proyectos -------------------------- */

export function obtenerProyectos() {
  // Llama a tu endpoint existente GET /eventos/
  return request("/eventos/");
}

export async function obtenerProyecto(id) {
  // Llama a tu endpoint existente GET /eventos/{id} (Asegúrate de crearlo en auth.py si no lo tienes)
  return request(`/eventos/${id}`);
}

// ============================================================================
// RUTAS PENDIENTES DE DESARROLLAR EN FASTAPI
// (Mantenemos retornos vacíos o estructurados para que no truene React)
// ============================================================================

export function interpretarPerfil(textos) {
  // TODO(backend): POST /ia/interpretar-perfil
  return Promise.resolve({ fortalezas: [], reforzar: [], intereses: [] });
}

export function solicitarUnirse(projectId, { rolId, mensaje }) {
  // TODO(backend): POST /proyectos/{id}/solicitudes
  return Promise.resolve({ id: `s${Date.now()}`, estado: "pendiente" });
}

export function interpretarProyecto(proyecto) {
  // TODO(backend): POST /ia/interpretar-proyecto
  return Promise.resolve({ roles: [] });
}

export function obtenerRecomendaciones() {
  // TODO(backend): GET /recomendaciones (Requiere FastAPI + Ollama)
  return Promise.resolve({ companeros: [], proyectos: [] });
}

export function obtenerCandidatos(projectId) {
  // TODO(backend): GET /proyectos/{id}/candidatos
  return Promise.resolve([]);
}

export function enviarRetroalimentacion(recomendacionId, datos) {
  // TODO(backend): POST /recomendaciones/{id}/retroalimentacion
  return Promise.resolve({ ok: true });
}

export function obtenerInvitaciones() {
  // TODO(backend): GET /invitaciones
  return Promise.resolve([]);
}

export function enviarInvitacion({ paraId, projectId, rol, mensaje }) {
  // TODO(backend): POST /invitaciones
  return Promise.resolve({ id: `i${Date.now()}`, estado: "pendiente" });
}

export function responderInvitacion(id, estado) {
  // TODO(backend): PATCH /invitaciones/{id}
  return Promise.resolve({ id, estado });
}

export function obtenerEquipos() {
  // TODO(backend): GET /equipos/mios
  return Promise.resolve([]);
}

export function buscarEstudiantes({ q = "", carrera, habilidad, disponibilidad, semestre } = {}) {
  // TODO(backend): GET /estudiantes?q=...
  return Promise.resolve([]);
}