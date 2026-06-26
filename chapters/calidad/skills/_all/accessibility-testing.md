---
id: calidad-accessibility-testing
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Política transversal de pruebas de accesibilidad (WCAG 2.1/2.2 AA) para suites automatizadas del chapter calidad: cuándo correr, dimensiones a verificar, severidad que bloquea, tags y evidencia. Aplica a web (Playwright) y móvil (Appium); enlaza a la implementación por stack."
tags: [accessibility, a11y, wcag, transversal, web, mobile, all-stacks]
---

# Accesibilidad — Política transversal de pruebas

## Instrucción

Esta skill define **qué** verificar y **cuándo** en accesibilidad para cualquier suite
del chapter, independiente del stack. El **cómo** específico vive en la reference del
stack correspondiente. No dupliques esta política dentro de un stack: enlázala.

Aplica a accesibilidad de aplicaciones bajo prueba (web y móvil). Para accesibilidad
a nivel del HTML servido por una página (auditoría SEO/on-page) ver
`[[calidad-seo]]`, que es complementaria a esta.

## Cuándo aplicar

- Sobre las pantallas/páginas priorizadas (`CRITICAL`, `HIGH`) según
  `[[calidad-business-driven-prioritization]]`.
- En cada PR, en un job filtrado por tag — **no** en cada test del pipeline.
- En greenfield se genera la suite de a11y desde el inicio; en brownfield se agrega
  sobre las pantallas priorizadas sin tocar tests preexistentes
  (`[[calidad-brownfield-vs-greenfield]]`).

## Dimensiones mínimas (WCAG 2.1/2.2 AA)

Universales a web y móvil; el mapeo técnico concreto está en la reference del stack.

- **Contenido no textual (1.1.1):** texto alternativo / `contentDescription` /
  `accessibilityLabel` en imágenes informativas; decorativas marcadas como tales.
- **Info y relaciones (1.3.1):** roles correctos (button, header, link) y labels
  asociados a inputs.
- **Contraste (1.4.3 / 1.4.11):** ≥ 4.5:1 texto normal, ≥ 3:1 texto grande e iconos
  significativos / bordes de input.
- **Foco visible y orden coherente (2.4.7):** sin trampas de foco; orden sigue el flujo visual.
- **Tamaño de objetivo (2.5.5):** ≥ 48dp Android / 44pt iOS / objetivo táctil suficiente en web.
- **Labels o instrucciones (3.3.2):** cada input expone label o hint significativo.
- **Name, Role, Value (4.1.2):** cada control expone name, role y state correctos.

## Severidad que bloquea

El escenario falla cuando hay al menos una violación de severidad **serious/critical**
(web, axe-core) o **ERROR o superior** (móvil). Las exclusiones de nodos conocidos y
aceptados deben ser explícitas y justificadas en el código.

## Tags y evidencia

- Etiquetar los escenarios con `@accessibility @a11y` (más `@mobile` en suites móviles)
  además de los tags del chapter.
- Anexar cada hallazgo como evidencia del reporte según
  `[[calidad-test-evidence-and-traceability]]` y `[[calidad-execution-metadata-schema]]`.

## Implementación por stack

- **Web (Playwright):** axe-core + WCAG tags. Ver
  `[accessibility-axe-wcag](../../playwright/playwright-greenfield/references/accessibility-axe-wcag.md)`.
- **Móvil (Appium/Screenplay):** Espresso a11y + accessibility-test-framework / Accessibility
  Scanner. Ver
  `[mobile-accessibility](../../appium/appium-screenplay-android/references/mobile-accessibility.md)`.
