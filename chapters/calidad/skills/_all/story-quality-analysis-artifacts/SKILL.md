---
id: calidad-story-quality-analysis-artifacts
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "OBLIGATORIO al analizar historias antes de automatizar. Estructura del análisis de calidad: una carpeta por historia con dudas, estrategia y datos y accesos, generada desde plantillas, más la regla de registro único que impide crear documentos paralelos con lo que ya existe."
tags: [analisis, historias, dossier, plantillas, dudas, datos, registro-unico, mandatory]
enforcement: mandatory
verification:
  - check: "existe .evidence/analisis con una carpeta por historia del lote y sus tres archivos, generados desde las plantillas del skill"
    failure_message: "Bloqueado: el analisis no esta separado por historia o no salio de las plantillas. Un analisis consolidado obliga a rehacerlo en cuanto alguien pide una historia suelta, y ya costo un turno entero."
  - check: "cada duda, dato y acceso lleva responsable del catalogo, y el de datos y accesos cubre los cinco roles y no solo lo que se pide al cliente"
    failure_message: "Bloqueado: hay hallazgos sin dueño, o el documento de datos se redujo a lo que se le pide al cliente. Lo que queda fuera se queda sin canal y aparece el dia de la ejecucion."
  - check: "no se creo ningun documento de analisis fuera de .evidence/analisis/<HU>/: nada de registros paralelos con hallazgos que ya tienen sitio"
    failure_message: "Bloqueado: se creo un registro paralelo. Ya ocurrio duplicar en un documento nuevo las dudas que ya vivian en cada historia, y deshacerlo costo un turno completo."
---

# Artefactos del Análisis de Calidad por Historia

## Problema que resuelve

Entre "llegaron las historias" y "hay pruebas automatizadas" hay una fase que el chapter
cubría solo por su lado de refinamiento: **el análisis que hace Calidad para poder probar**.
No es el análisis INVEST de `[[calidad-funcional-story-analysis]]`, que juzga si la historia
está lista; es el que produce las tres preguntas operativas: qué no se entiende, dónde se
prueba cada criterio, y qué hace falta conseguir.

Sin una estructura fijada pasan dos cosas medidas en campo. La primera: el análisis sale
consolidado en un documento por lote, y en cuanto alguien necesita una historia suelta hay
que rehacerlo separado — costó un turno entero. La segunda: cuando hay que sacar algo de un
sitio, el agente crea un documento nuevo en lugar de enrutarlo al que ya existe, y deshacer
la duplicación cuesta otro turno.

## Cuándo aplicar

Siempre que el trabajo empiece por historias y no por código: análisis previo a la
automatización, preparación de un refinamiento, o estimación de qué hace falta para
certificar un alcance. Después de `[[calidad-story-evidence-baseline]]` — no se analiza una
historia que no está descargada íntegra.

> **No aplica a la ruta de generación.** Un intent de automatización no pasa por aquí,
> aunque nombre historias y aunque falten datos: las dos rutas se excluyen y la bifurcación
> la decide el router una sola vez (`[[calidad-route-test-generation]]`). Sus artefactos
> obligatorios se activan solo con `"route": "analisis-y-datos"` en la traza, que únicamente
> escribe el workflow de análisis.


## Lectura obligatoria

| Reference | Para qué |
|---|---|
| `references/single-registry-rule.md` | Dónde vive cada tipo de hallazgo, y por qué no se crean documentos paralelos |
| `references/template-01-dudas.md` | Plantilla de dudas |
| `references/template-02-estrategia-de-pruebas.md` | Plantilla de estrategia |
| `references/template-03-datos-y-accesos.md` | Plantilla de datos y accesos |

## Instrucción

### 1. Una carpeta por historia, tres archivos, siempre los mismos

```
.evidence/analisis/
  README.md                      indice del lote, generado
  <HU>-<slug>/
    01-dudas.md                  que no se entiende, con dueño
    02-estrategia-de-pruebas.md  donde se prueba cada criterio
    03-datos-y-accesos.md        que hace falta conseguir, de quien
```

Cada historia es **autocontenida**: se puede leer sola, sin abrir las otras doce. Es lo que
permite entregar una historia sin rehacer el lote.

### 2. El andamiaje lo pone la herramienta

```
python3 scripts/normalize-stories.py --input historias.json   # el agente trajo el JSON del ALM
python3 scripts/scaffold-dossier.py                            # crea las carpetas y rellena cabeceras
```

Cabecera, épica, fecha, fuente y leyenda de responsables son idénticas en todos los archivos
del lote: las pone la plantilla. El agente escribe **solo lo que exige criterio**. Y es
aditivo — volver a correrlo cuando entra una historia nueva no toca lo ya escrito.

Cuando la leyenda cambie, cambia la plantilla. En el caso medido, cambiarla a mano en trece
archivos dejó unos actualizados y otros no.

### 3. Cada hallazgo lleva dueño

Los cinco roles de `[[calidad-responsibility-routing-of-blockers]]`, en las dudas y en los
datos. Un hallazgo sin dueño no se resuelve: se queda en el documento hasta que alguien
tropieza con él ejecutando.

### 4. El documento de datos es el panorama completo, no la lista para el cliente

Éste es el error que más caro sale de los tres. `03-datos-y-accesos.md` cubre **todo** lo que
Calidad necesita: lo del cliente, lo del arquitecto, lo del PO, lo de desarrollo y lo que
monta el propio equipo. Solo el subconjunto de responsable `cliente-datos` viaja a la
solicitud de `[[calidad-client-test-data-request]]`; el resto sigue vivo aquí, con su dueño.

Reducirlo a "lo que le pedimos al banco" deja el resto sin canal, y es exactamente lo que
hubo que corregir en campo, historia por historia.

### 5. El estado exigido, no la entidad

En datos, la columna que hace el trabajo no es qué entidad hace falta sino **en qué estado**.
"Una cuenta" no es un requisito. "Una cuenta con saldo por debajo del mínimo de la operación"
sí. Ver `[[calidad-test-data-management]]`.

### 6. Un registro por tipo de hallazgo

Cuando algo tenga que salir de un documento, **se enruta al suyo**; no se crea uno nuevo. La
tabla completa de dónde vive cada cosa está en `references/single-registry-rule.md`, y es lo
único que impide que la instrucción "esto no va aquí" produzca un documento paralelo.

## Restricciones

- **NUNCA** emitir el análisis consolidado en un solo documento para varias historias.
- **NUNCA** crear un documento de dudas, datos o estrategia fuera de `.evidence/analisis/<HU>/`.
- **NUNCA** reducir `03-datos-y-accesos.md` a lo que se le pide al cliente.
- **NUNCA** escribir un ítem de datos sin el estado que exige ni sin responsable.
- **NUNCA** editar a mano la cabecera o la leyenda de un dossier: se cambia la plantilla.
- **NUNCA** sobrescribir un dossier ya escrito al reprocesar el lote; el scaffolder es aditivo.
- **NUNCA** analizar una historia que no esté descargada íntegra (`[[calidad-story-evidence-baseline]]`).

## Verificación

Asset de **cumplimiento obligatorio**. Antes de cerrar la fase que lo invoca, comprobar cada punto. Si alguno no se cumple, se detiene y se reporta con el mensaje indicado.

| # | Comprobación | Si no se cumple |
|---|---|---|
| 1 | existe .evidence/analisis con una carpeta por historia del lote y sus tres archivos, generados desde las plantillas del skill | Bloqueado: el analisis no esta separado por historia o no salio de las plantillas. Un analisis consolidado obliga a rehacerlo en cuanto alguien pide una historia suelta, y ya costo un turno entero. |
| 2 | cada duda, dato y acceso lleva responsable del catalogo, y el de datos y accesos cubre los cinco roles y no solo lo que se pide al cliente | Bloqueado: hay hallazgos sin dueño, o el documento de datos se redujo a lo que se le pide al cliente. Lo que queda fuera se queda sin canal y aparece el dia de la ejecucion. |
| 3 | no se creo ningun documento de analisis fuera de .evidence/analisis/<HU>/: nada de registros paralelos con hallazgos que ya tienen sitio | Bloqueado: se creo un registro paralelo. Ya ocurrio duplicar en un documento nuevo las dudas que ya vivian en cada historia, y deshacerlo costo un turno completo. |

La comprobación 1 la impone `scripts/scaffold-dossier.py`, que es quien crea las rutas y
regenera el índice: la estructura es salida de la herramienta, no una convención que alguien
recuerda (`[[calidad-deterministic-work-to-tooling]]`).

## Cross-links

- `references/single-registry-rule.md`, `references/template-01-dudas.md`,
  `references/template-02-estrategia-de-pruebas.md`, `references/template-03-datos-y-accesos.md`
- `[[calidad-story-evidence-baseline]]`, `[[calidad-responsibility-routing-of-blockers]]`,
  `[[calidad-client-test-data-request]]`, `[[calidad-analyze-stories-and-request-data]]`
- `[[calidad-funcional-story-analysis]]` — el otro análisis: INVEST y Definition of Ready.
- `[[calidad-test-data-management]]`, `[[calidad-automation-feasibility-assessment]]`,
  `[[calidad-pipeline-state-tracking]]`, `[[calidad-deterministic-work-to-tooling]]`
