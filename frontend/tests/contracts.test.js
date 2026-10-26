import { after, before, test } from "node:test"
import assert from "node:assert/strict"
import { createElement } from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { createServer } from "vite"
import { MemoryRouter } from "react-router-dom"
import { availableRoles, responseMessage, reviewedSummary } from "../src/lib/contracts.js"

let server
before(async () => { server = await createServer({ server: { middlewareMode: true, hmr: false }, appType: "custom" }) })
after(async () => { await server?.close() })
async function render(path, props) {
  const { default: Component } = await server.ssrLoadModule(`/src/${path}.jsx`)
  return renderToStaticMarkup(createElement(MemoryRouter, null, createElement(Component, props)))
}

test("QA-08: unknown viewer never claims shared interests or schedules", async () => {
  const html = await render("components/profile/PublicProfile", { student: {
    id: "qa", nombre: "Persona QA", fortalezas: [], intereses: ["Videojuegos"],
    disponibilidad: ["lun-tarde", "sab-manana"], reforzar: [],
  } })
  assert.doesNotMatch(html, /en común|los intereses que compartes/)
})

test("QA-07: missing coverage never claims the team covers everything", async () => {
  const html = await render("components/team/TeamCoverageChart", { roles: [] })
  assert.doesNotMatch(html, /cubre todo lo necesario/)
  assert.match(html, /[Dd]esconocid/)
})

test("QA-07: global confirmed requirements are visible even with empty role skills", async () => {
  const html = await render("components/team/TeamCoverageChart", { roles: [], coverage: {
    estado: "conocida", cubiertas: ["Python"], por_acreditar: ["SQL"], total: 2,
  } })
  assert.match(html, /Python/)
  assert.match(html, /SQL/)
  assert.doesNotMatch(html, /cubre todo lo necesario/)
})

test("QA-08: real viewer with empty schedule has no invented overlap", async () => {
  const html = await render("components/profile/PublicProfile", { viewer: {
    id: "owner", perfil_estado_ia: "listo", intereses: [], disponibilidad: [],
  }, student: { id: "qa", nombre: "Persona QA", fortalezas: [], intereses: [],
    disponibilidad: ["lun-tarde"], reforzar: [] } })
  assert.doesNotMatch(html, /en común/)
})

test("QA-08: real shared schedule and interest remain visible", async () => {
  const html = await render("components/profile/PublicProfile", { viewer: {
    id: "owner", perfil_estado_ia: "listo", intereses: ["web"], disponibilidad: ["lun-tarde"],
  }, student: { id: "qa", nombre: "Persona QA", fortalezas: [], intereses: ["web"],
    disponibilidad: ["lun-tarde"], reforzar: [] } })
  assert.match(html, /en común/)
  assert.doesNotMatch(html, /Coincide con el proyecto/)
})

test("QA-08: recommendation never trusts demo common-block counts", async () => {
  const html = await render("components/recommendation/RecommendationCard", {
    student: { id: "qa", nombre: "Persona QA", intereses: [], disponibilidad: ["lun-tarde"] },
    rec: { aporta: [], bloquesComunes: 99, porQue: "Ejemplo" }, variant: "expanded",
  })
  assert.doesNotMatch(html, /Coinciden|en común/)
})

test("QA-06: spare global capacity never restores occupied roles", () => {
  assert.deepEqual(availableRoles({ cupos_disponibles: 5, roles: [{ nombre: "Backend" }],
    acepta_participacion: false, roles_disponibles: [] }), [])
  assert.equal(availableRoles({ acepta_participacion: true,
    roles_disponibles: [{ nombre: "Backend", vacantes_disponibles: 2 }] })[0].vacantes_disponibles, 2)
})

test("QA-06: partially occupied roles display actual slot counts", async () => {
  const html = await render('components/project/RoleCoverage', { roles: [{ id: 'backend', nombre: 'Backend',
    habilidades: [], vacantes: 2, ocupados: 1, integrantesIds: ['qa'], cubiertoPor: null }] })
  assert.match(html, /1 de 2 vacantes ocupadas/)
  assert.match(html, /Pendiente/)
})

test("QA-12: search sends filters to the server before pagination", async (t) => {
  const { buscarEstudiantes } = await server.ssrLoadModule('/src/services/api.js')
  const storage = Object.getOwnPropertyDescriptor(globalThis, 'sessionStorage')
  Object.defineProperty(globalThis, 'sessionStorage', { configurable: true, value: { getItem: () => null } })
  t.after(() => { if (storage) Object.defineProperty(globalThis, 'sessionStorage', storage); else delete globalThis.sessionStorage })
  let url
  t.mock.method(globalThis, 'fetch', async (value) => { url = value; return { ok: true, json: async () => [] } })
  await buscarEstudiantes({ q: 'Python', disponibilidad: 'tarde', habilidad: 'SQL' })
  const params = new URL(url).searchParams
  assert.equal(params.get('q'), 'Python')
  assert.equal(params.get('disponibilidad'), 'tarde')
  assert.equal(params.get('habilidad'), 'SQL')
  assert.equal(params.get('limit'), '100')
})

test("QA-16: acceptance message addresses the recipient of each request type", () => {
  assert.match(responseMessage({ tipoSolicitud: "unirse" }, "aceptada"), /Solicitud aceptada/)
  assert.doesNotMatch(responseMessage({ tipoSolicitud: "unirse" }, "aceptada"), /Te uniste/)
  assert.match(responseMessage({ tipoSolicitud: "invitacion" }, "aceptada"), /Te uniste/)
  assert.equal(responseMessage({ tipoSolicitud: "unirse" }, "rechazada"), "Solicitud rechazada.")
})

test("QA-17: meeting route clearly unavailable and contains no send action", async () => {
  const html = await render("pages/MeetingPage")
  assert.match(html, /Reuniones no disponibles/)
  assert.doesNotMatch(html, /Enviar propuesta|Propuesta enviada|Equipo Hábitos/)
})

test('empty candidate list explains opt-in without exposing excluded accounts', async () => {
  const html=await render('components/project/CandidatesEmptyState',{available:true})
  assert.match(html,/activen Recomendaciones/)
  assert.match(html,/Actualizar candidatos/)
  assert.doesNotMatch(html,/Hay \d+ perfiles|anonymous-|QA Web/)
})

test('a role without a vacancy explains availability instead of claiming no profiles exist', async () => {
  const html=await render('components/project/CandidatesEmptyState',{available:false,reason:'No hay vacantes de rol disponibles.'})
  assert.match(html,/No hay vacantes de rol disponibles/)
  assert.doesNotMatch(html,/Pide a quienes/)
})

test("QA-10: explicitly corrected or cleared biography is confirmed; old semantic summaries remain invalidated", () => {
  const previous = { bio: 'Domino Python', resumen_publico: 'Domino Python' }
  assert.equal(reviewedSummary({ ...previous, bio: 'Texto revisado' }, previous, true), 'Texto revisado')
  assert.equal(reviewedSummary({ ...previous, bio: '' }, previous, true), '')
  assert.equal(reviewedSummary(previous, previous, true), '')
})

test("QA-09: project confirmation sends the reviewed fingerprint and refuses a missing one", async (t) => {
  const { confirmarProyecto } = await server.ssrLoadModule('/src/services/api.js')
  assert.throws(() => confirmarProyecto({ id: '1' }, {}), /Recarga el proyecto/)
  const storage = Object.getOwnPropertyDescriptor(globalThis, 'sessionStorage')
  Object.defineProperty(globalThis, 'sessionStorage', { configurable: true, value: { getItem: () => null } })
  t.after(() => { if (storage) Object.defineProperty(globalThis, 'sessionStorage', storage); else delete globalThis.sessionStorage })
  let body
  t.mock.method(globalThis, 'fetch', async (_url, options) => {
    body = JSON.parse(options.body)
    return { ok: true, json: async () => ({ id_evento: 1 }) }
  })
  await confirmarProyecto({ id: '1', tipo: 'academico', fuente_revision: 'a'.repeat(64) }, {})
  assert.equal(body.fuente_revision, 'a'.repeat(64))
  assert.equal(body.confirmado_por_creador, true)
})

test('publishing role skills never repeats obligatory skills as desirable', async (t) => {
  const { crearProyecto }=await server.ssrLoadModule('/src/services/api.js')
  const previous=Object.getOwnPropertyDescriptor(globalThis,'sessionStorage')
  Object.defineProperty(globalThis,'sessionStorage',{configurable:true,value:{getItem:(key)=>key==='usuario'?JSON.stringify({id_usuario:5}):null}})
  t.after(()=>{if(previous)Object.defineProperty(globalThis,'sessionStorage',previous);else delete globalThis.sessionStorage})
  let body
  t.mock.method(globalThis,'fetch',async(_url,options)=>{body=JSON.parse(options.body);return {ok:true,json:async()=>({id_evento:1})}})
  await crearProyecto({titulo:'QA',descripcion:'SQL y Figma',tipo:'academico',integrantes:3,
    roles:[{nombre:'Backend',habilidades:['SQL'],indispensable:false},{nombre:'Diseñador',habilidades:['Figma'],indispensable:false}],
    requirements:{habilidades_obligatorias:['SQL','Figma'],habilidades_deseables:['Git']}})
  assert.deepEqual(body.requisitos_confirmados.habilidades_deseables,['Git'])
})
