# Smoke 1:1 Gate — Validación end-to-end del scaffold

Antes de declarar `success` en cualquier suite K6 generada en modo `full`, el agente DEBE ejecutar un smoke mínimo con exactamente **1 VU y 1 iteración** para validar que el scaffold (imports, headers, payloads, auth, base URL) funciona end-to-end. Este gate NO ejecuta carga; solo valida que el código generado puede llegar al SUT y completar al menos una iteración.

## Comando obligatorio

Según el vocabulario de escenarios elegido (ver `[[k6-vocabulary-and-scenario-mapping]]`):

```bash
# Nomenclatura de negocio (default si user_story usa "linea base"):
k6 run tests/linea-base/main.js --vus 1 --iterations 1

# Nomenclatura k6 docs (default si user_story no usa vocabulario de negocio):
k6 run tests/smoke/main.js --vus 1 --iterations 1
```

## Reglas de decisión

- **Exit 0** → continuar. El scaffold es válido. El agente puede proceder a la siguiente fase (preguntar al usuario cómo continuar con la suite completa).
- **Exit != 0** → status `partial` con `blocker: "smoke_1_1_failed"`. Escalar al usuario incluyendo `stderr` completo y los últimos 50 lines de `stdout`. NO intentar correcciones automáticas más allá de las permitidas por `[[calidad-test-self-correction-loop]]` (max 3 iteraciones, anti-cheating estricto).

## Que NO hace este gate

- NO ejecuta el escenario completo (no aplica stages, no llega a target VUs).
- NO valida thresholds de carga.
- NO sustituye la ejecución formal de Carga / Estrés / Spike / Soak (esos se ejecutan via `[[calibrate-k6-thresholds]]` bajo ventana coordinada).
- NO se ejecuta en modo `dry-run` ni `scaffold-only`.

## Persistencia

Registrar en el `delivery_gate` (campo `execution.smoke_1_1`):

- `executed: true|false|skipped`
- `exit_code: <int>`

Y persistir el output completo en `.evidence/smoke-1-1-<timestamp>.log`.

## Cross-links

- `[[k6-greenfield]]`
- `[[k6-vocabulary-and-scenario-mapping]]`
- `[[calidad-post-generation-protocol]]`
- `[[calidad-delivery-gate-contract]]`
- `[[calidad-test-self-correction-loop]]`
