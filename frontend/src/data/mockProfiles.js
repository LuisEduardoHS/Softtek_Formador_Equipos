import { projects, recommendations, studentById, students } from "./mockData"

// Perfiles de ejemplo para la vitrina de la landing
export const mockProfiles = ["u1", "u2", "u3", "u7", "u4", "u5"].map((id) => {
  const s = students.find((x) => x.id === id)
  return { name: s.nombre, role: s.carrera, skills: s.fortalezas.map((f) => f.nombre) }
})

// Coincidencia destacada para la pantalla de match
const rec = recommendations[0]
export const mockMatch = {
  student: studentById(rec.studentId),
  rol: projects[0].roles.find((r) => r.id === rec.rolId),
  project: projects[0],
  rec,
}
