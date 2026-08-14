---
id: calidad-repo-capability-discovery
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Barrido obligatorio del repositorio antes de generar o ejecutar en brownfield: qué scripts, runbook, convenciones, alcance del ejecutor e integraciones ya existen. Produce un mapa de recursos y prohíbe inventar comandos o reimplementar a mano lo que el repo ya resuelve."
tags: [brownfield, discovery, runbook, inventario, mandatory, gate, universal, all-stacks]
enforcement: mandatory
verification:
  - check: "antes de generar el primer archivo y antes de la primera ejecución se emitió .evidence/repo-capability-map.md y se mostró al usuario"
    failure_message: "Bloqueado: se generó o ejecutó sin barrer el repositorio. El agente no sabe qué herramientas ya existen y va a inventar las que faltan."
  - check: "todo comando ejecutado contra el proyecto proviene del mapa de recursos o de confirmación explícita del usuario"
    failure_message: "Bloqueado: se ejecutó un comando inventado. Un comando que no sale del repositorio no es reproducible por el equipo del cliente."
  - check: "ninguna operación se implementó a mano existiendo en el repositorio un recurso que ya la resuelve"
    failure_message: "Bloqueado: se reimplementó a mano algo que el repositorio ya provee. Eso es deuda nueva y trabajo duplicado."
---

# Repo Capability Discovery — Mirar Antes de Construir

## Problema que resuelve

En brownfield el repositorio ya sabe cómo se ejecutan sus pruebas, con qué etiquetas se filtran, qué integraciones tiene resueltas y qué no debe tocarse. El agente que no lo mira **inventa lo que ya existe**: comandos que nadie usa, etiquetas que contradicen la convención del equipo, y procesos manuales paso a paso cuando el repositorio trae un ejecutor que los hace de una pasada.

Verificado en campo: el agente inventó comandos de ejecución que el propio repositorio documentaba en el texto de ayuda de sus scripts; creó una etiqueta de compuerta nueva cuando la convención real aparecía en los ejemplos de uso de esos mismos scripts; y automatizó plataforma por plataforma a mano existiendo un ejecutor multiplataforma. No faltaba conocimiento del chapter: faltaba mirar el repositorio.

Este skill **mapea**, no copia. El detalle de cada recurso vive en el recurso, que es donde no se desactualiza; el mapa dice qué existe, dónde y para qué.

## Cuándo aplicar

**Obligatorio en toda ruta brownfield**, antes de generar el primer archivo y antes de la primera ejecución. Es parte del `[[calidad-pre-generation-protocol]]` y precede al inventario de arquetipo de `[[calidad-brownfield-vs-greenfield]]`.

En greenfield sobre un repositorio existente (se agrega una suite nueva a un proyecto que ya tiene otras cosas), aplica igual: el proyecto tiene convenciones aunque no tenga pruebas.

## Barrido obligatorio

| Qué buscar | Dónde mirar | Qué se extrae |
|---|---|---|
| **Scripts propios** | carpeta de scripts, tareas declaradas del gestor de paquetes o del build, utilidades del repo | qué hace cada uno, cómo se invoca, qué variables o credenciales exige |
| **Runbook de ejecución** | texto de ayuda y validaciones de los propios scripts, documentación del repo, definición de CI | el comando real, sus argumentos y sus valores válidos. **La CI es la fuente más fiable**: es el comando que funciona en limpio |
| **Convenciones vivas** | cómo el ejecutor arma los filtros; qué etiquetas aparecen en los ejemplos de uso y en las validaciones | la taxonomía real de etiquetas, perfiles y nombres. **Manda sobre cualquier default del chapter** |
| **Alcance del ejecutor** | qué archivos carga realmente: globs de features, módulos requeridos, rutas de steps o de specs | **qué queda fuera** y por tanto no se ejecutará aunque exista |
| **Integraciones resueltas** | scripts que hablan con el ALM, con el gestor de pruebas, con la nube de dispositivos o con reportería | qué operación ya está resuelta, con qué credencial y con qué contrato |
| **Datos y configuración** | archivos de datos de prueba, plantillas de variables de entorno, perfiles por ambiente | dónde viven los datos y cómo los cargan las pruebas existentes |
| **Recursos frágiles** | llamadas a APIs internas o no públicas, dependencias a interfaces no documentadas | se marcan **no reutilizables**, con la razón |

## Salida obligatoria

`.evidence/repo-capability-map.md`, mostrado al usuario antes de continuar. Índice, no transcripción:

```markdown
| Recurso | Ubicación | Propósito | Credencial/requisito | Cuándo usarlo |
|---|---|---|---|---|
| Ejecutor por plataforma | <ruta> | corre una plataforma con filtro de etiquetas | ninguna | ejecución dirigida y gate de humo |
| Ejecutor multiplataforma | <ruta> | corre todas las plataformas de un feature | ninguna | cobertura completa de una historia |
| Publicador de resultados | <ruta> | sube resultados al gestor de pruebas | <variable de entorno> | tras la corrida, con autorización |
| Reportador de defectos | <ruta> | crea defectos con el contrato del cliente | <variable de entorno> | tras confirmar defecto del SUT |

## Convenciones detectadas
- Taxonomía de etiquetas en uso: ...
- Cómo compone el filtro el ejecutor: ...
- Alcance cargado por el ejecutor: ... | **Queda fuera:** ...

## No usar
| Recurso | Razón |
|---|---|
| <script> | depende de una interfaz interna no pública; se rompe sin aviso |
```

## Reglas duras

1. **Prohibido ejecutar un comando que no salga del mapa** o que el usuario no haya confirmado. Si el mapa no se puede construir, blocker `capability_map_unknown`: se detiene y se pide el comando al usuario.
2. **Prohibido construir a mano lo que el repositorio ya resuelve.** Si existe un recurso que hace la operación, se usa. Reimplementarlo se reporta como hallazgo, no se ejecuta.
3. **La convención del repositorio manda** sobre los defaults del chapter en todo lo que sea nomenclatura, etiquetas, rutas y estructura. Cuando el chapter y el repositorio difieren, gana el repositorio y la diferencia se reporta; introducir una convención nueva exige confirmación explícita del usuario.
4. **El alcance del ejecutor se verifica, no se supone.** Antes de ejecutar, confirmar que los archivos generados quedan dentro de lo que el ejecutor carga. Un archivo fuera del alcance produce "no encontrado" o "indefinido" y parece un problema del test cuando es del ejecutor.
5. **Los recursos marcados como frágiles no se usan** salvo instrucción explícita del usuario, y nunca se toman como patrón a replicar.

## Restricciones

- **NUNCA** transcribir el contenido de los recursos dentro de este mapa ni dentro de un asset: el mapa referencia, el recurso manda. Un asset que copia comandos nace desactualizado.
- **NUNCA** declarar "el repositorio no tiene X" sin haber buscado: la afirmación exige el barrido, no la impresión.
- **NUNCA** modificar los recursos existentes del repositorio para acomodar la generación: eso es brownfield tocando lo preexistente (`[[calidad-brownfield-vs-greenfield]]`). Si un recurso estorba, se reporta.
- El mapa se construye una vez por corrida y se registra como fase en `[[calidad-pipeline-state-tracking]]`; al retomar sesión se relee, no se reconstruye de memoria.

## Verificación

Asset de **cumplimiento obligatorio**. Antes de cerrar la fase que lo invoca, comprobar cada punto. Si alguno no se cumple, se detiene y se reporta con el mensaje indicado.

| # | Comprobación | Si no se cumple |
|---|---|---|
| 1 | antes de generar el primer archivo y antes de la primera ejecución se emitió .evidence/repo-capability-map.md y se mostró al usuario | Bloqueado: se generó o ejecutó sin barrer el repositorio. El agente no sabe qué herramientas ya existen y va a inventar las que faltan. |
| 2 | todo comando ejecutado contra el proyecto proviene del mapa de recursos o de confirmación explícita del usuario | Bloqueado: se ejecutó un comando inventado. Un comando que no sale del repositorio no es reproducible por el equipo del cliente. |
| 3 | ninguna operación se implementó a mano existiendo en el repositorio un recurso que ya la resuelve | Bloqueado: se reimplementó a mano algo que el repositorio ya provee. Eso es deuda nueva y trabajo duplicado. |

## Cross-links

`[[calidad-brownfield-vs-greenfield]]`, `[[calidad-pre-generation-protocol]]`, `[[calidad-execution-preflight]]`, `[[calidad-test-execution-orchestration]]`, `[[calidad-smoke-gate-policy]]`, `[[calidad-cross-platform-learning-propagation]]`, `[[calidad-alm-test-publishing-cycle]]`, `[[calidad-pipeline-state-tracking]]`.
