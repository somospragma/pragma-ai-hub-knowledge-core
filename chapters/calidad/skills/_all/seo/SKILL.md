---
id: calidad-seo
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
applies_to_stacks: [playwright]
description: "Auditoria SEO tecnica agnostica de stack para pruebas web del chapter calidad: cubre 8 dimensiones (tecnico, on-page, performance, schema, imagenes, sitemap, hreflang, accesibilidad) como references. Aplica a Playwright y futuros stacks web."
tags: [seo, web, auditoria, transversal, all-stacks]
---

# SEO — Auditoria tecnica para pruebas web

## Instruccion

Skill transversal de auditoria SEO corregible desde desarrollo, agnostica de stack.
Cubre las dimensiones SEO evaluables sobre el HTML/output observable; **el detalle de
cada dimension vive en su reference**. Usa la dimension que corresponda al hallazgo o
checklist solicitado.

Aplica a pruebas web (hoy Playwright; extensible a futuros stacks web del chapter).
El proceso completo de auditoria (pesos, puntuacion, entregables) esta en el workflow
`[[calidad-seo-audit-workflow]]`. Para accesibilidad de la app bajo prueba (no del HTML
servido) ver `[[calidad-accessibility-testing]]`, complementaria a la dimension de
accesibilidad SEO.

## Dimensiones (references)

- [technical](references/technical.md) — Auditoría técnica SEO agnóstica de tecnología
- [on-page](references/on-page.md) — Auditoría on-page agnóstica de tecnología con cobertura multi-motor
- [performance](references/performance.md) — Auditoría de rendimiento agnóstica de tecnología
- [schema](references/schema.md) — Detección, validación y generación de datos estructurados (JSON-LD) con cobertura multi-motor
- [images](references/images.md) — Auditoría de imágenes agnóstica de tecnología
- [sitemap](references/sitemap.md) — Auditoría y configuración del sitemap XML agnóstica de tecnología
- [hreflang](references/hreflang.md) — Auditoría e implementación de hreflang agnóstica de tecnología con cobertura multi-motor
- [accessibility](references/accessibility.md) — Auditoría de accesibilidad y HTML semántico agnóstica de tecnología

## Cuando aplicar

- Sobre paginas priorizadas (`CRITICAL`, `HIGH`) segun `[[calidad-business-driven-prioritization]]`.
- Solo caracteristicas corregibles desde codigo o configuracion (no estrategia de
  contenido ni link building).
- Anexar hallazgos como evidencia segun `[[calidad-test-evidence-and-traceability]]`.
