# gRPC Service — Patrones y Adaptación

## Patrones canónicos

- **Proto contract**: el `.proto` es el contrato. Cambios al proto son cambios al contrato y requieren contract testing.
- **Tipos de RPC**:
  - **Unary**: request/response simple. Test como REST.
  - **Server-streaming**: cliente envía 1 request, servidor responde N messages. Validar count, orden, terminación correcta del stream.
  - **Client-streaming**: cliente envía N requests, servidor responde 1. Validar agregación correcta.
  - **Bidirectional streaming**: ambos lados envían N messages independientemente. Validar concurrencia y backpressure.
- **Deadlines**: cada RPC debe llevar deadline. Validar que el servidor respete `DEADLINE_EXCEEDED`.
- **Cancellation**: el cliente cancela el contexto; validar limpieza de recursos en el servidor.
- **Status codes**: `OK`, `INVALID_ARGUMENT`, `NOT_FOUND`, `ALREADY_EXISTS`, `PERMISSION_DENIED`, `UNAUTHENTICATED`, `RESOURCE_EXHAUSTED`, `UNAVAILABLE`. No usar HTTP codes.
- **Metadata**: equivalente a headers HTTP. Auth típicamente en `authorization: Bearer ...`.

## Framework primario

- **ghz** para perf y carga (escrito en Go, soporta unary y streaming, exporta JSON/HTML).
- **grpcurl** para exploración manual y smoke tests desde shell.
- **Karate** como proxy HTTP/JSON cuando el servicio está expuesto vía **grpc-gateway** (REST proxy generado del `.proto`). Esto permite reusar el toolkit del chapter para flows funcionales.

## Complementarios

- **Buf** (`buf breaking`, `buf lint`) para validar el `.proto` y prevenir breaking changes en CI.
- **k6 con xk6-grpc** para perf desde el toolchain k6 (mismos thresholds, tiers y reportes que el resto del chapter).
- **Wireshark / grpcdebug** para inspección de frames HTTP/2 cuando hay problemas de transporte.
- **Pact con plugin gRPC** (experimental) para contract testing consumer-driven.

## Streaming RPC — cómo testear

- **Server-streaming**: abrir el stream, consumir hasta `EOF`, validar count y schema de cada mensaje, validar deadline.
- **Client-streaming**: enviar N mensajes con `SendMsg`, cerrar con `CloseAndRecv`, validar respuesta agregada.
- **Bidirectional**: dos goroutines/threads (envío y recepción). Validar que no hay race conditions y que cierre de una dirección no impide la otra (`half-close`).

## Antipatrones

- Probar gRPC vía REST proxy solamente — pierdes cobertura de streaming, metadata binaria y deadlines.
- Ignorar `buf breaking` en CI — el proto cambia y los clientes rompen sin aviso.
- Hardcodear puertos sin TLS en tests — gRPC en prod casi siempre va sobre TLS, los tests deben replicarlo.
- Asumir que k6 default (HTTP/1.1) sirve para gRPC — requiere `xk6-grpc`.
