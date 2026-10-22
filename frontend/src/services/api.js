/**
 * Capa de servicios conectada a FastAPI (MySQL).
 */

const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000"
const CATEGORIES = { academico: "Academico", personal: "Personal", deportivo: "Deportivo",
  videojuegos: "Videojuegos", general: "General" }
const toCategory = (tipo) => CATEGORIES[tipo] ?? "General"

// Cliente HTTP conectado a tu backend local
async function request(path, { method = "GET", body } = {}) {
  const token = sessionStorage.getItem("access_token")
  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  })
  
  if (!res.ok) {
    if (res.status === 401 && !path.startsWith("/auth/")) {
      sessionStorage.removeItem("access_token")
      localStorage.removeItem("usuario")
      window.dispatchEvent(new Event("session-expired"))
    }
    const errorData = await res.json().catch(() => ({}));
    const error = new Error(typeof errorData.detail === "string" ? errorData.detail : `Error ${res.status} en ${path}`)
    error.status = res.status
    throw error
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

export function verificarSesion() {
  return request("/auth/me")
}

/* ---------------------------- Perfil ---------------------------- */

export async function obtenerPerfil() {
  const usuarioLocal = JSON.parse(localStorage.getItem("usuario") || "{}");
  if (!usuarioLocal.id_usuario) {
    throw new Error("No hay usuario autenticado.");
  }
  const perfil = await request(`/perfil/${encodeURIComponent(usuarioLocal.id_usuario)}`)
  return mapPerfil(perfil)
}

function mapPerfil(perfil) {
  const datos = perfil.datos_crudos ?? {}
  const fortalezas = Array.isArray(datos.fortalezas)
    ? datos.fortalezas
      .map((fortaleza) =>
        typeof fortaleza === "string" ? { nombre: fortaleza, nivel: null } : fortaleza,
      )
      .filter((fortaleza) => fortaleza && typeof fortaleza.nombre === "string")
    : Array.isArray(datos.habilidades)
      ? datos.habilidades.map((nombre) => ({ nombre, nivel: null }))
      : []

  return {
    ...datos,
    id: String(perfil.usuario_id),
    usuario_id: perfil.usuario_id,
    nombre: perfil.nombre,
    correo: perfil.correo ?? "",
    carrera: perfil.carrera,
    estado_geografico: perfil.estado_geografico ?? "",
    municipio: perfil.municipio ?? "",
    semestre: Number(datos.semestre) || 1,
    fortalezas,
    reforzar: Array.isArray(datos.reforzar) ? datos.reforzar : [],
    intereses: Array.isArray(datos.intereses) ? datos.intereses : [],
    disponibilidad: Array.isArray(datos.disponibilidad) ? datos.disponibilidad : [],
    visibilidad: {
      fortalezas: true,
      intereses: true,
      disponibilidad: true,
      reforzar: false,
      correo: false,
      ...(datos.visibilidad ?? {}),
    },
    pausado: Boolean(datos.pausado),
  }
}

export async function obtenerPerfilUsuario(id) {
  const perfil = await request(`/perfil/publico/${encodeURIComponent(id)}`)
  return mapPerfil(perfil)
}

export async function guardarPerfil(perfil) {
  const usuarioLocal = JSON.parse(localStorage.getItem("usuario") || "{}")
  if (!usuarioLocal.id_usuario) {
    throw new Error("No hay usuario autenticado.")
  }

  const datos_crudos = Object.fromEntries(
    Object.entries(perfil).filter(([key]) =>
      !["id", "usuario_id", "correo", "estado_geografico", "municipio"].includes(key),
    ),
  )
  const actualizado = await request(`/perfil/${usuarioLocal.id_usuario}`, {
    method: "PUT",
    body: {
      nombre: perfil.nombre,
      carrera: perfil.carrera,
      datos_crudos,
    },
  })
  return mapPerfil(actualizado)
}

export async function confirmarPerfil(perfil) {
  const confirmado = await request("/perfil/confirmar", { method: "POST", body: perfil })
  return mapPerfil(confirmado)
}

export function reintentarEmbeddingPerfil() {
  return request("/perfil/embedding/reintentar", { method: "POST" })
}

export async function obtenerEstudiantes({ q = "", excludeId, limit = 100 } = {}) {
  const params = new URLSearchParams({ limit: String(limit) })
  if (q.trim()) params.set("q", q.trim())
  if (excludeId) params.set("exclude_id", String(excludeId))
  const perfiles = await request(`/perfil/estudiantes/?${params.toString()}`)
  return perfiles.map(mapPerfil)
}

/* --------------------------- Proyectos -------------------------- */

function mapEventoAProyecto(evento) {
  const detalles = evento.detalles_especificos ?? {}
  const requisitos = evento.requisitos_ia ?? {}
  const rolesEvento = Array.isArray(detalles.roles)
    ? detalles.roles
    : Array.isArray(requisitos.roles)
      ? requisitos.roles
      : Array.isArray(requisitos.roles_buscados)
        ? requisitos.roles_buscados.map((nombre) => ({ nombre, habilidades: [], indispensable: false }))
        : []

  return {
    id: String(evento.id_evento),
    titulo: evento.titulo,
    descripcion: evento.descripcion_libre ?? "",
    tipo: detalles.tipo || evento.categoria_principal?.toLowerCase() || "academico",
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

export function crearProyecto({ titulo, descripcion, tipo, materia, integrantes, fechaLimite, roles, requirements }) {
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
      categoria_principal: toCategory(tipo),
      descripcion_libre: descripcion,
      detalles_especificos: {
        tipo,
        materia,
        integrantes,
        fechaLimite: fechaLimite || null,
        roles,
      },
      requisitos_confirmados: requirements ? {
        ...requirements,
        categoria: toCategory(tipo),
        roles_buscados: roles.map((r) => r.nombre.trim()).filter(Boolean),
        habilidades_obligatorias: [...new Set([...(requirements.habilidades_obligatorias ?? []),
          ...roles.filter((r) => r.indispensable).flatMap((r) => r.habilidades)])],
        habilidades_deseables: [...new Set([...(requirements.habilidades_deseables ?? []),
          ...roles.filter((r) => !r.indispensable).flatMap((r) => r.habilidades)])],
      } : null,
      confirmado_por_creador: Boolean(requirements),
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
  return request("/perfil/interpretar", { method: "POST", body: {
    fortalezas: textos.fortalezas, reforzar: textos.reforzar, intereses: textos.intereses,
  } })
}

export function solicitarUnirse(projectId, { rolId, mensaje }) {
  // TODO(backend): POST /proyectos/{id}/solicitudes
  return Promise.resolve({ id: `s${Date.now()}`, estado: "pendiente" });
}

export function interpretarProyecto(proyecto) {
  return request("/eventos/interpretar", { method: "POST", body: {
    descripcion_libre: proyecto.descripcion,
    categoria_principal: toCategory(proyecto.tipo),
    detalles_especificos: { titulo: proyecto.titulo, materia: proyecto.materia,
      integrantes: proyecto.integrantes, fechaLimite: proyecto.fechaLimite || null },
  } })
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
  const usuarioLocal = JSON.parse(localStorage.getItem("usuario") || "{}")
  if (!usuarioLocal.id_usuario) {
    throw new Error("No hay usuario autenticado.")
  }
  return request(`/invitaciones/${encodeURIComponent(usuarioLocal.id_usuario)}`)
}

export function obtenerNotificaciones() {
  const usuarioLocal = JSON.parse(localStorage.getItem("usuario") || "{}")
  if (!usuarioLocal.id_usuario) {
    throw new Error("No hay usuario autenticado.")
  }
  return request(`/notificaciones/${encodeURIComponent(usuarioLocal.id_usuario)}`)
}

export function enviarInvitacion({ paraId, projectId, rol, mensaje }) {
  const usuarioLocal = JSON.parse(localStorage.getItem("usuario") || "{}")
  if (!usuarioLocal.id_usuario) {
    throw new Error("No hay usuario autenticado.")
  }
  const body = {
    id_destinatario: Number(paraId),
    id_evento: Number(projectId),
    mensaje_explicacion: `${mensaje}${rol ? `\n\nRol propuesto: ${rol}` : ""}`,
  }
  return request(`/invitaciones/?de_id=${encodeURIComponent(usuarioLocal.id_usuario)}`, {
    method: "POST",
    body,
  })
}

export function responderInvitacion(id, estado) {
  return request(`/invitaciones/${encodeURIComponent(id)}`, {
    method: "PATCH",
    body: { estado },
  })
}

export function obtenerEquipos() {
  const usuarioLocal = JSON.parse(localStorage.getItem("usuario") || "{}")
  if (!usuarioLocal.id_usuario) {
    throw new Error("No hay usuario autenticado.")
  }
  return request(`/equipos/${encodeURIComponent(usuarioLocal.id_usuario)}`).then((equipos) =>
    equipos.map((equipo) => ({
      ...equipo,
      proyecto: mapEventoAProyecto(equipo.proyecto),
      miembros: equipo.miembros.map((miembro) => ({
        ...miembro,
        id: String(miembro.id),
        fortalezas: Array.isArray(miembro.fortalezas) ? miembro.fortalezas : [],
      })),
    })),
  )
}

export async function obtenerEquipo(id) {
  const equipos = await obtenerEquipos()
  const equipo = equipos.find((item) => item.id === String(id))
  if (!equipo) {
    throw new Error("No encontramos este equipo.")
  }
  return equipo
}

export function buscarEstudiantes({ q = "", carrera, habilidad, disponibilidad, semestre } = {}) {
  return obtenerEstudiantes({ q }).then((estudiantes) =>
    estudiantes.filter((estudiante) =>
      (!carrera || estudiante.carrera === carrera) &&
      (!habilidad || estudiante.fortalezas.some((fortaleza) => fortaleza.nombre === habilidad)) &&
      (!disponibilidad || estudiante.disponibilidad.includes(disponibilidad)) &&
      (!semestre || estudiante.semestre === Number(semestre)),
    ),
  )
}
