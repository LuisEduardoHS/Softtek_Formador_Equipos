export function countPendingInvitations(invitations = []) {
  return invitations.filter(
    (invitation) => invitation.tipo === "recibida" && invitation.estado === "pendiente",
  ).length
}
