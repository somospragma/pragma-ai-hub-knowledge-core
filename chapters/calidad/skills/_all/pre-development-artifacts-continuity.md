---
id: calidad-pre-development-artifacts-continuity
version: 1.1.0
scope: chapter
type: skill
chapter: calidad
description: "OBLIGATORIO cuando se construye contra mock o prototipo. Los artefactos pre-desarrollo —prototipo de front, prototipo de app y mock de servicios— no son andamio de una historia: son activos del producto que crecen. Qué se conserva y qué se regenera, el manifiesto de estado que evita reanalizarlos, y el refresco incremental desde lo ya desplegado."
tags: [mock, prototipo, shift-left, continuidad, reuso, costo, manifiesto, deriva, universal, mandatory]
enforcement: mandatory
verification:
  - check: "antes de construir cualquier prototipo o mock se leyó .evidence/mock-manifest.json y se declaró qué se hereda y qué se añade"
    failure_message: "Bloqueado: se iba a construir sin saber qué existía. Reconstruir lo que ya estaba es el desperdicio más caro de las entregas pre-desarrollo, y el manifiesto existe para que sea una lectura, no una investigación."
  - check: "lo añadido en esta historia es aditivo: no se editó ninguna pantalla, ruta ni estado que otra historia ya usaba"
    failure_message: "Bloqueado: se modificó un artefacto compartido que sostiene suites anteriores. La extensión es aditiva; editar lo existente rompe historias ya certificadas."
  - check: "ningún artefacto generado fue editado a mano, y la frontera entre lo generado y lo escrito está declarada y es física"
    failure_message: "Bloqueado: se parcheó a mano algo generado. O la siguiente regeneración se lleva el parche, o nadie regenera nunca por miedo a perderlo: en los dos casos el generador muere y vuelve el coste manual."
---

# Continuidad de los Artefactos Pre-Desarrollo

## Problema que resuelve

Cuando el desarrollo no está desplegado, la suite se construye contra un mock de servicios y, si hace falta, contra un prototipo del front o de la app. El chapter sabe construirlos. Lo que no dice —y es lo que hace impagable el modo pre-desarrollo— es **qué pasa con ellos cuando llega la historia siguiente**.

Tratados como andamio de una entrega, cada historia los reconstruye. El producto es el mismo, la app es la misma, y la única diferencia es que ahora el flujo entra una pantalla más adentro; aun así se paga entero otra vez. Con dos o tres canales, el coste de la construcción pre-desarrollo supera al de certificar contra un ambiente real.

## Cuándo aplicar

Siempre que `execution_target` sea `mock` o `hybrid` (`[[calidad-sut-readiness-gate]]`), tanto al abrir la historia —para saber qué se hereda— como al cerrarla, para dejar el estado listo para la siguiente.

## Instrucción

### 1. Son tres capas, y sólo una se tira

La confusión habitual es tratar "el mock" como una sola cosa. Son tres, con destinos distintos:

| Capa | Qué es | Destino |
|---|---|---|
| **Fuentes** | mapa de identificadores por pantalla, fixtures de respuesta, manifiesto de estado | **Se conservan y crecen en cada historia** |
| **Proyecto generador** | el esqueleto del prototipo, su shell de navegación, la configuración de build, el código que traduce las fuentes en pantallas y respuestas | **Se conserva, se versiona y crece despacio** |
| **Salida** | pantallas emitidas, archivo de entorno del mock, compilado | **Se regenera; el compilado se tira** |

El proyecto generador es un activo permanente con la misma disciplina que cualquier herramienta: vive en el repositorio de pruebas, versionado, documentado y registrado en el mapa de capacidades (`[[calidad-deterministic-work-to-tooling]]`). Conservarlo es lo que abarata la historia siguiente.

**Las dos capas que crecen lo hacen a ritmos distintos.** Las fuentes crecen en cada historia —pantallas e identificadores nuevos, estados nuevos— y eso es declarativo y barato. El generador crece sólo cuando aparece un tipo de componente o de interacción que no sabía emitir. Que una historia nueva apenas roce el generador y sólo añada a las fuentes es la señal de que el diseño está bien.

### 2. La frontera entre lo generado y lo escrito es física, y lo generado no se toca

> Lo escrito a mano se conserva. Lo generado se regenera y **no se edita nunca a mano**. Las dos cosas viven en carpetas distintas y la frontera está declarada en la documentación del proyecto.

Es donde mueren casi todos los generadores. Si alguien parchea a mano una pantalla generada pasa una de dos, y las dos son malas: la siguiente regeneración se lleva el parche, o —más frecuente— nadie vuelve a regenerar por miedo a perderlo y el generador se convierte en código muerto que hay que mantener a mano.

### 3. El manifiesto de estado: saber qué hay sin analizarlo

Preguntarle al agente "¿en qué estado está el mock?" y que lo averigüe abriendo el proyecto es caro y se paga en cada historia. El estado se **declara en un manifiesto que se genera**, nunca se escribe a mano, y que se lee en segundos.

Cabecera: de qué versión de contrato salieron las fixtures, qué versión del design system está anclada, de qué revisión del repositorio de front se extrajo por última vez, y en qué historia.

Y una fila por unidad:

| Unidad | Procedencia | Confianza | Historia | Estado |
|---|---|---|---|---|
| pantalla o ruta, con sus identificadores y el componente del design system de cada uno | cosechado de la app desplegada / extraído del repo de front / derivado del design system / inferido del diseño | alta · media · baja | la que lo aportó | mockeado · desplegado · obsoleto |
| endpoint + estado, con su fixture | grabada del servicio real / derivada del contrato / sintética | alta · media · baja | la que lo aportó | mockeado · desplegado · obsoleto |

El campo **estado** es el que dispara trabajo, y por eso no es decorativo:

- `mockeado` — sigue sin existir en el ambiente real; el prototipo lo genera.
- `desplegado` — ya existe; sus pruebas se repuntan a real y **deja de generarse**. No hay nada que mantener.
- `obsoleto` — su fuente desapareció; exige decisión explícita, no se arrastra.

Con el manifiesto, la pregunta "¿qué heredo?" al abrir una historia es una **lectura**, no una investigación: el agente no abre el proyecto generador ni el mock.

### 4. La extensión es aditiva

La historia nueva **añade** pantallas, identificadores, rutas y estados. **No edita** los que otra historia ya usa: eso rompe suites ya certificadas. Si algo existente resulta estar mal, no se corrige de tapadillo — se trata como deriva (punto 6) y la corrección se declara con las suites que afecta.

### 5. Refrescar desde lo que ya se desplegó, por diferencias

Cuando una parte pasa a estar desplegada, el prototipo puede dejar de ser una hipótesis y pasar a reflejar lo real. **Eso no se hace leyendo el producto: se hace extrayéndolo con herramienta**, en este orden de fidelidad:

1. **Cosechar el árbol de accesibilidad de la app desplegada.** Es literalmente lo que verá el driver — la fuente más fiel que existe después de la propia app. En un arquetipo maduro la utilidad de volcado de pantalla ya existe: se comprueba antes de construir nada.
2. **Extraer del repositorio de front** los identificadores declarados, el componente al que pertenece cada uno, el grafo de rutas y los puntos donde se llama a cada servicio.
3. **Derivar del design system** la estructura de los componentes que aún no existen en ninguna pantalla desplegada.

Cada entrada anota **de cuál de las tres salió**, porque no valen lo mismo. Y la fuente correcta depende de la pregunta: para *qué pantallas hay y cómo se navega* manda el flujo (aplicación viva, prototipo de diseño, diseño estático); para *qué árbol publica un elemento* manda la estructura (aplicación viva, design system, repositorio de front), donde el diseño estático es de las peores fuentes porque muestra píxeles y no dice nada del árbol. Confundir las dos jerarquías es lo que produce selectores inventados que pasan contra el prototipo y se rompen el día del despliegue.

**Nunca leyendo el repositorio con el modelo.** Un front entero entrando al contexto cuesta más que todo lo que ahorra, y se sigue pagando el resto de la sesión. El extractor recorre y emite; el agente lee la salida.

**Y el refresco es por diferencias.** El manifiesto guarda la revisión de la que se extrajo; el siguiente refresco emite **sólo el delta**: qué apareció, qué cambió de estructura, qué desapareció. El agente lee decenas de líneas, no un repositorio.

Ese delta vale por sí mismo, más allá de la fidelidad: **cada diferencia entre lo que el prototipo publicaba y lo que la app real publica es un verde falso latente** en las suites que ya se construyeron sobre ese supuesto. El refresco es, además de mantenimiento, un detector de los supuestos equivocados de las historias anteriores.

### 6. Deriva: el riesgo que crece con el reuso

Un prototipo que lleva cinco historias encima y se separó del producto produce verdes falsos en cascada, y con más autoridad cada vez porque "siempre pasó". Tres anclajes, y los tres viven en las fuentes:

- La **versión del design system** que el generador usa está fijada y es la que publica la app.
- La **versión del contrato** de la que salieron las fixtures está registrada.
- La **revisión del repositorio de front** de la última extracción está registrada.

Un verificador compara los tres anclajes contra lo vigente y reporta sólo lo que cambió. Comparar es determinista; analizar no. Ver `[[calidad-deterministic-work-to-tooling]]`.

### 7. No se encadena lo real con lo prototipado: se parte el escenario

En servicios el modo híbrido funciona y está resuelto: rutas declaradas al mock, el resto al backend real. **En el front, depende de la tecnología de render, y la diferencia es tajante:**

| Front | ¿Se puede servir una pantalla prototipada dentro del recorrido real? | Por qué |
|---|---|---|
| **Web con DOM** (React, Angular, Vue, server-rendered…) | **Sí**, con matices | Una ruta no construida puede servirse desde el prototipo por proxy inverso, en el mismo origen, conservando sesión y cookies. Es el equivalente en el front del modo proxy del mock |
| **Web sobre lienzo** (Flutter Web y equivalentes) | **No** | La interfaz no vive en el DOM: no hay punto de composición donde insertar una pantalla externa en la aplicación en ejecución |
| **Móvil compilado** (nativo, Flutter, React Native) | **No** | No se pueden inyectar pantallas en un binario ya instalado |

Donde dice **sí**, el empalme por proxy es la mejor opción y se diseña con las mismas reglas del modo híbrido de servicios: se declara qué rutas van al prototipo, se documenta en la estrategia, y la parte prototipada nunca se presenta como certificada.

Donde dice **no**, cualquier diseño que pretenda encadenar aplicación real → prototipo → aplicación real es inviable, y lo que se hace es esto, en este orden:

1. **Comprobar si el front nuevo realmente falta.** Muchas veces la pantalla ya existe y lo único nuevo es el comportamiento del servicio: ahí el híbrido correcto es front real + mock de servicios, sin prototipo.
2. **Pedir un build de desarrollo con la funcionalidad tras una bandera.** Si el repositorio de front existe, ese build es más fiel que cualquier prototipo y no cuesta construcción.
3. **Sólo si no hay ninguna de las dos:** partir el escenario en la frontera. Lo que existe se certifica contra real; lo nuevo arranca en el prototipo con su estado sembrado y queda con `certification: pending_real_integration`.

## Restricciones

- **NUNCA** reconstruir un artefacto pre-desarrollo sin haber leído antes el manifiesto. Ya ocurrió en campo reconstruir a mano lo que el propio repositorio ya resolvía.
- **NUNCA** editar a mano un artefacto generado, ni "sólo esta vez".
- **NUNCA** editar pantallas, rutas o estados que sostienen suites de historias anteriores: la extensión es aditiva.
- **NUNCA** leer el repositorio de front o el design system con el modelo para "entenderlos": se extraen con herramienta y se lee la salida.
- **NUNCA** ajustar la semántica o la estructura de un prototipo para que una prueba pase. Es el contrato de fidelidad, y es anti-cheating extendido al prototipo (`[[calidad-sut-readiness-gate]]`).
- **NUNCA** presentar resultados obtenidos contra prototipo o mock como certificación del sistema real. Con reuso entre historias esta regla se vuelve más crítica, no menos.
- El manifiesto **no se escribe a mano**: si alguien lo edita, deja de reflejar el estado y vuelve el coste de averiguarlo.

## Verificación

Asset de **cumplimiento obligatorio**. Antes de cerrar la fase que lo invoca, comprobar cada punto. Si alguno no se cumple, se detiene y se reporta con el mensaje indicado.

| # | Comprobación | Si no se cumple |
|---|---|---|
| 1 | antes de construir cualquier prototipo o mock se leyó .evidence/mock-manifest.json y se declaró qué se hereda y qué se añade | Bloqueado: se iba a construir sin saber qué existía. Reconstruir lo que ya estaba es el desperdicio más caro de las entregas pre-desarrollo, y el manifiesto existe para que sea una lectura, no una investigación. |
| 2 | lo añadido en esta historia es aditivo: no se editó ninguna pantalla, ruta ni estado que otra historia ya usaba | Bloqueado: se modificó un artefacto compartido que sostiene suites anteriores. La extensión es aditiva; editar lo existente rompe historias ya certificadas. |
| 3 | ningún artefacto generado fue editado a mano, y la frontera entre lo generado y lo escrito está declarada y es física | Bloqueado: se parcheó a mano algo generado. O la siguiente regeneración se lleva el parche, o nadie regenera nunca por miedo a perderlo: en los dos casos el generador muere y vuelve el coste manual. |

## Cross-links

`[[calidad-sut-readiness-gate]]`, `[[calidad-service-virtualization-mockoon]]`, `[[calidad-ui-locator-map-contract]]`, `[[calidad-deterministic-work-to-tooling]]`, `[[calidad-repo-capability-discovery]]`, `[[calidad-figma-mcp-integration]]`, `[[calidad-delivery-gate-contract]]`, `[[calidad-test-data-management]]`, `[[calidad-pipeline-state-tracking]]`.
