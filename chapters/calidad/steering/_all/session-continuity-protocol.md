---
id: calidad-session-continuity-protocol
version: 1.0.0
scope: chapter
type: steering
chapter: calidad
description: "Primer turno de toda sesión: si el output_path ya tiene evidencia, leer la traza y la bitácora y reportar dónde quedó el proceso ANTES de responder cualquier otra cosa. Aplica sin importar qué pida el usuario."
tags: [protocol, mandatory, session, continuity, traza, bitacora, enforcement]
---

# Session Continuity Protocol — Antes de Responder, Saber Dónde Quedaste

## Rol

Toda sesión del Chapter Calidad empieza leyendo el pasado. **Aplica sin importar qué pida el usuario**: "continúa", "corre los tests", "arregla esto" o una pregunta suelta. Si el `output_path` de la corrida ya tiene `.evidence/`, el primer turno hace esto antes que nada:

1. Leer `.evidence/pipeline-state.json` y `.evidence/session-log.md` (`[[calidad-pipeline-state-tracking]]`).
2. Abrir la respuesta con: **fase actual · siguiente acción · bloqueos vigentes · pendientes abiertos · correcciones del usuario aún vigentes**, estas últimas reafirmadas en voz alta.
3. Recién entonces atender lo que el usuario pidió.

Si no existen, crearlos antes de trabajar. Si el usuario pide algo que contradice `next_action`, decirlo y dejar que él decida; no se descarta la traza en silencio.

## Lo que nunca debes hacer

- **NUNCA** empezar a editar, generar o ejecutar sin haber leído la traza y la bitácora de un `output_path` que ya existe. Una sesión que arranca "donde cree que iba" repite fases y pierde correcciones ya pagadas.
- **NUNCA** reconstruir el estado de memoria ni del resumen automático de contexto: el resumen habla de archivos, no de proceso.
- **NUNCA** cerrar sesión sin escribir la entrada de cierre con el punto exacto de retome.
- **NUNCA** reescribir, resumir ni compactar la bitácora: es append-only.

**Nota de enforcement**: esto es contexto, no configuración forzada. Cuando el IDE lo permita, respaldarlo con un hook de inicio de sesión que inyecte la traza; el protocolo lo hace probable, el hook lo hace seguro.
