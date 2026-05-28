# LLM-Driven Selector Repair

Cuando la cadena de fallback (`multi-locator-fallback-pattern.md`) se agota, en lugar de fallar el suite indefinidamente, se invoca un LLM para proponer un selector nuevo a partir del DOM real y la screenshot del estado actual. La salida del LLM **nunca** entra a `main` sin validación local; este flujo es asistente del QA, no piloto automático.

## Flujo

1. **Detectar fallo terminal del fallback.** El `ResilientLocator` lanza `Error('All locator strategies exhausted ...')`. El runner captura el error y dispara el hook de reparación si el suite no está etiquetado `@security`, `@contract` o `@regression-strict`.
2. **Capturar contexto.** El hook toma:
   - DOM snapshot del estado actual (`page.content()` en Playwright).
   - Screenshot completa (`page.screenshot({ fullPage: true })`).
   - El error con la lista completa de selectors intentados.
   - El último selector que se sabe que funcionó (último commit donde el test pasó).
3. **Invocar el prompt** `[[playwright-extract-pages-from-live-app-prompt]]` con esos cuatro inputs. El prompt está parametrizado para devolver selector siguiendo la prioridad del chapter (`getByTestId > getByRole > getByLabel`).
4. **Validar el selector propuesto** ejecutando el test contra el live app **localmente** (smoke), nunca contra CI. El test debe pasar tres veces consecutivas antes de aceptar la propuesta.
5. **Abrir PR** con el cambio del Page Object, incluyendo en la descripción: el log de healing original, la propuesta del LLM, el costo del call y la captura de las tres ejecuciones verdes. El PR pasa por code review humano obligatorio.

## Snippet de prompt completo

```text
Eres asistente de QA del Chapter Calidad de Pragma. Un selector dejó
de resolver en un Page Object Playwright. Tu tarea es proponer un
selector nuevo cumpliendo estrictamente la prioridad del chapter.

Prioridad obligatoria (de mayor a menor):
1. getByTestId(...)
2. getByRole(..., { name: ... })
3. getByLabel(...)
4. getByText(...)
5. CSS selector (último recurso, solo si los anteriores no aplican)

Contexto:
- test_id: {{test_id}}
- last_known_good_selector: {{last_good_selector}}
- error: All locator strategies exhausted: {{strategies_tried}}
- DOM snapshot (truncado a 50KB): {{dom_snippet}}
- Screenshot adjunta (base64): {{screenshot_b64}}

Instrucciones:
- Devuelve EXCLUSIVAMENTE el siguiente JSON, sin texto adicional:
  {
    "selector_strategy": "<getByTestId|getByRole|getByLabel|getByText|css>",
    "selector_args": <args literales TypeScript>,
    "confidence": <0.0-1.0>,
    "reasoning_short": "<máx 200 chars>",
    "fallback_chain_suggestion": [<lista de hasta 3 alternativas con la misma forma>]
  }
- No inventes data-testid que no exista en el DOM provisto.
- Si no hay candidato razonable, devuelve {"selector_strategy": "none", ...}.
```

## Costo y latencia

- Cada reparación invoca un call con DOM + screenshot — coste no trivial (input largo, vision). No usar en cada run; reservar para cuando el healing automático **agota** todas las estrategias.
- Latencia típica esperada: 5–15s. No bloquea el CI: el flujo se ejecuta offline o en un job manual, y se materializa como PR.
- Establecer presupuesto mensual de calls de reparación por suite y alertar al lead del chapter si se excede.

## Reglas

- **Nunca** auto-commitear la propuesta del LLM. Siempre vía PR con code review humano.
- **Nunca** invocar el flujo si el suite está marcado como `@security`, `@contract` o `@regression-strict`. Ver `over-healing-guardrails.md`.
- **Nunca** loguear el screenshot/base64 ni el DOM sensible en el log público — sanitizar inputs (tokens, PII) antes de mandar al LLM.
- La PR debe incluir cross-link al issue de tracking del cambio del SUT (si se identificó) para que `[[calidad-failure-triage-and-classification]]` pueda decidir si en realidad era un bug.
