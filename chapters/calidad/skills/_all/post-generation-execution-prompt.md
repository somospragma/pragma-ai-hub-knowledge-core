# Post-Generation Execution Prompt — Confirmación universal antes de smoke gate

## Propósito

Inmediatamente después de emitir el último archivo del scaffold y **antes** de ejecutar el smoke gate del `[[calidad-post-generation-protocol]]`, el agente DEBE preguntar al usuario cómo procede la ejecución. Este prompt es universal: aplica a Karate, Playwright, K6 y Appium, en greenfield y brownfield, en los 5 IDEs soportados.

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
| Karate      | (a)              | Suite full es barata (HTTP, sin bootstrap pesado). Vale la cobertura completa. |
| Playwright  | (a) si la URL del SUT es accesible; (c) si scaffold-only o sin BASE_URL | El costo de levantar browser es razonable cuando hay app viva. Sin URL, no tiene sentido ejecutar. |
| K6          | (b) o (c)        | La suite completa (Carga + Estrés) puede tardar minutos y consumir recursos del SUT. El smoke 1:1 suele ser suficiente como gate inicial; el resto se ejecuta a demanda. |
| Appium      | (a)              | El smoke valida que el emulador/dispositivo y Appium server estén OK; la suite completa es corta y crítica para validar locators. |

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
6. Si la respuesta es **(b) smoke 1:1**, ejecutar SOLO el smoke gate del stack (ej. K6 `--vus 1 --iterations 1`, Karate `@smoke`, Playwright `--grep @smoke`, Appium `LoginRunner @smoke`). NO ejecutar el resto.
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
