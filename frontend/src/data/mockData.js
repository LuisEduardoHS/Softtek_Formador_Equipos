// Datos de ejemplo para la demo. Se reemplazan por respuestas del backend
// a través de src/services/api.js.

export const DIAS = ["lun", "mar", "mie", "jue", "vie", "sab"]
export const DIAS_LABEL = { lun: "Lun", mar: "Mar", mie: "Mié", jue: "Jue", vie: "Vie", sab: "Sáb" }
export const FRANJAS = ["manana", "tarde", "noche"]
export const FRANJAS_LABEL = { manana: "Mañana", tarde: "Tarde", noche: "Noche" }

export const currentUser = {
  id: "u0",
  nombre: "Mariana López",
  carrera: "Ing. en Sistemas Computacionales",
  semestre: 6,
  correo: "mariana.lopez@universidad.edu.mx",
  grupoExterno: "",
  perfilCompleto: 80,
  pausado: false,
  fortalezas: [
    { nombre: "Python", nivel: "avanzado" },
    { nombre: "Análisis de datos", nivel: "intermedio" },
    { nombre: "Explicar temas", nivel: "avanzado" },
  ],
  reforzar: ["Diseño de interfaces", "Hablar en público"],
  intereses: ["Salud digital", "Educación", "Sostenibilidad"],
  disponibilidad: ["lun-tarde", "mar-tarde", "mie-tarde", "jue-noche", "sab-manana"],
  visibilidad: { fortalezas: true, intereses: true, disponibilidad: true, reforzar: false, correo: true },
}

export const students = [
  {
    id: "u1",
    nombre: "Ana Torres",
    carrera: "Diseño Gráfico",
    semestre: 5,
    correo: "ana.torres@universidad.edu.mx",
    fortalezas: [
      { nombre: "Diseño de interfaces", nivel: "avanzado" },
      { nombre: "Figma", nivel: "avanzado" },
      { nombre: "Investigación de usuarios", nivel: "intermedio" },
    ],
    intereses: ["Salud digital", "Accesibilidad"],
    disponibilidad: ["lun-tarde", "mar-tarde", "jue-noche", "vie-manana"],
  },
  {
    id: "u2",
    nombre: "Diego Ramírez",
    carrera: "Ing. en Software",
    semestre: 7,
    correo: "diego.ramirez@universidad.edu.mx",
    fortalezas: [
      { nombre: "Backend", nivel: "avanzado" },
      { nombre: "FastAPI", nivel: "intermedio" },
      { nombre: "Bases de datos", nivel: "avanzado" },
    ],
    intereses: ["Fintech", "Educación"],
    disponibilidad: ["lun-tarde", "mie-tarde", "jue-noche"],
  },
  {
    id: "u3",
    nombre: "Sofía Hernández",
    carrera: "Administración de Empresas",
    semestre: 6,
    correo: "sofia.hernandez@universidad.edu.mx",
    fortalezas: [
      { nombre: "Gestión de proyectos", nivel: "avanzado" },
      { nombre: "Scrum", nivel: "intermedio" },
      { nombre: "Presentaciones", nivel: "avanzado" },
    ],
    intereses: ["Emprendimiento", "Sostenibilidad"],
    disponibilidad: ["mar-tarde", "mie-tarde", "sab-manana"],
  },
  {
    id: "u4",
    nombre: "Luis Medina",
    carrera: "Ing. Mecatrónica",
    semestre: 8,
    correo: "luis.medina@universidad.edu.mx",
    fortalezas: [
      { nombre: "Arduino", nivel: "avanzado" },
      { nombre: "Electrónica", nivel: "avanzado" },
      { nombre: "C++", nivel: "intermedio" },
    ],
    intereses: ["IoT", "Sostenibilidad"],
    disponibilidad: ["lun-manana", "mie-noche", "vie-tarde"],
  },
  {
    id: "u5",
    nombre: "Valeria Castro",
    carrera: "Comunicación",
    semestre: 4,
    correo: "valeria.castro@universidad.edu.mx",
    fortalezas: [
      { nombre: "Redacción", nivel: "avanzado" },
      { nombre: "Redes sociales", nivel: "intermedio" },
      { nombre: "Hablar en público", nivel: "avanzado" },
    ],
    intereses: ["Educación", "Cultura"],
    disponibilidad: ["mar-tarde", "jue-noche", "sab-manana"],
  },
  {
    id: "u6",
    nombre: "Jorge Salinas",
    carrera: "Actuaría",
    semestre: 5,
    correo: "jorge.salinas@universidad.edu.mx",
    fortalezas: [
      { nombre: "Estadística", nivel: "avanzado" },
      { nombre: "R", nivel: "intermedio" },
      { nombre: "Visualización de datos", nivel: "intermedio" },
    ],
    intereses: ["Salud digital", "Fintech"],
    disponibilidad: ["lun-tarde", "mie-tarde", "vie-tarde"],
  },
  {
    id: "u7",
    nombre: "Camila Ortega",
    carrera: "Psicología",
    semestre: 6,
    correo: "camila.ortega@universidad.edu.mx",
    fortalezas: [
      { nombre: "Investigación de usuarios", nivel: "avanzado" },
      { nombre: "Entrevistas", nivel: "avanzado" },
      { nombre: "Facilitación", nivel: "intermedio" },
    ],
    intereses: ["Salud digital", "Bienestar"],
    disponibilidad: ["mar-tarde", "mie-tarde", "jue-noche"],
  },
  {
    id: "u8",
    nombre: "Ricardo Pineda",
    carrera: "Ing. en Sistemas Computacionales",
    semestre: 8,
    correo: "ricardo.pineda@universidad.edu.mx",
    fortalezas: [
      { nombre: "React", nivel: "avanzado" },
      { nombre: "Frontend", nivel: "avanzado" },
      { nombre: "Git", nivel: "intermedio" },
    ],
    intereses: ["Educación", "Videojuegos"],
    disponibilidad: ["lun-tarde", "mar-tarde", "jue-noche", "sab-manana"],
  },
  {
    id: "u9",
    nombre: "Fernanda Ruiz",
    carrera: "Arquitectura",
    semestre: 7,
    correo: "fernanda.ruiz@universidad.edu.mx",
    correoVisible: false, // decidió no compartir su correo
    fortalezas: [
      { nombre: "Modelado 3D", nivel: "avanzado" },
      { nombre: "Diseño de interfaces", nivel: "intermedio" },
      { nombre: "Ilustración", nivel: "intermedio" },
    ],
    intereses: ["Sostenibilidad", "Ciudad"],
    disponibilidad: ["mie-tarde", "vie-manana", "sab-manana"],
  },
]

export const studentById = (id) => (id === currentUser.id ? currentUser : students.find((s) => s.id === id))

export const projects = [
  {
    id: "p1",
    titulo: "App de seguimiento de hábitos saludables",
    descripcion:
      "Aplicación móvil que ayuda a estudiantes a registrar sueño, hidratación y actividad física, con recordatorios y un panel de progreso semanal.",
    tipo: "academico",
    materia: "Desarrollo de Aplicaciones Móviles",
    creadorId: "u0",
    integrantes: 4,
    fechaLimite: "2026-12-05",
    creado: "2026-10-02",
    roles: [
      { id: "r1", nombre: "Análisis de datos", habilidades: ["Python", "Análisis de datos"], indispensable: true, cubiertoPor: "u0" },
      { id: "r2", nombre: "Diseño de interfaces", habilidades: ["Diseño de interfaces", "Figma"], indispensable: true, cubiertoPor: null },
      { id: "r3", nombre: "Programación backend", habilidades: ["Backend", "Bases de datos"], indispensable: true, cubiertoPor: null },
      { id: "r4", nombre: "Investigación de usuarios", habilidades: ["Investigación de usuarios", "Entrevistas"], indispensable: false, cubiertoPor: "u7" },
    ],
  },
  {
    id: "p2",
    titulo: "Sensor de calidad del aire para el campus",
    descripcion:
      "Prototipo de estaciones de medición con Arduino que publican datos en un tablero abierto para la comunidad universitaria.",
    tipo: "personal",
    materia: "",
    creadorId: "u4",
    integrantes: 4,
    fechaLimite: "2027-01-20",
    creado: "2026-09-28",
    roles: [
      { id: "r1", nombre: "Electrónica", habilidades: ["Arduino", "Electrónica"], indispensable: true, cubiertoPor: "u4" },
      { id: "r2", nombre: "Visualización de datos", habilidades: ["Visualización de datos", "Python"], indispensable: true, cubiertoPor: null },
      { id: "r3", nombre: "Comunicación del proyecto", habilidades: ["Redacción", "Redes sociales"], indispensable: false, cubiertoPor: "u5" },
      { id: "r4", nombre: "Gestión de proyectos", habilidades: ["Gestión de proyectos"], indispensable: false, cubiertoPor: null },
    ],
  },
  {
    id: "p3",
    titulo: "Plataforma de tutorías entre pares",
    descripcion:
      "Sitio web donde estudiantes de semestres avanzados ofrecen asesorías a los de nuevo ingreso, con agenda y materiales compartidos.",
    tipo: "academico",
    materia: "Ingeniería de Software",
    creadorId: "u8",
    integrantes: 5,
    fechaLimite: "2026-11-28",
    creado: "2026-09-20",
    roles: [
      { id: "r1", nombre: "Frontend", habilidades: ["React", "Frontend"], indispensable: true, cubiertoPor: "u8" },
      { id: "r2", nombre: "Programación backend", habilidades: ["Backend", "FastAPI"], indispensable: true, cubiertoPor: "u2" },
      { id: "r3", nombre: "Gestión de proyectos", habilidades: ["Gestión de proyectos", "Scrum"], indispensable: true, cubiertoPor: "u3" },
      { id: "r4", nombre: "Contenido educativo", habilidades: ["Explicar temas", "Redacción"], indispensable: false, cubiertoPor: "u0" },
      { id: "r5", nombre: "Diseño de interfaces", habilidades: ["Diseño de interfaces"], indispensable: false, cubiertoPor: "u9" },
    ],
  },
  {
    id: "p4",
    titulo: "Tablero de movilidad sostenible del campus",
    descripcion:
      "Analizar cómo llega la comunidad a la universidad (bici, transporte público, auto) y proponer rutas y horarios que reduzcan emisiones.",
    tipo: "academico",
    materia: "Estadística Aplicada",
    creadorId: "u6",
    integrantes: 3,
    fechaLimite: "2026-12-12",
    creado: "2026-10-08",
    roles: [
      { id: "r1", nombre: "Análisis de datos", habilidades: ["Python", "Análisis de datos"], indispensable: true, cubiertoPor: null },
      { id: "r2", nombre: "Estadística", habilidades: ["Estadística", "R"], indispensable: true, cubiertoPor: "u6" },
      { id: "r3", nombre: "Presentación de resultados", habilidades: ["Presentaciones", "Redacción"], indispensable: false, cubiertoPor: null },
    ],
  },
]

export const projectById = (id) => projects.find((p) => p.id === id)

// Recomendaciones de compañeros que genera la IA (para el usuario actual).
export const recommendations = [
  {
    id: "rec1",
    studentId: "u1",
    projectId: "p1",
    rolId: "r2",
    nivel: "muy",
    aporta: ["Diseño de interfaces", "Figma", "Investigación de usuarios"],
    bloquesComunes: 3,
    porQue: "Ana cubre el diseño de interfaces que tu proyecto aún no tiene y ya ha prototipado apps de salud. Comparten tres tardes libres.",
  },
  {
    id: "rec2",
    studentId: "u2",
    projectId: "p1",
    rolId: "r3",
    nivel: "muy",
    aporta: ["Backend", "Bases de datos", "FastAPI"],
    bloquesComunes: 3,
    porQue: "Diego aporta backend y bases de datos, justo lo que complementa tu perfil de análisis. Tiene experiencia con APIs en Python.",
  },
  {
    id: "rec3",
    studentId: "u8",
    projectId: "p1",
    rolId: "r3",
    nivel: "comp",
    aporta: ["Git", "React", "Frontend"],
    bloquesComunes: 4,
    porQue: "Ricardo no es especialista en backend, pero conoce bien el flujo con Git y puede conectar la app con la API. Coinciden cuatro bloques.",
  },
  {
    id: "rec4",
    studentId: "u9",
    projectId: "p1",
    rolId: "r2",
    nivel: "comp",
    aporta: ["Diseño de interfaces", "Ilustración", "Modelado 3D"],
    bloquesComunes: 2,
    porQue: "Fernanda también cubre diseño de interfaces y suma ilustración, útil para hacer la app más cercana.",
  },
]

// Proyectos que la IA sugiere al usuario actual.
export const projectSuggestions = [
  { projectId: "p2", rolId: "r2", nivel: "muy", porQue: "Tu Python y tu experiencia en análisis de datos cubren la visualización que este proyecto necesita." },
  { projectId: "p4", rolId: "r1", nivel: "muy", porQue: "Jorge ya cubre la estadística; tu Python y tu interés en sostenibilidad completan el análisis de datos." },
]

export const teams = [
  { id: "t1", projectId: "p1", nombre: "Equipo Hábitos", enlaceGrupo: "" },
  { id: "t2", projectId: "p3", nombre: "Tutorías Pares", enlaceGrupo: "https://chat.whatsapp.com/ejemplo" },
]

export const invitations = [
  { id: "i1", tipo: "recibida", deId: "u6", paraId: "u0", projectId: "p4", rol: "Análisis de datos", estado: "pendiente", fecha: "2026-10-13", mensaje: "¡Hola Mariana! Yo me encargo de la estadística; con tu Python podríamos limpiar y cruzar los datos de movilidad. ¿Te animas?" },
  { id: "i2", tipo: "recibida", deId: "u4", paraId: "u0", projectId: "p2", rol: "Visualización de datos", estado: "pendiente", fecha: "2026-10-12", mensaje: "Necesitamos a alguien que convierta los datos del sensor en gráficas claras. ¿Te sumas?" },
  { id: "i3", tipo: "enviada", deId: "u0", paraId: "u7", projectId: "p1", rol: "Investigación de usuarios", estado: "aceptada", fecha: "2026-10-10", mensaje: "" },
  { id: "i4", tipo: "enviada", deId: "u0", paraId: "u2", projectId: "p1", rol: "Programación backend", estado: "pendiente", fecha: "2026-10-11", mensaje: "" },
  { id: "i5", tipo: "enviada", deId: "u0", paraId: "u6", projectId: "p1", rol: "Análisis de datos", estado: "rechazada", fecha: "2026-10-03", mensaje: "" },
  { id: "i6", tipo: "recibida", deId: "u3", paraId: "u0", projectId: "p3", rol: "Gestión de proyectos", estado: "expirada", fecha: "2026-09-15", mensaje: "" },
]

// Personas a las que el usuario ya invitó (pendientes) en un proyecto
export const pendingInviteIds = (projectId) =>
  new Set(invitations.filter((i) => i.tipo === "enviada" && i.estado === "pendiente" && i.projectId === projectId).map((i) => i.paraId))

export const campusStats = { estudiantes: 1240, equipos: 186, carreras: 23 }

export const testimonials = [
  { nombre: "Camila Ortega", carrera: "Psicología", texto: "Nunca pensé trabajar con ingenieros. Mi parte de investigación fue lo que hizo que el proyecto funcionara." },
  { nombre: "Diego Ramírez", carrera: "Ing. en Software", texto: "Ya no armamos equipos solo con amigos. Me recomendaron justo a la diseñadora que nos faltaba." },
  { nombre: "Sofía Hernández", carrera: "Administración", texto: "Me gustó que me explicara por qué me recomendaba cada proyecto. Se siente transparente." },
]

export const filtros = {
  carreras: [...new Set(students.map((s) => s.carrera))],
  habilidades: [...new Set(students.flatMap((s) => s.fortalezas.map((f) => f.nombre)))],
  semestres: [1, 2, 3, 4, 5, 6, 7, 8, 9],
}
