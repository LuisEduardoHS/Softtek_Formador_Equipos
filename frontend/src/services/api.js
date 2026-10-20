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

/* ---------------------------- Autenticación ---------------------------- */

export function registrarUsuario({ nombre, correo, carrera, estado_geografico, municipio, password }) {
  return request("/auth/registro", {
    method: "POST",
    body: {
      nombre,
      correo,
      carrera,
      estado_geografico,
      municipio,
      password,
    },
  })
}

export function iniciarSesion({ correo, password }) {
  return request("/auth/login", {
    method: "POST",
    body: { correo, password },
  })
}

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

function mapEventoAProyecto(evento) {
  const detalles = evento.detalles_especificos ?? {}
  const requisitos = evento.requisitos_ia ?? {}
  const rolesEvento = Array.isArray(detalles.roles)
    ? detalles.roles
    : Array.isArray(requisitos.roles)
      ? requisitos.roles
      : []

  return {
    id: String(evento.id_evento),
    titulo: evento.titulo,
    descripcion: evento.descripcion_libre ?? "",
    tipo: detalles.tipo === "personal" || evento.categoria_principal?.toLowerCase() === "personal" ? "personal" : "academico",
    materia: detalles.materia ?? "",
    creadorId: String(evento.creador_id),
    integrantes: Number(detalles.integrantes) || 1,
    fechaLimite: detalles.fechaLimite || null,
    creado: evento.fecha_creacion?.slice(0, 10) ?? "",
    estado: evento.estado,
    roles: rolesEvento.map((rol, index) => ({
      id: String(rol.id ?? index),
      nombre: typeof rol.nombre === "string" ? rol.nombre : "Rol sin nombre",
      habilidades: Array.isArray(rol.habilidades) ? rol.habilidades : [],
      indispensable: Boolean(rol.indispensable),
      cubiertoPor: rol.cubiertoPor ?? null,
    })),
  }
}

export function obtenerProyectos() {
  return request("/eventos/").then((eventos) => eventos.map(mapEventoAProyecto))
}

export function crearProyecto({ titulo, descripcion, tipo, materia, integrantes, fechaLimite, roles }) {
  const usuarioLocal = JSON.parse(localStorage.getItem("usuario") || "{}")
  const creadorId = Number(usuarioLocal.id_usuario)
  if (!Number.isInteger(creadorId) || creadorId <= 0) {
    throw new Error("Inicia sesión para poder publicar un proyecto.")
  }

  return request("/eventos/", {
    method: "POST",
    body: {
      creador_id: creadorId,
      titulo,
      categoria_principal: tipo === "personal" ? "Personal" : "Academico",
      descripcion_libre: descripcion,
      detalles_especificos: {
        tipo,
        materia,
        integrantes,
        fechaLimite: fechaLimite || null,
        roles,
      },
      requisitos_ia: { roles },
    },
  }).then(mapEventoAProyecto)
}

export async function obtenerProyecto(id) {
  return request(`/eventos/${id}`).then(mapEventoAProyecto)
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