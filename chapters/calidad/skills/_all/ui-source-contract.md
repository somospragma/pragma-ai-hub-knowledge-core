---
id: calidad-ui-source-contract
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "OBLIGATORIO para front (web y móvil). Qué es exactamente una fuente de interfaz, qué se espera de cada una y qué no puede dar: aplicación viva, design system, repositorio de front, prototipo interactivo, diseño estático y catálogo de componentes. Una sola fuente casi nunca basta, y hay que declarar cuál cubre el flujo y cuál la estructura."
tags: [insumos, front, web, mobile, ui-source, design-system, figma, locators, suficiencia, universal, mandatory]
enforcement: mandatory
verification:
  - check: "existe .evidence/ui-sources.md declarando qué eje cubre cada fuente —flujo o estructura— y ninguna se usa para el eje que no puede responder"
    failure_message: "Bloqueado: se está usando una fuente para lo que no puede dar. Un diseño estático no dice qué árbol publica un componente, y de ahí salen los selectores inventados que pasan contra el prototipo y se rompen el día del despliegue."
  - check: "todo identificador que llega al mapa lleva la fuente de la que salió y su confianza"
    failure_message: "Bloqueado: hay identificadores sin procedencia. Uno cosechado de la aplicación real y uno inferido de un diseño no valen lo mismo y no pueden parecerlo."
---

# Contrato de las Fuentes de Interfaz

## Problema que resuelve

`ui_source` se venía usando como término paraguas para cosas que no son intercambiables: un enlace de Figma, un design system, una aplicación corriendo y una historia con pantallas enumeradas entraban por la misma casilla. El resultado es que se pide "una fuente UI", llega una, y el agente descubre a mitad de camino que esa fuente **no puede responder la pregunta que él tenía**.

Y hay una segunda confusión, más cara: la jerarquía de fuentes respondía bien a *qué pantallas hay y cómo se navega*, y mal a *qué árbol publica este elemento*, que es de la que dependen los selectores. Verificado en campo: tres sobrecostes de una misma certificación fueron detalle de componente —un campo anidado dentro de cada casilla de un código de un solo uso, una opción de menú que era texto y no botón, un ícono sin nombre accesible— y **ninguno de los tres se ve en un diseño**.

## Cuándo aplicar

Al recolectar insumos de cualquier entrega de front, web o móvil, antes de escribir el primer localizador.

## Instrucción

### 1. Dos preguntas, dos jerarquías

| Pregunta | Jerarquía |
|---|---|
| **Flujo** — qué pantallas hay, cómo se llega, qué dice cada una | aplicación viva > prototipo interactivo > diseño estático > historia > catálogo de componentes |
| **Estructura** — qué árbol publica un elemento, qué rol, qué anidamiento | aplicación viva > **design system** > repositorio de front > diseño estático |

Para la segunda, el diseño estático es de las peores fuentes: muestra píxeles y no dice nada del árbol. Confundir las dos jerarquías es lo que produce localizadores inventados.

### 2. Qué se espera de cada fuente, y qué no puede dar

| Fuente | Qué se espera de ella | Qué **no** da |
|---|---|---|
| **Aplicación viva** — desplegada y autenticable | Recorrido real, árbol de accesibilidad, copys exactos, formatos, estados observados | Nada: es la mejor en los dos ejes |
| **Design system** — el paquete de componentes que usa la aplicación | La estructura que publica cada componente, su rol y su convención de identificadores. Se toma **como dependencia**, no leyendo su código | Flujo, copys de negocio, datos |
| **Repositorio de front** | Identificadores declarados, grafo de rutas, puntos donde se llama a cada servicio. Se extrae **con herramienta y por diferencias** | **Comportamiento esperado**: derivarlo del código es probar la implementación contra sí misma |
| **Prototipo interactivo** — export navegable del diseño | Copys, formatos, estados y grafo de navegación. Se recorre como una aplicación | El árbol real que publicará la implementación |
| **Diseño estático** — Figma, maquetas | Copys, jerarquía visual, estados diseñados y las ramas del flujo | El árbol. Para estructura, la peor de la lista |
| **Catálogo de componentes** — Storybook | Estructura por componente, con sus variantes | Flujo y navegación |

### 3. Una fuente casi nunca basta

**`ui_source` no es una fuente: son las que hagan falta para cubrir los dos ejes**, y hay que **declarar cuál cubre cuál**. La combinación más frecuente en pre-desarrollo es diseño estático para el flujo y los copys, más design system para la estructura. Declararlo evita la pregunta que sale tarde: "¿de dónde sacaste ese selector?".

### 4. Toda pieza extraída lleva procedencia y confianza

Un identificador cosechado del árbol de la aplicación real y uno inferido de un diseño **no valen lo mismo**, y el mapa tiene que distinguirlos (`[[calidad-ui-locator-map-contract]]`). La confianza sale de la procedencia:

| Procedencia | Confianza | Qué exige antes de darse por buena |
|---|---|---|
| Cosechada de la aplicación desplegada | Alta | Nada: es lo que verá el driver |
| Extraída del repositorio de front | Alta | Que la revisión extraída sea la desplegada o la que se desplegará |
| Derivada del design system | Media | Que la versión anclada sea la que publica la aplicación |
| Inferida del diseño o de la historia | **Baja** | Verificación contra la aplicación real antes de darse por buena |

Con esos campos, el veredicto de suficiencia deja de ser sí o no y pasa a ser medible: *el sesenta por ciento de los identificadores de este flujo son inferidos* es accionable; *no hay mapa* no lo es.

### 5. Cuando el copy es la aserción

Los textos que van a convertirse en valor esperado se persisten **con el identificador del nodo del que salieron** y marcados con su fuente. Un copy del diseño no es evidencia de ejecución: ya ocurrió dar por buena, como si fuera de una corrida, una imagen que venía de la maqueta y describía un desenlace que nunca se produjo. Ver `[[calidad-figma-mcp-integration]]` y `[[calidad-data-volatility-and-assertion-anchoring]]` para distinguir rótulo de contenido.

## Restricciones

- **NUNCA** usar una fuente para el eje que no puede responder, ni aunque sea la única disponible. Si sólo hay diseño estático, la estructura queda declarada como inferida y de confianza baja, no se disfraza.
- **NUNCA** leer el repositorio de front o el design system con el modelo para "entenderlos": se extraen con herramienta y se lee la salida (`[[calidad-deterministic-work-to-tooling]]`).
- **NUNCA** convertir en localizador el contenido de un dato. Rótulos, títulos y textos de control son anclas; el contenido cambia con cada registro.
- **NUNCA** dar por equivalente un prototipo construido con otra tecnología que la de la aplicación real: lo que el driver ve depende de la implementación, y validar contra otra estructura valida en falso.

## Verificación

Asset de **cumplimiento obligatorio**. Antes de cerrar la fase que lo invoca, comprobar cada punto. Si alguno no se cumple, se detiene y se reporta con el mensaje indicado.

| # | Comprobación | Si no se cumple |
|---|---|---|
| 1 | existe .evidence/ui-sources.md declarando qué eje cubre cada fuente —flujo o estructura— y ninguna se usa para el eje que no puede responder | Bloqueado: se está usando una fuente para lo que no puede dar. Un diseño estático no dice qué árbol publica un componente, y de ahí salen los selectores inventados que pasan contra el prototipo y se rompen el día del despliegue. |
| 2 | todo identificador que llega al mapa lleva la fuente de la que salió y su confianza | Bloqueado: hay identificadores sin procedencia. Uno cosechado de la aplicación real y uno inferido de un diseño no valen lo mismo y no pueden parecerlo. |

## Cross-links

`[[calidad-mandatory-inputs-protocol]]`, `[[calidad-ui-locator-map-contract]]`, `[[calidad-functional-flow-input]]`, `[[calidad-figma-mcp-integration]]`, `[[calidad-sut-readiness-gate]]`, `[[calidad-pre-development-artifacts-continuity]]`, `[[calidad-deterministic-work-to-tooling]]`, `[[calidad-data-volatility-and-assertion-anchoring]]`.
