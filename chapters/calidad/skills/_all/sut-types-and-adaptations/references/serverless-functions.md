# Serverless Functions — Patrones y Adaptación

## Patrones canónicos

- **Cold-start**: la primera invocación tras inactividad o tras un deploy paga el costo de inicialización (carga del runtime, conexiones, layers). Validar P95/P99 con cold-start aislado vs warm. Reportar ambos.
- **Idempotency keys**: las funciones suelen ser invocadas más de una vez (retry de SQS, replay de EventBridge). Usar `Idempotency-Key` con persistencia (DynamoDB, Redis) y validar que la segunda invocación no duplique side-effects.
- **Concurrency limits**: reserved concurrency (AWS), max instances (GCP), max instances (Azure). Validar comportamiento bajo throttling (`429`/`TooManyRequestsException`).
- **Timeout corto**: 15 min máximo en Lambda, 9 min en Cloud Functions Gen 2, 10 min en Azure default. Funciones largas requieren orquestación (Step Functions, Durable Functions).
- **Stateless**: no asumir estado en `/tmp` entre invocaciones (puede o no persistir).
- **Permissions**: cada función con su IAM/role de menor privilegio. Validar que la función rechaza operaciones fuera de su scope.

## Frameworks primarios

- **Karate** sobre el endpoint HTTP (API Gateway, Function URL, HTTP-triggered Cloud/Azure Function) — flujos funcionales como cualquier REST.
- **localstack** / **SAM Local** / **Azure Functions Core Tools** / **Firebase Emulator** para integration tests locales sin desplegar.
- **k6** para cold-start measurement: scenarios con `vus: 1, iterations: 1` espaciados, y scenarios con ramp-up gradual.

## Complementarios

- **AWS SAM Accelerate** / **Serverless Framework** con plugin `serverless-offline` para desarrollo local fiel.
- **Lumigo / Datadog Serverless / X-Ray** para tracing distribuido y aislamiento del cold-start vs runtime.
- **Powertools (AWS Lambda Powertools, Azure Functions Worker)** para idempotency, structured logging y métricas.

## Cold-start measurement con k6

```javascript
export const options = {
  scenarios: {
    cold: { executor: 'per-vu-iterations', vus: 1, iterations: 5, maxDuration: '10m', startTime: '0s' },
    warm: { executor: 'constant-vus', vus: 5, duration: '2m', startTime: '11m' },
  },
  thresholds: {
    'http_req_duration{scenario:cold}': ['p(95)<3000'],
    'http_req_duration{scenario:warm}': ['p(95)<300'],
  },
};
```

Entre cada iteración del scenario `cold`, esperar a que el container expire (5-15 min según provider). Para acelerar: forzar nuevo deploy o cambiar variable de entorno.

## Antipatrones

- Medir perf solo en warm — reporta latencias optimistas que no representan tráfico real con burst.
- Tests que dependen del filesystem local en `/tmp` (puede reciclarse entre invocaciones).
- No probar bajo concurrency limit — bajo carga, el cliente recibe `429` sin recovery.
- Asumir que el environment local (SAM Local) reproduce 100% el provider — diferencias en IAM, networking y cold-start son reales. Validar en staging.
