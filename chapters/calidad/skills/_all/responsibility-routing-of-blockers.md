---
id: calidad-responsibility-routing-of-blockers
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Catálogo de los cinco responsables de lo que Calidad necesita para probar, y la regla de enrutamiento: todo hallazgo lleva dueño, y cada destinatario recibe solo lo suyo. Sacar algo de un canal obliga a decir a cuál va."
tags: [responsables, enrutamiento, bloqueos, datos, dudas, refinamiento, analisis]
---

# Enrutamiento de Bloqueos por Responsable

## Problema que resuelve

Cuando Calidad analiza un alcance, lo que le falta para probar no es una lista: son cinco
listas con cinco destinatarios distintos, que se descubren mezcladas y se resuelven por
canales que no se parecen en nada. Un contrato de servicio se pregunta en una reunión
técnica; un usuario de prueba se pide por ticket y tarda días; una regla de negocio va al
refinamiento del sprint.

Mezclarlas tiene dos costes simétricos y los dos se pagaron en campo:

- **Mezclar hacia afuera**: la solicitud de datos salió con ítems de arquitecto y de negocio.
  Quien la recibió tuvo que separar lo suyo de lo ajeno, y lo ajeno se quedó ahí, sin dueño.
- **Separar sin enrutar**: al sacarlos, se crearon en un documento nuevo en vez de mandarlos
  al registro donde ya vivían. Deshacer la duplicación costó un turno entero.

La regla que evita las dos es una: **todo hallazgo lleva dueño desde que se escribe, y
sacarlo de un canal obliga a decir a cuál va.**

## Cuándo aplicar

Al escribir cualquier duda, dato, acceso o bloqueo en el análisis de una historia, y antes
de emitir cualquier documento dirigido a alguien de fuera del equipo.

## El catálogo

Cinco responsables. El valor exacto es el que consumen las herramientas del chapter, así que
se escribe tal cual.

| `responsable` | Quién es | Qué le corresponde | Canal | Cuánto tarda |
|---|---|---|---|---|
| `cliente-datos` | Quien administra usuarios y productos del ambiente del cliente | Usuarios, productos, estados del sistema de origen, permisos de canal, habilitación de segundo factor | Solicitud formal (`[[calidad-client-test-data-request]]`) | Días. Se pide primero aunque se necesite después |
| `arquitecto` | Arquitectura del cliente o del proyecto | Contratos de servicio, endpoints, mecanismos técnicos, ambientes, qué componente resuelve qué | Consulta técnica; queda en `01-dudas.md` | Horas o días |
| `po-negocio` | Product owner o negocio | Reglas de negocio, textos exactos, parámetros de consola de administración, qué se espera ver | Refinamiento; queda en `01-dudas.md` | El ciclo del refinamiento |
| `dev-pragma` | Desarrollo, incluido el propio equipo | Mocks, fixtures, temporizadores de configuración, builds firmadas, dispositivos, entorno local | Acuerdo con la célula | Horas |
| `qa` | El propio equipo de Calidad | Perfiles y usuarios derivados que se crean desde otro ya provisto, estados alcanzables operando, herramientas del repositorio | Se hace, no se pide | Inmediato |

## Las cuatro reglas

### 1. Un hallazgo sin dueño no existe

Se escribe con `responsable` desde el primer momento. Un ítem sin dueño no lo resuelve
nadie: se queda en el documento hasta que alguien tropieza con él ejecutando, que es el
momento más caro posible para descubrirlo.

### 2. Cada destinatario recibe solo lo suyo

La solicitud al cliente lleva únicamente `cliente-datos`. Las preguntas técnicas van a
arquitectura. Las de negocio, al refinamiento. Un documento que mezcla obliga a su
destinatario a hacer el trabajo de clasificación que le correspondía a quien lo escribió.

La excepción es deliberada: lo de `qa` **aparece** en los documentos que salen, marcado como
propio, porque quien los lea tiene que ver que ese caso está cubierto. Aparece, no se pide.

### 3. Sacar de un canal obliga a decir a cuál va

"Esto no va en la solicitud de datos" es media instrucción. La otra mitad es dónde sí va. Sin
ella, el hallazgo se pierde o —lo que ocurrió— se duplica en un documento nuevo. El registro
de destino ya existe casi siempre: la tabla está en
`[[calidad-story-quality-analysis-artifacts]]` (`references/single-registry-rule.md`).

### 4. Lo que depende de terceros se pide primero, aunque se necesite después

`cliente-datos` es el único que se cuenta en días y el único que puede exigir trámite. El
orden de trabajo no es el orden de necesidad: se abre por lo que tarda.

## El caso frontera que más se equivoca

**Un dato que el propio equipo puede provisionar no se le pide al cliente**, aunque sea un
dato de negocio y aunque "lo tenga el banco".

Medido: se pidieron usuarios secundarios al cliente durante toda una versión del documento.
Resulta que el equipo los crea desde el usuario administrador y, al crearlos, define qué
cuentas ve cada uno. El dato del cliente no era el secundario: era **el administrador con la
función de crear secundarios habilitada**. Un ítem, no siete.

La pregunta que resuelve la frontera no es de quién es el dato, sino: **¿puede el equipo
llegar a ese estado con lo que ya tiene, sin permisos ni terceros?** Si sí, es `qa` y se
documenta. Si no, es del cliente y se pide. Y responderla exige conocer el modelo de
usuarios del producto, que es conocimiento de la cuenta y se consulta antes de clasificar.

## Restricciones

- **NUNCA** escribir una duda, dato o bloqueo sin responsable.
- **NUNCA** meter en un documento externo ítems de un responsable distinto al destinatario,
  salvo los de `qa` marcados explícitamente como propios.
- **NUNCA** sacar un hallazgo de un canal sin declarar a cuál va.
- **NUNCA** crear un registro nuevo para hallazgos que ya tienen sitio.
- **NUNCA** clasificar como `cliente-datos` algo que el equipo puede provisionar, ni al revés
  sin haber consultado el modelo del producto en el conocimiento de la cuenta.
- **NUNCA** dejar `cliente-datos` para el final del trabajo: es el único que se cuenta en días.

## Cross-links

`[[calidad-client-test-data-request]]`, `[[calidad-story-quality-analysis-artifacts]]`,
`[[calidad-story-evidence-baseline]]`, `[[calidad-analyze-stories-and-request-data]]`,
`[[calidad-test-data-management]]`, `[[calidad-sut-readiness-gate]]`,
`[[calidad-funcional-story-refinement]]`, `[[calidad-human-fix-request-protocol]]`.
