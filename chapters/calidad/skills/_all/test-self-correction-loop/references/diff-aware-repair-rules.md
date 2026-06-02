# Diff-Aware Repair Rules

Reglas para decidir, dado el diff entre lo esperado y lo observado, si el cambio justifica un fix automático o si debe escalar a humano por ser bug del SUT.

> Premisa: este árbol asume que `[[calidad-failure-triage-and-classification]]` ya descartó flakiness y la corrección sería sobre el test. Aun así, ciertos diffs son siempre bug.

## Tabla de decisión

| Diferencia detectada (expected vs actual) | Clasificación | Acción permitida |
|---|---|---|
| Campo nuevo opcional en response | drift tolerable | Tolerar con `ignore extra fields` (Karate `##optional`, Playwright `expect.objectContaining`, K6 `check` permisivo) |
| Campo requerido faltante | **BUG del SUT** | Reportar, NO modificar |
| Tipo de dato cambió (`string → number`, `int → float`, `array → object`) | **BUG del SUT (breaking)** | Reportar, NO modificar |
| Nuevo enum value añadido | drift tolerable | Tolerar si el test no asume set cerrado (matcher abierto) |
| Enum value eliminado que el test usa | **BUG del SUT (breaking)** | Reportar, NO modificar |
| Status code cambió `200 → 201` | caso especial | Revisar release notes; si es legítimo, ajustar test + audit log con link; si no, BUG |
| Status code cambió `200 → 4xx` | **BUG del SUT** | Reportar, NO modificar |
| Status code cambió `200 → 5xx` | **BUG del SUT (severo)** | Reportar, NO modificar; abrir incidente |
| Selector text cambió por i18n (`"Sign in" → "Iniciar sesión"`) | healing válido | Ajustar selector a regex multi-locale o `getByRole` + `name` regex |
| Selector text cambió con cambio funcional (`"Sign in" → "Continue"`) | escalar | Puede ser cambio de flujo; revisar UX/PR antes de cambiar |
| Endpoint movido (`/api/v1/x → /api/v2/x`) | **BUG (breaking change)** | Reportar; el cliente debe versionar |
| Endpoint deprecado pero responde con warning header `Deprecation` o `Sunset` | tolerable temporal | Mantener test funcionando + abrir ticket de migración con SLA |
| Cookie de auth cambió de nombre (`session → sid`) | healing válido | Auto-corregir + log de cambio en audit |
| Header de auth cambió (`Authorization → X-Auth-Token`) | caso especial | Revisar release notes; si legítimo, ajustar; si no, BUG |
| Payload validation más estricta (campo antes opcional, ahora requerido) | **BUG si rompe consumers** | Coordinar con backend; el contrato debe versionar |
| Pagination shape cambió (`results → data.items`) | **BUG (breaking)** | Reportar |
| Rate limit reducido y test ahora golpea 429 | escalar | Ajustar throttle del test puede ser válido; aflojar threshold de error_rate NO |
| Schema añade nullable a campo antes no-null | tolerable | Ajustar matcher para aceptar null si el negocio lo permite |
| Schema quita nullable (campo antes null-permitido, ahora no-null) | revisar | Verificar si el cambio rompe historia de datos existentes |
| Locator `getByLabel('Email')` no resuelve, DOM tiene `getByPlaceholder('Email')` | healing válido | Aplicar fallback multi-locator |
| Locator desaparece (elemento eliminado del DOM) | **BUG o cambio de flujo** | Escalar; no inventar locator |
| Timing: test pasa con `waitFor 10s`, falla con `5s`, métricas SUT muestran p99=7s | tolerable medido | Subir waitFor con justificación (audit log incluye p99 real) |
| Timing: test falla a 5s, p99 SUT subió de 2s a 6s | **regresión de performance** | Escalar (bug de performance del SUT) |
| Date format en response cambió (`"2025-01-01" → "01/01/2025"`) | **BUG (breaking)** | Reportar |
| Currency / locale formatting cambió en UI | revisar | Si i18n legítimo, ajustar selector; si no, bug |

## Cómo detectar cada caso desde el diff del response/error

### REST/GraphQL response diff (Karate / Playwright API / K6)

```
1. comparar estructura JSON keys(expected) vs keys(actual):
   - keys_only_in_expected = expected - actual  → campos requeridos faltantes (BUG)
   - keys_only_in_actual   = actual - expected  → drift tolerable (campo nuevo opcional)
   - keys_in_both          → comparar tipo y valor
2. para cada key compartida:
   - typeof(expected[k]) != typeof(actual[k])   → BUG (cambio de tipo)
   - expected[k] != actual[k] y tipo es enum    → revisar catálogo enum del contrato
   - expected[k] != actual[k] y tipo es valor   → revisar reglas de la tabla
3. comparar status code:
   - rangos (2xx → 4xx, 2xx → 5xx)  → BUG
   - dentro del mismo rango (200 → 201)  → revisar release notes
4. comparar headers (auth, deprecation, sunset, rate-limit)
   - Deprecation/Sunset present  → tolerable temporal + ticket migración
```

### UI locator diff (Playwright / Appium)

```
1. capturar snapshot del DOM/UI tree del estado actual fallido.
2. ejecutar fallback multi-locator (ver [[calidad-test-self-healing]]):
   - probar getByTestId → getByRole → getByLabel → getByText.
   - si ALGUNO resuelve al mismo elemento (heurística de bounding box / accessibility name) → healing válido.
3. si NINGUNO resuelve:
   - revisar si el flujo cambió (screenshot vs baseline) → escalar.
4. para text changes:
   - calcular similitud (i18n hash, traducción conocida) → ajustar selector a regex.
   - si el texto cambió semánticamente (acción distinta) → escalar.
```

### Performance diff (K6)

```
1. NUNCA aflojar thresholds para que el test pase. Regla absoluta.
2. comparar métricas observadas con baseline histórico:
   - p95/p99 subió > 20% sin cambio de carga  → regresión de performance (BUG).
   - error_rate subió > umbral baseline       → BUG.
3. el único ajuste permitido sobre el test K6 es:
   - corregir errores de scripting (typos, refactor de setup) que no tocan thresholds.
   - thresholds se recalibran solo vía [[calibrate-k6-thresholds]] con evidencia.
```

## Snippet: pseudo-código de detección automática

```ts
function decideRepair(diff: ResponseDiff, contract: Contract): RepairDecision {
  // 1. campos requeridos faltantes
  const missingRequired = contract.required.filter(k => !(k in diff.actual));
  if (missingRequired.length) return { action: 'BUG_REPORT', reason: 'missing_required_fields', fields: missingRequired };

  // 2. cambios de tipo
  for (const k of Object.keys(diff.expected)) {
    if (k in diff.actual && typeof diff.expected[k] !== typeof diff.actual[k]) {
      return { action: 'BUG_REPORT', reason: 'type_change', field: k };
    }
  }

  // 3. status code
  if (diff.expectedStatus !== diff.actualStatus) {
    if (rangeOf(diff.expectedStatus) !== rangeOf(diff.actualStatus)) {
      return { action: 'BUG_REPORT', reason: 'status_range_change' };
    }
    return { action: 'ESCALATE', reason: 'status_in_range_change' };
  }

  // 4. campos nuevos opcionales en actual → tolerable
  const extraInActual = Object.keys(diff.actual).filter(k => !(k in diff.expected));
  if (extraInActual.length) {
    return { action: 'AUTO_FIX_TOLERATE_EXTRA', fields: extraInActual };
  }

  return { action: 'NO_FIX_NEEDED' };
}
```
