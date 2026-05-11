---
id: backend-skill-java-webflux-api-design
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: java-webflux
---

# Diseño de APIs — Java WebFlux (Reactivo)

## Propósito

Definir los estándares REST de Pragma para microservicios reactivos: RouterFunction + HandlerFunction, manejo de errores con RFC 7807 reactivo, estrategias de versionamiento, documentación con SpringDoc/OpenAPI para WebFlux, y estándares AsyncAPI para eventos.

---

## 1. Estándares REST

### Naming de Recursos

```
✓ CORRECTO                     ✗ INCORRECTO
/customers                    /getCustomers
/customers/{id}               /customer/{id}
/customers/{id}/orders        /customers/{id}/getOrders
```

### Métodos HTTP

| Método | Uso | Idempotente | Body |
|--------|-----|-------------|------|
| GET | Obtener recurso(s) | Sí | No |
| POST | Crear recurso | No | Sí |
| PUT | Reemplazar recurso | Sí | Sí |
| PATCH | Actualización parcial | No | Sí |
| DELETE | Eliminar recurso | Sí | No |

### Códigos de Estado

```
2xx - Éxito
├── 200 OK
├── 201 Created (recurso creado)
├── 204 No Content (DELETE exitoso)

4xx - Error del Cliente
├── 400 Bad Request
├── 401 Unauthorized
├── 403 Forbidden
├── 404 Not Found
├── 409 Conflict
├── 429 Too Many Requests

5xx - Error del Servidor
├── 500 Internal Server Error
├── 503 Service Unavailable
```

---

## 2. RouterFunction + HandlerFunction (Obligatorio)

En WebFlux **NO** se usa `@RestController`. Se usa el patrón funcional Router + Handler.

### DTOs como Java Records

```java
public record CreateCustomerRequest(
    @NotBlank(message = "Nombre es requerido")
    @Size(max = 100) String name,

    @NotBlank(message = "Email es requerido")
    @Email(message = "Formato de email inválido") String email,

    @Pattern(regexp = "^\\+?[1-9]\\d{1,14}$", message = "Formato de teléfono inválido")
    String phone
) {}

public record CustomerResponse(
    String id, String name, String email, String status, Instant createdAt
) {}
```

### Router — Definición de Rutas

```java
@Configuration
@RequiredArgsConstructor
public class CustomerRouter {
    private final CustomerHandler handler;

    @Bean
    public RouterFunction<ServerResponse> customerRoutes() {
        return RouterFunctions.route()
            .path("/api/v1/customers", builder -> builder
                .GET("", handler::findAll)
                .GET("/{id}", handler::findById)
                .POST("", handler::create)
                .PUT("/{id}", handler::update)
                .DELETE("/{id}", handler::delete)
            )
            .build();
    }
}
```

### Handler — Lógica de Request/Response

```java
@Component
@RequiredArgsConstructor
public class CustomerHandler {
    private final CreateCustomerUseCase createCustomerUseCase;
    private final GetCustomerUseCase getCustomerUseCase;
    private final DeleteCustomerUseCase deleteCustomerUseCase;
    private final CustomerRestMapper mapper;
    private final Validator validator;

    public Mono<ServerResponse> findAll(ServerRequest request) {
        int page = Integer.parseInt(request.queryParam("page").orElse("0"));
        int size = Integer.parseInt(request.queryParam("size").orElse("20"));

        return getCustomerUseCase.findAll(page, size)
            .map(mapper::toResponse)
            .collectList()
            .flatMap(list -> ServerResponse.ok().bodyValue(list));
    }

    public Mono<ServerResponse> findById(ServerRequest request) {
        String id = request.pathVariable("id");
        return getCustomerUseCase.execute(id)
            .map(mapper::toResponse)
            .flatMap(response -> ServerResponse.ok().bodyValue(response))
            .switchIfEmpty(ServerResponse.notFound().build());
    }

    public Mono<ServerResponse> create(ServerRequest request) {
        return request.bodyToMono(CreateCustomerRequest.class)
            .flatMap(this::validate)
            .map(mapper::toModel)
            .flatMap(createCustomerUseCase::execute)
            .map(mapper::toResponse)
            .flatMap(response -> {
                URI location = URI.create("/api/v1/customers/" + response.id());
                return ServerResponse.created(location).bodyValue(response);
            });
    }

    public Mono<ServerResponse> delete(ServerRequest request) {
        String id = request.pathVariable("id");
        return deleteCustomerUseCase.execute(id)
            .then(ServerResponse.noContent().build());
    }

    private <T> Mono<T> validate(T body) {
        Set<ConstraintViolation<T>> violations = validator.validate(body);
        if (!violations.isEmpty()) {
            return Mono.error(new ValidationException(violations));
        }
        return Mono.just(body);
    }
}
```

### Respuesta Paginada

```java
public record PagedResponse<T>(
    List<T> data,
    PaginationInfo pagination
) {
    public record PaginationInfo(int page, int pageSize, long totalItems, int totalPages) {}

    public static <T> PagedResponse<T> of(List<T> data, int page, int size, long total) {
        return new PagedResponse<>(data,
            new PaginationInfo(page, size, total, (int) Math.ceil((double) total / size)));
    }
}
```

---

## 3. Manejo de Errores con RFC 7807 (Reactivo)

### Estructura del Error

```json
{
  "type": "https://api.pragma.com/errors/validation-error",
  "title": "Error de Validación",
  "status": 400,
  "detail": "La solicitud contiene campos inválidos",
  "instance": "/api/v1/customers",
  "traceId": "abc-123-def",
  "timestamp": "2024-01-15T10:30:00Z",
  "errors": [
    { "field": "email", "message": "Formato de email inválido" }
  ]
}
```

### Global Error Handler Reactivo

En WebFlux se usa `AbstractErrorWebExceptionHandler` en lugar de `@RestControllerAdvice`:

```java
@Component
@Order(-2)
public class GlobalErrorWebExceptionHandler extends AbstractErrorWebExceptionHandler {

    public GlobalErrorWebExceptionHandler(
            ErrorAttributes errorAttributes,
            WebProperties.Resources resources,
            ApplicationContext applicationContext,
            ServerCodecConfigurer configurer) {
        super(errorAttributes, resources, applicationContext);
        this.setMessageWriters(configurer.getWriters());
    }

    @Override
    protected RouterFunction<ServerResponse> getRoutingFunction(ErrorAttributes errorAttributes) {
        return RouterFunctions.route(RequestPredicates.all(), this::renderErrorResponse);
    }

    private Mono<ServerResponse> renderErrorResponse(ServerRequest request) {
        Throwable error = getError(request);

        if (error instanceof ValidationException ve) {
            return buildProblemResponse(HttpStatus.BAD_REQUEST,
                "validation-error", "Error de Validación",
                "La solicitud contiene campos inválidos",
                request.path(), Map.of("errors", ve.getErrors()));
        }

        if (error instanceof ResourceNotFoundException) {
            return buildProblemResponse(HttpStatus.NOT_FOUND,
                "resource-not-found", "Recurso No Encontrado",
                error.getMessage(), request.path(), null);
        }

        if (error instanceof ConflictException) {
            return buildProblemResponse(HttpStatus.CONFLICT,
                "conflict", "Conflicto de Recurso",
                error.getMessage(), request.path(), null);
        }

        log.error("Error inesperado", error);
        return buildProblemResponse(HttpStatus.INTERNAL_SERVER_ERROR,
            "internal-error", "Error Interno",
            "Ocurrió un error inesperado", request.path(), null);
    }

    private Mono<ServerResponse> buildProblemResponse(
            HttpStatus status, String errorCode, String title,
            String detail, String instance, Map<String, Object> extras) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("type", "https://api.pragma.com/errors/" + errorCode);
        body.put("title", title);
        body.put("status", status.value());
        body.put("detail", detail);
        body.put("instance", instance);
        body.put("timestamp", Instant.now().toString());
        if (extras != null) body.putAll(extras);

        return ServerResponse.status(status)
            .contentType(MediaType.APPLICATION_PROBLEM_JSON)
            .bodyValue(body);
    }
}
```

---

## 4. Estrategias de Versionamiento

### Versionamiento por Path (Recomendado para WebFlux)

```java
@Configuration
public class ApiRouterConfig {

    @Bean
    public RouterFunction<ServerResponse> apiV1Routes(CustomerHandlerV1 handlerV1) {
        return RouterFunctions.route()
            .path("/api/v1/customers", builder -> builder
                .GET("/{id}", handlerV1::findById)
                .POST("", handlerV1::create)
            )
            .build();
    }

    @Bean
    public RouterFunction<ServerResponse> apiV2Routes(CustomerHandlerV2 handlerV2) {
        return RouterFunctions.route()
            .path("/api/v2/customers", builder -> builder
                .GET("/{id}", handlerV2::findById)
                .POST("", handlerV2::create)
            )
            .build();
    }
}
```

### Versionamiento por Header

```java
@Configuration
public class VersionedRouterConfig {

    @Bean
    public RouterFunction<ServerResponse> versionedRoutes(
            CustomerHandlerV1 v1, CustomerHandlerV2 v2) {
        return RouterFunctions.route()
            .path("/api/customers", builder -> builder
                .POST("", request -> {
                    String version = request.headers().firstHeader("X-API-Version");
                    if ("2.0".equals(version)) {
                        return v2.create(request);
                    }
                    return v1.create(request);
                })
            )
            .build();
    }
}
```

---

## 5. Documentación con SpringDoc/OpenAPI para WebFlux

### Dependencia

```groovy
implementation 'org.springdoc:springdoc-openapi-starter-webflux-ui:2.7.0'
```

### Configuración

```yaml
springdoc:
  api-docs:
    path: /api-docs
  swagger-ui:
    path: /swagger-ui.html
    operationsSorter: method
```

### Documentación de RouterFunction

```java
@Configuration
public class CustomerRouter {

    @Bean
    @RouterOperations({
        @RouterOperation(
            path = "/api/v1/customers/{id}",
            method = RequestMethod.GET,
            operation = @Operation(
                operationId = "getCustomerById",
                summary = "Obtener cliente por ID",
                responses = {
                    @ApiResponse(responseCode = "200", description = "Cliente encontrado"),
                    @ApiResponse(responseCode = "404", description = "Cliente no encontrado")
                }
            )
        ),
        @RouterOperation(
            path = "/api/v1/customers",
            method = RequestMethod.POST,
            operation = @Operation(
                operationId = "createCustomer",
                summary = "Crear cliente",
                requestBody = @RequestBody(
                    content = @Content(schema = @Schema(implementation = CreateCustomerRequest.class))
                ),
                responses = {
                    @ApiResponse(responseCode = "201", description = "Cliente creado"),
                    @ApiResponse(responseCode = "400", description = "Datos inválidos")
                }
            )
        )
    })
    public RouterFunction<ServerResponse> customerRoutes(CustomerHandler handler) {
        return RouterFunctions.route()
            .GET("/api/v1/customers/{id}", handler::findById)
            .POST("/api/v1/customers", handler::create)
            .build();
    }
}
```

---

## 6. Estándares AsyncAPI para Eventos

### Estructura de Evento de Dominio

```java
@Data @Builder
public class DomainEvent {
    private String eventId;
    private String eventType;
    private String aggregateId;
    private String aggregateType;
    private int version;
    private Instant timestamp;
    private Map<String, Object> payload;
    private Map<String, String> metadata;
}
```

### Convenciones de Naming para Eventos

| Patrón | Ejemplo |
|--------|---------|
| `{Aggregate}{Action}` | `OrderCreated`, `PaymentProcessed` |
| Source | `com.pragma.{service-name}` |
| Detail-type | Nombre del evento en PascalCase |

---

## 7. Streaming de Datos (Server-Sent Events)

WebFlux permite streaming nativo con `Flux`:

```java
@Configuration
public class StreamRouter {

    @Bean
    public RouterFunction<ServerResponse> streamRoutes(StreamHandler handler) {
        return RouterFunctions.route()
            .GET("/api/v1/events/stream", handler::streamEvents)
            .build();
    }
}

@Component
@RequiredArgsConstructor
public class StreamHandler {
    private final IEventStreamGateway eventStreamGateway;

    public Mono<ServerResponse> streamEvents(ServerRequest request) {
        Flux<ServerSentEvent<DomainEvent>> eventStream = eventStreamGateway.subscribe()
            .map(event -> ServerSentEvent.<DomainEvent>builder()
                .id(event.getEventId())
                .event(event.getEventType())
                .data(event)
                .build());

        return ServerResponse.ok()
            .contentType(MediaType.TEXT_EVENT_STREAM)
            .body(eventStream, new ParameterizedTypeReference<ServerSentEvent<DomainEvent>>() {});
    }
}
```

---

## Reglas Importantes

- **NO** usar `@RestController` — solo `RouterFunction` + `HandlerFunction`.
- **NO** usar `@RestControllerAdvice` — solo `AbstractErrorWebExceptionHandler`.
- Usar sustantivos plurales para recursos.
- URLs en minúsculas con guiones.
- Versionar APIs en la URL (path) o header.
- Siempre usar Content-Type `application/problem+json` para errores.
- Incluir `traceId` para correlación de logs.
- No exponer detalles internos ni stack traces en producción.
- Documentar todas las APIs con SpringDoc para WebFlux.
- Incluir headers de correlación (`X-Request-ID`).
- Implementar paginación para colecciones.
- Usar `ServerResponse` para construir respuestas (NO `ResponseEntity`).
