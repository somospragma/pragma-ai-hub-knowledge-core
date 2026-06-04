
# Coverage formula — K6 (prophylactic K-A)

Reemplazo del concepto generico de "coverage" para una suite K6. Como K6 no testea logica de negocio sino comportamiento de carga, la cobertura se mide por la combinacion (tipo-de-script x endpoint x metrica). Esta formula es **obligatoria** y se declara antes de generar.

## Formula

```
Los 5 scripts son OBLIGATORIOS: smoke, load, stress, spike, soak.

Por endpoint del spec:
  thresholds en http_req_duration{endpoint:X}
  thresholds en http_req_failed{endpoint:X}
  thresholds en checks{endpoint:X}

Coverage = (scripts_generados == 5) AND (todos_los_endpoints_tienen_tags)
         AND (cada_endpoint_tiene_threshold_en_las_3_metricas)
```

No es valido entregar solo `smoke-test.js` con la frase "el resto sigue el mismo patron". La suite entera (5 archivos) es la unidad minima de entrega.

## Declaracion obligatoria

Antes de generar codigo, persiste en `.evidence/coverage-declared.json`:

```json
{
  "scripts": ["smoke", "load", "stress", "spike", "soak"],
  "endpoints": [
    { "method": "POST",   "path": "/users",      "tagged": true },
    { "method": "GET",    "path": "/users/{id}", "tagged": true },
    { "method": "DELETE", "path": "/users/{id}", "tagged": true }
  ],
  "metrics_per_endpoint": ["http_req_duration", "http_req_failed", "checks"],
  "tier_declared": "Moderate"
}
```

## Verificacion (post-generation)

Comandos que el agente debe correr antes de cerrar la entrega:

```bash
# 1. Conteo de scripts (>=5 obligatorio)
test "$(ls tests/*.js | grep -E '(smoke|load|stress|spike|soak)-test\.js' | wc -l)" -ge 5

# 2. Cada script debe declarar thresholds y stages
for f in tests/{smoke,load,stress,spike,soak}-test.js; do
  grep -q "thresholds" "$f" || { echo "missing thresholds in $f"; exit 1; }
  grep -q "stages"     "$f" || { echo "missing stages in $f";     exit 1; }
done

# 3. Cada script debe declarar handleSummary
for f in tests/{smoke,load,stress,spike,soak}-test.js; do
  grep -q "handleSummary" "$f" || { echo "missing handleSummary in $f"; exit 1; }
done
```

Si cualquiera de las 3 verificaciones falla, la generacion es invalida y se debe regenerar — no se "completa parcialmente".

## Anti-pattern

- Entregar solo smoke "porque load/stress/spike/soak son repetitivos". Es una decision del consumidor, no del generador.
- Comentar `thresholds:` en uno de los 5 scripts "porque aun no hay baseline". Use el tier por default (Moderate) y declare el tier en `.evidence/tier-declared.md`.
- Generar un solo `index.js` con todos los stages cambiando segun `__ENV.SCENARIO`. Rompe la trazabilidad por archivo y la separacion de evidencias por tipo.

## Cross-links

- `[[k6-five-script-types]]` — perfil VU/duracion por script.
- `[[k6-thresholds-three-tiers]]` — tiers y derivacion.
- `[[k6-handle-summary-evidence]]` — formato de evidencia por corrida.
- `[[calidad-pre-generation-protocol]]` — donde se persiste `.evidence/coverage-declared.json`.
- `[[calidad-post-generation-protocol]]` — donde se verifica.
- `[[calidad-delivery-gate-contract]]` — bloqueo de entrega si coverage no se cumple.
