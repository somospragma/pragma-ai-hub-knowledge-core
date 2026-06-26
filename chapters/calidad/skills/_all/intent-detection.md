---
id: calidad-intent-detection
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: Decide qué framework de automatización (Karate, K6, Playwright, Appium) aplicar a partir del intent del usuario.
tags: [intent, routing, karate, k6, playwright, appium]
---

# Intent Detection — Selección de Framework de Automatización

## Cuándo aplicar

Aplica este skill **siempre** al inicio de cualquier solicitud de generación de pruebas, antes de validar spec o de pedir inputs adicionales. Es el primer paso del workflow `[[calidad-route-test-generation]]`.

Tu trabajo aquí es **enrutar**, no generar. El resultado del skill es el nombre del workflow/skill específico que el agente debe invocar a continuación.

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
| Appium     | "mobile", "Android", "app", "Appium", "Screenplay mobile", "APK", "app_package", "app_activity"                        | (no se trata brownfield)                                          | `[[calidad-appium-screenplay-android]]`                                         |

## Restricciones

- Si el intent no es claro o cae entre dos frameworks, **pregunta explícitamente**; nunca asumas Playwright por defecto.
- **Appium requiere señales explícitas de Android** (APK, `app_package`, `app_activity`, "mobile Android"). La versión actual del Chapter (Appium V2) **no soporta iOS**: si el usuario pide mobile iOS, repórtalo como fuera de alcance y detente.
- K6 y Playwright/Karate pueden coexistir en un mismo programa de pruebas, pero **no en una sola solicitud de generación**: cada framework se genera por separado, en su propio `output_path`.
- Una vez decidido el framework, transfiere el control al workflow específico; no mezcles instrucciones de generación de distintos frameworks.
- Cuando detectes brownfield, antes de delegar al skill brownfield, asegúrate de que el `output_path` realmente contiene código previo (ver `[[calidad-brownfield-vs-greenfield]]`).
