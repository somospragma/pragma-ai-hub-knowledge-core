---
id: calidad-post-generation-execution-prompt
version: 1.1.0
scope: chapter
type: skill
chapter: calidad
description: "OBLIGATORIO. Prompt universal post-scaffold para confirmar modo de ejecución (full/dry-run/scaffold-only/execute-only) antes de invocar el smoke gate. Aplica a todos los stacks del chapter en los 5 IDEs."
tags: [post-generation, prompt, universal, mandatory]
enforcement: mandatory
---

# Post-Generation Execution Prompt — Confirmación universal antes de smoke gate

## Propósito

Inmediatamente después de emitir el último archivo del scaffold y **antes** de ejecutar el smoke gate del `[[calidad-post-generation-protocol]]`, el agente DEBE preguntar al usuario cómo procede la ejecución. Este prompt es universal: aplica a Karate, Playwright, K6, Appium y serenity-wdio, en greenfield y brownfield, en los 5 IDEs soportados.

El modo inicial (`full | dry-run | scaffold-only | execute-only`) se confirma en `[[calidad-pre-generation-protocol]]`. Aquí se confirma **operativamente** cómo ejecutar lo recién generado, ya con visibilidad real de los archivos emitidos.

## Mensaje exacto al usuario

El agente DEBE emitir literalmente este bloque (puede traducir mínimamente, pero las opciones (a)(b)(c)(d) no cambian de letra ni de orden):

> Generación completa ✓. ¿Cómo procedemos?
>
> (a) Ejecutar smoke 1:1 + suite completa (modo full)
> (b) Ejecutar solo smoke 1:1 (gate mínimo)
> (c) Solo dejar scaffold y ejecutar después manualmente
> (d) Cancelar — necesito revisar algo

## Default sugerido por framework

El agente puede acompañar el prompt con una sugerencia explícita según el stack detectado. La sugerencia NO sustituye la respuesta del usuario.

| Stack       | Default sugerido | Razonamiento                                                                 |
|-------------|------------------|------------------------------------------------------------------------------|
| Karate      | (a)              | Suite full es barata (HTTP, sin bootstrap pesado). Vale la cobertura completa. Aplica igual con `execution_target: mock` (el mock levantado es la URL accesible). |
| Playwright  | (a) si la URL del SUT es accesible (incluye front local contra mock); (c) solo si no hay front alguno donde ejecutar | El costo de levantar browser es razonable cuando hay app viva o front local contra mock. Sin front, no tiene sentido ejecutar. |
| K6          | (b) o (c); con `execution_target: mock` siempre (b) | La suite completa (Carga + Estrés) puede tardar minutos y consumir recursos del SUT. Contra mock, SOLO smoke 1:1 (métricas de carga contra mock son inválidas). |
| Appium      | (a)              | El smoke valida que el emulador/dispositivo y Appium server estén OK; la suite completa es corta y crítica para validar locators. |
| serenity-wdio | (a) si `--mode=web` o `--mode=api` con SUT accesible; (c) si modo `movil` sin device/emulador disponible | El bootstrap de WebdriverIO + Serenity es rápido para web/api; mobile requiere device o emulador activo. Sin device, (c) evita un fallo de ambiente. |

**Regla con mock** (`[[calidad-sut-readiness-gate]]`): la ausencia de ambiente real NO empuja el default a (c). Si el gate resolvió `execution_target: mock` y el mock está levantado, la sugerencia default es (a) — o (b) en K6 — contra el mock. Sugerir (c) de entrada y luego redirigir a mocks es el anti-patrón detectado en pruebas.

## Reglas duras

1. **NUNCA proceder a ejecución sin respuesta explícita del usuario.** Si no hay respuesta en la sesión, el agente NO ejecuta — emite el prompt y espera.
2. **NUNCA asumir la respuesta** aunque el modo inicial sea `full`. El modo inicial autoriza ejecutar; este prompt elige el alcance operativo.
3. La respuesta del usuario queda registrada en `.evidence/session-config.json` como:
   ```json
   {
     "execution_decision": "a|b|c|d",
     "execution_decision_label": "full_suite | smoke_only | scaffold_only | cancel",
     "execution_decision_timestamp": "<ISO-8601>",
     "execution_decision_source": "user_explicit"
   }
   ```
4. Si la respuesta es **(d) Cancelar**, el agente detiene el `[[calidad-post-generation-protocol]]` en el paso de ejecución, emite delivery gate con `status: cancelled_by_user` y conserva los archivos generados sin ejecutar nada.
5. Si la respuesta es **(c) scaffold-only**, omitir smoke gate y suite completa; documentar en `audit-log` que la ejecución se deja al usuario.
6. Si la respuesta es **(b) smoke 1:1**, ejecutar SOLO el smoke gate 1:1 del stack — UN escenario (ej. K6 `--vus 1 --iterations 1`, Karate `--tags @smoke-gate`, Playwright `--grep @smoke-gate`, Appium `-Dcucumber.filter.tags=@smoke-gate`, serenity-wdio `node ./scripts/run.mjs --tags=@smoke`). **En brownfield el filtro sale de la taxonomía del proyecto, no de estos ejemplos** (`[[calidad-smoke-gate-policy]]`). NO ejecutar el resto.
7. Si la respuesta es **(a) full**, ejecutar smoke gate primero; solo si pasa, ejecutar la suite completa.

## Mapeo a los pasos del post-generation-protocol

Este prompt se inserta entre el paso 1 (Coherence checks) y el paso 2 (Ejecutar tests según modo) de `[[calidad-post-generation-protocol]]`. Visualmente:

```
1. Coherence checks
2. >>> Emitir post-generation-execution-prompt y esperar respuesta <<<
3. Ejecutar según respuesta (a|b|c|d) y según modo declarado
4. Re-run N=3 sobre fallos (solo si (a) o (b))
5. Auto-corrección con guardrails (solo si (a) o (b))
6. Persistir evidencia
7. Delivery gate
```

## Cross-links

`[[calidad-pre-generation-protocol]]`, `[[calidad-post-generation-protocol]]`, `[[calidad-delivery-gate-contract]]`, `[[calidad-smoke-gate-policy]]`, `[[calidad-test-evidence-and-traceability]]`.
