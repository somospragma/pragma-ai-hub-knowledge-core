---
id: calidad-funcional-analyze-story-prompt
version: 1.0.0
scope: chapter
type: prompt
chapter: calidad
description: "Prompt puntual que analiza UNA historia de usuario (INVEST, criterios de aceptación, ambigüedades, veredicto DoR) y devuelve el reporte accionable, sin workflow ni escritura al ALM."
tags: [funcional, prompt, user-story, invest, analysis, dor]
---

# Prompt — Analizar una Historia de Usuario

## Cuándo invocar este prompt

Cuando se necesita el análisis de UNA HU como artefacto puntual (pegar el reporte en el refinamiento, decidir si entra al sprint), sin el workflow completo `[[calidad-analyze-and-refine-stories]]` ni publicación al ALM. Para lotes o escritura de vuelta, usar el workflow.

## Variables

- `{{story}}` — La HU COMPLETA: título, narrativa, descripción y criterios de aceptación. Si faltan los CA, el análisis lo reporta como hallazgo mayor (no los inventa).
- `{{context}}` — Opcional: dominio del producto, definiciones del equipo (DoR propia, formato de CA preferido), HUs relacionadas.

## Instrucción para el LLM

Aplica `[[calidad-funcional-story-analysis]]` estrictamente (consultar `references/invest-scoring.md`, `references/acceptance-criteria-quality.md` y `references/ambiguity-taxonomy.md` en su subfolder):

1. Scoring INVEST: los 6 criterios con `pass|warn|fail` y **evidencia textual citada** de la HU — nunca un veredicto sin cita.
2. Auditoría de cada CA: formato, atomicidad, decidibilidad, datos concretos, cobertura de familias (autorización, validación, estados, errores de dependencias) y proporción happy/negativo.
3. Ambigüedades y vacíos clasificados por la taxonomía, cada uno convertido en **pregunta concreta para el PO** con severidad `bloqueante|menor`.
4. Veredicto DoR (`ready | ready_with_warnings | not_ready`) con la lista exacta de lo que falta para `ready`. `T: fail` o bloqueantes abiertos fuerzan `not_ready`.
5. Salida en el formato de `references/analysis-report-format.md` (veredicto arriba, tablas, preguntas listas para pegar).

Reglas duras: NO reescribas la HU (eso es refinamiento), NO respondas las preguntas por el PO, NO suavices el veredicto, NO emitas hallazgos sin cita textual.
