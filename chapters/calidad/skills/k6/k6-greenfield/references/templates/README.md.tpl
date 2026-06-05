# {{project_name}}

Suite de performance testing K6 generada por el chapter calidad.

## Prerequisitos

| Herramienta              | Versión          | Obligatoriedad        | Notas                                                          |
|--------------------------|------------------|-----------------------|----------------------------------------------------------------|
| k6                       | `>= 0.50.0`      | Obligatorio           | Runtime de los scripts. Instalar desde https://k6.io/docs/      |
| jq                       | cualquier 1.x    | Recomendado, opcional | Pretty-print y extracción rápida de métricas en `results/*.json` |
| python (`json.tool`)     | `>= 3.6`         | Alternativa portable  | Reemplaza a `jq` cuando no esté disponible                      |
| node (`-e ...`)          | `>= 18`          | Alternativa portable  | Reemplazo extra cuando ni `jq` ni `python` estén disponibles    |

**Alternativas portables a `jq`** (cuando `jq` no está instalado):

```bash
# Opción A — python (suele venir preinstalado en mac/linux)
python -m json.tool results/*-summary.json

# Opción B — node
node -e 'console.log(JSON.parse(require("fs").readFileSync(0)))' < results/*-summary.json
```

## Variables de entorno

| Variable      | Obligatoriedad                                | Descripción                                                 |
|---------------|-----------------------------------------------|-------------------------------------------------------------|
| `BASE_URL`    | Obligatoria                                   | URL base del SUT                                            |
| `AUTH_TOKEN`  | Obligatoria si `auth_mode = external`         | Token Bearer emitido fuera de k6 (IdP, gateway, mTLS, etc.) |

## Quick start

Sin asumir `jq` instalado. Reemplazar `BASE_URL` por el valor real:

```bash
# 1. Verificar k6 instalado y versión >= 0.50.0
k6 version

# 2. Smoke 1:1 (validación end-to-end del scaffold, 1 VU + 1 iteración)
BASE_URL=https://api.example.com k6 run tests/smoke-test.js --vus 1 --iterations 1

# 3. Smoke completo según options.stages
BASE_URL=https://api.example.com k6 run tests/smoke-test.js

# 4. Suite completa (linea-base -> carga -> estres + opt-in)
BASE_URL=https://api.example.com bash run-all.sh

# 5. Ver resumen (sin jq) — alternativa portable
python -m json.tool results/*-summary.json | grep -E '(http_req_duration|http_req_failed|iterations)'
```

## Escenarios

Esta suite incluye 3 escenarios **obligatorios** y hasta 2 escenarios **opt-in** (activados con justificación documentada en `.evidence/scenarios-opt-in.md`):

| Negocio    | k6 docs | Default      | Archivo            |
|------------|---------|--------------|--------------------|
| Línea Base | Smoke   | Obligatorio  | `tests/smoke-test.js` |
| Carga      | Load    | Obligatorio  | `tests/load-test.js`  |
| Estrés     | Stress  | Obligatorio  | `tests/stress-test.js` |
| (opt-in)   | Spike   | Solo si aplica | `tests/spike-test.js` |
| (opt-in)   | Soak    | Solo si aplica | `tests/soak-test.js`  |

## Evidencia

Cada ejecución genera `results/<timestamp>-summary.json`. Conservar para trazabilidad y para alimentar `[[calibrate-k6-thresholds]]`.
