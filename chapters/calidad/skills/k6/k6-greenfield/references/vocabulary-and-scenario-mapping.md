# Vocabulario de negocio y mapping de escenarios K6

Esta referencia define cómo traducir el vocabulario de negocio que el usuario usa en `user_story` o `firma` al vocabulario técnico de k6, y cuándo cada escenario es obligatorio vs opt-in.

## Tabla canónica

| Negocio        | k6 docs | Default                                                                              |
|----------------|---------|--------------------------------------------------------------------------------------|
| Línea Base     | Smoke   | Obligatorio                                                                          |
| Carga          | Load    | Obligatorio                                                                          |
| Estrés         | Stress  | Obligatorio                                                                          |
| (opt-in)       | Spike   | Solo si `user_story` lo solicita o `risk_map` >= HIGH lo amerita                     |
| (opt-in)       | Soak    | Solo si `user_story` lo solicita o SLA de larga duración lo exige                    |

## Regla de nomenclatura

Si `user_story` o `firma` usan vocabulario de negocio (Línea Base / Carga / Estrés), entonces los `filenames`, los `reports`, el `delivery_gate` y las carpetas del proyecto DEBEN usar ese vocabulario:

```
tests/
  linea-base/main.js
  carga/main.js
  estres/main.js
```

Si el usuario no usa vocabulario de negocio (o pide explícitamente nomenclatura k6 docs), usar la terminología de k6 docs:

```
tests/
  smoke/main.js
  load/main.js
  stress/main.js
```

La decisión se toma una sola vez al inicio del workflow y se aplica a TODOS los artefactos (scripts, carpetas, scripts npm en `package.json`, scripts orquestadores `run-all.sh`, secciones del README y campos del `delivery_gate`).

## Cambio fuerte respecto a la versión anterior

**Spike y Soak dejan de ser obligatorios.** Antes los 5 escenarios (smoke/load/stress/spike/soak) eran obligatorios por defecto. Ahora:

- Obligatorios siempre: Línea Base, Carga, Estrés (3 escenarios).
- Opt-in con justificación documentada: Spike, Soak.

Razones para activar opt-in:

- `user_story` o `firma` solicitan explícitamente picos súbitos o estabilidad de larga duración.
- `risk_map` clasifica el endpoint o el flujo como `HIGH` o superior y el patrón de tráfico esperado incluye picos.
- SLA del servicio incluye disponibilidad sostenida (24h+) o tolerancia a ráfagas estacionales.

Cuando se active Spike o Soak, registrar la razón en `.evidence/scenarios-opt-in.md` con la cita textual del `user_story`, `firma` o `risk_map` que lo amerita.

## Snippet de mapping en codigo

Cuando se genere el proyecto, incluir en `tests/config.js` o `tests/utils.js` el mapping canónico para que los scripts orquestadores y los reportes resuelvan el nombre indistintamente:

```javascript
const SCENARIO_LABELS = { 'linea-base': 'smoke', 'carga': 'load', 'estres': 'stress' };
```

Uso típico en `run-all.sh` y en `handleSummary()`: resolver el label de negocio a partir del nombre del script para que los reportes mantengan la terminología del usuario.

## Cross-links

- `[[calidad-k6-greenfield]]`
- ``five-script-types.md``
- ``thresholds-three-tiers.md``
- `[[calidad-mandatory-inputs-protocol]]`
- `[[calidad-delivery-gate-contract]]`
