function hasText(value) {
  return typeof value === "string" && value.trim().length > 0
}

function hasItems(value) {
  return Array.isArray(value) && value.some((item) =>
    typeof item === "string" ? hasText(item) : hasText(item?.nombre),
  )
}

export function calculateProfileCompletion(profile) {
  const fields = [
    hasText(profile.correo),
    hasText(profile.carrera),
    Number.isInteger(Number(profile.semestre)) && Number(profile.semestre) >= 1 && Number(profile.semestre) <= 12,
    hasItems(profile.fortalezas) || hasItems(profile.habilidades),
    hasItems(profile.reforzar),
    hasItems(profile.intereses),
    hasItems(profile.disponibilidad),
    hasText(profile.grupoExterno),
  ]

  return Math.round((fields.filter(Boolean).length / fields.length) * 100)
}
