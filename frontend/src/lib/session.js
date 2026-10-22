export function getSessionUser() {
  try {
    const user = JSON.parse(localStorage.getItem("usuario") || "{}")
    return user && typeof user === "object" && !Array.isArray(user) ? user : {}
  } catch (error) {
    console.error("No se pudo leer el usuario de la sesión:", error)
    return {}
  }
}
