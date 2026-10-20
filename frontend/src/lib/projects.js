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

// Habilidades requeridas por los roles: cubiertas (rol con integrante) vs. faltantes
export function skillCoverage(roles) {
  const cubiertas = new Set()
  const todas = new Set()
  roles.forEach((r) =>
    r.habilidades.forEach((h) => {
      todas.add(h)
      if (r.cubiertoPor) cubiertas.add(h)
    }),
  )
  return {
    cubiertas: [...cubiertas],
    faltantes: [...todas].filter((h) => !cubiertas.has(h)),
    total: todas.size,
  }
}

export function formatDate(iso, opts = { day: "numeric", month: "short" }) {
  return new Date(`${iso}T12:00:00`).toLocaleDateString("es-MX", opts)
}

export function firstName(nombre = "") {
  return nombre.split(" ")[0]
}
