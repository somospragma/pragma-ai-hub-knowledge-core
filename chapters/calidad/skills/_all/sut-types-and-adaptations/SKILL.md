---
id: calidad-sut-types-and-adaptations
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Catálogo de tipos de sistema bajo prueba (SUT) y cómo adaptar los frameworks del chapter a cada uno (REST, GraphQL, gRPC, serverless, event-driven, batch/streaming, ML, mobile, SPA, desktop, IoT, legacy)."
tags: [sut, system-under-test, microservice, graphql, grpc, serverless, event-driven, ml, iot, legacy]
---

# SUT Types and Adaptations — Catálogo y Adaptación de Frameworks por Tipo de Sistema Bajo Prueba

## Cuándo aplicar

Aplica este skill **antes de elegir el framework de testing** para cualquier entregable del chapter. La clasificación del SUT determina las herramientas, los patrones y las restricciones operativas. El chapter por convención tiende a defaultear a Karate + Playwright + k6 + Appium porque la mayoría de los clientes históricos entregan REST + web + mobile + perf — pero los clientes reales también entregan GraphQL, gRPC, funciones serverless, sistemas event-driven, pipelines de datos batch/streaming, servicios de inferencia ML, aplicaciones legacy SOAP/EJB, monolitos web server-rendered, SPAs, mobile híbrido, desktop y embebidos/IoT. **Asumir REST como default cuando el SUT es de otro tipo es un antipatrón** y degrada la calidad del entregable.

Activa este skill antes de `[[karate-greenfield]]`, `[[playwright-greenfield]]`, `[[k6-greenfield]]` o cualquier otro generador específico de framework, y combínalo con `[[calidad-chapter-perspective]]` y `[[calidad-context-determined-defaults]]`.

## Instrucción

1. **Identificar el tipo de SUT** — Revisa la documentación entregada (OpenAPI, proto, AsyncAPI, código fuente, arquitectura de referencia). Si no es claro, pregunta al PO/arquitecto del cliente. No defaultear a REST por inercia.
2. **Revisar la reference correspondiente** — Cada tipo de SUT tiene un documento en `references/` con patrones, antipatrones y frameworks recomendados.
3. **Elegir framework primario y complementarios** — Usa la matriz de la sección siguiente. El primario cubre el flujo principal; los complementarios cubren perf, contract, seguridad y otros ángulos.
4. **Mapear los patrones específicos del SUT** — Cada SUT tiene patrones propios (idempotencia REST, N+1 GraphQL, streaming RPC, cold-start serverless, exactly-once en event-driven, drift en ML, etc.). Estos patrones cambian las assertions, no solo las herramientas.
5. **Activar skills cross-cutting según aplique** — `[[calidad-security-testing]]`, `[[calidad-business-driven-prioritization]]`, `[[calidad-test-evidence-and-traceability]]` aplican independiente del SUT; los thresholds (`[[k6-thresholds-three-tiers]]`) y la fórmula de cobertura (`[[karate-negative-coverage-formula]]`) se interpretan según el SUT.

## Matriz SUT → Framework principal → Complementarios

| SUT | Framework primario | Complementarios |
|---|---|---|
| REST microservice | Karate | k6 (perf), Pact (contract) |
| GraphQL API | Karate o postman-newman | k6 con browser-recorder; Apollo-tracing |
| gRPC service | ghz (perf) + grpcurl + Karate (proxy HTTP/JSON) | Buf for proto contract, k6 con xk6-grpc |
| Serverless function (AWS Lambda / Cloud Functions / Azure Functions) | Karate (HTTP API), localstack/SAM Local (integration), k6 (cold-start perf) | AWS SAM Accelerate, Serverless Framework testing |
| Event-driven (Kafka, SNS/SQS, RabbitMQ) | Pact Messaging / AsyncAPI tests | k6 con producer plugins; Confluent Schema Registry validation |
| Batch pipeline (Spark, Airflow) | Great Expectations (data quality) + dbt tests | Custom Pytest fixtures; k6 NO aplica (no es HTTP load) |
| Streaming pipeline (Flink, Kinesis Analytics) | Flink Test Harness + Schema Registry | Custom integration tests; consumer lag monitoring |
| ML inference service | Karate (HTTP API si REST), Deepchecks/Great Expectations (model behavior), Locust/k6 (perf) | Adversarial testing (Foolbox, ART), fairness (Aequitas) |
| Mobile native (iOS/Android) | Appium Screenplay | Detox (RN), Espresso (Android), XCUITest (iOS) |
| Mobile hybrid (Cordova/Ionic, Capacitor) | Appium + Playwright (webview) | Detox |
| SPA web (React, Angular, Vue) | Playwright | Karate (backend), k6 (load) |
| Monolith web (server-rendered) | Playwright | Karate (form/POST), k6 |
| Desktop (Electron, WPF, JavaFX) | Playwright (Electron), WinAppDriver (Win), TestComplete | Sikuli para visual fallback |
| Embedded / IoT (firmware, MQTT) | MQTT client tests, Pact Messaging, hardware-in-the-loop | k6 con xk6-mqtt; conformance OASIS MQTT |
| Legacy SOAP/EJB | Karate (SOAP envelopes) | SoapUI (legacy); SOAPSonar |

## Restricciones

- **NO asumir REST como default**. Si el SUT es GraphQL, gRPC, event-driven, batch, streaming, ML, desktop, IoT o legacy SOAP, el flujo de generación cambia desde la elección de framework.
- **NO mapear todo el chapter a Karate + Playwright + k6 + Appium** cuando el SUT es de otro tipo. Cada tipo tiene una pila reconocida; respétala aun si implica salir de los frameworks "estrella".
- Cuando un complementario no aplica (p. ej. k6 sobre un batch pipeline), márcalo explícitamente como "no aplica" con la razón — no lo omitas en silencio.
- Si el SUT mezcla tipos (p. ej. SPA web + gRPC backend + Kafka events), entrega una estrategia compuesta documentando cada ángulo por separado.
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
- `references/desktop-applications.md`
- `references/embedded-iot-systems.md`
- `[[calidad-chapter-perspective]]`
- `[[calidad-business-driven-prioritization]]`
- `[[calidad-context-determined-defaults]]`
- `[[calidad-security-testing]]`
- `[[k6-thresholds-three-tiers]]`
- `[[karate-negative-coverage-formula]]`
