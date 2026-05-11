---
id: backend-skill-java-webflux-patrones
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: java-webflux
---

# Patrones de Diseño y Convenciones — Java WebFlux

## Propósito

Definir las convenciones de naming, principios SOLID aplicados al paradigma reactivo, validación de inputs, mapeo DTO↔Entity con MapStruct, y patrones de diseño estándar para microservicios Java reactivos con Spring WebFlux.

---

## 1. Convenciones de Naming

### Clases e Interfaces (PascalCase)

| Componente | Sufijo | Ejemplo |
|-----------|--------|---------|
| Entidad de dominio | _(ninguno)_ | `Account` |
| Value object | _(ninguno)_ | `Money` |
| Puerto de salida | `I*Gateway` | `IAccountGateway` |
| Caso de uso | `*UseCase` | `CreateAccountUseCase` |
| Driven adapter | `*Adapter` | `AccountR2dbcAdapter` |
| Entidad R2DBC | `*Entity` | `AccountEntity` |
| Entidad Mongo | `*Document` | `AccountDocument` |
| Entidad DynamoDB | `*Item` | `AccountItem` |
| Repositorio framework | `*Repository` | `AccountR2dbcRepository` |
| Mapper persistencia | `*EntityMapper` | `AccountEntityMapper` |
| Mapper REST | `*RestMapper` | `AccountRestMapper` |
| Router | `*Router` | `AccountRouter` |
| Handler | `*Handler` | `AccountHandler` |
| DTO request | `*Request` (Record) | `CreateAccountRequest` |
| DTO response | `*Response` (Record) | `AccountResponse` |
| Excepción | `*Exception` | `AccountNotFoundException` |
| Config | `*Config` | `UseCasesConfig` |
| WebFilter | `*WebFilter` | `CorrelationWebFilter` |

### Reglas Críticas

- **Todas** las interfaces DEBEN tener prefijo `I` (ej: `IAccountGateway`).
- **No** usar sufijo `Impl` en adapters (usar `AccountR2dbcAdapter`, no `AccountGatewayImpl`).
- **Todos** los mappers son interfaces MapStruct `@Mapper` — NO mappers estáticos/manuales.
- DTOs son Java Records. NO usar sufijo `*DTO`. Usar `*Request` / `*Response`.
- Use cases terminan en `UseCase`, no `Service` ni `Handler`.
- Entry-points usan `*Router` + `*Handler`, **NO** `*Controller`.

### Módulos (kebab-case)

| Tipo | Patrón | Ejemplo |
|------|--------|---------|
| Driven adapter REST | `{system}-client-api` | `t24-client-api` |
| Driven adapter DB | `r2dbc-persistence` | `r2dbc-persistence` |
| Entry point reactivo | `reactive-web` | `reactive-web` |
| Helpers | `helpers` | `helpers` |
| App assembler | `app-service` | `app-service` |

---

## 2. Principios SOLID Aplicados (Reactivo)

### S — Responsabilidad Única

```java
// CORRECTO: UseCase con responsabilidad única, retorno reactivo
@RequiredArgsConstructor
public class CreateLoanUseCase {
    private final ILoanGateway loanGateway;

    public Mono<Loan> execute(LoanRequest request) {
        Loan loan = Loan.builder()
            .amount(request.amount())
            .customerId(request.customerId())
            .status(LoanStatus.PENDING)
            .build();
        return loanGateway.save(loan);
    }
}

// Validación separada (reactiva)
@Component
public class LoanValidator {
    public Mono<LoanRequest> validate(LoanRequest request) {
        if (request.amount().compareTo(BigDecimal.ZERO) <= 0) {
            return Mono.error(new ValidationException("Amount must be positive"));
        }
        return Mono.just(request);
    }
}
```

### O — Abierto/Cerrado

```java
public interface INotificationSender {
    Mono<Void> send(String message, String recipient);
    NotificationType getType();
}

@Component
public class EmailNotificationSender implements INotificationSender {
    @Override
    public Mono<Void> send(String message, String recipient) {
        return webClient.post()
            .uri("/emails")
            .bodyValue(Map.of("to", recipient, "body", message))
            .retrieve()
            .bodyToMono(Void.class);
    }

    @Override
    public NotificationType getType() { return NotificationType.EMAIL; }
}

@Component
public class NotificationService {
    private final Map<NotificationType, INotificationSender> senders;

    public NotificationService(List<INotificationSender> senderList) {
        this.senders = senderList.stream()
            .collect(Collectors.toMap(INotificationSender::getType, Function.identity()));
    }

    public Mono<Void> send(NotificationType type, String message, String recipient) {
        return senders.get(type).send(message, recipient);
    }
}
```

### D — Inversión de Dependencias

```java
// El dominio define la abstracción con tipos reactivos
public interface ILoanGateway {
    Mono<Loan> findById(String id);
    Mono<Loan> save(Loan loan);
}

// La infraestructura implementa con R2DBC
@Repository
@RequiredArgsConstructor
public class LoanR2dbcAdapter implements ILoanGateway {
    private final LoanR2dbcRepository r2dbcRepository;
    private final LoanEntityMapper mapper;

    @Override
    public Mono<Loan> findById(String id) {
        return r2dbcRepository.findById(id).map(mapper::toModel);
    }

    @Override
    public Mono<Loan> save(Loan loan) {
        LoanEntity entity = mapper.toEntity(loan);
        return r2dbcRepository.save(entity).map(mapper::toModel);
    }
}
```

---

## 3. Validación de Inputs (Reactiva)

### Principios

1. **Validar temprano** — en la frontera del sistema (handlers).
2. **Whitelist > Blacklist** — definir lo permitido.
3. **Fail fast** — rechazar datos inválidos inmediatamente con `Mono.error()`.
4. **Mensajes claros** — indicar qué campo falló.

### DTOs con Bean Validation

```java
public record CreateOrderRequest(
    @NotNull(message = "Customer ID es requerido")
    @Pattern(regexp = "^[a-zA-Z0-9-]{1,50}$", message = "Formato de ID inválido")
    String customerId,

    @NotEmpty(message = "Items no puede estar vacío")
    @Size(min = 1, max = 100, message = "Debe tener entre 1 y 100 items")
    @Valid
    List<OrderItemRequest> items,

    @NotNull(message = "Moneda es requerida")
    @Pattern(regexp = "^[A-Z]{3}$", message = "Moneda debe ser código ISO de 3 letras")
    String currency
) {}
```

### Validación en Handler (Reactiva)

```java
@Component
@RequiredArgsConstructor
public class OrderHandler {
    private final Validator validator;
    private final CreateOrderUseCase createOrderUseCase;

    public Mono<ServerResponse> create(ServerRequest request) {
        return request.bodyToMono(CreateOrderRequest.class)
            .flatMap(this::validate)
            .flatMap(createOrderUseCase::execute)
            .flatMap(order -> ServerResponse.status(HttpStatus.CREATED).bodyValue(order));
    }

    private <T> Mono<T> validate(T body) {
        Set<ConstraintViolation<T>> violations = validator.validate(body);
        if (!violations.isEmpty()) {
            List<Map<String, String>> errors = violations.stream()
                .map(v -> Map.of("field", v.getPropertyPath().toString(),
                                  "message", v.getMessage()))
                .toList();
            return Mono.error(new ValidationException(errors));
        }
        return Mono.just(body);
    }
}
```

### Manejo de Errores de Validación (Reactivo)

```java
@Component
@Order(-2)
public class GlobalErrorWebExceptionHandler extends AbstractErrorWebExceptionHandler {

    // ... constructor omitido

    private Mono<ServerResponse> renderErrorResponse(ServerRequest request) {
        Throwable error = getError(request);
        if (error instanceof ValidationException ve) {
            return ServerResponse.badRequest()
                .contentType(MediaType.APPLICATION_PROBLEM_JSON)
                .bodyValue(Map.of(
                    "type", "https://api.pragma.com/errors/validation-error",
                    "title", "Error de Validación",
                    "status", 400,
                    "errors", ve.getErrors()
                ));
        }
        return ServerResponse.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .bodyValue(Map.of("error", "Internal server error"));
    }
}
```

---

## 4. Mapeo DTO↔Entity con MapStruct

### Mapper Básico

```java
@Mapper(componentModel = "spring")
public interface OrderEntityMapper {
    Order toModel(OrderEntity entity);
    OrderEntity toEntity(Order model);
    List<Order> toModelList(List<OrderEntity> entities);
}
```

### Mapper con Lógica Personalizada

```java
@Mapper(
    componentModel = "spring",
    unmappedTargetPolicy = ReportingPolicy.ERROR,
    nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE
)
public interface OrderMapper {

    @Mapping(target = "id", ignore = true)
    @Mapping(target = "createdAt", expression = "java(java.time.Instant.now())")
    @Mapping(target = "status", constant = "PENDING")
    Order toEntity(CreateOrderRequest request);

    @Mapping(source = "createdAt", target = "createdDate", dateFormat = "yyyy-MM-dd")
    OrderResponse toResponse(Order entity);
}
```

### Configuración Global MapStruct

```java
@MapperConfig(
    componentModel = "spring",
    unmappedTargetPolicy = ReportingPolicy.ERROR,
    nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE
)
public interface MapStructConfig {}

@Mapper(config = MapStructConfig.class)
public interface AccountEntityMapper {
    Account toModel(AccountEntity entity);
    AccountEntity toEntity(Account model);
}
```

---

## 5. Patrones de Diseño Comunes (Reactivos)

### Strategy Pattern

```java
public interface IEncryptionStrategy {
    Mono<String> encrypt(String data);
    Mono<String> decrypt(String data);
}

@Component
public class AesEncryption implements IEncryptionStrategy {
    @Override
    public Mono<String> encrypt(String data) {
        return Mono.fromCallable(() -> doEncrypt(data))
            .subscribeOn(Schedulers.boundedElastic());
    }

    @Override
    public Mono<String> decrypt(String data) {
        return Mono.fromCallable(() -> doDecrypt(data))
            .subscribeOn(Schedulers.boundedElastic());
    }
}
```

### Factory Pattern

```java
@Component
public class DataProviderFactory {
    public IDataProvider getDataProvider(String type) {
        return switch (type) {
            case "SQL" -> new SqlDataProvider();
            case "NOSQL" -> new NoSqlDataProvider();
            default -> throw new IllegalArgumentException("Tipo no soportado: " + type);
        };
    }
}
```

### Builder Pattern (con Lombok)

```java
@Data @Builder @NoArgsConstructor @AllArgsConstructor
public class Account {
    private String id;
    private String holderName;
    private BigDecimal balance;
    private String status;
    private LocalDateTime createdAt;
}

// Uso
Account account = Account.builder()
    .holderName("John Doe")
    .balance(BigDecimal.ZERO)
    .status("ACTIVE")
    .createdAt(LocalDateTime.now())
    .build();
```

### Observer Pattern (Reactor Sinks)

```java
@Component
public class DomainEventPublisher {
    private final Sinks.Many<DomainEvent> sink = Sinks.many().multicast().onBackpressureBuffer();

    public void publish(DomainEvent event) {
        sink.tryEmitNext(event);
    }

    public Flux<DomainEvent> subscribe() {
        return sink.asFlux();
    }
}

// Listener reactivo
@Component
@RequiredArgsConstructor
public class OrderNotificationListener {
    private final DomainEventPublisher eventPublisher;

    @PostConstruct
    public void listen() {
        eventPublisher.subscribe()
            .filter(event -> event instanceof OrderCreatedEvent)
            .flatMap(this::handleOrderCreated)
            .subscribe();
    }

    private Mono<Void> handleOrderCreated(DomainEvent event) {
        // Reaccionar al evento de forma reactiva
        return Mono.empty();
    }
}
```

---

## 6. Sanitización de Inputs

```java
@Component
public class InputSanitizer {
    public String sanitizeForLog(String input) {
        if (input == null) return null;
        return input.replaceAll("[\\r\\n]", " ")
                   .replaceAll("[^\\p{Print}]", "");
    }

    public String sanitizeHtml(String input) {
        if (input == null) return null;
        return Encode.forHtml(input);
    }
}
```

---

## Reglas Importantes

- Preferir composición sobre herencia.
- Programar contra interfaces, no implementaciones.
- Aplicar responsabilidad única desde el diseño inicial.
- Mantener patrones simples, no sobre-ingenierizar.
- Validar en la frontera del sistema (handlers).
- Usar tipos fuertes y validación de esquema.
- Establecer límites de tamaño en todos los campos.
- Todos los retornos de métodos públicos son `Mono<T>` o `Flux<T>`.
- Nunca usar `.block()` fuera de tests.
