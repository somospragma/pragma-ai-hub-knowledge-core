# Comerciales vs OSS — Herramientas de Self-Healing

Tabla comparativa de las herramientas más comunes en el mercado para self-healing de tests. La recomendación del chapter es **OSS por default**, salvo que el cliente ya licencie alguna comercial.

## Tabla comparativa

| Tool | Tipo | Frameworks soportados | Mecanismo de self-healing | Costo |
|---|---|---|---|---|
| Healenium | OSS | Selenium, Appium | ML-based selector replacement (compara estructura DOM histórica) | Free (self-hosted) |
| Mabl | Comercial | Web E2E propietario | Visual + heuristic + auto-stabilize | Premium (per-user + per-run) |
| Testim | Comercial | Web, mobile (limitado) | AI selectors (smart locators) | Premium |
| Functionize | Comercial | Web, mobile, API | NLP-based + visual ML | Premium |
| Reflect | Comercial | Web no-code | Auto-stabilize selectors visualmente | Premium |
| ResilientLocator pattern (chapter) | OSS / propio | Playwright, Cypress, Appium | Multi-locator fallback chain + LLM repair on-demand | Free |
| Applitools | Comercial (con tier free) | Playwright, Cypress, Selenium, Appium | Visual AI (Layout/Content/Strict) | Freemium → Premium |

## Recomendación Pragma (default chapter)

- **Playwright (web)**: `ResilientLocator` (ver `multi-locator-fallback-pattern.md`) + Applitools en modo `Layout` solo para suites con UI volátil.
- **Appium (mobile)**: Healenium para proyectos legacy donde el equipo dev no expone `accessibility-id`; `ResilientLocator` en proyectos nuevos.
- **Karate (REST/GraphQL)**: matchers `##type` nativos del framework, sin herramienta externa.
- **K6 (perf)**: `check()` permisivo con telemetría custom, sin herramienta externa.

## Cuándo licenciar comercial

Activar negociación con el cliente para usar comercial **solo si**:

- El cliente ya tiene licencia activa de Mabl / Testim / Functionize / Reflect y exige que el suite se construya allí.
- El equipo del cliente carece de capacidad para mantener Healenium self-hosted y el costo de no usar comercial supera la licencia.
- La aplicación tiene cambios de UI tan frecuentes que el costo de mantener la fallback chain manualmente excede el comercial (caso raro).

## Antipatrones

- Empezar con comercial "por si acaso" — genera lock-in y costo recurrente que el cliente no asumió.
- Combinar Mabl/Testim con suites en Playwright/Karate del chapter en paralelo — duplica esfuerzo y confunde la evidencia de `[[calidad-test-evidence-and-traceability]]`.
- Usar Functionize para tests de contract o security — explícitamente bloqueado por `over-healing-guardrails.md`.

## Criterio de decisión

| Pregunta | Sí → | No → |
|---|---|---|
| ¿Cliente ya licencia herramienta comercial? | Usar la del cliente | OSS chapter |
| ¿La UI tiene >10 reflows/release? | Aplitools `Layout` o comercial | `ResilientLocator` puro |
| ¿Suite es `@security` / `@contract`? | NO healing (bloqueado) | Aplica healing |
| ¿Proyecto greenfield mobile? | `ResilientLocator` + accessibility-id obligatorio | Healenium si legacy |
