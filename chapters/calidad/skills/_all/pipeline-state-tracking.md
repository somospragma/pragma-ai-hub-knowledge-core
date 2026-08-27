---
id: calidad-pipeline-state-tracking
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "OBLIGATORIO. Traza viva del pipeline en .evidence/pipeline-state.json más la bitácora append-only .evidence/session-log.md: qué fase está hecha, cuál falta, con qué evidencia y qué pasó en el camino. Se escriben tras cada fase y evento, y se leen al abrir CUALQUIER sesión, para que el proceso sobreviva a los cortes de contexto."
tags: [pipeline, state, traceability, session-continuity, session-log, mandatory, gate, universal]
enforcement: mandatory
verification:
  - check: "al iniciar cualquier sesión sobre un output_path existente, se leyeron .evidence/pipeline-state.json y .evidence/session-log.md y se reportó al usuario dónde quedó el proceso"
    failure_message: "Bloqueado: se retomó trabajo sin leer la traza ni la bitácora. Riesgo de repetir fases, saltarse pendientes y perder las correcciones del usuario."
  - check: "cada fase completada actualizó su entrada en pipeline-state.json con status, timestamp y evidencia verificable"
    failure_message: "Bloqueado: hay fases ejecutadas sin registrar en la traza. La traza desactualizada es peor que no tenerla."
  - check: "ninguna fase se marcó done sin la evidencia que su propio gate exige"
    failure_message: "Bloqueado: fase marcada done sin evidencia. Marcar done por haberlo intentado es falsear la traza."
  - check: "la bitácora tiene al menos una entrada por cada fase marcada done y por cada escritura ejecutada en el ALM"
    failure_message: "Bloqueado: hay fases o escrituras sin registro en la bitácora. Una traza sin historia no permite retomar ni auditar."
---

# Pipeline State Tracking — La Traza que Sobrevive a la Sesión

## Problema que resuelve

Una generación real no cabe en una sesión: el contexto se llena y el trabajo continúa en otra instancia con un resumen automático que habla de **archivos**, no de **proceso**. Verificado en campo: seis sesiones encadenadas donde el agente saltó fases, repitió trabajo, olvidó correcciones del usuario dentro de la misma sesión y emitió el contrato de cierre dos veces sin haber ejecutado la suite. El conocimiento del chapter no falla ahí; falla la **memoria del progreso**.

La traza es un archivo en disco, no un recuerdo: `.evidence/pipeline-state.json` en el `output_path`.

Pero la traza registra **fases**, no **historia**, y eso no alcanza. Verificado en campo tras varias sesiones encadenadas: el flujo se perdió por completo — el agente no sabía qué se había intentado, qué había fallado, qué había pedido el usuario ni por qué se decidió lo que se decidió. Por eso la traza tiene un hermano **append-only**: `.evidence/session-log.md`.

**Los dos son obligatorios y cumplen funciones distintas**: el estado dice *dónde estamos*; la bitácora dice *cómo llegamos*. El primero se actualiza; la segunda solo crece.

## Cuándo aplicar

- **Al inicio de CUALQUIER sesión** (nueva o continuación) sobre un `output_path` que ya existe: leer la traza ANTES de hacer nada y reportar al usuario en qué fase quedó, qué sigue y qué está bloqueado. Es el paso 0 de `[[calidad-route-test-generation]]`.
- **Tras completar cada fase** del pipeline: actualizarla en el mismo turno en que la fase termina.
- **Antes de emitir `[[calidad-delivery-gate-contract]]`**: el gate lee la traza y no se emite con fases obligatorias pendientes.

Aplica a los stacks de automatización (Karate, Playwright, K6, Appium Serenity, Appium WebdriverIO, serenity-wdio) y a la ruta funcional; las fases cambian por ruta, el mecanismo no.

## Schema

```json
{
  "schema_version": "1.0",
  "run_id": "2026-08-10T14:05:00Z",
  "project_name": "appium-poc-flujo-credito",
  "stack": "appium",
  "route": "greenfield",
  "mode": "full",
  "execution_target": "mock",
  "sessions": 3,
  "phases": [
    {
      "id": "mandatory_inputs",
      "status": "done",
      "updated_at": "2026-08-10T14:07:11Z",
      "evidence": ".evidence/session-config.json",
      "notes": "5 insumos recibidos; extracción declarada por insumo"
    },
    { "id": "sut_readiness_gate", "status": "done", "evidence": "STRATEGY.md#6" },
    { "id": "strategy_approved",  "status": "done", "evidence": "STRATEGY.md (aprobado por usuario 14:22)" },
    { "id": "mock_up",            "status": "done", "evidence": ".evidence/mock-verification.json" },
    { "id": "prototype_accepted", "status": "blocked", "blocker": "parity_gate_failed: 3 selectores con 0 coincidencias" },
    { "id": "scaffold_emitted",   "status": "pending" },
    { "id": "instrumentation_verified", "status": "pending" },
    { "id": "smoke_gate",         "status": "pending" },
    { "id": "suite_executed",     "status": "pending" },
    { "id": "report_verified",    "status": "pending" },
    { "id": "triage_and_correction", "status": "pending" },
    { "id": "executive_report",   "status": "pending" },
    { "id": "delivery_gate",      "status": "pending" }
  ],
  "next_action": "Corregir los 3 identificadores faltantes en el prototipo y re-correr el gate de paridad",
  "open_corrections": [
    "Usuario pidió usar evidencia visual antes de hipotetizar (sesión 2) — aplicar en todo triage"
  ]
}
```

`status`: `pending | in_progress | done | blocked | skipped`. Todo `skipped` lleva `reason`; todo `blocked` lleva `blocker` con evidencia del sondeo que lo comprobó (ver Restricciones).

`open_corrections` es la memoria de las instrucciones que dio el usuario y que aplican a todo el resto del trabajo: se arrastran entre sesiones y **se reafirman en voz alta** al abrir cada una, no solo se releen. Una corrección del usuario que se pierde al cambiar de sesión se paga dos veces.

## La bitácora: `.evidence/session-log.md`

**Append-only. Nunca se reescribe, nunca se resume, nunca se compacta.** Una bitácora reconstruida o condensada pierde justo lo que la hace útil: el detalle de lo que ya se intentó y falló.

Una entrada por evento significativo, con marca de tiempo:

```markdown
## Sesión 3 — 2026-08-13

- `14:02` **Apertura.** Fase actual: suite_executed. Pendiente: triage. Bloqueos: ninguno.
  Correcciones vigentes: usar evidencia visual antes de hipotetizar.
- `14:05` **Comando** `<comando>` → exit 0. Evidencia: `reports/...`
- `14:11` **Decisión**: se ancla la aserción por rótulo y no por el nombre del registro.
  Motivo: el contenido es volátil, verificado en dos corridas.
- `14:18` **Instrucción del usuario** (textual): "no ejecutes la suite completa hasta que
  el primero pase". → agregada a open_corrections.
- `14:30` **Bloqueo**: dispositivo no autorizado. Evidencia: salida de `<comando>`.
- `14:41` **Escritura en ALM**: 4 casos creados. Autorizó: usuario, 14:39. Resultado: 4 OK.
- `15:02` **Cierre.** Retomar en: triage del escenario 3.
```

### Granularidad mínima (regla contable, no criterio)

"Una entrada por evento significativo" se interpreta a la baja bajo presión de contexto. La regla es contable:

- **Una entrada por cada turno del usuario**, con lo que pidió.
- **Una entrada por cada lote de acciones** del agente: comandos ejecutados, archivos emitidos, consultas al ALM.
- **Una entrada por cada uno** de estos, sin agrupar: comando con su código de salida, decisión con su motivo, instrucción del usuario **citada textualmente**, bloqueo con la evidencia que lo comprueba, corrección aplicada con su resultado, y escritura en el ALM con quién autorizó (`[[calidad-alm-write-authorization-gate]]`).
- **Escrita en el turno en que ocurre**, nunca "al final". Una bitácora redactada al cierre es un resumen, y el resumen es justo lo que se pierde.

Si una sesión termina con menos entradas que turnos del usuario, la bitácora está incompleta.

### Registro de pendientes

Cada entrada de cierre lleva un bloque de pendientes, **reescrito** (no acumulado) para reflejar el estado actual. Es lo distinto de `next_action`, que es una sola línea, y de `open_corrections`, que son instrucciones del usuario:

```markdown
### Pendientes al cierre
- **A medias**: escenario 3 con el ancla corregida pero sin re-ejecutar.
- **Intentado y fallido**: instalación en el dispositivo físico — rechaza el paquete; falta provisionar.
- **Esperando a un tercero**: carga masiva de los 14 casos, pedida al equipo con permisos.
- **Decidido y no aplicado**: propagar a iOS las dos correcciones compartidas de Android.
```

Las cuatro categorías importan por separado: "intentado y fallido" es lo que evita repetir el mismo callejón, y "esperando a un tercero" es lo que evita declarar bloqueada una entrega que solo está en cola.

### Rotación: append-only no significa sin techo

Una bitácora append-only crece sin límite, y este mismo protocolo obliga a leerla
al abrir cada sesión. En una certificación larga eso se vuelve el gasto fijo más
grande de la sesión: **medido, una bitácora de 93 KB —unos 26.000 tokens— releída
en cada apertura**, además de todo lo demás.

Rotar **no es** reescribir ni resumir, que es lo que el append-only prohíbe. Es
**mover texto verbatim a otro archivo**:

- El archivo activo `.evidence/session-log.md` tiene un **techo** (referencia:
  unas 400 líneas). Al superarlo, las entradas más antiguas se **mueven tal cual**
  a `.evidence/session-log-archive-{YYYYMMDD}.md`.
- El activo conserva **la sesión en curso y la anterior completas**, más un índice
  de una línea por sesión archivada: fecha, fases cubiertas, archivo.
- **Nada se edita al mover.** Si hay que cambiar una palabra, no es rotación.

**El ritual de apertura lee el activo, no el archivo.** El archivado se abre solo
cuando hay una pregunta concreta que solo él contesta —"¿ya intentamos esto?"—, y
se abre por búsqueda, no entero.

Lo que **nunca** se rota son los `open_corrections` ni los pendientes: viven en
`pipeline-state.json` y en el bloque de cierre del activo, que es donde el ritual
de apertura los busca.

## Rituales de sesión

Los rituales viven además en el steering `[[calidad-session-continuity-protocol]]`, que es lo que garantiza que se disparen aunque la sesión abra con una petición cualquiera y este skill no se cargue.

**Apertura (obligatorio, antes de tocar ningún archivo).** El primer mensaje de toda sesión sobre un `output_path` existente lee estado y bitácora, y responde con: fase actual, siguiente acción, bloqueos vigentes, pendientes abiertos y las `open_corrections` reafirmadas. Sin ese resumen no se empieza a trabajar.

**Cierre.** Ante señal de cierre o de contexto lleno, se escribe la entrada final con el bloque de pendientes y el punto exacto de retome. Es lo que va a leer la sesión siguiente.

**Límite honesto de este mecanismo.** La traza y la bitácora son **contexto, no configuración forzada**: dependen de que el agente decida leerlas. El respaldo real, donde el IDE lo soporte, es un **hook de inicio de sesión** que inyecte el estado sin depender de esa decisión. Mientras no exista, este protocolo lo hace probable; no lo hace seguro. Ya se verificó en campo que un mandato equivalente escrito solo como skill no se cumplió.

## Fases mínimas por ruta

| Ruta | Fases obligatorias |
|---|---|
| Automatización (todos los stacks) | mandatory_inputs · [capability_map si brownfield] · sut_readiness_gate · strategy_approved · [mock_up · prototype_accepted si aplica] · scaffold_emitted · instrumentation_verified · preflight · smoke_gate · suite_executed · report_verified · triage_and_correction · executive_report · delivery_gate |
| Funcional | mandatory_inputs · insumos_analizados · [analysis · refinement_approved] o [design_traceability] o [strategy/plan_approved] · alm_write_confirmed · delivery_gate |

Las fases de mock/prototipo solo existen si `execution_target != real`. `executive_report` se marca `skipped` con razón en modos `scaffold-only`/`dry-run`.

## Instrucción

1. **Abrir sesión**: si existe `.evidence/pipeline-state.json`, leerlo junto con `.evidence/session-log.md` y abrir el turno con el ritual de apertura — fase actual, qué falta, qué está bloqueado — más las `open_corrections` reafirmadas. Si no existen y el `output_path` es nuevo, crearlos: el estado con todas las fases en `pending`, la bitácora con la entrada de apertura.
2. **Trabajar la fase**: marcarla `in_progress` al empezar.
3. **Cerrar la fase**: marcarla `done` **solo con la evidencia que su gate exige** (path del archivo, comando y exit code, o confirmación explícita del usuario). Sin evidencia no hay `done`.
4. **Registrar correcciones del usuario** en `open_corrections` y, textualmente, en la bitácora, en el mismo turno en que las recibe.
5. **Actualizar `next_action`** en cada escritura: es lo primero que lee la siguiente sesión.
6. **Anotar en la bitácora** cada evento significativo en el turno en que ocurre, y la entrada de cierre al terminar la sesión.

## Restricciones

- **NUNCA marcar `done` una fase por haberla intentado.** Compilar no es ejecutar; ofrecer no es aprobar; generar no es verificar.
- **NUNCA declarar `blocked` sin evidencia del sondeo.** Un blocker de ambiente exige el comando ejecutado y su salida (`adb devices`, `curl` al mock, `appium --version`). Declarar bloqueos por suposición y cerrar sobre ellos ya ocurrió en campo: dos de tres bloqueos declarados eran falsos y el gate se emitió igual.
- **NUNCA emitir el delivery gate con fases obligatorias en `pending`** — el gate lee esta traza (`[[calidad-delivery-gate-contract]]`).
- La traza **no reemplaza** la evidencia: la referencia. Si el `evidence` apunta a un archivo que no existe, la fase no está `done`.
- La traza se actualiza en el turno de la fase, no "al final": una traza reconstruida de memoria es ficción.
- **NUNCA reescribir, resumir ni compactar la bitácora.** Es append-only por diseño: lo que se borra es justamente el detalle de lo ya intentado, que es lo que evita repetirlo. Rotar sí está permitido, y es otra cosa: mover entradas verbatim a un archivo fechado, sin tocar una palabra.
- **NUNCA leer el archivado en el ritual de apertura.** Se abre solo ante una pregunta concreta que solo él contesta, y por búsqueda.
- **NUNCA empezar a trabajar sin el ritual de apertura** cuando el `output_path` ya existe. El delivery gate no se emite si la bitácora tiene menos entradas que fases marcadas `done`.

## Verificación

Asset de **cumplimiento obligatorio**. Antes de cerrar la fase que lo invoca, comprobar cada punto. Si alguno no se cumple, se detiene y se reporta con el mensaje indicado.

| # | Comprobación | Si no se cumple |
|---|---|---|
| 1 | al iniciar cualquier sesión sobre un output_path existente, se leyeron .evidence/pipeline-state.json y .evidence/session-log.md y se reportó al usuario dónde quedó el proceso | Bloqueado: se retomó trabajo sin leer la traza ni la bitácora. Riesgo de repetir fases, saltarse pendientes y perder las correcciones del usuario. |
| 2 | cada fase completada actualizó su entrada en pipeline-state.json con status, timestamp y evidencia verificable | Bloqueado: hay fases ejecutadas sin registrar en la traza. La traza desactualizada es peor que no tenerla. |
| 3 | ninguna fase se marcó done sin la evidencia que su propio gate exige | Bloqueado: fase marcada done sin evidencia. Marcar done por haberlo intentado es falsear la traza. |
| 4 | la bitácora tiene al menos una entrada por cada fase marcada done y por cada escritura ejecutada en el ALM | Bloqueado: hay fases o escrituras sin registro en la bitácora. Una traza sin historia no permite retomar ni auditar. |

## Cross-links

`[[calidad-route-test-generation]]`, `[[calidad-delivery-gate-contract]]`, `[[calidad-smoke-gate-policy]]`, `[[calidad-mandatory-inputs-protocol]]`, `[[calidad-test-evidence-and-traceability]]`, `[[calidad-post-generation-execution-prompt]]`, `[[calidad-execution-preflight]]`, `[[calidad-repo-capability-discovery]]`, `[[calidad-alm-write-authorization-gate]]`, `[[calidad-cross-platform-learning-propagation]]`.
