---
id: calidad-intent-detection
version: 1.1.0
scope: chapter
type: skill
chapter: calidad
description: Decide qué stack aplicar a partir del intent del usuario — los 4 frameworks de automatización (Karate, K6, Playwright, Appium) o el stack funcional (análisis/refinamiento de HUs, diseño de casos, estrategia y planes).
tags: [intent, routing, karate, k6, playwright, appium, funcional]
---

# Intent Detection — Selección de Framework de Automatización

## Cuándo aplicar

Aplica este skill **siempre** al inicio de cualquier solicitud de generación de pruebas, antes de validar spec o de pedir inputs adicionales. Es el primer paso del workflow `[[calidad-route-test-generation]]`.

Tu trabajo aquí es **enrutar**, no generar. El resultado del skill es el nombre del workflow/skill específico que el agente debe invocar a continuación.

Esta skill decide **con qué framework** se generan las pruebas. La decisión de **qué capas transversales complementarias** (accesibilidad, SEO, seguridad, regresión visual, contract, performance) tejer la toma `[[calidad-transversal-capabilities]]` en el paso 2.5 del router. Algunas keywords de abajo (p.ej. "accessibility", "visual") sirven aquí solo como señal de que el SUT es web (framework Playwright); la capa transversal correspondiente la resuelve esa otra skill.

## Instrucción

1. Lee el campo `intent` del usuario en su literalidad (no parafrasees).
2. Busca **keywords disparadoras** del framework en la tabla de detección.
3. Determina si el contexto sugiere **brownfield** (proyecto existente al que se agregan/actualizan tests) o **greenfield** (proyecto nuevo). Para esto usa también `[[calidad-brownfield-vs-greenfield]]`.
4. Devuelve el skill/workflow destino. Si dos frameworks pueden aplicar (p. ej. "pruebas de carga sobre el frontend"), **pregunta al usuario** cuál es la prioridad; no asumas.
5. Si NO se detecta ningún keyword claro: **detente y pregunta** explícitamente al usuario qué tipo de prueba quiere (funcional API, performance, web E2E, mobile).

## Tabla de detección

| Framework  | Keywords disparadoras                                                                                                  | Señal brownfield                                                  | Skill / workflow destino                                                |
|------------|------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------|-------------------------------------------------------------------------|
| Karate     | "pruebas funcionales", "API testing", "REST", "SOAP", "OpenAPI", "Swagger", "WSDL", "contract testing", "Karate"       | "proyecto existente", "agregar tests", "integrar", "ya tenemos"   | greenfield → `[[calidad-karate-greenfield]]` · brownfield → `[[calidad-karate-brownfield]]` |
| K6         | "performance", "carga", "load", "stress", "spike", "soak", "K6", "VUs", "latencia", "throughput", "p95", "p99"          | (no se trata brownfield)                                          | `[[calidad-k6-greenfield]]`                                                     |
| Playwright | "web", "browser", "E2E", "UI", "frontend", "Playwright", "page object", "visual", "accessibility", "regresión visual" | "proyecto existente", "actualizar selectores", "ya hay tests web" | greenfield → `[[calidad-playwright-greenfield]]` · brownfield → `[[calidad-playwright-brownfield]]` |
| Appium (JVM) | "mobile", "Android", "app", "Appium", "Screenplay mobile", "APK", "app_package", "app_activity", "Serenity", "Gradle" | "proyecto existente", "agregar escenarios", "ya tenemos suite mobile" | greenfield → `[[calidad-appium-screenplay-android]]` · brownfield → `[[calidad-appium-brownfield]]` |
| Appium (TypeScript) | "mobile" + "TypeScript"/"WebdriverIO"/"WDIO"/"cucumber-js"/"Node", "iPad", "tablet", "web móvil", "app y navegador móvil" | "proyecto existente", "actualizar selectores", "agregar plataforma" | greenfield → `[[calidad-appium-wdio-greenfield]]` · brownfield → `[[calidad-appium-wdio-brownfield]]` |
| Funcional  | "analizar historia", "HU", "INVEST", "criterios de aceptación", "refinamiento", "refinar", "casos de prueba" (diseño, no código), "test cases", "test plan", "plan de pruebas", "estrategia de pruebas", "matriz de trazabilidad", "Azure DevOps"/"Jira" como fuente de HUs | (no aplica greenfield/brownfield)                                 | análisis/refinamiento → `[[calidad-analyze-and-refine-stories]]` · diseño de casos → `[[calidad-design-test-cases]]` · estrategia/plan → `[[calidad-build-test-strategy-and-plan]]` |

**Desambiguación mobile: ¿JVM o TypeScript?** Los dos stacks Appium comparten el servidor Appium y difieren en todo lo demás (lenguaje, cliente, runner, patrón, build). La decisión **no la toma el agente por preferencia**: la determina el ecosistema del equipo y, en brownfield, el proyecto que ya existe.

| Señal | Stack |
|---|---|
| `build.gradle` con `appium-java-client`, `pom.xml`, Serenity, Screenplay | Appium JVM |
| `package.json` con `webdriverio`, `cucumber.config.js`, `.steps.ts`, objetos de pantalla en TypeScript | Appium TypeScript |
| El equipo pide explícitamente Java o TypeScript | Lo pedido |
| Greenfield sin señal de ecosistema | **Pregunta.** No asumas |

Señales que **no** desambiguan por sí solas: "Appium", "mobile", "Android", "iOS". Aparecen en los dos stacks.

**Repos híbridos web y mobile**: un mismo repositorio puede necesitar dos stacks a la vez —por ejemplo, navegador con Playwright y app nativa con Appium TypeScript, orquestados por un único cucumber-js—. En ese caso se entregan **ambos** bundles y las convenciones comunes de la capa Cucumber vienen de `[[calidad-cucumber-bdd-conventions]]`. No se fuerza un stack único ni se ignora la mitad del repositorio.

**Desambiguación "pruebas funcionales"**: si el intent pide *generar/automatizar* pruebas funcionales de una API (hay spec, endpoints, "automatiza") → Karate. Si pide *diseñar, documentar o gestionar* — analizar HUs, escribir casos de alto nivel, plan, estrategia — → stack funcional. Ante la duda, la pregunta es: "¿el entregable es código de pruebas ejecutable, o documentos/casos en el ALM?". El camino natural completo es funcional primero (diseño) y automatización después (los casos diseñados alimentan a los stacks).

## Restricciones

- Si el intent no es claro o cae entre dos frameworks, **pregunta explícitamente**; nunca asumas Playwright por defecto.
- Los intents funcionales NO pasan por spec-validation ni brownfield-vs-greenfield: el router los bifurca directo al workflow funcional (ver la ruta funcional en `[[calidad-route-test-generation]]`).
- **iOS sí está soportado por el chapter.** Lo que tiene alcance Android es el *scaffolder* greenfield del stack JVM (`[[calidad-appium-screenplay-android]]`), no el chapter: para iOS greenfield en JVM se aplica el scaffold manual documentado en su `references/android-only-scope-rationale.md`; el stack TypeScript (`[[calidad-appium-wdio-greenfield]]`) genera iOS de forma nativa, y el brownfield de ambos stacks soporta Android e iOS. Nunca reportes iOS como fuera de alcance.
- **iOS exige entorno macOS** con Xcode y, en dispositivo físico, credenciales de firma. Si el entorno no lo cumple, no se degrada a Android en silencio: se genera lo pedido, se declara que no se pudo ejecutar y se reporta `partial`.
- K6 y Playwright/Karate pueden coexistir en un mismo programa de pruebas, pero **no en una sola solicitud de generación**: cada framework se genera por separado, en su propio `output_path`.
- Una vez decidido el framework, transfiere el control al workflow específico; no mezcles instrucciones de generación de distintos frameworks.
- Cuando detectes brownfield, antes de delegar al skill brownfield, asegúrate de que el `output_path` realmente contiene código previo (ver `[[calidad-brownfield-vs-greenfield]]`).
