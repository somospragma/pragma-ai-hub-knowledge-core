---
id: calidad-client-test-data-request
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "OBLIGATORIO al pedir datos de prueba al cliente. La solicitud se declara como datos y se renderiza, no se escribe como prosa: quien la recibe administra el ambiente y no conoce las historias. Enumeración uno a uno, nada derivable, nada de otro dueño, y una auditoría criterio a dato que condiciona la emisión."
tags: [datos-de-prueba, solicitud, cliente, cobertura, auditoria, alm, determinismo, mandatory]
enforcement: mandatory
verification:
  - check: "la solicitud existe como .evidence/data-request.json y el markdown entregado se genero desde ahi, no se escribio a mano"
    failure_message: "Bloqueado: la solicitud se escribio como prosa. Cada correccion de forma obliga entonces a reescribir el documento entero; medido en campo, cuatro de siete turnos de reproceso de una sesion fueron exactamente eso."
  - check: "check-data-coverage.py paso en verde y .evidence/data-coverage-audit.json lo registra antes de emitir o publicar la solicitud"
    failure_message: "Bloqueado: se iba a emitir sin cruzar los criterios contra los datos. Ya ocurrio pedir dos usuarios multiempresa y ningun monoempresa, que era el caso base de media docena de criterios; ninguna relectura lo encontro."
  - check: "todo item de la solicitud declara sujeto, condicion exigida y responsable, y solo viajan al cliente los de responsable cliente-datos"
    failure_message: "Bloqueado: hay items sin condicion exigida o de otro dueño en la solicitud. Quien administra el ambiente no puede conseguir un identificador que no sabe interpretar, y lo ajeno se queda sin canal."
  - check: "ningun dato derivable de otro ya pedido aparece en la solicitud, y el bloque de exclusiones declara el motivo de cada uno"
    failure_message: "Bloqueado: se esta pidiendo trabajo que no hace falta, o se omitio sin decir por que. Un derivable sin declarar genera la pregunta que el bloque de exclusiones existe para evitar."
---

# Solicitud de Datos de Prueba al Cliente

## Problema que resuelve

Antes de que exista una línea de automatización, alguien tiene que conseguir los datos con
los que se va a probar. En un cliente eso no es un `INSERT`: es un documento que viaja a
quien administra usuarios y productos del ambiente, y que puede tardar días en atenderse.

El chapter ya cubre la conversación hacia adentro —qué le dice el agente al QA cuando falta
un estado, en `[[calidad-test-data-management]]`—. Esto cubre la conversación **hacia
afuera**, que tiene otra audiencia, otra forma y otro riesgo: si el documento sale
incompleto, el hueco no se descubre revisándolo, se descubre el día de la ejecución.

Medido en una sesión real de trece historias: la solicitud se rehízo **cuatro veces**, y
ninguna de las cuatro trajo información nueva. Cambió la audiencia, cambió la columna de
trazabilidad, cambió el modelo de usuarios y faltó un caso base. Con la solicitud como
prosa, cada uno de esos cambios costó reescribir el documento entero.

## Cuándo aplicar

**Solo dentro de la ruta de análisis** (`[[calidad-analyze-stories-and-request-data]]`), y
después de tener las historias descargadas íntegras (`[[calidad-story-evidence-baseline]]`) y
el análisis por historia (`[[calidad-story-quality-analysis-artifacts]]`): la solicitud se
deriva de los criterios, no de la lectura general de un backlog.

### Cuándo NO aplicar, que es lo que más se confunde

**Una generación no abre una solicitud de datos.** Si a una automatización le faltan datos
del cliente, esto no es lo que se invoca:

| Situación | Qué se hace | Con qué |
|---|---|---|
| Automatizando, y falta un estado de dato | Se le dice al QA qué estado falta, con dueño y fecha, en el chat | `[[calidad-test-data-management]]` (`references/data-sufficiency-gate.md`) |
| Automatizando, y el dato depende del cliente | Se declara **bloqueo con fecha**, se reporta y se planifica | `[[calidad-sut-readiness-gate]]`, delivery gate |
| Automatizando algo que nunca se analizó | Se dice con esas palabras y se ofrece la ruta de análisis como trabajo aparte | `[[calidad-route-test-generation]]` |

La diferencia no es de formato sino de **ciclo**: una solicitud formal al cliente tarda días
y no se resuelve dentro de la sesión que la abrió. Tomarla en mitad de una generación detiene
la entrega sin desbloquear nada. Es trabajo previo, y previo quiere decir antes.

> Sus artefactos obligatorios se activan solo con `"route": "analisis-y-datos"` en la traza,
> que únicamente escribe el workflow de análisis. Una generación nunca los ve exigidos.

## Lectura obligatoria antes de emitir

| Reference | Para qué |
|---|---|
| `references/audience-and-enumeration.md` | Quién recibe el documento y qué forma exige |
| `references/non-derivable-data.md` | Qué no se pide, y la diferencia entre derivable y de otro dueño |
| `references/coverage-audit-ca-to-data.md` | La auditoría que condiciona la emisión |
| `references/data-request-schema.md` | El contrato de la fuente de datos |
| `references/jira-rendering-rules.md` | Cómo se renderiza en el ticket de destino |
| `references/template-solicitud.md` | La plantilla, que es también la del renderizador |

## Instrucción

### 1. La solicitud se declara como datos

`.evidence/data-request.json` es la fuente. El markdown es salida. Esto no es preferencia de
formato: es lo que convierte una corrección de forma en una línea en vez de en una
reescritura, y es lo que permite que la auditoría sea un cruce y no una relectura.

Contrato completo en `references/data-request-schema.md`.

### 2. Cada ítem se escribe para quien no conoce la historia

Un sujeto por fila, enumerado uno a uno aunque sean treinta. La **condición exigida**, no el
identificador. El para qué, que es lo que permite proponer alternativas. Y el ambiente
declarado en la cabecera con la negación de producción al lado.

Las reglas completas, con el caso medido que las motiva, en
`references/audience-and-enumeration.md`.

### 3. Lo que no es del destinatario, se enruta; no se mezcla ni se pierde

Cada ítem lleva `responsable`, con el catálogo de `[[calidad-responsibility-routing-of-blockers]]`.
Solo `cliente-datos` viaja en el cuerpo. Lo que resuelve el propio equipo se marca
`documentar` y sale en un bloque aparte con cómo se obtiene — aparece porque quien lee tiene
que ver que ese caso está cubierto. Lo del arquitecto, el PO o desarrollo **sale de aquí y
entra en su registro**, que es el `01-dudas.md` de la historia.

### 4. Nada derivable

Un dato es derivable cuando se produce usando otro ya pedido, sin permisos ni terceros. Se
declara con `derivado_de` y va al bloque de exclusiones, nunca a la solicitud.
Ver `references/non-derivable-data.md`.

### 5. La auditoría no es un paso, es una dependencia

```
python3 scripts/extract-ca.py            # inventario de criterios desde las historias
python3 scripts/check-data-coverage.py   # el cruce; exit != 0 bloquea
python3 scripts/render-data-request.py   # no emite si el anterior no paso
```

`render-data-request.py` invoca la auditoría y **se niega a emitir** si falla. Es deliberado:
la versión de esta regla que solo decía "audita antes de emitir" existió, y hizo falta que
una persona lo pidiera dos veces, la segunda después de que faltara un caso base.

### 6. La entrega es una escritura en el ALM

Crear el ticket y vincularlo a cada historia pasan por la ficha de
`[[calidad-alm-write-authorization-gate]]`. El markdown emitido se conserva en `.evidence/`
aunque su destino sea el ticket: el ticket es el canal, el repositorio es el registro.

### 7. Lo que llega, se cierra

Una solicitud emitida no está terminada: está pendiente. Cuando el cliente responde, cada
ítem se marca como recibido o no montable en la propia fuente, y lo no montable vuelve al
análisis como riesgo con su alternativa. Un ítem que nadie cerró es un caso que alguien va a
intentar ejecutar sin dato. **Las credenciales que lleguen se marcan como recibidas y jamás
se transcriben** a la fuente, al documento ni a la evidencia.

## Restricciones

- **NUNCA** escribir la solicitud directamente como markdown. La fuente es el JSON.
- **NUNCA** emitir ni publicar sin la auditoría en verde.
- **NUNCA** pedir un dato derivable de otro ya pedido, ni omitirlo sin declarar por qué.
- **NUNCA** meter en la solicitud lo que resuelve otro rol, ni sacarlo sin enrutarlo a su registro.
- **NUNCA** pedir un identificador concreto en lugar de la condición que debe cumplir.
- **NUNCA** aflojar un criterio para que el dato existente alcance: es anti-cheating
  (`[[calidad-test-self-correction-loop]]`), y el caso se declara no ejecutable.
- **NUNCA** transcribir una credencial recibida a ningún artefacto.
- **NUNCA** omitir el ambiente de destino: una solicitud sin ambiente es una que alguien
  puede ejecutar en producción.

## Verificación

Asset de **cumplimiento obligatorio**. Antes de cerrar la fase que lo invoca, comprobar cada punto. Si alguno no se cumple, se detiene y se reporta con el mensaje indicado.

| # | Comprobación | Si no se cumple |
|---|---|---|
| 1 | la solicitud existe como .evidence/data-request.json y el markdown entregado se genero desde ahi, no se escribio a mano | Bloqueado: la solicitud se escribio como prosa. Cada correccion de forma obliga entonces a reescribir el documento entero; medido en campo, cuatro de siete turnos de reproceso de una sesion fueron exactamente eso. |
| 2 | check-data-coverage.py paso en verde y .evidence/data-coverage-audit.json lo registra antes de emitir o publicar la solicitud | Bloqueado: se iba a emitir sin cruzar los criterios contra los datos. Ya ocurrio pedir dos usuarios multiempresa y ningun monoempresa, que era el caso base de media docena de criterios; ninguna relectura lo encontro. |
| 3 | todo item de la solicitud declara sujeto, condicion exigida y responsable, y solo viajan al cliente los de responsable cliente-datos | Bloqueado: hay items sin condicion exigida o de otro dueño en la solicitud. Quien administra el ambiente no puede conseguir un identificador que no sabe interpretar, y lo ajeno se queda sin canal. |
| 4 | ningun dato derivable de otro ya pedido aparece en la solicitud, y el bloque de exclusiones declara el motivo de cada uno | Bloqueado: se esta pidiendo trabajo que no hace falta, o se omitio sin decir por que. Un derivable sin declarar genera la pregunta que el bloque de exclusiones existe para evitar. |

Las cuatro las comprueba `scripts/check-data-coverage.py`, y `scripts/render-data-request.py` no emite sin ellas: la obligación es una dependencia de la salida, no una intención (`[[calidad-deterministic-work-to-tooling]]`).

## Cross-links

- `references/audience-and-enumeration.md`, `references/non-derivable-data.md`,
  `references/coverage-audit-ca-to-data.md`, `references/data-request-schema.md`,
  `references/jira-rendering-rules.md`, `references/template-solicitud.md`
- `[[calidad-story-evidence-baseline]]`, `[[calidad-story-quality-analysis-artifacts]]`,
  `[[calidad-responsibility-routing-of-blockers]]`, `[[calidad-analyze-stories-and-request-data]]`
- `[[calidad-test-data-management]]` — la conversación hacia adentro, con el QA de la célula.
- `[[calidad-alm-write-authorization-gate]]`, `[[calidad-alm-mcp-integration]]`,
  `[[calidad-deterministic-work-to-tooling]]`, `[[calidad-pipeline-state-tracking]]`
