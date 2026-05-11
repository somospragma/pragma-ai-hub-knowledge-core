---
id: backend-skill-java-spring-api-design
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: java-spring
---

# Diseño de APIs — Java Spring

## Propósito

Definir los estándares REST de Pragma, manejo de errores con RFC 7807, estrategias de versionamiento, documentación con SpringDoc/OpenAPI, y estándares AsyncAPI para eventos.

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

### Controller REST Estándar

```java
@RestController
@RequestMapping("/api/v1/customers")
@RequiredArgsConstructor
@Tag(name = "Customers", description = "API de gestión de clientes")
public class CustomerController {

    private final CreateCustomerUseCase createCustomerUseCase;
    private final GetCustomerUseCase getCustomerUseCase;

    @GetMapping
    @Operation(summary = "Listar clientes con paginación")
    public ResponseEntity<PagedResponse<CustomerResponse>> list(
            @RequestParam(defaultValue = "0") @Min(0) int page,
            @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size) {
        Page<Customer> customers = getCustomerUseCase.findAll(PageRequest.of(page, size));
        return ResponseEntity.ok(PagedResponse.of(customers, CustomerRestMapper::toResponse));
    }

    @GetMapping("/{id}")
    @Operation(summary = "Obtener cliente por ID")
    public ResponseEntity<CustomerResponse> getById(@PathVariable String id) {
        Customer customer = getCustomerUseCase.execute(id);
        return ResponseEntity.ok(CustomerRestMapper.toResponse(customer));
    }

    @PostMapping
    @Operation(summary = "Crear cliente")
    public ResponseEntity<CustomerResponse> create(
            @Valid @RequestBody CreateCustomerRequest request) {
        Customer created = createCustomerUseCase.execute(request.name(), request.email());
        URI location = ServletUriComponentsBuilder.fromCurrentRequest()
            .path("/{id}").buildAndExpand(created.getId()).toUri();
        return ResponseEntity.created(location).body(CustomerRestMapper.toResponse(created));
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public ResponseEntity<Void> delete(@PathVariable String id) {
        deleteCustomerUseCase.execute(id);
        return ResponseEntity.noContent().build();
    }
}
```

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

### Respuesta Paginada

```json
{
  "data": [
    { "id": "cust-123", "name": "John Doe" }
  ],
  "pagination": {
    "page": 0,
    "pageSize": 20,
    "totalItems": 150,
    "totalPages": 8
  }
}
```

---

## 2. Manejo de Errores con RFC 7807

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

### Tipos de Error

```java
public enum ErrorType {
    VALIDATION_ERROR("validation-error", "Error de Validación", 400),
    RESOURCE_NOT_FOUND("resource-not-found", "Recurso No Encontrado", 404),
    CONFLICT("conflict", "Conflicto de Recurso", 409),
    UNAUTHORIZED("unauthorized", "No Autenticado", 401),
    FORBIDDEN("forbidden", "No Autorizado", 403),
    INTERNAL_ERROR("internal-error", "Error Interno del Servidor", 500),
    SERVICE_UNAVAILABLE("service-unavailable", "Servicio No Disponible", 503);

    private final String code;
    private final String title;
    private final int status;

    public String getTypeUri() {
        return "https://api.pragma.com/errors/" + code;
    }
}
```

### Global Exception Handler

```java
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ProblemDetail> handleValidation(
            MethodArgumentNotValidException ex, HttpServletRequest request) {
        ProblemDetail problem = ProblemDetail.forStatus(HttpStatus.BAD_REQUEST);
        problem.setType(URI.create(ErrorType.VALIDATION_ERROR.getTypeUri()));
        problem.setTitle("Error de Validación");
        problem.setDetail("La solicitud contiene campos inválidos");
        problem.setInstance(URI.create(request.getRequestURI()));
        problem.setProperty("errors", ex.getBindingResult().getFieldErrors().stream()
            .map(e -> Map.of("field", e.getField(), "message", e.getDefaultMessage()))
            .toList());
        return ResponseEntity.badRequest()
            .contentType(MediaType.APPLICATION_PROBLEM_JSON).body(problem);
    }

    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ProblemDetail> handleNotFound(
            ResourceNotFoundException ex, HttpServletRequest request) {
        ProblemDetail problem = ProblemDetail.forStatus(HttpStatus.NOT_FOUND);
        problem.setType(URI.create(ErrorType.RESOURCE_NOT_FOUND.getTypeUri()));
        problem.setTitle("Recurso No Encontrado");
        problem.setDetail(ex.getMessage());
        problem.setInstance(URI.create(request.getRequestURI()));
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
            .contentType(MediaType.APPLICATION_PROBLEM_JSON).body(problem);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ProblemDetail> handleGeneric(Exception ex, HttpServletRequest request) {
        log.error("Error inesperado", ex);
        ProblemDetail problem = ProblemDetail.forStatus(HttpStatus.INTERNAL_SERVER_ERROR);
        problem.setType(URI.create(ErrorType.INTERNAL_ERROR.getTypeUri()));
        problem.setTitle("Error Interno");
        problem.setDetail("Ocurrió un error inesperado");
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .contentType(MediaType.APPLICATION_PROBLEM_JSON).body(problem);
    }
}
```

---

## 3. Estrategias de Versionamiento

### Versionamiento Nativo (Spring Boot 4)

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void configureApiVersioning(ApiVersionConfigurer configurer) {
        configurer
            .useRequestHeader("X-API-Version")
            .addSupportedVersions("1.0", "2.0")
            .setDefaultVersion("1.0");
    }
}
```

### Uso en Controllers

```java
@RestController
@RequestMapping("/api/customers")
public class CustomerController {

    @PostMapping(version = "1.0")
    public ResponseEntity<CustomerResponseV1> createV1(@Valid @RequestBody CreateCustomerRequestV1 request) {
        // versión 1
    }

    @PostMapping(version = "2.0")
    public ResponseEntity<CustomerResponseV2> createV2(@Valid @RequestBody CreateCustomerRequestV2 request) {
        // versión 2 con campos extendidos
    }
}
```

### Estrategias Disponibles

| Estrategia | Configuración | Ejemplo de Request |
|-----------|---------------|-------------------|
| Header | `useRequestHeader("X-API-Version")` | `X-API-Version: 2.0` |
| Path segment | `usePathSegment(1)` | `/api/v2/customers` |
| Query param | `useQueryParam("version")` | `?version=2.0` |

---

## 4. Documentación con SpringDoc/OpenAPI

### Dependencia

```groovy
implementation 'org.springdoc:springdoc-openapi-starter-webmvc-ui:2.7.0'
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

### Anotaciones en Controller

```java
@RestController
@RequestMapping("/api/v1/orders")
@Tag(name = "Orders", description = "API de gestión de órdenes")
public class OrderController {

    @PostMapping
    @Operation(
        summary = "Crear orden",
        description = "Crea una nueva orden para el cliente especificado"
    )
    @ApiResponses({
        @ApiResponse(responseCode = "201", description = "Orden creada exitosamente"),
        @ApiResponse(responseCode = "400", description = "Datos de entrada inválidos",
            content = @Content(schema = @Schema(implementation = ProblemDetail.class))),
        @ApiResponse(responseCode = "404", description = "Cliente no encontrado")
    })
    public ResponseEntity<OrderResponse> create(@Valid @RequestBody CreateOrderRequest request) {
        // implementación
    }
}
```

---

## 5. Estándares AsyncAPI para Eventos

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

### Especificación AsyncAPI

```yaml
asyncapi: 2.6.0
info:
  title: Order Events API
  version: 1.0.0
channels:
  order-events:
    publish:
      message:
        payload:
          type: object
          properties:
            eventId:
              type: string
              format: uuid
            eventType:
              type: string
              enum: [OrderCreated, OrderUpdated, OrderCancelled]
            aggregateId:
              type: string
            timestamp:
              type: string
              format: date-time
            payload:
              type: object
```

---

## Reglas Importantes

- Usar sustantivos plurales para recursos.
- URLs en minúsculas con guiones.
- Versionar APIs en la URL o header.
- Siempre usar Content-Type `application/problem+json` para errores.
- Incluir `traceId` para correlación de logs.
- No exponer detalles internos ni stack traces en producción.
- Documentar todas las APIs con OpenAPI.
- Incluir headers de correlación (`X-Request-ID`).
- Implementar paginación para colecciones.
