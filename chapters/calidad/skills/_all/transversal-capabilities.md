---
id: calidad-transversal-capabilities
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Detecta qué capacidades transversales complementarias (accesibilidad, SEO, seguridad, regresión visual, contract testing, performance) debe tejer el diseño de pruebas, a partir del intent, el tipo de SUT y el contexto regulatorio. Complementa la detección de framework con la decisión de qué capas integrales aplicar."
tags: [transversal, routing, accessibility, seo, security, visual, contract, risk-first]
---

# Detección de Capacidades Transversales Complementarias

## Cuándo aplicar

Después de identificar el framework (`[[calidad-intent-detection]]`) y antes de emitir
archivos, dentro del paso 2.5 del router `[[calidad-route-test-generation]]`. Mientras
`[[calidad-intent-detection]]` decide **con qué framework** se generan las pruebas, esta
skill decide **qué capas complementarias** las hacen una prueba integral.

Operacionaliza el principio *risk-first* del `[[calidad-chapter-perspective]]`: la
profundidad y el tipo de prueba son proporcionales al impacto del flujo y a la exposición
regulatoria.

## Instrucción

1. Reúne las **señales**: el `intent` literal, el framework ya detectado, el tipo de SUT
   (`[[calidad-sut-types-and-adaptations]]`), las características del flujo (auth, PII,
   dinero, público) y el contexto sectorial/regulatorio (banca, salud, gobierno…).
2. Recorre la **matriz de detección** y arma la lista de capacidades candidatas.
3. **Propón** al usuario las capas detectadas con su justificación (risk-first). No las
   asumas: confirma alcance. Si el usuario las acota, respétalo y regístralo.
4. Para cada capacidad aceptada, devuelve: la **skill a aplicar**, el **tag/suite** y la
   **sección del plan** que se añade. Esto alimenta el plan de generación y el bloque
   `transversal_capabilities` del `[[calidad-delivery-gate-contract]]`.
5. Registra también las capacidades **omitidas** y por qué (fuera de alcance, no aplica,
   el usuario las descartó) — para trazabilidad.

## Matriz de detección

| Capacidad | Señales del intent | Señales de SUT / flujo / sector | Skill a tejer | Tag |
|-----------|--------------------|----------------------------------|---------------|-----|
| Accesibilidad | "accesibilidad", "a11y", "WCAG", "inclusión", "lectores de pantalla" | UI web o móvil; banca/financiero, salud, gobierno (escala con `regulatory-framework`); flujos de cara al usuario | `[[calidad-accessibility-testing]]` | `@accessibility @a11y` |
| SEO | "SEO", "posicionamiento", "metadatos", "indexación", "sitemap" | Sitio/portal web **público** (no aplica a intranets/apps internas ni APIs) | `[[calidad-seo]]` | `@seo` |
| Seguridad | "seguridad", "OWASP", "vulnerabilidad", "pentest", "authz/authn" | Flujos con auth, manejo de PII/PCI, dinero (pagos/transferencias/créditos), endpoints expuestos | `[[calidad-security-testing]]` | `@security` |
| Regresión visual | "visual", "regresión visual", "pixel", "snapshot UI" | UI web o móvil con identidad visual relevante / pantallas estables priorizadas | `[[calidad-visual-regression]]` | `@visual` |
| Contract testing | "contrato", "contract", "consumer/provider", "schema registry" | API con múltiples consumidores o integración entre servicios | `[[calidad-contract-testing]]` | `@contract` |
| Performance (complemento) | "carga", "rendimiento", "p95", "SLA", "concurrencia" | Flujo crítico con SLAs o alta concurrencia (transacciones, picos) | suite K6 aparte (`[[calidad-generate-k6-suite]]`) | `@performance` |

## Reglas

- **Proponer, no imponer.** Toda capa detectada se confirma con el usuario antes de tejerla.
- **Por tipo de SUT (defaults sugeridos):**
  - UI web pública → accesibilidad + regresión visual + SEO (+ seguridad si hay auth/datos sensibles).
  - UI web interna / app → accesibilidad + regresión visual (SEO no aplica).
  - Móvil (Appium) → accesibilidad (móvil) + regresión visual.
  - API (Karate) → seguridad (OWASP API) + contract testing cuando hay múltiples consumidores.
  - Performance (K6) ES la capa de performance; como complemento de otra suite se genera por separado.
- **Risk-first / escalamiento:** en flujos críticos (login, MFA/OTP, pagos, transferencias,
  créditos, firma, onboarding) y en sectores regulados (banca, salud, gobierno), las capas
  de seguridad y accesibilidad pasan de *sugeridas* a **recomendadas con fuerza**, y la
  accesibilidad usa el `regulatory-framework`; la seguridad usa
  `[[calidad-security-testing]]` con su `compliance-regulatory-mapping`.
- **No aplica:** SEO solo en web pública; contract solo cuando hay contratos consumer/provider.
- **Anti-cheating:** las suites resultantes con tags `@security`, `@contract`,
  `@compliance`, `@regulatory` NO se modifican por auto-corrección (regla maestra del chapter,
  ver `[[calidad-test-self-correction-loop]]`).
- **Una capa transversal no cambia el framework**: se teje dentro del mismo proyecto del
  framework detectado (p.ej. accesibilidad axe en la suite Playwright) o se entrega como
  suite separada cuando requiere otro runtime (p.ej. performance K6).

## Salida esperada

Una lista estructurada que el router usa para el plan y el delivery-gate, por ejemplo:

```yaml
transversal_capabilities:
  detected:
    - capability: accessibility
      skill: calidad-accessibility-testing
      tag: "@accessibility"
      rationale: "UI web de banca; flujo de login (crítico) + exposición regulatoria"
      confirmed_by_user: true
    - capability: security
      skill: calidad-security-testing
      tag: "@security"
      rationale: "Flujo con autenticación y datos sensibles (PII)"
      confirmed_by_user: true
  omitted:
    - capability: seo
      reason: "Portal transaccional autenticado, no indexable"
```
