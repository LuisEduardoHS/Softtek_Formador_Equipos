# Documentación de Complementa

## Para empezar

1. [Clonar, configurar e iniciar](../README.md).
2. [Guía manual completa: 12 perfiles, 5 proyectos y resultados esperados](pruebas-manuales/guia-completa.md).
3. [Perfiles y proyectos con IA: operación y recuperación](operacion/ia-perfiles-proyectos.md).
4. [Recomendaciones, privacidad, invitaciones y equipos](operacion/recomendaciones-equipos.md).

## Estado y evidencia

| Documento | Para qué sirve |
| --- | --- |
| [Candidatos vacíos y consentimiento](qa/informes/2026-10-26-consentimiento-candidatos.md) | Caso MANUAL01, permisos de Beatriz/Carla, atajo de activación y elección en registro |
| [Seguimiento del MVP](qa/seguimiento-mvp.md) | Historial de correcciones y límites; las últimas secciones recogen el cierre más reciente |
| [Validación final del flujo web](qa/informes/2026-10-26-flujo-web.md) | Perfil IA → candidatos reales → equipo; tres cuentas y otra convocatoria abierta |
| [Escenarios reales de matching](qa/informes/2026-10-26-escenarios-matching.md) | 14 escenarios, tres dominios visuales, extracción, concurrencia y límites de ranking |
| [Auditoría inicial](qa/informes/2026-10-25-auditoria-real.md) | Fallos originales antes de las correcciones; no describe el estado actual por sí sola |
| [Evidencias por ejecución](qa/evidencias/README.md) | JSON, logs y capturas ficticias que respaldan los informes |

## Diseño e historia

- [Diseño de matching](arquitectura/diseno-matching.md) y [recomendaciones](arquitectura/diseno-recomendaciones.md): decisiones de referencia previas a la integración. Los contratos actuales están en operación y código.
- [Archivo histórico](archivo/README.md): diagnóstico y cierre del 25 de octubre, conservados para entender la evolución.

## Organización y limpieza

```text
docs/
  README.md
  operacion/
  pruebas-manuales/
  qa/
    seguimiento-mvp.md
    informes/
    evidencias/
  arquitectura/
  archivo/
```

Se movieron y renombraron documentos para separar instrucciones actuales, pruebas y antecedentes. Se retiraron `.gitkeep` y los dos planes de integración del 21/22 de octubre, superados por la implementación y el seguimiento. El README genérico de Vite se sustituyó por instrucciones del cliente real. Los planes retirados siguen disponibles en Git; no se borraron evidencias de defectos ni resultados de auditoría.

Los enlaces Markdown internos apuntan a las nuevas ubicaciones. Los JSON/logs de evidencia conservan sus contenidos y pueden mencionar rutas antiguas del momento de ejecución; no son scripts de instalación ni una descripción de la estructura actual. No se cambiaron código de aplicación, esquema ni bases de datos en esta reorganización.
