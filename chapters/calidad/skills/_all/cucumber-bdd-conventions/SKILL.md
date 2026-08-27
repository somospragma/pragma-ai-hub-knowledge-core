---
id: calidad-cucumber-bdd-conventions
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
applies_to_stacks: [karate, playwright, appium-core, appium-wdio, appium-serenity]
description: Convenciones de un arquetipo Cucumber multi-plataforma — catálogo de steps, sufijo de plataforma, tagging, estructura de archivos y propiedades verificables por análisis estático.
tags: [cucumber, bdd, gherkin, steps, tagging, multiplataforma, convenciones]
---

# Cucumber BDD — Convenciones de arquetipo multi-plataforma

## Cuándo aplicar

Cuando el proyecto usa **Cucumber como orquestador único** de una suite que cubre varias plataformas o varios drivers a la vez: web y mobile, Android e iOS, teléfono y tablet, app nativa y navegador móvil. Es el caso de los arquetipos donde un solo `cucumber.config.js` (o `cucumber.json`, o el runner JVM equivalente) define perfiles por plataforma y todos comparten `features/`, hooks y World.

Aplica sin importar qué librería mueve el driver debajo: Appium/WebdriverIO, Playwright usado como librería, Selenium, Karate o serenity-wdio (Cucumber 11 como orquestador único de sus cinco canales: web, web_movil, movil Android/iOS, desktop y api). Lo que este skill gobierna es la **capa Cucumber**, que es la que se rompe primero cuando crecen las plataformas.

No aplica cuando el proyecto usa el runner nativo del framework (`@playwright/test` con `*.spec.ts`, Serenity con runner JUnit) y Gherkin no existe o es marginal. Para esos casos, las convenciones viven en el skill del stack correspondiente.

Antes de activar este skill confirma intent con `[[calidad-intent-detection]]` y recolecta inputs obligatorios con `[[calidad-mandatory-inputs-protocol]]`. Aplica la perspectiva del chapter en `[[calidad-chapter-perspective]]`.

## Por qué existe este skill

En un arquetipo mono-plataforma, un step duplicado es una molestia. En uno multi-plataforma es un fallo de ejecución: **Cucumber mantiene un registro global de steps por perfil**, y carga todos los archivos de definiciones que el perfil declara — de todas las épicas, no solo de la que se está tocando. Dos definiciones que matchean el mismo texto producen `Ambiguous step definition` y la suite entera queda roja por un archivo que nadie estaba mirando.

Esto es exactamente el fallo que produce un agente generando features sin contexto: reimplementa el login por quinta vez porque no sabe que ya existe en otra épica. Las cuatro reglas que lo evitan son el catálogo de steps, el sufijo de plataforma, la ubicación por transversalidad y la verificación estática antes de entregar.

## Lectura obligatoria antes de escribir el primer `.feature`

| Reference | Para qué |
|---|---|
| `references/step-catalog.md` | El catálogo como artefacto vivo y el protocolo de consulta antes de crear cualquier step |
| `references/platform-suffix-and-ambiguity.md` | Por qué todo step lleva sufijo de plataforma y cómo se resuelve una ambigüedad |
| `references/gherkin-tagging-and-naming.md` | Tags de plataforma, browser, story y tipo; patrón de nombre de escenario; placeholder de ID |
| `references/file-structure-conventions.md` | Dónde va cada archivo: features, steps, pages, screens, test-data |
| `references/hooks-and-world-contract.md` | Un hook por tag de plataforma, World tipado, timeouts, evidencia por step, teardown |
| `references/static-correctness-properties.md` | Las 12 propiedades verificables y sus comandos de verificación |

## Instrucción

1. **Inventariar antes de escribir.** Localiza el catálogo de steps del proyecto (`step-catalog.md` o equivalente). Si no existe, **genéralo** a partir del código antes de continuar: recorre todos los archivos de definiciones y extrae texto, tipo, plataformas y ruta. Un arquetipo multi-plataforma sin catálogo no está listo para que un agente le agregue features. Aplica `references/step-catalog.md`.
2. **Buscar en todas las épicas, no solo en la propia.** Para cada step candidato, busca por texto literal y por variación semántica en el árbol completo de definiciones. La búsqueda por épica es el error clásico: el step existe, pero en otra carpeta, y se descubre cuando la suite explota en ambigüedad.
3. **Clasificar cada step candidato** en uno de cuatro estados, y declararlo en el turno:
   - `reuse` — existe con el texto y la plataforma que necesito. Se referencia, no se implementa.
   - `extend-platform` — existe el texto pero no para esta plataforma. Se implementa **solo** la plataforma faltante, con el mismo texto y el sufijo correspondiente.
   - `new-local` — no existe y es específico de esta épica. Va en la carpeta de la épica.
   - `new-shared` — no existe y aplica a más de una épica. Va en la carpeta compartida y **se registra en el catálogo** en el mismo cambio.
4. **Aplicar el sufijo de plataforma** a todo step nuevo, sin excepción, según `references/platform-suffix-and-ambiguity.md`. Un step sin sufijo es un choque futuro garantizado.
5. **Escribir el `.feature`** siguiendo `references/gherkin-tagging-and-naming.md`: exactamente un tag de plataforma por escenario, tag de browser cuando la plataforma es web, tag de story (real o placeholder), al menos un tag de tipo, y nombre de escenario autoexplicativo. El texto del step debe describir lo que su implementación realmente hace — un `Then` que dice "el sistema responde correctamente" mientras verifica un mensaje de error concreto es un defecto, no un matiz de estilo.
6. **Ubicar los archivos** según `references/file-structure-conventions.md`. Los selectores nunca viven en el código de steps ni en los objetos de página o pantalla: van al archivo de test-data de la plataforma correspondiente.
7. **Cablear hooks y World** según `references/hooks-and-world-contract.md` si la plataforma es nueva en el arquetipo. Un tag de plataforma sin hook que cree su driver produce escenarios que fallan en el primer step con un driver `undefined`.
8. **Verificar antes de entregar.** Ejecuta las 12 propiedades de `references/static-correctness-properties.md` sobre los archivos tocados **y** sobre el árbol completo cuando se creó un step compartido. Reporta el resultado como parte del delivery gate (`[[calidad-delivery-gate-contract]]`). Una propiedad que falla es un blocker, no una observación.
9. **Actualizar el catálogo** si se creó algún step `new-shared`. El catálogo desactualizado es peor que no tenerlo: induce a reimplementar lo que sí existe.
10. **Registrar trazabilidad** con `[[calidad-test-evidence-and-traceability]]`: cada escenario mapea a un caso o historia. Si el ID del ALM todavía no existe, se usa el placeholder documentado en `references/gherkin-tagging-and-naming.md` y se deja el reemplazo como paso pendiente explícito, nunca como deuda silenciosa.

## Restricciones

- **Nunca crear un step nuevo sin haber ejecutado el paso 2.** La búsqueda incompleta es la causa raíz número uno de ambigüedad en estos arquetipos.
- **Nunca modificar un step existente para que "encaje"** en el escenario nuevo. Ese step lo consumen otras épicas: cambiarlo las rompe en silencio. Si el comportamiento requerido difiere, es un step nuevo.
- **Nunca mover un step a la carpeta compartida sin registrarlo en el catálogo** en el mismo cambio.
- **Nunca hardcodear selectores** en definiciones de steps, objetos de página u objetos de pantalla. La propiedad 3 lo detecta por grep y es motivo de rechazo.
- Las convenciones del proyecto del cliente **siempre mandan** sobre las de este skill: idioma de los steps, nomenclatura de tags, patrón de nombres. Este skill aporta la estructura y los controles; los valores concretos se detectan del arquetipo existente.
- En brownfield, si detectas violaciones preexistentes de estas propiedades, **repórtalas con evidencia y propone el fix — no las corrijas por tu cuenta**. Corregir código ajeno fuera del alcance pedido viola el guardrail del chapter.

## Ejemplo

Solicitud: agregar a un arquetipo con perfiles `web`, `android`, `ios`, `ipad` y `tablet` un escenario de bloqueo de cuenta tras tres intentos fallidos, para Android e iOS.

Resultado esperado del paso 3, declarado antes de escribir nada:

| Step | Estado | Acción |
|---|---|---|
| el usuario desea ingresar a la banca digital en Android | `reuse` | Existe en la épica de login |
| el usuario desea ingresar a la banca digital en iOS | `reuse` | Existe en la épica de login |
| el usuario ingresa credenciales inválidas 3 veces en Android | `new-local` | Nuevo, específico de esta épica |
| el usuario ingresa credenciales inválidas 3 veces en iOS | `new-local` | Nuevo, específico de esta épica |
| el sistema debe mostrar el mensaje {string} en Android | `reuse` | Step parametrizado transversal ya existente |
| el sistema debe mostrar el mensaje {string} en iOS | `reuse` | Step parametrizado transversal ya existente |

Cuatro de los seis steps no se implementan. Sin el paso 2, un agente habría escrito los seis y roto los dos últimos por ambigüedad con la épica de mensajes.
