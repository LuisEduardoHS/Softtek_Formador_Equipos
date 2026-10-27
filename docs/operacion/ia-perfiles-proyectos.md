# Operación de perfiles y proyectos con IA

Instalación y arranque: [README principal](../../README.md). Datos completos para probar: [guía manual](../pruebas-manuales/guia-completa.md). Estado comprobado: [validación real](../qa/informes/2026-10-26-flujo-web.md).

## Perfil

1. Registro/login entregan un Bearer JWT. React valida `/auth/me`; token e identidad se guardan en `sessionStorage` de la misma pestaña. El backend determina titularidad, nunca un ID del navegador por sí solo.
2. `POST /perfil/interpretar` recibe fortalezas, aprendizaje e intereses en texto. Guarda borrador y devuelve sugerencias `ia_sin_confirmar`; todavía no acredita habilidades.
3. La persona revisa etiquetas, niveles, experiencia, resumen público, disponibilidad y consentimiento. Intereses, negaciones y deseos de aprender no deben pasar a fortalezas.
4. `POST /perfil/confirmar` persiste la revisión y genera Nomic desde habilidades, intereses y experiencia confirmados, sin áreas de mejora. `POST /perfil/embedding/reintentar` recupera un vector pendiente sin repetir el registro.
5. Cambiar contenido semántico del perfil invalida la evidencia anterior hasta revisar/confirmar; la UI ofrece «Confirmar y generar análisis».

La interpretación comparte solo solicitudes idénticas en vuelo por sesión/entrada; al fallar o terminar, un nuevo intento vuelve a llamar al servicio. El backend rechaza el resultado si el texto pendiente cambió durante el análisis. No se cachea una interpretación exitosa para futuros cambios.

## Proyecto

- `POST /eventos/interpretar`: sugerencias de requisitos y roles, sin publicar.
- `POST /eventos/`: con requisitos revisados y confirmación del creador, publica y genera Nomic; sin revisión guarda borrador. La UI envía `Idempotency-Key` UUID por intento y conserva el borrador para no duplicar una creación al repetir el mismo envío.
- `PUT /eventos/{id}`: solo creador; conserva capacidad/roles compatibles con integrantes reales, invalida IA anterior y obliga a revisar de nuevo.
- `POST /eventos/{id}/confirmar`: exige `requirements`, `confirmado_por_creador=true` y `fuente_revision`, la huella vigente del detalle entregada al creador. Sin huella: 422; huella obsoleta: 409.
- `POST /eventos/{id}/embedding/reintentar`: usa requisitos ya confirmados. No sustituye la reconfirmación tras una edición.

La revisión humana puede corregir cualquier omisión de Llama, pero conviene registrar primero la salida incorrecta para no ocultar defectos del parser. No se acreditan habilidades por similitud de embeddings.

## Estados y recuperación

| Estado interno | Interpretación / acción |
| --- | --- |
| interpretando | Petición generativa en curso; esperar o revisar manualmente |
| pendiente_revision | Hay sugerencia para revisar; todavía no es hecho confirmado |
| interpretacion_pendiente | Interpretación fallida; conserva borrador y permite reintentar |
| pendiente_embedding | Confirmación guardada; Nomic pendiente o no disponible; reintentar vector |
| sin_contenido | Perfil sin contenido confirmado suficiente para un vector; agregar hechos reales y confirmar |
| listo | Confirmación y representación actuales |
| obsoleto | Edición invalidó el análisis previo; revisar y confirmar de nuevo |

Una caída de Ollama durante confirmación no debe convertirse en un 500 después de guardar: perfil responde 200 y creación de proyecto 201 con estado recuperable. Una interpretación no disponible responde 503, conserva el texto y protege confirmaciones anteriores; no equivale a perder toda la cuenta. No subas timeouts sin distinguir fallo de conexión, latencia e interpretación semántica.

Los vectores se almacenan en JSON, con 768 dimensiones Nomic finitas, modelo, versión de pipeline y revisión de fuente. No se exponen en DTO públicos. Un vector obsoleto/incompatible no se usa como actual; el motor puede trabajar con evidencia explícita confirmada aunque falte el embedding.

## Privacidad y límites actuales

- Consentimiento de recomendaciones desactivado por defecto. Pausa y visibilidad se respetan al descubrir perfiles y acreditar habilidades.
- La biografía es un texto público independiente: ocultar una lista no elimina automáticamente las palabras de su resumen. Revisar ambos campos.
- Foto e idiomas del onboarding son controles de presentación que no se envían en el contrato de confirmación actual; no se promete persistencia. En las pruebas manuales se dejan vacíos.
- El onboarding exige al menos una fortaleza para habilitar «Confirmar perfil». El caso de texto ambiguo sin habilidades sirve para comprobar que no se inventen competencias; no completes ese flujo agregando una fortaleza falsa.
- El catálogo de equivalencias es finito y la salida de Llama varía. Revisión humana, incluidos resúmenes y experiencia, sigue siendo necesaria.

## Base de datos y comprobaciones

FastAPI no crea ni migra tablas al importar. El SQL inicial es para una base nueva; la revisión `20261022_6a` agrega columnas de IA que falten. No ejecutar el SQL inicial ni un downgrade sobre una base en uso para «reparar» un arranque.

Ejecutar pytest/pip check en backend y npm test/build/lint en frontend según el README. La suite automática y las pruebas reales de MySQL/Ollama son comprobaciones diferentes. Para escribir datos ficticios utiliza una base QA aislada; la guía incluye cómo configurar procesos separados sin cambiar la conexión principal.
