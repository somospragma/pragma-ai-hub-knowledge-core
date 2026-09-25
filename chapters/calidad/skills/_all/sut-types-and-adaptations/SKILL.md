---
id: calidad-sut-types-and-adaptations
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Catálogo de tipos de sistema bajo prueba (SUT) y cómo adaptar los frameworks del chapter a cada uno (REST, GraphQL, gRPC, serverless, event-driven, batch/streaming, ML, mobile native/híbrido, SPA, monolito web, legacy SOAP)."
tags: [sut, system-under-test, microservice, graphql, grpc, serverless, event-driven, ml, mobile, web, legacy]
---

# SUT Types and Adaptations — Catálogo y Adaptación de Frameworks por Tipo de Sistema Bajo Prueba

## Cuándo aplicar

Aplica este skill **antes de elegir el framework de testing** para cualquier entregable del chapter. La clasificación del SUT determina las herramientas, los patrones y las restricciones operativas. El chapter cubre **aplicaciones web, aplicaciones mobile y sus integraciones backend** (APIs REST/GraphQL/gRPC, eventos, pipelines de datos que alimentan web/mobile, servicios de inferencia ML consumidos por web/mobile, integraciones legacy SOAP). Por convención tiende a defaultear a Karate + Playwright + k6 + Appium porque la mayoría de los clientes históricos entregan REST + web + mobile + perf — pero los clientes reales también entregan GraphQL, gRPC, funciones serverless, sistemas event-driven, pipelines de datos batch/streaming y aplicaciones legacy SOAP/EJB (común en bancos LATAM en migración). **Asumir REST como default cuando el SUT es de otro tipo es un antipatrón** y degrada la calidad del entregable.

SUTs fuera de este alcance (desktop nativo, embedded, IoT, hardware-in-the-loop) están fuera del scope del Chapter Calidad — escalar para evaluación caso a caso.

Activa este skill antes de `[[calidad-karate-greenfield]]`, `[[calidad-playwright-greenfield]]`, `[[calidad-k6-greenfield]]`, `[[serenity-wdio-greenfield]]` o cualquier otro generador específico de framework, y combínalo con `[[calidad-chapter-perspective]]` y `[[calidad-context-determined-defaults]]`.

## Instrucción

1. **Identificar el tipo de SUT dentro del alcance** — Revisa la documentación entregada (OpenAPI, proto, AsyncAPI, código fuente, arquitectura de referencia). Si no es claro, pregunta al PO/arquitecto del cliente. No defaultear a REST por inercia. Si el SUT está fuera del alcance del chapter (desktop, embedded, IoT), escalar.
2. **Revisar la reference correspondiente** — Cada tipo de SUT dentro del alcance tiene un documento en `references/` con patrones, antipatrones y frameworks recomendados.
3. **Elegir framework primario y complementarios** — Usa la matriz de la sección siguiente. El primario cubre el flujo principal; los complementarios cubren perf, contract, seguridad y otros ángulos.
4. **Mapear los patrones específicos del SUT** — Cada SUT tiene patrones propios (idempotencia REST, N+1 GraphQL, streaming RPC, cold-start serverless, exactly-once en event-driven, drift en ML, etc.). Estos patrones cambian las assertions, no solo las herramientas.
5. **Activar skills cross-cutting según aplique** — `[[calidad-security-testing]]`, `[[calidad-business-driven-prioritization]]`, `[[calidad-test-evidence-and-traceability]]` aplican independiente del SUT; los thresholds ([[calidad-k6-greenfield]] (consultar `references/thresholds-three-tiers.md` en su subfolder)) y la fórmula de cobertura ([[calidad-karate-greenfield]] (consultar `references/negative-coverage-formula.md` en su subfolder)) se interpretan según el SUT.

## Matriz SUT → Framework principal → Complementarios

| SUT | Framework primario | Complementarios |
|---|---|---|
| REST microservice (backend de web/mobile) | Karate | k6 (perf), Pact (contract) |
| GraphQL API | Karate o postman-newman | k6, schema diff |
| gRPC service (backend de mobile/web vía proxy) | ghz + grpcurl + Karate (vía grpc-gateway) | Buf for proto, k6 xk6-grpc |
| Serverless function (AWS Lambda / Cloud Functions / Azure Functions) | Karate (HTTP), localstack/SAM Local (integration), k6 (cold-start) | - |
| Event-driven (Kafka, SNS/SQS, RabbitMQ) — backend de apps | Pact Messaging / AsyncAPI | k6 con producer plugins, Confluent Schema Registry validation |
| Batch pipeline (Spark, Airflow) — alimenta data a web/mobile | Great Expectations + dbt tests | Pytest fixtures |
| Streaming pipeline (Flink, Kinesis) — feed real-time a web/mobile | Flink Test Harness + Schema Registry | Custom integration tests |
| ML inference service consumido por web/mobile | Karate (HTTP), Deepchecks (modelo), Locust/k6 (perf) | Adversarial (Foolbox/ART), drift (Evidently AI) |
| Mobile native (iOS / Android) | Appium Screenplay | serenity-wdio (modo `movil`, Appium/WebdriverIO), Detox (RN), Espresso, XCUITest |
| Mobile hybrid (Cordova/Ionic, Capacitor) | Appium + Playwright (webview) | serenity-wdio (modo `web_movil`, WebView via WebdriverIO), Detox |
| SPA web (React, Angular, Vue) | Playwright | serenity-wdio (modo `web`, Screenplay puro), Karate (backend), k6 |
| Monolito web server-rendered | Playwright | serenity-wdio (modo `web`), Karate (form/POST), k6 |
| Legacy SOAP/EJB (común en bancos LATAM en migración) | Karate (SOAP envelopes) | SoapUI legacy |

## Restricciones

- **NO asumir REST como default**. Si el SUT es GraphQL, gRPC, event-driven, batch, streaming, ML o legacy SOAP, el flujo de generación cambia desde la elección de framework.
- **NO mapear todo el chapter a Karate + Playwright + k6 + Appium** cuando el SUT es de otro tipo. Cada tipo tiene una pila reconocida; respétala aun si implica salir de los frameworks "estrella". serenity-wdio es complementario válido para SUTs web, mobile native y mobile híbrido — no para backends especializados (gRPC, Kafka, Spark, ML).
- Cuando un complementario no aplica (p. ej. k6 sobre un batch pipeline), márcalo explícitamente como "no aplica" con la razón — no lo omitas en silencio.
- Si el SUT mezcla tipos (p. ej. SPA web + gRPC backend + Kafka events), entrega una estrategia compuesta documentando cada ángulo por separado.
- **SUTs fuera del alcance del Chapter** (desktop nativo, embedded, IoT, hardware-in-the-loop) no se cubren por defecto: escalar para evaluación caso a caso antes de comprometer entregable.
- Encadena con `[[calidad-context-determined-defaults]]` para fijar tiers y prioridades; la elección de SUT NO determina el tier — el tier viene del contexto (datos, tráfico, impacto, regulación).

## Cross-links

- `references/rest-microservice.md`
- `references/graphql-api.md`
- `references/grpc-service.md`
- `references/serverless-functions.md`
- `references/event-driven-messaging.md`
- `references/data-pipeline-batch-streaming.md`
- `references/ml-inference-service.md`
- `references/legacy-soap-ejb.md`
- `[[calidad-chapter-perspective]]`
- `[[calidad-business-driven-prioritization]]`
- `[[calidad-context-determined-defaults]]`
- `[[calidad-security-testing]]`
- [[calidad-k6-greenfield]] (consultar `references/thresholds-three-tiers.md` en su subfolder)
- [[calidad-karate-greenfield]] (consultar `references/negative-coverage-formula.md` en su subfolder)
