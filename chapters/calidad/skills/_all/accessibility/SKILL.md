---
id: calidad-accessibility-testing
version: 2.0.0
scope: chapter
type: skill
chapter: calidad
description: "Accesibilidad transversal del chapter calidad: política y metodología de evaluación (WCAG 2.1/2.2 bajo principios POUR) tanto en revisión desde diseño (Product Designer) como en pruebas automatizadas (web/móvil), con marco normativo (foco banca/financiero LATAM), tipos de discapacidad, severidad, formato de hallazgo y estructura de reporte. Detalle por dimensión en references."
tags: [accessibility, a11y, wcag, pour, transversal, design-review, banca, all-stacks]
---

# Accesibilidad — Política y metodología transversal

## Instrucción

Skill transversal de accesibilidad del chapter. Define **qué** evaluar, **cuándo** y
**cómo clasificarlo y reportarlo**, agnóstico de stack. El detalle de cada bloque vive
en su reference; úsalo según el tipo de evaluación solicitada.

Cubre dos momentos complementarios del ciclo de calidad:

- **Revisión desde diseño** (antes de código): pantallas, flujos, prototipos, UX
  Writing y Design System desde la perspectiva de un Product Designer experto en
  accesibilidad. Ver `[design-review](references/design-review.md)`.
- **Pruebas automatizadas** (sobre el producto): suites de a11y en web y móvil.
  Implementación por stack abajo.

Toda evaluación se fundamenta en WCAG bajo principios POUR
(`[wcag-pour](references/wcag-pour.md)`) y, cuando aplique al producto financiero/bancario,
en el marco normativo (`[regulatory-framework](references/regulatory-framework.md)`).

## Cuándo aplicar

- Sobre pantallas/flujos priorizados (`CRITICAL`, `HIGH`) según
  `[[calidad-business-driven-prioritization]]`; en banca, priorizar los flujos críticos
  (login, MFA/OTP, pagos, transferencias, onboarding, firma digital…) listados en
  `[severity-and-findings](references/severity-and-findings.md)`.
- En cada PR, en un job filtrado por tag — no en cada test del pipeline.
- Greenfield: suite/revisión desde el inicio. Brownfield: se agrega sobre lo priorizado
  sin tocar tests preexistentes (`[[calidad-brownfield-vs-greenfield]]`).
- Nivel mínimo recomendado: **WCAG AA** (banca/financiero), salvo que el negocio o la
  jurisdicción exijan un nivel superior.

## Cómo evaluar y reportar

- **Principios POUR** y criterios a validar: `[wcag-pour](references/wcag-pour.md)`.
- **Tipos de discapacidad y barreras** a contemplar: `[disability-types-and-barriers](references/disability-types-and-barriers.md)`.
- **Severidad, formato de hallazgo y flujos críticos**: `[severity-and-findings](references/severity-and-findings.md)`.
- **Marco normativo y trazabilidad** (foco banca/financiero): `[regulatory-framework](references/regulatory-framework.md)`.
- **Estructura del reporte/entregable** (resumen + matriz): `[audit-report-structure](references/audit-report-structure.md)`.

Regla de evidencia: ningún criterio se marca como cumplido sin evidencia suficiente;
si falta, clasificar como *no verificable*, *evidencia insuficiente* o *riesgo potencial*.
Anexar hallazgos como evidencia según `[[calidad-test-evidence-and-traceability]]` y
`[[calidad-execution-metadata-schema]]`.

## Implementación por stack (pruebas automatizadas)

- **Web (Playwright):** axe-core + WCAG tags. Ver
  [[calidad-playwright-greenfield]] (consultar `references/accessibility-axe-wcag.md` en su subfolder).
- **Móvil (Appium/Screenplay):** Espresso a11y + accessibility-test-framework /
  Accessibility Scanner. Ver
  [[calidad-appium-screenplay-android]] (consultar `references/mobile-accessibility.md` en su subfolder).

## Relación con otras skills

- `[[calidad-seo]]` incluye accesibilidad a nivel del HTML servido (dimensión SEO);
  esta skill cubre la accesibilidad del producto bajo prueba y la revisión desde diseño.
- `[[calidad-visual-regression]]` y `[[calidad-failure-triage-and-classification]]`
  complementan la evidencia y la clasificación de hallazgos.
