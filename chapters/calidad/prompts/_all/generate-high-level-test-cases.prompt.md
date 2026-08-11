---
id: calidad-funcional-generate-test-cases-prompt
version: 1.0.0
scope: chapter
type: prompt
chapter: calidad
description: "Prompt puntual que diseña los casos de prueba de alto nivel de UNA historia de usuario con técnicas formales declaradas y matriz CA-caso, en Gherkin español data-driven, sin publicar al ALM."
tags: [funcional, prompt, test-design, gherkin, bva, data-driven]
---

# Prompt — Generar Casos de Prueba de Alto Nivel

## Cuándo invocar este prompt

Cuando se necesitan los casos de UNA HU como artefacto puntual (markdown listo para revisar o pegar), sin las fases del workflow `[[calidad-design-test-cases]]` ni publicación al ALM. Para test plans completos, lotes o creación en Azure/Jira, usar el workflow.

## Variables

- `{{story}}` — HU completa con criterios de aceptación. Si la HU no tiene CA o es visiblemente ambigua, DETENTE y devuelve el problema (sugiere `[[calidad-funcional-analyze-story-prompt]]` primero): diseñar sobre HU rota produce casos que validan ambigüedades.
- `{{example_map}}` — Opcional: reglas y ejemplos del refinamiento (semilla directa de casos).
- `{{formato}}` — `gherkin` (default) | `paso-a-paso`.
- `{{risk_map}}` — Opcional: prioridades por flujo. Sin él, prioridad `[A CONFIRMAR]` (nunca inferida por keywords).

## Instrucción para el LLM

Aplica `[[calidad-funcional-test-design]]` estrictamente (consultar `references/technique-selection-guide.md`, `references/equivalence-partitioning-bva.md` y `references/test-case-format.md` en su subfolder):

1. Abre declarando las **técnicas seleccionadas y por qué** (según el tipo de comportamiento de cada CA).
2. Diseña con las técnicas: BVA obligatorio ante límites (exacto, +1, −1), tabla de decisión ante reglas combinadas, transición de estados ante ciclos de vida, pairwise ante matrices de configuración.
3. Redacta cada caso con el formato canónico: título=comportamiento, trazabilidad a CA, técnica, tipo, precondiciones, Gherkin español declarativo (un Cuando por escenario, Entonces decidibles) y **tabla `@param` para las variantes** (variantes de la misma lógica = UN caso data-driven, no N casos).
4. Cierra con la **matriz CA↔casos**: 100% de CA cubiertos (positivo y, donde aplique, negativo); casos huérfanos eliminados o con su regla justificada; conteo happy/negativo/borde.
5. Marca el `Nivel sugerido` (api|ui|mobile|manual) por caso — insumo para automatización posterior.

Reglas duras: NO inventes reglas/límites que la HU no declara (repórtalos como pregunta), NO limites la cantidad de casos por estética ni infles con redundantes, NO uses "correctamente/adecuadamente" en ningún Entonces, NO incluyas selectores ni endpoints internos (comportamiento observable, no implementación).
