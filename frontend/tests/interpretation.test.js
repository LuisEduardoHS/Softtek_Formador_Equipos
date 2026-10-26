import { after, before, test } from 'node:test'
import assert from 'node:assert/strict'
import { createServer } from 'vite'

let server
before(async () => { server = await createServer({ server: { middlewareMode: true, hmr: false }, appType: 'custom' }) })
after(async () => { await server?.close() })
function storage(t, token='fictitious-session') {
  const original=Object.getOwnPropertyDescriptor(globalThis,'sessionStorage')
  Object.defineProperty(globalThis,'sessionStorage',{configurable:true,value:{getItem:()=>token}})
  t.after(()=>{if(original) Object.defineProperty(globalThis,'sessionStorage',original); else delete globalThis.sessionStorage})
}

test('StrictMode subscriptions share one profile interpretation; later attempts are fresh', async (t) => {
  storage(t)
  const { interpretarPerfil }=await server.ssrLoadModule('/src/services/api.js')
  let release, calls=0
  t.mock.method(globalThis,'fetch',async ()=>{
    calls++
    await new Promise((resolve)=>{release=resolve})
    return {ok:true,json:async()=>({fortalezas:[{nombre:'Python'}]})}
  })
  const input={fortalezas:'Sé Python.',reforzar:'',intereses:''}
  const first=interpretarPerfil(input), second=interpretarPerfil({...input})
  assert.equal(calls,1,'two effect subscriptions must not race on the same backend profile')
  release();assert.deepEqual(await first,await second)
  const retry=interpretarPerfil(input)
  assert.equal(calls,2,'no successful result cache may hide a later analysis')
  release();await retry
})

test('failed interpretation releases its slot and a real retry can recover', async (t) => {
  storage(t)
  const { interpretarPerfil }=await server.ssrLoadModule('/src/services/api.js')
  let calls=0
  t.mock.method(globalThis,'fetch',async ()=>{calls++;return calls===1
    ? {ok:false,status:503,json:async()=>({detail:'Ollama temporalmente no disponible'})}
    : {ok:true,json:async()=>({fortalezas:[]})}})
  await assert.rejects(interpretarPerfil({fortalezas:'No sé SQL.'}),/temporalmente/)
  await interpretarPerfil({fortalezas:'No sé SQL.'})
  assert.equal(calls,2)
})

test('different texts or sessions must not reuse an in-flight interpretation', async (t) => {
  let token='session-one'
  const original=Object.getOwnPropertyDescriptor(globalThis,'sessionStorage')
  Object.defineProperty(globalThis,'sessionStorage',{configurable:true,value:{getItem:()=>token}})
  t.after(()=>{if(original)Object.defineProperty(globalThis,'sessionStorage',original);else delete globalThis.sessionStorage})
  const { interpretarPerfil }=await server.ssrLoadModule('/src/services/api.js')
  let calls=0;const releases=[]
  t.mock.method(globalThis,'fetch',async()=>{calls++;await new Promise(r=>releases.push(r));return{ok:true,json:async()=>({})}})
  const jobs=[interpretarPerfil({fortalezas:'Python'}),interpretarPerfil({fortalezas:'SQL'})]
  token='session-two';jobs.push(interpretarPerfil({fortalezas:'Python'}))
  assert.equal(calls,3);releases.forEach(r=>r());await Promise.all(jobs)
})

test('project interpretation also shares StrictMode subscribers', async (t) => {
  storage(t)
  const { interpretarProyecto }=await server.ssrLoadModule('/src/services/api.js')
  let release,calls=0
  t.mock.method(globalThis,'fetch',async()=>{calls++;await new Promise(r=>{release=r});return {ok:true,json:async()=>({requisitos:{}})}})
  const input={titulo:'QA proyecto',descripcion:'Figma obligatorio',tipo:'personal',integrantes:3}
  const first=interpretarProyecto(input),second=interpretarProyecto({...input})
  assert.equal(calls,1);release();await Promise.all([first,second])
})
