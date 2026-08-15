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

## Cuando la instrumentación hace desaparecer el fallo

Ocurre y desconcierta: se agrega logging, un heartbeat o un wrapper para observar el fallo, y **el test pasa siempre**. El reflejo es descartarlo como ruido. Es exactamente al revés: **la instrumentación es el hallazgo**. Algo que ella introduce —un temporizador vivo, un retardo, un orden distinto de operaciones— está cambiando la condición que producía el fallo, y eso acota la causa mucho más que cualquier hipótesis.

Convertirlo en evidencia exige un A/B, no una anécdota:

1. **Una sola variable entre los brazos.** Con y sin la instrumentación; todo lo demás idéntico, incluido el orden de ejecución. Si además cambió un timeout o una capability, la corrida no dice nada.
2. **N>=3 por brazo**, con el mismo criterio de la tabla de arriba. Un cuelgue intermitente necesita repetición en los dos lados, no solo en el que falla.
3. **Publicar los números crudos**, no la conclusión:

| | Resultado | Duración |
|---|---|---|
| Con la instrumentación activa | 4/4 verdes | 65-75 s |
| Sin ella | 3/3 colgadas | 138 s (muerte por timeout) |

4. **La verificación final corre sin la instrumentación.** Un verde con el andamio puesto prueba que el andamio funciona, no que el fix funcione. Este paso es el que cierra el caso.

Aplica igual cuando el efecto es el inverso —la instrumentación *provoca* el fallo—, que suele delatar una condición de carrera que el test tenía latente.

## Cuando el ambiente se degrada a mitad del experimento

Un protocolo de re-corridas contra un ambiente compartido puede quedar contaminado en el medio: el backend empieza a devolver errores, la granja se satura, el ambiente se despliega. **Los brazos medidos después de ese punto se descartan, no se reportan.**

Verificado en campo: una serie de variantes medidas tras la degradación de un ambiente dio 0/3 en todas, un resultado que parecía concluyente y no significaba nada. Reportarlo habría instalado una conclusión falsa sobre variantes que nunca se midieron de verdad.

El reporte declara explícitamente qué quedó sin medir y por qué. "No concluyente por degradación del ambiente" es un resultado válido; presentar el dato contaminado como evidencia no lo es.

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
