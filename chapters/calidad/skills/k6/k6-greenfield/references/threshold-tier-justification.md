
# Threshold tier justification — K6 (enforcement K-B)

Cada proyecto K6 debe declarar **explicitamente** el tier de thresholds (Conservative / Moderate / Relaxed) y la razon, antes de generar codigo. Esta declaracion bloquea el patron anti-cheating de "aflojar thresholds hasta que smoke pase".

## Declaracion obligatoria

Persiste en `.evidence/tier-declared.md` (o `.evidence/tier-declared.json`) con:

```markdown
# Threshold tier declaration

- project: {{project_name}}
- tier: Moderate
- reason: API de negocio normal sin SLA explicito en spec ni firma. Default por defecto.
- p95: 1000ms
- p99: 2000ms
- error_rate: 0.01
- checks_pass: 0.95
- source: default (no explicit SLA)
```

Si la declaracion no existe en `.evidence/`, la generacion debe abortar.

## Tabla de derivacion

| Tier | Cuando aplica | p95 | p99 | error rate | checks pass |
|---|---|---|---|---|---|
| Conservative | Firma del cliente declara SLA estricto (<500ms p95) o sistema mission-critical: financiero (pagos, trading), salud (EHR, prescripcion), identidad/IdP, checkout en peak, gaming live, defensa. | <500ms | <1000ms | <0.001 | >0.99 |
| **Moderate (DEFAULT)** | API de negocio normal sin SLA en spec/firma. Use esto salvo razon explicita. | <1000ms | <2000ms | <0.01 | >0.95 |
| Relaxed | Servicios internos, batch, integraciones B2B donde latencia humana no aplica, herramientas internas. Requiere firma o user_story que lo justifique. | <2000ms | <5000ms | <0.05 | >0.90 |

## Anti-pattern (anti-cheating)

Aflojar el tier **despues** de ver fallar el smoke es **violacion grave** del contrato de calidad:

- Si smoke falla en Moderate y el agente cambia a Relaxed solo para que pase, esta ocultando un bug del SUT detras de un threshold permisivo. La metrica deja de ser una senal y se convierte en ruido.
- Si smoke falla, la respuesta correcta es: (a) reportar el fallo como bug y abrir issue contra el SUT, (b) calibrar con `[[calidad-calibrate-k6-thresholds]]` usando datos reales del baseline (NO ajustes arbitrarios), o (c) bajar de tier SOLO si la firma o user_story lo soporta documentalmente.

Tres reglas asociadas:

1. El tier declarado en `.evidence/tier-declared.md` es la fuente unica de verdad. Cambiar el tier requiere actualizar el archivo y agregar entry en `.evidence/tier-changelog.md` con razon y commit hash.
2. Si el smoke pasa pero load/stress fallan, NO se afloja: ese es el "punto de quiebre" que stress busca, y debe reportarse como hallazgo, no como falla del test.
3. NO esta permitido `thresholds: { http_req_duration: ['p(95)<99999'] }` ni equivalentes (thresholds inertes). Si la metrica no se va a usar, omitir el threshold y documentarlo — no neutralizarlo.

## Cross-links

- ``thresholds-three-tiers.md`` — tabla completa de tiers con snippets.
- ``five-script-types.md`` — todos los 5 scripts deben respetar el mismo tier.
- `[[calidad-test-self-correction-loop/references/anti-cheating-guardrails]]` — politica chapter-wide de no aflojar para hacer pasar.
- `[[calidad-calibrate-k6-thresholds]]` — la unica via legitima para mover thresholds despues de la primera corrida.
- `[[calidad-pre-generation-protocol]]` — donde se persiste la declaracion.
- `[[calidad-post-generation-protocol]]` — donde se verifica.
- `[[calidad-delivery-gate-contract]]` — bloqueo de entrega si falta la declaracion.
