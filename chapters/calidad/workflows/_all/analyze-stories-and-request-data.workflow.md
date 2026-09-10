---
id: calidad-analyze-stories-and-request-data
version: 1.1.0
scope: chapter
type: workflow
chapter: calidad
description: "Workflow de la fase previa a automatizar: bajar las historias íntegras con su arquitectura, analizarlas una por una, enrutar cada hallazgo a su responsable y emitir la solicitud de datos al cliente auditada criterio a criterio."
tags: [funcional, workflow, historias, analisis, datos, solicitud, cliente, alm]
---

# Workflow — Analizar Historias y Pedir los Datos

## Cuándo usar

Cuando el trabajo empieza por historias y el objetivo no es refinarlas sino **poder
probarlas**: "analiza estas HU", "dime qué datos y accesos hay que solicitar", "prepara la
solicitud de datos", "qué necesitamos para certificar este alcance".

No es `[[calidad-analyze-and-refine-stories]]`, que juzga la historia contra INVEST y la
Definition of Ready y propone reescrituras. Éste da por buena la historia como está y
produce lo que Calidad necesita para trabajar sobre ella.

## Cuándo NO usar

**Cuando el intent es automatizar.** Este workflow es trabajo **previo** a que una
funcionalidad entre en un flujo de automatización, y las dos rutas se excluyen: el router
bifurca una sola vez y no vuelve (`[[calidad-route-test-generation]]`).

Que a una generación le falten datos no la trae aquí. La solicitud formal al cliente tarda
días y no se resuelve en la sesión que la abre; tomarla en mitad de una entrega la detiene
sin desbloquear nada. Lo que hace una generación con datos que faltan es comunicarlo al QA
con dueño y fecha (`[[calidad-test-data-management]]`) y, si depende del cliente, declararlo
bloqueo con fecha. Si la funcionalidad nunca pasó por aquí, se dice y se ofrece este
workflow como trabajo aparte.

Los tres momentos son secuenciales: se refina la historia si está rota, se analiza y se
consiguen los datos, y **cuando los datos están** se automatiza.

## Inputs

| Input | Obligatorio | Notas |
|---|---|---|
| `stories_source` | Sí | IDs o consulta del gestor, o el contenido pegado |
| `output_path` | Sí | Ruta absoluta. La evidencia vive en `output_path/.evidence/` |
| `fuentes_de_arquitectura` | Sí | Dónde vive la arquitectura de estos componentes en esta cuenta, **o** la declaración de que no existe |
| `mapa_de_capas` | Sí | Qué repositorio prueba qué capa en esta cuenta. Sin él, la estrategia reparte los criterios por dónde se ven |
| `ambiente_objetivo` | Sí | A qué ambiente se refieren los datos. Nunca producción |
| `audiencia_de_la_solicitud` | Sí | Quién recibe el documento y qué conoce |
| `capacidades_de_qa` | Sí | Qué puede provisionar el equipo por su cuenta en este producto |
| `write_back` | No | Publicar al gestor. Default `false` hasta autorización explícita |

Los cuatro del medio son los que faltaron en campo y produjeron el reproceso. El contrato
completo de la ruta está en `[[calidad-mandatory-inputs-protocol]]`.

## Pasos

### Paso 0 — Abrir por el estado, no por la tarea

Si `output_path/.evidence/` ya existe, leer la traza y la bitácora y abrir la respuesta con
fase, siguiente acción, bloqueos y correcciones vigentes
(`[[calidad-session-continuity-protocol]]`, `[[calidad-pipeline-state-tracking]]`). Si no
existen, se crean **antes** de tocar nada.

La traza de esta ruta declara `"route": "analisis-y-datos"`. No es decorativo: es lo único
que activa los artefactos obligatorios de esta fase en la puerta de
`[[calidad-delivery-gate-contract]]`. Sin esa marca no se comprueban, y con ella puesta en
una generación se exigirían artefactos que esa entrega no tiene por qué producir — por eso
la escribe este workflow y ningún otro. En la sesión medida no se crearon hasta la tercera
sesión, y las correcciones del usuario se reafirmaron de memoria.

### Paso 1 — Contrato de entrada

Confirmar los inputs de arriba y emitir la tabla de extracción de todo insumo entregado. Las
carencias se nombran por la pieza, no por el documento: "falta saber qué repositorio prueba
la capa de servicios" es accionable; "falta contexto" no.

### Paso 2 — Base de evidencia (BLOCKER)

`[[calidad-story-evidence-baseline]]`. El agente trae del gestor cada historia íntegra, sus
dependencias técnicas con estado real y su arquitectura; el normalizador escribe a disco y
emite `.evidence/story-sources.json`. **No se avanza con el dictamen en rojo.**

### Paso 3 — Dossier por historia

`[[calidad-story-quality-analysis-artifacts]]`. `scaffold-dossier.py` crea una carpeta por
historia con sus tres archivos y regenera el índice del lote. El agente escribe únicamente lo
que exige criterio: qué no se entiende, dónde se prueba cada criterio, qué hace falta.

### Paso 4 — Enrutar cada hallazgo

`[[calidad-responsibility-routing-of-blockers]]`. Todo hallazgo con dueño. La frontera que
más se falla —lo que el propio equipo puede provisionar frente a lo que se pide al cliente—
se decide consultando el modelo del producto en el conocimiento de la cuenta, no por
intuición.

### Paso 5 — Inventario de criterios

```
python3 <client-test-data-request>/scripts/extract-ca.py
```

Una fila por criterio, desde las historias ya descargadas. Es lo que hace posible que la
auditoría del paso siguiente sea un cruce y no una relectura.

### Paso 6 — Solicitud de datos, declarada y auditada (BLOCKER)

`[[calidad-client-test-data-request]]`. Se escribe `.evidence/data-request.json`, se cruza
contra el inventario y se renderiza:

```
python3 <client-test-data-request>/scripts/check-data-coverage.py
python3 <client-test-data-request>/scripts/render-data-request.py
```

El renderizador **no emite** si la auditoría falla. Un criterio sin dato es un caso que no se
va a poder ejecutar, y conseguir un dato en el ambiente de un cliente tarda días.

### Paso 7 — Publicar y vincular, bajo ficha

Solo con `write_back` y con la ficha de `[[calidad-alm-write-authorization-gate]]`:
autorización explícita, previa, específica y con conteo. Se crea el ticket con la solicitud y
se vincula a cada historia. El tipo de enlace y la credencial son de la cuenta.

Lo que va a arquitectura y a negocio **no viaja aquí**: sale por su canal, desde el
`01-dudas.md` de cada historia.

### Paso 8 — Cierre

Bloque de `[[calidad-delivery-gate-contract]]` con `framework: funcional` y `execution.*: null`.
En `coverage`, criterios inventariados contra criterios con dato. Entrada de cierre en la
bitácora con el punto exacto de retome, y `next_action` en la traza. `status: success` solo
si el lote completo tiene dossier, la auditoría está en verde y toda escritura al gestor fue
autorizada.

## Criterios de finalización

- [ ] Cada historia del lote está descargada íntegra, con dependencias y arquitectura, o con la ausencia declarada.
- [ ] Cada historia tiene su carpeta con los tres archivos, generada desde las plantillas.
- [ ] Cada duda, dato y acceso lleva responsable del catálogo.
- [ ] `03-datos-y-accesos.md` cubre los cinco roles, no solo lo que se pide al cliente.
- [ ] `.evidence/data-request.json` existe y la solicitud entregada se renderizó desde él.
- [ ] `check-data-coverage.py` en verde: ningún criterio sin dato ni justificación.
- [ ] Cero derivables y cero ítems de otro dueño en la solicitud al cliente.
- [ ] Escrituras al gestor: solo las autorizadas, con su ficha y su conteo.
- [ ] Traza y bitácora al día, con el punto de retome escrito.
- [ ] La traza declara `route: analisis-y-datos`, y no se generó una línea de código de pruebas.
