export function coverage(project) {
  const total = project.roles.length
  const cubiertos = project.roles.filter((r) => r.cubiertoPor).length
  return {
    total,
    cubiertos,
    pendientes: project.roles.filter((r) => !r.cubiertoPor),
    porcentaje: total ? cubiertos / total : 0,
  }
}

export function formatDate(iso, opts = { day: "numeric", month: "short" }) {
  return new Date(`${iso}T12:00:00`).toLocaleDateString("es-MX", opts)
}

export function firstName(nombre = "") {
  return nombre.split(" ")[0]
}
