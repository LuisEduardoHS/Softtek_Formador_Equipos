export function availableRoles(project) {
  return project?.acepta_participacion === true && Array.isArray(project.roles_disponibles)
    ? project.roles_disponibles : []
}

export function responseMessage(invitation, state) {
  if (invitation.tipoSolicitud === "unirse") {
    return state === "aceptada" ? "Solicitud aceptada. Se incorporó el solicitante al equipo." : "Solicitud rechazada."
  }
  return state === "aceptada" ? "Te uniste al equipo." : "Invitación rechazada."
}

export function confirmedComparison(profile) {
  return ["listo", "pendiente_embedding", "sin_contenido"].includes(profile?.perfil_estado_ia) ? profile : null
}

export function reviewedSummary(profile, previous, discardOld) {
  if (profile.bio !== previous.bio) return profile.bio ?? ""
  return discardOld ? "" : profile.resumen_publico ?? profile.bio ?? ""
}
