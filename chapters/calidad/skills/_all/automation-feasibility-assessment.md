---
id: calidad-automation-feasibility-assessment
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "OBLIGATORIO antes de comprometer alcance de automatización. Descompone cada escenario en pasos, clasifica la factibilidad de cada uno, busca en el repositorio si los pasos difíciles ya están resueltos, y decide automatizable / automatizable con capacidad nueva / manual trazable. Un escenario no automatizable no se descarta: se entrega como caso manual con su feature y su caso en el ALM."
tags: [factibilidad, automatizabilidad, alcance, brownfield, greenfield, manual, universal, mandatory]
enforcement: mandatory
verification:
  - check: "cada escenario del alcance tiene veredicto de factibilidad emitido y mostrado al usuario antes de escribir el primer archivo"
    failure_message: "Bloqueado: se comprometió alcance de automatización sin evaluar factibilidad por escenario. El alcance imposible se descubre a mitad de la entrega."
  - check: "en brownfield se buscó en el repositorio cada paso difícil antes de declararlo no automatizable"
    failure_message: "Bloqueado: se declaró un paso no automatizable sin buscar si el repositorio ya lo resuelve. Es la causa más común de reimplementar o de descartar alcance viable."
  - check: "los escenarios no automatizables se entregan como caso manual trazable, no se descartan en silencio"
    failure_message: "Bloqueado: se redujo el alcance sin dejar el escenario cubierto como caso manual. Una historia queda reportada con menos cobertura de la que se acordó."
---

# Automation Feasibility Assessment — Qué se puede automatizar, y qué se hace con lo que no

## Cuándo aplicar

**Obligatorio antes de comprometer el alcance de automatización de una historia**, después de tener los escenarios diseñados y antes de escribir el primer archivo. Se ejecuta en el paso de pre-diseño de `[[calidad-route-test-generation]]`, junto con la matriz de suficiencia de datos, porque las dos responden a la misma pregunta: *¿esto se puede ejecutar de verdad?*

Aplica en **greenfield y en brownfield**. Cambia dónde se busca la solución, no la obligación de evaluar.

## El problema

El alcance se compromete mirando los criterios de aceptación, que describen **qué** hay que verificar y no dicen nada de **cómo** se llega hasta ahí. El escenario "el usuario consulta el detalle de su producto" esconde una autenticación con segundo factor, una clave dinámica que llega por otro canal y un estado de cuenta que hay que preparar. Nada de eso está en el criterio de aceptación.

Las dos formas de equivocarse son simétricas y las dos son caras:

- **Comprometer lo imposible.** Se descubre a mitad de la entrega, con la historia ya planificada y el tiempo consumido.
- **Descartar lo que sí era posible.** Se declara "no automatizable" un paso que el propio repositorio ya resolvió para otro flujo, y se entrega menos cobertura de la que había disponible gratis.

## Instrucción

### 1. Descomponer el escenario en pasos ejecutables

Antes de juzgar nada, escribir la secuencia real que hay que ejecutar, incluyendo lo que el criterio de aceptación da por sentado: preparación del estado, autenticación, navegación, la acción bajo prueba, la verificación y la limpieza. **Un escenario no se declara automatizable ni imposible como un todo**: la factibilidad es de cada paso, y basta un paso bloqueante para condicionar el escenario completo.

### 2. Clasificar cada paso

| Clase | Qué significa | Qué hacer |
|---|---|---|
| **Directo** | El stack lo resuelve con sus mecanismos habituales | Automatizar |
| **Ya resuelto** | Existe en el repositorio o en la plataforma del cliente | **Reutilizar**, nunca reimplementar |
| **Requiere capacidad nueva** | Es posible, pero exige construir algo que hoy no existe | Estimar y proponer explícitamente al usuario antes de comprometerlo |
| **Bloqueado por terceros** | Depende de un permiso, una credencial, un acceso o un dato que hay que gestionar | Pedirlo ya, con dueño y fecha |
| **No automatizable** | No hay camino razonable con lo disponible | Caso manual trazable (sección final) |

La clase **"requiere capacidad nueva" no es sinónimo de no automatizable**, y confundirlas es lo que reduce alcance sin necesidad. La diferencia es si existe un camino; el costo se discute con el usuario, no se decide en silencio.

### 3. En brownfield: buscar antes de declarar

**Regla dura: ningún paso se declara no automatizable sin haber buscado en el repositorio.** El equipo del cliente lleva sprints resolviendo estos flujos y lo difícil suele estar resuelto en algún rincón que nadie mencionó, porque para ellos es rutina.

Catálogo de pasos que casi siempre resultan estar ya resueltos, con dónde suelen vivir:

| Paso que parece imposible | Dónde suele estar resuelto |
|---|---|
| Obtener un token de sesión o de servicio | Utilidad de autenticación, hooks de arranque, cliente de API del propio repositorio |
| Segundo factor, clave dinámica o código de un solo uso | Utilidad que lo deriva del secreto compartido, o que lo lee de donde el ambiente de pruebas lo deposita |
| Leer o actualizar un valor en base de datos | Cliente de base de datos ya configurado para el ambiente de pruebas, con sus credenciales |
| Preparar el estado de una entidad | Script de siembra, servicio interno de datos, o endpoint administrativo del ambiente |
| Correo, mensajería o notificación | Buzón de pruebas con API, o servicio de captura del ambiente |
| Firma, certificado o dispositivo de seguridad | Perfil de pruebas del ambiente con la verificación relajada |
| Descarga y verificación de un archivo | Utilidad de descarga y comparación ya usada por otra suite |

El barrido no se improvisa: es el de `[[calidad-repo-capability-discovery]]`, que ya produce el mapa de recursos del repositorio. Este skill le agrega **una pregunta dirigida por cada paso difícil**, y su resultado se anota en el mismo mapa.

Si el repositorio no lo resuelve, la segunda pregunta es al equipo del cliente: *"¿cómo hacen hoy este paso?"*. La respuesta suele ser un procedimiento manual que se puede automatizar, o una herramienta interna que nadie documentó.

En **greenfield** el barrido no aplica, pero la pregunta al equipo sí, y la clasificación es idéntica.

### 4. Emitir el veredicto por escenario, antes de escribir nada

```markdown
| Escenario | Pasos bloqueantes | Veredicto | Qué se necesita |
|---|---|---|---|
| Consulta de detalle | ninguno | **automatizable** | — |
| Transferencia con clave dinámica | generación del código de un solo uso | **automatizable reutilizando** | utilidad existente del repositorio |
| Alta con validación biométrica | captura biométrica en dispositivo físico | **manual trazable** | ejecución manual con evidencia |
| Consulta con estado especial | dato inexistente en el ambiente | **bloqueado** | dato gestionado por la célula, fecha comprometida |
```

Se muestra al usuario y **se espera confirmación del alcance** antes de generar. El alcance de automatización es una decisión del usuario informada por este análisis, no una consecuencia silenciosa de lo que el agente pudo resolver.

### 5. Lo no automatizable no se descarta: se entrega como caso manual trazable

Este es el desenlace que suele faltar. Un escenario que no se puede automatizar **sigue siendo parte de la cobertura de la historia**, y dejarlo fuera hace que la historia se reporte con menos cobertura de la acordada, sin que nadie registre por qué.

Lo que se entrega:

1. **El feature se escribe igual.** El Gherkin es la especificación del caso, no solo la entrada del ejecutor. Sirve para que el QA ejecute paso a paso, para revisión, y para el día en que el paso bloqueante se resuelva.
2. **El escenario se marca como manual** con la etiqueta que el proyecto use, y **se excluye del ejecutor** para que no aparezca como fallo ni infle el conteo de pendientes.
3. **El caso se crea en el gestor de pruebas** con sus pasos, de modo que el QA solo tenga que ejecutarlo y adjuntar la evidencia. La creación es automatizable aunque la ejecución no lo sea, y es donde está la mayor parte del trabajo repetitivo. Requiere la autorización de `[[calidad-alm-write-authorization-gate]]`.
4. **La entrega lo declara**: cuántos escenarios quedaron manuales, por qué paso concreto, y qué haría falta para automatizarlos después. Va en el `[[calidad-delivery-gate-contract]]` y en el reporte ejecutivo.

**El motivo se registra por paso, no como "no se pudo".** "Requiere captura biométrica en dispositivo físico" es accionable dentro de seis meses; "no automatizable" no le sirve a nadie.

## Restricciones

- **NUNCA** declarar un paso no automatizable en brownfield sin haber barrido el repositorio y preguntado al equipo cómo lo hacen hoy.
- **NUNCA** reimplementar a mano un paso que el repositorio ya resuelve, aunque la implementación propia parezca más limpia. Es deuda nueva y trabajo duplicado (`[[calidad-repo-capability-discovery]]`).
- **NUNCA** reducir el alcance en silencio. Un escenario que sale de la automatización entra a la cobertura manual, con su caso creado y su motivo.
- **NUNCA** ablandar un escenario para hacerlo automatizable —quitarle el paso difícil, sustituir la verificación real por una más débil, saltarse la autenticación fuerte—. Eso produce un test que pasa sin verificar lo que dice verificar, y es la regla anti-cheating maestra del chapter.
- **NUNCA** comprometer un alcance que dependa de una capacidad nueva sin haberla propuesto explícitamente y recibido confirmación.
- El veredicto se registra como fase en `[[calidad-pipeline-state-tracking]]`: al retomar la sesión se relee, no se rehace de memoria.

## Verificación

Asset de **cumplimiento obligatorio**. Antes de cerrar la fase que lo invoca, comprobar cada punto. Si alguno no se cumple, se detiene y se reporta con el mensaje indicado.

| # | Comprobación | Si no se cumple |
|---|---|---|
| 1 | cada escenario del alcance tiene veredicto de factibilidad emitido y mostrado al usuario antes de escribir el primer archivo | Bloqueado: se comprometió alcance de automatización sin evaluar factibilidad por escenario. El alcance imposible se descubre a mitad de la entrega. |
| 2 | en brownfield se buscó en el repositorio cada paso difícil antes de declararlo no automatizable | Bloqueado: se declaró un paso no automatizable sin buscar si el repositorio ya lo resuelve. Es la causa más común de reimplementar o de descartar alcance viable. |
| 3 | los escenarios no automatizables se entregan como caso manual trazable, no se descartan en silencio | Bloqueado: se redujo el alcance sin dejar el escenario cubierto como caso manual. Una historia queda reportada con menos cobertura de la que se acordó. |

## Cross-links

`[[calidad-repo-capability-discovery]]`, `[[calidad-mandatory-inputs-protocol]]`, `[[calidad-test-data-management]]`, `[[calidad-sut-readiness-gate]]`, `[[calidad-brownfield-vs-greenfield]]`, `[[calidad-alm-test-publishing-cycle]]`, `[[calidad-alm-write-authorization-gate]]`, `[[calidad-delivery-gate-contract]]`, `[[calidad-pipeline-state-tracking]]`, `[[calidad-pre-design-strategy-document]]`.
