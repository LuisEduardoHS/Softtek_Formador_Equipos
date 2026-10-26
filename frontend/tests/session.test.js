import { test } from 'node:test'
import assert from 'node:assert/strict'
import { getSessionUser } from '../src/lib/session.js'

test('tab identity follows its own session, not another tab shared localStorage', (t) => {
  for(const [key,value] of Object.entries({sessionStorage:{getItem:()=>JSON.stringify({id_usuario:11,nombre:'QA organizador'})},localStorage:{getItem:()=>JSON.stringify({id_usuario:22,nombre:'QA otra sesión'})}})) {
    const original=Object.getOwnPropertyDescriptor(globalThis,key)
    Object.defineProperty(globalThis,key,{configurable:true,value})
    t.after(()=>{if(original)Object.defineProperty(globalThis,key,original);else delete globalThis[key]})
  }
  assert.equal(getSessionUser().id_usuario,11)
})
