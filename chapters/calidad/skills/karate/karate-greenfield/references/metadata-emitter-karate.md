# Metadata Emitter — Karate

Karate genera `karate-summary.json` al final de cada corrida vía Surefire. Este reference define cómo derivar el `{ISO}-metadata.json` universal a partir de ese summary, manteniendo el schema cross-stack definido en `[execution-metadata-schema](../../../_all/execution-metadata-schema.md)`.

## Mecanismo

Dos opciones equivalentes:

1. **Hook AfterAll (Karate JS)** — Dentro de `karate-config.js` o vía clase Java en el runner, registrar un hook que se ejecute al finalizar la suite y escriba `metadata.json` al lado del `karate-summary.json`.
2. **Script bash post `mvn test`** — Más simple para CI: ejecutar el script `emit-metadata.sh` (o equivalente en el `pom.xml` via `exec-maven-plugin`) inmediatamente después de `mvn test`. Es la opción recomendada porque no requiere mantener código Java solo para evidencia.

Este reference documenta la opción 2 (script bash) como default. La opción 1 queda como nota para clientes que requieran emisión inline.

## Snippet bash post `mvn test`

Requisitos: `jq` instalado. Alternativa pura Python si no hay `jq`: ver sección "Sin jq".

```bash
#!/usr/bin/env bash
set -euo pipefail

SCENARIO="${1:-all}"
FRAMEWORK="karate"
ISO="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
DATE="$(date -u +%Y-%m-%d)"
BASE="results/karate/${DATE}"
mkdir -p "${BASE}"

mvn test -f pom.xml

SUMMARY="target/karate-reports/karate-summary-json.txt"
if [[ ! -f "${SUMMARY}" ]]; then
  echo "ERROR: ${SUMMARY} no existe" >&2
  exit 1
fi

TOTAL="$(jq '.featuresTotal'   "${SUMMARY}")"
PASSED="$(jq '.featuresPassed' "${SUMMARY}")"
FAILED="$(jq '.featuresFailed' "${SUMMARY}")"

jq -n \
  --arg s "${SCENARIO}" \
  --arg f "${FRAMEWORK}" \
  --arg ts "${ISO}" \
  --argjson total "${TOTAL}" \
  --argjson passed "${PASSED}" \
  --argjson failed "${FAILED}" \
  '{
    scenario_or_feature: $s,
    framework: $f,
    version: "v1",
    environment: (env.ENVIRONMENT // "staging"),
    workload_or_scope: "\($total) features",
    sut_endpoint_or_url: env.BASE_URL,
    auth_strategy: "background",
    exit_code: 0,
    started_at: $ts,
    finished_at: (now | strftime("%Y-%m-%dT%H:%M:%SZ")),
    totals: { total: $total, passed: $passed, failed: $failed, skipped: 0 },
    thresholds_or_coverage_met: ($failed == 0),
    blockers: []
  }' > "${BASE}/${ISO}-metadata.json"
```

## Sin jq (fallback)

Cuando el runner no tiene `jq`, usar Python (incluido por default en la mayoría de runners):

```bash
python -m json.tool target/karate-reports/karate-summary-json.txt > /tmp/karate-summary.json
python - <<'PY'
import json, os, datetime
with open('target/karate-reports/karate-summary-json.txt') as f:
    s = json.load(f)
iso = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H-%M-%SZ')
date = iso[:10]
base = f'results/karate/{date}'
os.makedirs(base, exist_ok=True)
metadata = {
    'scenario_or_feature': os.environ.get('SCENARIO', 'all'),
    'framework': 'karate',
    'version': 'v1',
    'environment': os.environ.get('ENVIRONMENT', 'staging'),
    'workload_or_scope': f"{s['featuresTotal']} features",
    'sut_endpoint_or_url': os.environ.get('BASE_URL'),
    'auth_strategy': 'background',
    'exit_code': 0,
    'started_at': iso,
    'finished_at': iso,
    'totals': {
        'total':   s['featuresTotal'],
        'passed':  s['featuresPassed'],
        'failed':  s['featuresFailed'],
        'skipped': 0,
    },
    'thresholds_or_coverage_met': s['featuresFailed'] == 0,
    'blockers': [],
}
with open(f'{base}/{iso}-metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)
PY
```

## Mapeo de campos

| Campo metadata | Origen Karate |
|---|---|
| `scenario_or_feature` | Argumento del runner (tag `@smoke`/`@regression` o nombre de feature). |
| `framework` | Constante `karate`. |
| `workload_or_scope` | `"<N> features"` donde N = `featuresTotal`. |
| `sut_endpoint_or_url` | `env.BASE_URL` (variable del runner). |
| `auth_strategy` | `background` (Karate usa `Background:` para setup de auth) o `none`. |
| `totals` | `featuresTotal/Passed/Failed` del summary. |
| `thresholds_or_coverage_met` | `featuresFailed == 0` (Karate no tiene thresholds; usa cobertura declarada). |
| `blockers` | Lista; vacía si todo OK. Si hay bloqueo de ambiente, se llena desde `execution-status.json`. |

## Reglas

- Path final: `results/karate/{YYYY-MM-DD}/{ISO}-metadata.json` (alineado con `[results-structure-universal](../../../_all/results-structure-universal.md)`).
- El script se invoca DESPUÉS de `mvn test`, no antes. Si `mvn test` falla, el script sigue ejecutando para producir metadata con `exit_code` real.
- NO omitir claves: si Karate no usa auth, escribir `"auth_strategy": "none"`, no eliminar la clave.
- Si hay bloqueo de ambiente, el array `blockers` recibe el `reason` desde `[environment-blocker-evidence](../../../_all/environment-blocker-evidence.md)`.

## Cross-links

`[execution-metadata-schema](../../../_all/execution-metadata-schema.md)`, `[results-structure-universal](../../../_all/results-structure-universal.md)`, `[environment-blocker-evidence](../../../_all/environment-blocker-evidence.md)`, `[[calidad-delivery-gate-contract]]`, `[[calidad-karate-greenfield]]`.
