# Re-Run Protocol for Determinism

Protocolo estándar del chapter para decidir si un fallo es determinista o intermitente. Sin este protocolo, cualquier clasificación de flakiness es opinión y no análisis.

## Protocolo

```
1. Test falla en run 1. Capturar evidencia (test_id, error, stack, screenshot/trace, env context).
2. Re-ejecutar el MISMO test, en el MISMO entorno, con los MISMOS datos N veces (default N=3).
   - "Mismo entorno" significa: misma URL del SUT, mismo commit del SUT, mismo runner,
     mismo browser/device, misma versión del framework.
   - "Mismos datos" significa: si el test usa fixtures, reusar el fixture exacto
     (sin regenerar IDs aleatorios entre runs).
3. Comparar resultados de los N re-runs:
   - 3/3 fail con el MISMO error (mensaje y stack idénticos)  → deterministic-fail (high confidence)
   - 3/3 fail con errores DISTINTOS                            → flaky_high_variance (race condition probable)
   - 1/3 o 2/3 fail                                            → flaky
   - 0/3 fail (todos pass)                                     → flaky (transient en run 1)
   - 3/3 pass                                                  → ignorar (transient, sin acción)
4. Documentar el resultado del protocolo en la evidencia del run inicial
   (campo `triage.rerun_outcome` en el reporte). Sin esta documentación
   el triage no es válido.
```

## Cuándo aumentar N

| Caso | N recomendado | Justificación |
|---|---|---|
| Test normal | 3 | Baseline; balancea confianza vs costo de CI. |
| Test `@critical` (smoke de checkout, pago, auth) | 5 | Falsos negativos en críticos son inaceptables. |
| Test `@security` o `@contract` | 5 | Deben ser deterministas; mayor confianza obligatoria. |
| Test mobile en device farm (BrowserStack/Sauce) | 3 (no más, por costo) | Cada run consume cuota; usar logs profundos en lugar de más runs. |
| Test de performance (K6) | **NO re-run** | Re-correr K6 puede degradar el SUT y los workloads no son comparables run-a-run. Analizar métricas manualmente. |
| Test visual regression | 3 | El anti-aliasing puede introducir diff esporádico; 3 runs lo confirman. |

## Anti-patrones

- **Cambiar el entorno entre re-runs**: invalida el protocolo. Si el SUT recibió un deploy entre el run 1 y el re-run, descartar y reiniciar.
- **Cambiar los datos entre re-runs**: si el test genera datos aleatorios (`faker`), fijar la seed para que los N runs sean idénticos.
- **Aceptar "pasó en local"** como evidencia de no-flakiness: el ambiente local no es representativo del CI.
- **Hacer N=1 y declarar deterministic**: un solo fail no distingue determinismo de intermitencia; siempre N>=3.

## Output esperado del protocolo

El resultado se persiste en el reporte de evidencia (ver `[[calidad-test-evidence-and-traceability]]`):

```json
{
  "test_id": "checkout.spec.ts#should_complete_with_visa",
  "initial_run": "fail",
  "rerun_count": 3,
  "rerun_outcomes": ["fail", "fail", "fail"],
  "errors_identical": true,
  "classification": "deterministic",
  "confidence": "high",
  "evidence_links": ["allure/run-2026-05-28-12-30/index.html"]
}
```
