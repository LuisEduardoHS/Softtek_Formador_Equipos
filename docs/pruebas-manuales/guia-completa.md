# Guía manual completa: perfiles IA, proyectos, recomendaciones y equipos

Datos **ficticios** para rellenar cada campo y contrastar el resultado. Hay **12 perfiles, 5 proyectos y 14 recorridos**. Los casos se basan en el contrato y en las validaciones del MVP; esta guía es una batería para que tú la ejecutes, no un informe que afirme que estos doce usuarios ya existen o que cada salida de Llama será idéntica.

Para una prueba rápida usa **P01 + P02 + P03 + PR01**, siguiendo R01–R05. Después amplía a videojuegos, deporte, negaciones, privacidad, edición y recuperación. Instalación general: [README](../../README.md). Evidencia de recorridos anteriores: [validación real](../qa/informes/2026-10-26-flujo-web.md).

## Contenido

- [Preparar una base y servidores QA](#preparacion).
- [Campos comunes de todas las cuentas](#campos-comunes).
- [Perfiles y revisión esperada](#perfiles).
- [Proyectos y requisitos esperados](#proyectos).
- [Recorridos de principio a fin](#recorridos).
- [Registrar tus resultados](#registro-resultados).

<a id="preparacion"></a>
## 1. Preparación: no mezclar pruebas y datos reales

Necesitas haber instalado dependencias y descargado los modelos siguiendo el README. Utiliza una base **nueva, sin datos personales**, por ejemplo `softtek_formador_equipos_qa_manual_01`. Si no tienes permiso para crearla, solicita ese permiso; no hagas estas altas en la base principal como alternativa.

### 1.1 Crear el esquema QA una sola vez

Desde la raíz, genera una copia del SQL que cambie **tanto CREATE DATABASE como USE**:

```powershell
$qaSql = (Get-Content -Raw .\database\db_actividad.sql).Replace('CREATE DATABASE IF NOT EXISTS Aplicacion;', 'CREATE DATABASE IF NOT EXISTS softtek_formador_equipos_qa_manual_01;').Replace('USE Aplicacion;', 'USE softtek_formador_equipos_qa_manual_01;')
$qaSqlPath = Join-Path $env:TEMP 'softtek_qa_manual_01.sql'
$qaSql | Set-Content -LiteralPath $qaSqlPath -Encoding utf8
$qaSqlPath
```

Abre el archivo mostrado con MySQL Workbench, verifica que sus dos primeras instrucciones apuntan a la QA y ejecútalo con una cuenta autorizada. Se crean las cinco tablas vacías. No ejecutes el SQL inicial sobre una base con tablas existentes. Si ya usaste ese nombre, conserva la base y elige otro sufijo para una ejecución nueva; cambia ese nombre también en los comandos siguientes.

### 1.2 Backend QA separado

Abre una terminal PowerShell **desde la raíz**. Estas variables solo afectan a esa terminal; no sobrescriben tu `backend/.env` habitual:

```powershell
Set-Location backend
$env:DATABASE_URL='mysql+pymysql://TU_USUARIO:TU_CLAVE@127.0.0.1:3306/softtek_formador_equipos_qa_manual_01'
$env:AUTH_SECRET = (& .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))")
$env:OLLAMA_HOST='http://127.0.0.1:11434'
$env:OLLAMA_LLM_MODEL='llama3.1:8b'
$env:OLLAMA_EMBEDDING_MODEL='nomic-embed-text'
.\.venv\Scripts\python.exe -c "from app.db.database import engine; c=engine.connect(); name=c.exec_driver_sql('SELECT DATABASE()').scalar_one(); assert name=='softtek_formador_equipos_qa_manual_01'; print(name); c.close()"
.\.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8011
```

Sustituye los marcadores por credenciales autorizadas de MySQL. El comando de comprobación debe imprimir solo el nombre QA; si falla, resuelve la configuración antes de migrar o registrar personas. Mantén esta terminal abierta para conservar el mismo secreto si reinicias su servidor durante R13. No detengas otros procesos que no hayas iniciado para estas pruebas.

### 1.3 Frontend QA separado

En otra terminal desde la raíz:

```powershell
Set-Location frontend
$env:VITE_API_URL='http://127.0.0.1:8011'
npm run dev -- --host 127.0.0.1 --port 5174 --strictPort
```

Abre **http://127.0.0.1:5174**. El puerto 5173 puede seguir siendo tu aplicación habitual; no mezcles ambas pestañas. En las herramientas de red del navegador comprueba que estas peticiones van a **8011**. Si 8011/5174 están ocupados, identifica antes si son tus procesos QA; no apagues servicios compartidos para liberar puertos.

### 1.4 Cuentas y sesiones

Usa pestañas nuevas para organizador y candidatos. Comprueba siempre el nombre de la sesión antes de invitar o aceptar. Las cuentas no vienen precargadas: debes registrarlas. Si un correo ya existe, usa la misma cuenta o sustituye el sufijo de todos tus correos, por ejemplo `p01.r2@manual.example.com`; no interpretes un duplicado de correo como fallo de IA.

<a id="campos-comunes"></a>
## 2. Campos comunes: valores que también debes rellenar

Estos valores aplican a **cada perfil**, salvo las excepciones P10, P11 y P12. Las tablas individuales completan nombre, correo, carrera y textos.

| Pantalla / campo | Valor para esta batería |
| --- | --- |
| Registro: Nombre completo | Nombre de la ficha individual |
| Registro: Correo electrónico | Correo de la ficha, con dominio ficticio manual.example.com |
| Registro: Carrera | Carrera de la ficha; obligatorio también para perfiles deportivos |
| Registro: Estado (opcional) | Dejar vacío |
| Registro: Municipio (opcional) | Dejar vacío |
| Registro: Contraseña | `PruebaManual2026!` (solo cuentas ficticias QA) |
| Registro: Confirmar contraseña | `PruebaManual2026!` |
| Configura tu perfil: Nombre | El mismo nombre de la ficha, aunque ya lo pusiste en registro |
| Foto de perfil | No subir archivo |
| Idiomas que hablas | Dejar vacío |
| ¿En qué eres bueno? | Copiar el texto de la ficha, no la lista esperada de etiquetas |
| ¿Qué te gustaría reforzar? | Copiar el texto de la ficha; si indica vacío, dejar vacío |
| ¿Qué temas te interesan? | Copiar el texto de la ficha |
| Tu disponibilidad | Solo **Lun → Tarde** seleccionado; resto sin seleccionar |
| Revisión: nivel de fortalezas | **Intermedio** en cada fortaleza positiva de la ficha, excepto P09: Básico |
| Revisión: fortalezas/intereses/aprendizaje/experiencia | Revisar contra la ficha; primero registra qué propuso Llama |
| Revisión: Resumen público | Usar el texto revisado de la ficha; no copiar metas como competencias |
| Activar recomendaciones y aparecer en el directorio | **Activado**, salvo P10 y P12 |
| Mi perfil: Semestre (si abres edición) | 1 |
| Mi perfil: enlace a grupo externo | Dejar vacío |
| Mostrar mis fortalezas / intereses / disponibilidad | Activados |
| Mostrar «Quiero reforzar» | Desactivado |
| Mostrar mi correo en perfil público y equipos | Desactivado |
| Pausar mi perfil | Desactivado, salvo el paso posterior de P11 |

Foto e idiomas se dejan vacíos porque el contrato de confirmación actual no los persiste; esta batería no promete una subida de imágenes ni persistencia de idiomas. La disponibilidad se expresa en bloques, no demuestra horas exactas.

**Cómo evaluar la IA:** una omisión o capacidad inventada es un fallo de extracción aunque luego puedas corregirla humanamente. Anota la salida original y después deja los hechos correctos antes de confirmar. El orden de etiquetas, mayúsculas iniciales o una paráfrasis fiel del resumen pueden variar; una meta convertida en fortaleza o una negación convertida en experiencia positiva no son variaciones aceptables. Si necesitas introducir muchas correcciones, no marques la extracción como aprobada solo porque la confirmación terminó guardándose.

<a id="perfiles"></a>
## 3. Perfiles de prueba

### P01 — Alex Backend (organizador web y datos)

| Campo | Copiar / revisar |
| --- | --- |
| Nombre completo y Nombre del perfil | Alex Backend QA |
| Correo | p01@manual.example.com |
| Carrera | Ingeniería de Software |
| ¿En qué eres bueno? | Sé programar en Python. Trabajo con FastAPI para crear aplicaciones web. Uso Git. |
| ¿Qué te gustaría reforzar? | Quiero aprender diseño UX/UI. |
| ¿Qué temas te interesan? | Me interesa la educación y las aplicaciones web. |
| Fortalezas esperadas | Python, FastAPI, Git |
| Quiero reforzar esperado | diseño UX/UI; sin convertirlo en fortaleza |
| Intereses esperados | educación, aplicaciones web; sin duplicar «Me interesa la educación» |
| Experiencia revisada | Creación de aplicaciones web con FastAPI |
| Resumen público revisado | Desarrollo aplicaciones web con Python y FastAPI y uso Git. Me interesan la educación y las aplicaciones web. |

Resultado: perfil confirmado, recomendaciones activadas y estado listo cuando Nomic esté operativo. No se acredita Figma ni UX/UI como habilidad adquirida. Será creador de PR01, PR04 y PR05; nunca debe recomendarse a sí mismo en esos proyectos.

### P02 — Beatriz SQL (especialista en bases de datos)

| Campo | Copiar / revisar |
| --- | --- |
| Nombre completo y Nombre del perfil | Beatriz SQL QA |
| Correo | p02@manual.example.com |
| Carrera | Ciencia de Datos |
| ¿En qué eres bueno? | Sé programar con SQL. Uso Git para controlar versiones de mis proyectos. No sé Figma. |
| ¿Qué te gustaría reforzar? | Quiero aprender Docker. |
| ¿Qué temas te interesan? | Me interesa la educación y las aplicaciones web. |
| Fortalezas esperadas | SQL, Git; nunca «programar con SQL» como capacidad distinta de SQL |
| Quiero reforzar esperado | Docker; Figma negado no implica automáticamente deseo de aprenderlo |
| Intereses esperados | educación, aplicaciones web |
| Experiencia revisada | Dejar vacía si no quieres registrar el uso de Git como experiencia; no inventar empleo o años |
| Resumen público revisado | Sé SQL y uso Git. Me interesan los proyectos educativos y las aplicaciones web. |

Resultado en PR01: debe acreditar SQL obligatorio y Git deseable; Figma permanece por verificar. Puede aparecer «Requiere revisión» por los requisitos globales que no cumple individualmente. En PR04 acredita SQL. No debe afirmar Docker ni Figma como fortalezas.

### P03 — Carla UX/UI (diseño)

| Campo | Copiar / revisar |
| --- | --- |
| Nombre completo y Nombre del perfil | Carla Diseño QA |
| Correo | p03@manual.example.com |
| Carrera | Diseño Digital |
| ¿En qué eres bueno? | Tengo experiencia en UX/UI y Figma. Hago prototipado de aplicaciones web. No sé SQL. |
| ¿Qué te gustaría reforzar? | Quiero aprender Blender. |
| ¿Qué temas te interesan? | Me interesa la educación y las aplicaciones web. |
| Fortalezas esperadas | UX/UI, Figma, prototipado |
| Quiero reforzar esperado | Blender, sin acreditarlo como herramienta dominada |
| Intereses esperados | educación, aplicaciones web |
| Experiencia revisada | UX/UI, Figma, prototipado de aplicaciones web |
| Resumen público revisado | Tengo experiencia en UX/UI, Figma y prototipado de aplicaciones web. Me interesa la educación. |

Resultado en PR01/PR05: acredita Figma. En PR01 SQL sigue desconocido/no acreditado. Ni la negación de SQL ni el deseo de aprender Blender deben convertirse en fortalezas.

### P04 — Diego UE5 (organizador de videojuegos)

| Campo | Copiar / revisar |
| --- | --- |
| Nombre completo y Nombre del perfil | Diego Videojuegos QA |
| Correo | p04@manual.example.com |
| Carrera | Desarrollo de Videojuegos |
| ¿En qué eres bueno? | Tengo experiencia en UE5. Hago diseño de niveles. Uso Git para controlar versiones. |
| ¿Qué te gustaría reforzar? | Quiero aprender Blender. |
| ¿Qué temas te interesan? | Me interesan los videojuegos y las game jams. |
| Fortalezas esperadas | Unreal Engine 5, diseño de niveles, Git |
| Quiero reforzar esperado | Blender |
| Intereses esperados | videojuegos, game jams |
| Experiencia revisada | Unreal Engine 5; conservar solo lo respaldado por el texto |
| Resumen público revisado | Trabajo con Unreal Engine 5, diseño de niveles y Git. Me interesan los videojuegos y las game jams. |

Resultado: UE5 debe equivaler a Unreal Engine 5, sin duplicar ambas etiquetas. No acredita Blender. Creador de PR02 y excluido como candidato de su propio proyecto.

### P05 — Elena Blender (artista 3D)

| Campo | Copiar / revisar |
| --- | --- |
| Nombre completo y Nombre del perfil | Elena Arte 3D QA |
| Correo | p05@manual.example.com |
| Carrera | Animación Digital |
| ¿En qué eres bueno? | Tengo experiencia en Blender para crear modelos 3D. No sé Unreal Engine 5. |
| ¿Qué te gustaría reforzar? | Quiero aprender Unreal Engine 5. |
| ¿Qué temas te interesan? | Me interesan los videojuegos y las game jams. |
| Fortalezas esperadas | Blender; no inferir rigging, animación, texturizado u otras herramientas |
| Quiero reforzar esperado | Unreal Engine 5, porque aquí sí expresó que quiere aprenderlo |
| Intereses esperados | videojuegos, game jams |
| Experiencia revisada | Creación de modelos 3D con Blender |
| Resumen público revisado | Creo modelos 3D con Blender. Me interesan los videojuegos y las game jams. |

Resultado en PR02: acredita Blender. Unreal Engine 5 no es una capacidad adquirida. Git puede quedar por verificar en su explicación; el creador aporta Git al equipo.

### P06 — Fabio Delantero (organizador deportivo)

| Campo | Copiar / revisar |
| --- | --- |
| Nombre completo y Nombre del perfil | Fabio Delantero QA |
| Correo | p06@manual.example.com |
| Carrera | Ciencias del Deporte |
| ¿En qué eres bueno? | Juego de delantero en un equipo amateur de fútbol. No sé jugar de portero. |
| ¿Qué te gustaría reforzar? | Quiero mejorar en defensa. |
| ¿Qué temas te interesan? | Me interesa el fútbol amateur. |
| Fortalezas esperadas | delantero |
| Quiero reforzar esperado | defensa, sin convertirla en fortaleza |
| Intereses esperados | fútbol amateur |
| Experiencia revisada | Fútbol amateur como delantero; sin inventar trayectoria profesional |
| Resumen público revisado | Juego de delantero en fútbol amateur. |

Resultado: no acredita portero ni defensa. Será creador de PR03; no debe recomendarse a sí mismo.

### P07 — Gabriela Portera (sin experiencia profesional)

| Campo | Copiar / revisar |
| --- | --- |
| Nombre completo y Nombre del perfil | Gabriela Portera QA |
| Correo | p07@manual.example.com |
| Carrera | Ciencias del Deporte |
| ¿En qué eres bueno? | Juego de portero y defensa. No tengo experiencia profesional. |
| ¿Qué te gustaría reforzar? | Dejar vacío |
| ¿Qué temas te interesan? | Me interesa el fútbol amateur. |
| Fortalezas esperadas | portero, defensa |
| Quiero reforzar esperado | Vacío; negar experiencia no crea una meta |
| Intereses esperados | fútbol amateur |
| Experiencia revisada | Puede conservar «Juego de portero y defensa» como actividad; nunca «experiencia profesional» positiva ni años inventados |
| Resumen público revisado | Juego de portero y defensa en fútbol amateur. |

Resultado en PR03: acredita portero y defensa, pero al aceptar ocupa **una sola vacante**. Dos habilidades cubiertas no significan dos roles ocupados.

### P08 — Hugo Defensa (portero negado y aprendizaje explícito)

| Campo | Copiar / revisar |
| --- | --- |
| Nombre completo y Nombre del perfil | Hugo Defensa QA |
| Correo | p08@manual.example.com |
| Carrera | Educación Física |
| ¿En qué eres bueno? | Juego de defensa en fútbol amateur. No sé jugar de portero. |
| ¿Qué te gustaría reforzar? | Quiero aprender a jugar de portero. |
| ¿Qué temas te interesan? | Me interesa el fútbol amateur. |
| Fortalezas esperadas | defensa |
| Quiero reforzar esperado | jugar de portero; es objetivo, no fortaleza |
| Intereses esperados | fútbol amateur |
| Experiencia revisada | Fútbol amateur como defensa |
| Resumen público revisado | Juego de defensa en fútbol amateur. |

Resultado en PR03: defensa acreditada; portero no acreditado. Puede aparecer con requisitos por revisar. Invitarlo al rol defensa no debe asignarle ni acreditar portero.

### P09 — Iris Aprendiz (intereses y negaciones sin habilidad de programación)

| Campo | Copiar / revisar |
| --- | --- |
| Nombre completo y Nombre del perfil | Iris Aprendiz QA |
| Correo | p09@manual.example.com |
| Carrera | Administración |
| ¿En qué eres bueno? | Soy principiante. Uso Git para controlar versiones. No sé Python ni SQL. No tengo experiencia profesional. |
| ¿Qué te gustaría reforzar? | Quiero aprender Docker. |
| ¿Qué temas te interesan? | Me interesa Python y el análisis de datos. |
| Fortalezas esperadas | Git, nivel **Básico**; no Python, SQL o Docker |
| Quiero reforzar esperado | Docker; no inventar aprendizaje de Python/SQL solo por su negación |
| Intereses esperados | Python, análisis de datos |
| Experiencia revisada | Vacía, o uso de Git si decide conservar esa actividad; nunca experiencia profesional positiva |
| Resumen público revisado | Uso Git a nivel básico y me interesa el análisis de datos. |

Resultado: puede aparecer como evidencia parcial/Requiere revisión, especialmente donde Git es deseable. **No es correcto exigir que nunca aparezca**; sí exigir que ninguna explicación acredite Python, SQL o Docker. El motor permite datos desconocidos y no convierte interés en competencia.

### P10 — Julia Sin Consentimiento

| Campo | Copiar / revisar |
| --- | --- |
| Nombre completo y Nombre del perfil | Julia Privada QA |
| Correo | p10@manual.example.com |
| Carrera | Ciencia de Datos |
| ¿En qué eres bueno? | Sé SQL y uso Git para trabajar con bases de datos. |
| ¿Qué te gustaría reforzar? | Quiero aprender FastAPI. |
| ¿Qué temas te interesan? | Me interesa la educación y las aplicaciones web. |
| Fortalezas esperadas | SQL, Git |
| Quiero reforzar esperado | FastAPI |
| Intereses esperados | educación, aplicaciones web |
| Experiencia revisada | No inventar puesto, empresa o años |
| Resumen público revisado | Sé SQL y uso Git en proyectos de bases de datos. |
| Excepción de permisos | **Desactivar** «Activar recomendaciones y aparecer en el directorio» antes de confirmar |

Resultado: confirmación válida y Nomic pueden completarse, pero Julia **no aparece** como candidata ni en el directorio descubrible. La pantalla propia de recomendaciones debe indicar que necesita activar el consentimiento; no es un fallo del motor ni debe resolverse publicándola automáticamente.

### P11 — Kevin Pausado

| Campo | Copiar / revisar |
| --- | --- |
| Nombre completo y Nombre del perfil | Kevin Pausado QA |
| Correo | p11@manual.example.com |
| Carrera | Diseño Digital |
| ¿En qué eres bueno? | Tengo experiencia en Figma y UX/UI para diseñar interfaces. |
| ¿Qué te gustaría reforzar? | Dejar vacío |
| ¿Qué temas te interesan? | Me interesa la educación y las aplicaciones web. |
| Fortalezas esperadas | Figma, UX/UI |
| Quiero reforzar esperado | Vacío |
| Intereses esperados | educación, aplicaciones web |
| Experiencia revisada | Diseño de interfaces con Figma y UX/UI |
| Resumen público revisado | Diseño interfaces con Figma y UX/UI. |
| Excepción posterior | Confirmar con Recomendaciones activadas. Después: **Mi perfil → Editar → Pausar mi perfil → Guardar cambios** |

Resultado final: Kevin queda fuera del directorio y de candidatos mientras esté pausado. Debe conservar cuenta y equipos existentes. Si solo lo registras y no guardas la pausa, no estás ejecutando este caso de exclusión.

### P12 — Luz Ambigua (caso negativo de extracción/onboarding)

| Campo | Copiar / revisar |
| --- | --- |
| Nombre completo y Nombre del perfil | Luz Ambigua QA |
| Correo | p12@manual.example.com |
| Carrera | Estudios Generales |
| ¿En qué eres bueno? | Todavía no sé qué puedo aportar. Tal vez pueda ayudar en algo, pero no tengo habilidades que pueda confirmar. |
| ¿Qué te gustaría reforzar? | Dejar vacío |
| ¿Qué temas te interesan? | Dejar vacío |
| Fortalezas, objetivos, intereses y experiencia esperados | Sin capacidades concretas inventadas; listas vacías |
| Resumen público revisado | Vacío, si no hay hechos útiles |
| Excepción de permisos | Recomendaciones desactivadas; no agregar fortalezas falsas |

Resultado: la IA no debe inventar Python, SQL, Figma ni experiencia. **Límite de la UI actual:** sin fortalezas, «Confirmar perfil» permanece deshabilitado. Detén este caso después de revisar y registrarlo; no lo cuentes como perfil confirmado/listo ni como fallo temporal de Nomic. El backend distingue sin_contenido, pero este onboarding no completa una confirmación de cero fortalezas. No se arregla la prueba inventándole una habilidad.

<a id="proyectos"></a>
## 4. Proyectos: todos los campos y revisión

Campos comunes a los cinco proyectos:

| Campo / acción | Valor |
| --- | --- |
| Fecha límite | Dejar vacía; no probar vencimiento en esta batería |
| Número de integrantes | Ajustar con +/− al valor indicado; **incluye al creador** |
| Roles de la revisión IA | Dejar solo los de cada ficha; corregir nombres y agregar habilidades manualmente si vienen vacías |
| Indispensable de cada rol | Dejar desactivado: las habilidades obligatorias se confirman explícitamente abajo |
| Vacantes | Una por rol en el formulario actual; no hay que rellenar un ID técnico |
| Habilidades obligatorias / deseables | Etiquetas separadas; agregar con Enter. Una obligatoria no debe repetirse como deseable |
| Condiciones de participación | Solo las indicadas, sin personas ya incorporadas ni habilidades mal clasificadas |
| Publicación | Revisar y pulsar Publicar una vez; esperar confirmación y abrir Ver proyecto |

No copies IDs de capturas o informes: el servidor genera los tuyos. En perfiles públicos y candidatos anota qué «Persona #…» corresponde a cada ficha usando «Ver perfil».

### PR01 — Web: Gestor de tareas

| Campo | Valor |
| --- | --- |
| Sesión creadora | P01 Alex |
| Título del proyecto | MANUAL01 Gestor de tareas |
| Descripción | Queremos crear un gestor de tareas para estudiantes. Buscamos especialista en bases de datos: SQL obligatorio y Git deseable. Buscamos diseñador UX/UI: Figma obligatorio. |
| Tipo de proyecto | Académico |
| Materia | Ingeniería de Software |
| Número de integrantes | 3 |
| Rol 1 / habilidades | especialista en bases de datos / SQL |
| Rol 2 / habilidades | diseñador UX/UI / Figma |
| Habilidades obligatorias revisadas | SQL, Figma |
| Habilidades deseables revisadas | Git |
| Condiciones revisadas | Vacías |

Esperado: P02 acredita SQL/Git y P03 Figma. Ambos pueden requerir revisión de la otra habilidad global; no deben desaparecer por no dominarlo todo. P01 excluido por ser creador; P10 sin consentimiento y P11 pausado excluidos. P09 no acredita SQL/Figma aunque pudiera aparecer como evidencia parcial. Tras aceptar P02 en bases de datos y P03 en diseño: tres integrantes, dos roles cubiertos y SQL/Figma/Git cubiertos.

### PR02 — Videojuegos: Game jam

| Campo | Valor |
| --- | --- |
| Sesión creadora | P04 Diego |
| Título del proyecto | MANUAL02 Game jam cooperativa |
| Descripción | Crearemos un videojuego cooperativo en Unreal Engine 5. Buscamos artista 3D con Blender obligatorio. Git es deseable. |
| Tipo de proyecto | Videojuegos |
| Materia | Desarrollo de Videojuegos |
| Número de integrantes | 2 |
| Rol 1 / habilidades | artista 3D / Blender |
| Habilidades obligatorias revisadas | Blender |
| Habilidades deseables revisadas | Git |
| Condiciones revisadas | Vacías |

Esperado: Blender obligatorio no debe desaparecer. Mencionar que el proyecto usa UE5 no obliga automáticamente a todo artista a dominarlo: revisa que no se agregue como obligatorio sin haberlo solicitado. P05 acredita Blender; P03/P04 querer aprender Blender no lo acredita. P04 aporta UE5 y Git como miembro creador. Tras aceptar P05: dos integrantes y rol cubierto; sin más vacantes utilizables.

### PR03 — Deporte: Equipo amateur

| Campo | Valor |
| --- | --- |
| Sesión creadora | P06 Fabio |
| Título del proyecto | MANUAL03 Fútbol amateur |
| Descripción | Equipo de fútbol amateur. Buscamos portero y defensa. Portero obligatorio. Defensa deseable. Entrenamos los lunes por la tarde. |
| Tipo de proyecto | Deportivo |
| Materia | Dejar vacía |
| Número de integrantes | 3 |
| Rol 1 / habilidades | portero / portero |
| Rol 2 / habilidades | defensa / defensa |
| Habilidades obligatorias revisadas | portero |
| Habilidades deseables revisadas | defensa |
| Condiciones revisadas | Entrenamos los lunes por la tarde |

Esperado: P07 acredita portero y defensa; P08 solo defensa. Primero incorpora P07 como portero: puede haber 2/2 habilidades cubiertas y **solo 1/2 roles** ocupados. Después incorpora P08 como defensa. Horario se conserva como condición por verificar; un bloque Lun-tarde no demuestra automáticamente compatibilidad exacta. No deben aparecer lenguajes de programación inventados por tratarse de un proyecto deportivo.

### PR04 — Datos: Análisis SQL

| Campo | Valor |
| --- | --- |
| Sesión creadora | P01 Alex |
| Título del proyecto | MANUAL04 Análisis de datos educativos |
| Descripción | Analizaremos datos educativos. Buscamos analista de bases de datos con SQL obligatorio. Python es deseable. |
| Tipo de proyecto | Académico |
| Materia | Análisis de Datos |
| Número de integrantes | 2 |
| Rol 1 / habilidades | analista de bases de datos / SQL |
| Habilidades obligatorias revisadas | SQL |
| Habilidades deseables revisadas | Python |
| Condiciones revisadas | Vacías |

Esperado: P02 acredita SQL aunque ya participe en PR01: la pertenencia se excluye por proyecto, no globalmente. P09 interesarse por Python o negar SQL no acredita ninguno. P10 sigue excluida por consentimiento. No exigir que todo candidato con un dato desconocido sea rechazado; revisar qué hechos respalda su explicación.

### PR05 — Diseño: Figma obligatorio, SQL opcional

| Campo | Valor |
| --- | --- |
| Sesión creadora | P01 Alex |
| Título del proyecto | MANUAL05 Prototipo de interfaz |
| Descripción | Diseñaremos una interfaz para una aplicación educativa. Buscamos diseñador UX/UI. Figma obligatorio. UX/UI deseable. SQL no es obligatorio. |
| Tipo de proyecto | Personal |
| Materia | Vacía; el control está deshabilitado para Personal |
| Número de integrantes | 2 |
| Rol 1 / habilidades | diseñador UX/UI / Figma |
| Habilidades obligatorias revisadas | Figma |
| Habilidades deseables revisadas | UX/UI; SQL puede quedar fuera de requisitos, pero nunca obligatorio |
| Condiciones revisadas | Vacías |

Esperado: P03 acredita Figma y UX/UI. No obligar SQL por mencionar «SQL no es obligatorio». P11 no aparece mientras esté pausado. Mantén este proyecto sin participantes para el ensayo de edición R11.

<a id="recorridos"></a>
## 5. Recorridos para ejecutar

### R01 — Arranque y primer perfil con IA

1. Abre 5174, crea P01 con todos sus campos de registro y completa el formulario de perfil.
2. Selecciona Lun-tarde y pulsa Continuar. Registra cuánto tarda y si funciona en el primer intento.
3. Comprueba Python/FastAPI/Git separados de aprender UX/UI. Conserva una captura antes de corregir.
4. Revisa experiencia y resumen, elige niveles, activa Recomendaciones y confirma.
5. Espera el guardado, ve al inicio y abre Mi perfil. Recarga.

**Esperado:** nombre y datos confirmados persisten; no hay error de análisis que obligue normalmente a reintentar. Con Nomic disponible, estado listo. Si aparece un error, registra tipo, duración y salida; no lo marques aprobado solo porque luego funcione.

### R02 — Demostrar cuándo aparecen los candidatos

1. Con **solo P01 confirmado**, publica PR01. Debe mostrar cero candidatos, con explicación de consentimiento/perfiles y dos roles pendientes.
2. En otra pestaña registra P02. Detente en la revisión IA antes de confirmar: aún no debe aparecer como habilidad confirmada en PR01.
3. Confirma P02 con recomendaciones activadas. En P01 pulsa Actualizar candidatos o recarga PR01.
4. Debe aparecer una tarjeta Persona #…; abre Ver perfil y comprueba que es Beatriz y que SQL/Git son sus fortalezas.
5. Crea y confirma P03 en otra pestaña. Actualiza PR01.

**Esperado:** con solo esas tres cuentas hay dos candidatos, uno con SQL/Git y otro con Figma. Figma no se atribuye a P02 ni SQL a P03. Con el resto de la batería cargado pueden aparecer más perfiles parciales; ya no exijas exactamente dos ni un orden fijo. El creador nunca aparece como candidato propio.

### R03 — Recomendación de proyectos para los candidatos

1. Desde P02 y P03, al terminar el perfil pulsa Explorar para abrir Proyectos para ti. También puedes entrar en Inicio.
2. Busca PR01 entre las recomendaciones y abre Ver proyecto.
3. Lee la explicación: P02 acredita SQL; P03 Figma; el resto global puede quedar Requiere revisión.

**Esperado:** proyecto real con su título e ID actuales, sin datos de demostración ni habilidades inventadas. Si otros proyectos existen, puede haber varias páginas/tarjetas; no exijas que PR01 sea siempre el primero.

### R04 — Invitación del organizador al especialista SQL

1. En la sesión P01 abre el perfil de P02 desde candidatos y revisa habilidades permitidas.
2. Selecciona PR01 y el rol **especialista en bases de datos**. Pulsa Invitar.
3. En el diálogo usa el mensaje: `Hola Beatriz, tu SQL y Git aportan al gestor de tareas. Te invito al rol de especialista en bases de datos.`
4. Pulsa **Enviar invitación**. Abrir el diálogo sin enviar todavía no crea la invitación.
5. Antes de aceptar, actualiza los candidatos de PR01: P02 debe estar excluida por acción pendiente.
6. En P02 abre Notificaciones → Responder (o Invitaciones desde Inicio/Mis equipos) y acepta.
7. En ambas cuentas abre Mis equipos, entra en PR01 y recarga.

**Esperado:** invitación aceptada, P02 incorporada una sola vez con su rol; dos integrantes contando al creador. SQL/Git cubiertos y Figma por acreditar. El mensaje «Te uniste al equipo» corresponde a P02, que está aceptando una invitación. No supera capacidad ni duplica integrantes al recargar.

### R05 — Solicitud de P03 y aceptación por el creador

1. No invites primero a P03: este caso prueba el sentido opuesto.
2. En la sesión P03 abre PR01 y pulsa Solicitar unirme. Selecciona **diseñador UX/UI**.
3. Mensaje: `Tengo experiencia en Figma, UX/UI y prototipado. Solicito la vacante de diseño.` Pulsa Enviar solicitud.
4. En P01 abre la solicitud recibida y acepta. En este paso P01 no se incorpora de nuevo.
5. Recarga el equipo desde P01, P02 y P03. Vuelve al detalle del proyecto.

**Esperado:** tres integrantes, dos roles cubiertos, Figma/SQL/Git cubiertos. P01 ve «Solicitud aceptada» o equivalente dirigido al creador, no «Tú te uniste». PR01 sin vacantes no debe seguir ofreciendo nuevas incorporaciones imposibles. Miembros y proyectos propios quedan fuera de las recomendaciones correspondientes.

### R06 — Duplicados y cupos, sin alterar datos por SQL

1. En una ejecución nueva de PR01 o antes de R05, intenta repetir la invitación SQL mientras está pendiente, incluso desde una pestaña antigua.
2. Desde P02 intenta enviar adhesión al mismo proyecto cuando ya existe esa invitación pendiente.
3. Después de aceptar, intenta invitar a la misma integrante o aceptar desde otra pestaña obsoleta.
4. Con PR01 lleno, abre el proyecto como otra cuenta de la batería.

**Esperado:** la UI deshabilita/retira acciones o el backend rechaza con conflicto; no aparecen dos solicitudes pendientes para el mismo par/proyecto ni dos filas de integrante. Una aceptación doble no agrega otra persona. Capacidad libre sin rol utilizable tampoco basta para marcar Disponible. Un 409 ante un estado que cambió es una protección correcta, no una recomendación garantizada.

### R07 — Videojuegos y complementariedad

1. Crea P04 y P05, revisando UE5/Unreal Engine 5 y Blender según sus fichas.
2. P04 publica PR02, revisa requisitos y encuentra a P05 entre los candidatos.
3. Abre el perfil de P05: no debe decir que sabe UE5. Invítala al rol artista 3D y acepta desde P05.
4. Recarga el equipo desde ambas sesiones.

**Esperado:** el creador aporta UE5/diseño de niveles/Git y Elena Blender; rol artista 3D cubierto, dos integrantes y proyecto sin vacantes. Querer aprender Blender no acredita esa habilidad a P04 ni P03. No exige que solo exista un candidato en toda la base.

### R08 — Fútbol y diferencia entre roles/habilidades

1. Crea P06, P07 y P08. Verifica que negaciones y «No tengo experiencia profesional» no generen capacidades/trayectoria inventadas.
2. P06 publica PR03 y comprueba portero, defensa y la condición de lunes por la tarde.
3. Invita P07 como portero y acepta. Abre el equipo antes de incorporar a P08.
4. Verifica que puede decir portero/defensa cubiertos como habilidades, aunque falta asignar el rol defensa.
5. Invita o recibe solicitud de P08 para defensa y acepta. Recarga.

**Esperado:** primero dos integrantes y un rol pendiente; al final tres integrantes, ambos roles cubiertos. Hugo no acredita portero. El horario puede quedar por verificar: no inventar una validación de horas exactas ni promoverlo como requisito técnico.

### R09 — Negaciones, intereses y consentimiento

1. Crea P09, P10 y P11 y aplica la pausa de Kevin.
2. Publica PR04 y PR05. Abre candidatos con P01.
3. P10 y P11 no deben aparecer mientras no tengan consentimiento o estén pausados.
4. Si P09 aparece, comprueba su explicación: Git puede estar acreditado; Python/SQL/Docker no. No marques fallo solo porque tenga evidencia parcial y Requiere revisión.
5. Desde P10 intenta abrir sus proyectos recomendados: debe indicar la condición de consentimiento, sin 500 ni sugerencias privadas ajenas.
6. Activa voluntariamente recomendaciones en P10, guarda y actualiza; ahora SQL puede acreditarse. Después restaura su consentimiento desactivado.
7. Quita temporalmente la pausa de P11 y actualiza PR05; Figma puede acreditarse. Restaura la pausa al acabar.

**Esperado:** las exclusiones cambian al cambiar permisos reales, sin modificar cuentas ajenas. Las recomendaciones se recalculan al actualizar/recargar; no prometen actualización en vivo entre pestañas sin nueva consulta.

### R10 — Habilidades ocultas y biografía pública

1. Desde P02, Mi perfil → Editar: desactiva Mostrar mis fortalezas y cambia su biografía a `Perfil ficticio de QA con fortalezas ocultas.`
2. Guarda, revisa y confirma si la UI lo solicita. Consulta su perfil desde P01 y revisa PR04.
3. No debe publicarse la lista SQL/Git ni acreditarse SQL mediante el campo oculto. La persona podría seguir apareciendo con datos permitidos y requisitos desconocidos.
4. Vuelve a activar fortalezas y restaura el resumen de P02; confirma los cambios.

**Esperado:** privacidad por campo respetada. Si no cambias la biografía, esta puede seguir revelando SQL porque es un texto público independiente; ocultar fortalezas no promete redactarla automáticamente. No confundas un interés visible con una habilidad acreditada.

### R11 — Editar proyecto, invalidar IA y reconfirmar

1. Usa PR05 todavía sin integrantes y guarda una captura de Figma obligatorio.
2. En P01, Editar proyecto: cambia la descripción por `Analizaremos datos de una aplicación educativa. Buscamos especialista en bases de datos con SQL obligatorio. Figma no es obligatorio.`
3. Cambia el rol vacío a **especialista en bases de datos** y sus habilidades a **SQL**. Mantén capacidad 2; guarda.
4. La pantalla debe avisar que requiere revisión; no tratar el antiguo Figma obligatorio/vector/cobertura como actuales.
5. Pulsa Interpretar descripción actual con IA. Revisa: SQL obligatorio, Figma no obligatorio; elimina requisitos viejos sin respaldo.
6. Marca la revisión y pulsa Confirmar y generar análisis. Si Nomic queda pendiente, usa el reintento del vector.
7. Actualiza candidatos y recarga el proyecto.

**Esperado:** estado listo cuando el servicio responde; P02 acredita SQL; P03 no pasa a dominar SQL por haber sido recomendada antes para diseño. Puede seguir apareciendo como parcial/desconocida, pero Figma no puede seguir declarado obligatorio obsoleto. El formulario maneja la huella de revisión: no tienes que escribir un hash. No intentes borrar roles ocupados ni reducir capacidad por debajo de un equipo existente para ejecutar este caso.

### R12 — Editar perfil y actualizar evidencia

1. Con P02 incorporada a PR01, abre su perfil en edición y elimina SQL de fortalezas. Reescribe el resumen a `Uso Git y me interesan las aplicaciones web.`
2. Guarda y observa el estado de revisión, sin acreditar la versión anterior como si estuviera vigente.
3. Marca la revisión y pulsa Confirmar y generar análisis. Consulta PR04 y el equipo PR01 desde P01; recarga.
4. SQL no debe acreditarse por el vector viejo. El equipo conserva a P02, pero su cobertura SQL puede quedar por acreditar.
5. Restaura SQL y el resumen original de P02; confirma para devolver la batería a su estado inicial.

**Esperado:** cambia la evidencia, no desaparece la membresía. Un vector obsoleto no resucita SQL. Si el candidato todavía aparece, su explicación debe reflejar SQL desconocido, no un cumplimiento inventado.

### R13 — Recuperación de IA sin detener Ollama compartido (opcional)

Usa **solo tu terminal QA 8011**. Hazlo antes de registrar P09, o con el mismo perfil y un correo de sufijo nuevo; no alteres el backend habitual ni el servicio Ollama de otras tareas.

1. `Ctrl+C` en el backend QA, manteniendo esa terminal y su AUTH_SECRET/DATABASE_URL.
2. En esa misma terminal apunta únicamente este proceso a un host inaccesible:

```powershell
$env:OLLAMA_HOST='http://127.0.0.1:9'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8011
```

3. Registra P09 y avanza hasta interpretar: debe verse error recuperable, con los textos conservados. Registra duración y HTTP 503 en red; no copies tokens.
4. Detén solo ese servidor QA. Restaura el host e inicia otra vez:

```powershell
$env:OLLAMA_HOST='http://127.0.0.1:11434'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8011
```

5. Pulsa el botón de reintento del análisis sin escribir todo de nuevo; revisa y confirma.
6. Para ensayar **Nomic** por separado, realiza un análisis exitoso y, antes de confirmar/publicar, deja inaccesible solo el backend QA del mismo modo. La confirmación debe guardarse con pendiente_embedding; la creación de un proyecto no debe devolver 500 después de persistir.
7. Restaura el host; desde el perfil/detalle usa el reintento del embedding. Si repites un envío de la misma publicación desde su borrador, no debe crear otra fila por un fallo previo del vector.

**Esperado:** borrador y confirmación conservados, recuperación sin pérdida de cuenta ni publicaciones duplicadas por el mismo intento, estado listo al completar Nomic. Un estado sin_contenido no es un fallo de conexión; para generarlo hacen falta datos confirmables, no inventar habilidades. No ejecutes este ensayo contra servicios compartidos.

### R14 — Accesos, persistencia y casos negativos básicos

| Acción manual | Esperado |
| --- | --- |
| Recargar equipo y volver a entrar con login | Mismos miembros y roles persistidos |
| Abrir una pantalla privada en pestaña sin sesión | Redirige a login; no entrega datos privados |
| Otro usuario intenta administrar candidatos/editar un proyecto ajeno | Sin acción autorizada; backend rechaza acceso si se solicita la ruta protegida |
| Registrar otra cuenta con el mismo correo | Error de duplicado; no otra cuenta creada |
| Registro con contraseña vacía/corta | Validación de alta, mínimo 8; no usar ese resultado como un ensayo de IA |
| Login con contraseña incorrecta | Rechazo, sin sesión autenticada |
| P12 texto ambiguo | Sin capacidades inventadas; confirmación deshabilitada por cero fortalezas, límite conocido del onboarding |
| Reuniones | Aviso de no disponible, sin anunciar un envío persistido |

La UI no ofrece controles para cambiar estado_cuenta a inactiva, vacantes múltiples o evidencia negativa estructurada. Esas pruebas necesitan API/QA técnica; no inventes botones en este recorrido. Tampoco hay que exigir porcentajes de compatibilidad o coincidencia exacta de horarios que el MVP no implementa.

<a id="registro-resultados"></a>
## 6. Qué registrar y cuándo darlo por aprobado

Completa una fila por caso y conserva por separado lo que propuso Llama y lo que confirmaste tú:

| Caso | Cuenta / proyecto e ID real | Entrada usada / variación | Tiempo IA y reintentos | Salida original / omisión o invención | Corrección humana | Resultado final y captura | Estado |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R01 | P01 / ID… | Texto de ficha | … s / … | … | … | … | APROBADO / FALLIDO / BLOQUEADO |
| R02 | P02, P03 / PR01… | Consentimiento antes/después | … | … | … | … | … |

APROBADO: ocurrió el resultado concreto observado. FALLIDO: apareció capacidad inventada, se perdió una habilidad explícita, falló el contrato, hubo error de aplicación o persistencia incoherente. BLOQUEADO: faltó servicio, permiso o respuesta evaluable. No declarar un caso aprobado por leer código ni ocultar un fallo original porque el reintento o la corrección humana lo arregló.

### Comprobación opcional de MySQL, solo lectura en QA

Primero comprueba `SELECT DATABASE();` y que sea tu QA. Sustituye IDs por los que generaste:

```sql
SELECT DATABASE();
SELECT id_evento, id_usuario, rol FROM participantes_evento ORDER BY id_evento, id_usuario;
SELECT id_evento, estado FROM solicitudes_equipo ORDER BY id_evento;
SELECT usuario_id, perfil_estado_ia, JSON_LENGTH(embedding_perfil) AS dimensiones,
       perfil_embedding_fuente_revision = perfil_fuente_revision AS revision_actual
FROM perfiles_usuarios;
SELECT id_evento, estado_ia, JSON_LENGTH(embedding_requisitos) AS dimensiones,
       embedding_fuente_revision = requisitos_fuente_revision AS revision_actual
FROM eventos;
```

Con Nomic operativo, los vectores confirmados listos deben tener 768 dimensiones y revision_actual=1. Un perfil no confirmado, obsoleto, sin_contenido o pendiente puede carecer de vector; no es correcto contarlo como vector listo. Los DTO públicos omiten embeddings intencionalmente.

**Cierre mínimo presentable:** R01–R05 completos sin errores inesperados; candidatos explicados por hechos confirmados, invitación y adhesión aceptadas con miembros correctos, equipo persistido tras recargar, consentimiento/pausa respetados, sin capacidades negadas o deseadas acreditadas. Amplía con R07–R13 para diversidad de dominio y recuperación. Al terminar, cierra solo los servidores y terminales QA que abriste; conserva la base ficticia y tus evidencias, sin limpiar ni reiniciar la principal. Para volver al arranque habitual abre terminales nuevas sin esas variables QA; cambiar de carpeta no elimina las variables de la terminal.
