---
id: calidad-functional-flow-input
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "OBLIGATORIO para front (web y móvil). El recorrido funcional detallado es un insumo, no algo que se descubra ejecutando: secuencia de pantallas, bifurcaciones y qué las condiciona, pantallas intermitentes, desenlaces y su duración. Puede vivir en la historia o en documento aparte; lo que no puede es no existir."
tags: [insumos, front, web, mobile, flujo, criterios-aceptacion, suficiencia, universal, mandatory]
enforcement: mandatory
verification:
  - check: "para toda entrega de front existe .evidence/functional-flow.md con las seis piezas del recorrido, y cada bifurcación declara qué la condiciona"
    failure_message: "Bloqueado: se iba a automatizar un recorrido que nadie describió. Descubrir el flujo ejecutando es lo más caro que hace un agente, y una compuerta no documentada ya produjo un diagnóstico de servicio caído que era una precondición."
  - check: "cada desenlace del flujo declara si es permanente o transitorio"
    failure_message: "Bloqueado: hay desenlaces sin declarar su duración. Un mensaje que aparece y desaparece se valida capturándolo en el instante; si nadie dice que es transitorio, la comprobación llega tarde y el fallo se confunde con un defecto."
---

# El Recorrido Funcional como Insumo

## Problema que resuelve

Una historia de usuario describe **qué debe cumplirse**. Casi nunca describe **por dónde se pasa para comprobarlo**. Y esa diferencia es la que un agente termina descubriendo ejecutando, que es la forma más cara que existe de averiguarla.

Verificado en campo y con factura: el diseño de un flujo declaraba desde el primer día un nodo de decisión que exigía autenticación reforzada antes de dejar avanzar. La historia no lo mencionaba. Nadie cruzó las dos fuentes. El resultado fue una carga infinita diagnosticada durante horas como servicio caído, un bloqueo de ambiente emitido, y un defecto documentado que no era tal. Del análisis posterior, ese hueco —una precondición declarada en el diseño que nadie llevó al plan— costó del orden de **cincuenta créditos en diagnóstico**, más las corridas que lo rodearon.

El recorrido no es documentación de apoyo: es **insumo de construcción**, del mismo rango que el contrato de un servicio para una suite de API.

## Cuándo aplicar

En toda entrega de front —web o móvil— antes de diseñar escenarios. No aplica a suites de API o de performance, donde el contrato del servicio cumple este papel.

## Instrucción

### 1. Las seis piezas

El recorrido puede vivir dentro de la historia, en un documento aparte, o reconstruirse a partir del diseño y de la aplicación viva. **Lo que no puede es no existir.** Tenga la forma que tenga, debe contener seis cosas:

1. **La secuencia de pantallas**, cada una con el nombre por el que la conoce el negocio.
2. **Por cada paso**: qué hace la persona, sobre qué elemento, y qué responde el sistema.
3. **Las bifurcaciones y qué las condiciona.** No "puede pedir autenticación", sino "pide autenticación cuando el token no está activo en este dispositivo". Una rama sin condición declarada es una rama que se descubre fallando.
4. **Las pantallas intermitentes**: las que aparecen sólo a veces —avisos de privacidad, permisos, invitación a activar biometría, modales de estado del producto— y **bajo qué condición aparecen**. Son la fuente número uno de esperas fijas que el escenario paga enteras cada corrida (`[[calidad-wait-cost-and-timeout-design]]`).
5. **Los desenlaces**: éxito, error de negocio y error técnico, con **su copy exacto** y, sobre todo, **si son permanentes o transitorios**. Un mensaje que aparece y desaparece se captura en el instante; si nadie lo declara, la comprobación llega tarde y el falso rojo se confunde con un defecto.
6. **Las precondiciones de entrada**: en qué estado tiene que estar la cuenta, el dato y la sesión para que el recorrido empiece.

### 2. Se persiste, no se recuerda

Lo extraído se escribe en `.evidence/functional-flow.md`, con la fuente de cada pieza declarada: qué salió de la historia, qué del diseño, qué de la aplicación viva y qué de una respuesta del negocio. Una pieza sin fuente no se puede reverificar cuando algo cambie.

### 3. Lo que este insumo desbloquea

No es burocracia: cada pieza alimenta una decisión concreta de construcción.

| Pieza | Qué decide |
|---|---|
| Secuencia de pantallas | Los escenarios y su punto de entrada |
| Pasos e interacciones | La cadena de steps y qué se reutiliza |
| Bifurcaciones y su condición | Los escenarios de rama y el dato que cada uno exige |
| Pantallas intermitentes | Dónde va una carrera de esperas en vez de un techo fijo |
| Desenlaces y su duración | Dónde se captura en el instante en vez de comprobar después |
| Precondiciones | Qué hay que orquestar antes, y si es orquestable |

### 4. Cuando falta, se nombra el hueco, no el documento

Si el recorrido no está completo, el gate **no pide "el flujo"**: pide la pieza. "No está declarado qué condiciona la rama de autenticación" es accionable en un mensaje; "falta documentación del flujo" no lo es y devuelve la pelota sin información.

Y si la respuesta es que nadie lo tiene escrito, hay dos salidas legítimas y una prohibida. Legítimas: reconstruirlo recorriendo la aplicación viva —y persistirlo, que es lo que lo vuelve reutilizable— o pedirlo a quien define el producto. Prohibida: **suponerlo y seguir**.

## Restricciones

- **NUNCA** dar por conocido un recorrido porque "se parece" a otro ya automatizado. Las bifurcaciones son lo que cambia entre flujos que se ven iguales.
- **NUNCA** derivar el comportamiento esperado del código de la aplicación: eso es probar la implementación contra sí misma. Del código se extrae estructura, nunca expectativa (`[[calidad-ui-source-contract]]`).
- **NUNCA** dejar una bifurcación sin su condición ni un desenlace sin su duración. Son las dos omisiones que más corridas cuestan.
- El recorrido **no sustituye a los criterios de aceptación**: describe el camino, no lo que hay que verificar. Los criterios siguen viniendo de la historia (`[[calidad-mandatory-inputs-protocol]]`).

## Verificación

Asset de **cumplimiento obligatorio**. Antes de cerrar la fase que lo invoca, comprobar cada punto. Si alguno no se cumple, se detiene y se reporta con el mensaje indicado.

| # | Comprobación | Si no se cumple |
|---|---|---|
| 1 | para toda entrega de front existe .evidence/functional-flow.md con las seis piezas del recorrido, y cada bifurcación declara qué la condiciona | Bloqueado: se iba a automatizar un recorrido que nadie describió. Descubrir el flujo ejecutando es lo más caro que hace un agente, y una compuerta no documentada ya produjo un diagnóstico de servicio caído que era una precondición. |
| 2 | cada desenlace del flujo declara si es permanente o transitorio | Bloqueado: hay desenlaces sin declarar su duración. Un mensaje que aparece y desaparece se valida capturándolo en el instante; si nadie dice que es transitorio, la comprobación llega tarde y el fallo se confunde con un defecto. |

## Cross-links

`[[calidad-mandatory-inputs-protocol]]`, `[[calidad-ui-source-contract]]`, `[[calidad-sut-readiness-gate]]`, `[[calidad-figma-mcp-integration]]`, `[[calidad-wait-cost-and-timeout-design]]`, `[[calidad-test-evidence-and-traceability]]`, `[[calidad-design-test-cases]]`.
