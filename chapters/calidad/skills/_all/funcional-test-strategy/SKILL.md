---
id: calidad-funcional-test-strategy
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Define la estrategia de pruebas de un producto/iniciativa: niveles y tipos, cuadrantes ágiles, enfoque risk-based, pirámide y frontera con lo unitario, qué stacks de automatización del chapter se activan y cuándo, y cómo el shift-left (mocks, locator map) habilita probar antes del desarrollo."
tags: [funcional, test-strategy, risk-based, levels, quadrants, pyramid, shift-left, automation]
---

# Test Strategy — Estrategia de Pruebas

## Cuándo aplicar

- Cuando el usuario pide definir o revisar la estrategia de pruebas de un producto, release o iniciativa.
- Como sección obligatoria del plan de pruebas (`[[calidad-funcional-test-plan]]`) — la estrategia puede emitirse sola (documento corto) o embebida en el plan.
- Cuando un proyecto de automatización arranca sin dirección: la estrategia decide QUÉ se automatiza, en qué nivel y con qué stack, antes de que el router genere nada.

## Instrucción

1. **Levantar el contexto** — producto, arquitectura del SUT (`[[calidad-sut-types-and-adaptations]]`), criticidad y regulación (`[[calidad-context-determined-defaults]]`), práctica de desarrollo del equipo (BDD/ATDD/tradicional), madurez de automatización existente, y restricciones (ambientes, datos, plazos). Lo que no se sepa se pregunta o se declara supuesto.
2. **Definir niveles y tipos** — con `references/levels-types-quadrants.md`: qué se cubre en unitarias (dev), integración/API, E2E UI, mobile; y qué tipos aplican (funcional, contract, performance, seguridad, accesibilidad, visual, SEO — apoyándose en `[[calidad-transversal-capabilities]]` para las capas complementarias). La pirámide como principio: empujar la cobertura al nivel más bajo que pueda verificar el comportamiento.
3. **Enfoque risk-based** — con `references/risk-based-approach.md`: el esfuerzo se distribuye por riesgo (probabilidad × impacto), no por uniformidad. El risk map resultante alimenta la priorización de casos (`[[calidad-business-driven-prioritization]]`) y el análisis de riesgos del plan.
4. **Mapear a los stacks del chapter** — con `references/automation-stack-mapping.md`: qué parte de la estrategia ejecuta cada stack (Karate/K6/Playwright/Appium), qué queda manual/exploratorio, y cómo el modo pre-desarrollo (`[[calidad-sut-readiness-gate]]`: mocks, datos sintéticos, locator map) permite construir pruebas antes de que el desarrollo exista.
5. **Declarar el enfoque de datos y ambientes** — estrategia de datos (`[[calidad-test-data-management]]`) y de ambientes por nivel; si no hay ambiente, el camino mock→real con su plan de switchover.
6. **Emitir el documento** — estrategia standalone (5-8 secciones, formato en el reference de niveles) o como sección del plan. Gate humano: la estrategia se presenta y se aprueba antes de regir el diseño y la automatización.

## Restricciones

- **La estrategia decide fronteras, no lista casos** — el detalle de casos es de `[[calidad-funcional-test-design]]`; el detalle operativo (cronograma, responsables) es del plan.
- **NUNCA prometer cobertura uniforme**: "probamos todo por igual" no es estrategia. Toda estrategia declara qué recibe MENOS esfuerzo y por qué (decisión de riesgo explícita y visible).
- La frontera con lo unitario se pacta con desarrollo, no se impone: sin ese pacto hay doble cobertura o huecos.
- Una estrategia que activa un stack de automatización debe ser ejecutable por él: verificar contra los inputs obligatorios del stack (spec para Karate/K6, fuente UI para Playwright, APK para Appium) antes de comprometerla.
- Estrategia sin aprobación humana no rige: mismo patrón de gate que `[[calidad-pre-design-strategy-document]]` (el STRATEGY.md por stack de automatización es hijo operativo de esta estrategia general cuando ambas existen).

## Cross-links

- `references/levels-types-quadrants.md`
- `references/risk-based-approach.md`
- `references/automation-stack-mapping.md`
- `[[calidad-funcional-test-plan]]`, `[[calidad-funcional-test-design]]`, `[[calidad-transversal-capabilities]]`, `[[calidad-sut-readiness-gate]]`, `[[calidad-build-test-strategy-and-plan]]`
