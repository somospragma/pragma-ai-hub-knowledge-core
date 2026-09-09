---
id: calidad-session-continuity-protocol
version: 1.1.0
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

## Una certificación son varias sesiones cortas, no una larga

La traza existe para que **cortar la sesión sea barato**. Una certificación
completa en una sola sesión acumula contexto hasta que el resumidor automático
empieza a descartar cosas, y lo primero que descarta es lo que se leyó al
principio: las compuertas. Ese es el mecanismo por el que un agente incumple una
regla que sí tenía delante en el turno 1.

**Corta al terminar cada fase**, no cuando el contexto ya se te esté yendo:

`diseño` → `generación` → `estabilización por plataforma`, una por sesión →
`publicación`

Señales de que la sesión ya debió cortarse, y cualquiera basta:

- Estás **releyendo** un archivo que ya abriste en esta misma sesión.
- No recuerdas una corrección del usuario sin volver a buscarla.
- Te falta contexto para responder algo que ya se decidió aquí.

Cuando aparezca alguna: **escribe la entrada de cierre con el punto exacto de
retome y dilo**. Reconstruir desde una traza de 2 KB cuesta menos que seguir
tirando de una sesión que ya perdió la mitad de lo que sabía. Continuar por
inercia no ahorra: multiplica el costo de cada turno restante y degrada lo que se
entrega.

## El traspaso tiene techo, y no absorbe al anterior

El resumen de traspaso se paga **dos veces**: al escribirlo en el cierre, y al reinyectarlo en la apertura de la sesión siguiente. Por eso su tamaño importa más que el de cualquier otro mensaje.

Medido en la certificación de referencia: seis traspasos que suman 104.290 caracteres —unos 29 mil tokens— y que **crecen sesión a sesión**: 12.706 → 16.003 → 14.688 → 19.473 → 18.089 → 23.331. El patrón es inequívoco: cada traspaso **copiaba** al anterior en lugar de apuntar a la traza, así que el último arrastraba todo lo que había pasado en cinco días.

La regla: el traspaso es **estado, siguiente acción y punteros**, y no supera una pantalla. Todo lo que necesite contarse en detalle ya está en la bitácora — se cita el archivo y la sección, no se copia. **Un traspaso que crece de una sesión a la siguiente es la señal de que se está copiando en vez de apuntando**, y se corta ahí mismo.

## Lo que nunca debes hacer

- **NUNCA** empezar a editar, generar o ejecutar sin haber leído la traza y la bitácora de un `output_path` que ya existe. Una sesión que arranca "donde cree que iba" repite fases y pierde correcciones ya pagadas.
- **NUNCA** reconstruir el estado de memoria ni del resumen automático de contexto: el resumen habla de archivos, no de proceso.
- **NUNCA** cerrar sesión sin escribir la entrada de cierre con el punto exacto de retome.
- **NUNCA** reescribir, resumir ni compactar la bitácora: es append-only.
- **NUNCA** dejar que el traspaso de una sesión absorba al de la anterior. Se apunta a la bitácora, no se la copia; si el traspaso creció respecto al previo, se recorta antes de cerrar.

**Nota de enforcement**: esto es contexto, no configuración forzada. Cuando el IDE lo permita, respaldarlo con un hook de inicio de sesión que inyecte la traza; el protocolo lo hace probable, el hook lo hace seguro.
