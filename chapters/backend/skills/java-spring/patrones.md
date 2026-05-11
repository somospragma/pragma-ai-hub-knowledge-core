---
id: backend-skill-java-spring-patrones
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: java-spring
---

# Patrones de Diseño y Convenciones — Java Spring

## Propósito

Definir las convenciones de naming, principios SOLID aplicados, validación de inputs, mapeo DTO↔Entity con MapStruct, y patrones de diseño estándar para microservicios Java con Spring Boot.

---

## 1. Convenciones de Naming

### Clases e Interfaces (PascalCase)

| Componente | Sufijo | Ejemplo |
|-----------|--------|---------|
| Entidad de dominio | _(ninguno)_ | `Account` |
| Value object | _(ninguno)_ | `Money` |
| Puerto de salida | `I*Gateway` | `IAccountGateway` |
| Caso de uso | `*UseCase` | `CreateAccountUseCase` |
| Driven adapter | `*Adapter` | `AccountJpaAdapter` |
| Entidad JPA | `*Entity` | `AccountEntity` |
| Entidad Mongo | `*Document` | `AccountDocument` |
| Entidad DynamoDB | `*Item` | `AccountItem` |
| Repositorio framework | `*Repository` | `AccountJpaRepository` |
| Mapper persistencia | `*EntityMapper` | `AccountEntityMapper` |
| Mapper REST | `*RestMapper` | `AccountRestMapper` |
| Controller | `*Controller` | `AccountController` |
| DTO request | `*Request` (Record) | `CreateAccountRequest` |
| DTO response | `*Response` (Record) | `AccountResponse` |
| Excepción | `*Exception` | `AccountNotFoundException` |
| Config | `*Config` | `UseCasesConfig` |

### Reglas Críticas

- **Todas** las interfaces DEBEN tener prefijo `I` (ej: `IAccountGateway`).
- **No** usar sufijo `Impl` en adapters (usar `AccountJpaAdapter`, no `AccountGatewayImpl`).
- **Todos** los mappers son interfaces MapStruct `@Mapper` — NO mappers estáticos/manuales.
- DTOs son Java Records. NO usar sufijo `*DTO`. Usar `*Request` / `*Response`.
- Use cases terminan en `UseCase`, no `Service` ni `Handler`.

### Módulos (kebab-case)

| Tipo | Patrón | Ejemplo |
|------|--------|---------|
| Driven adapter REST | `{system}-client-api` | `t24-client-api` |
| Driven adapter DB | `{technology}-persistence` | `r2dbc-persistence` |
| Entry point imperativo | `rest` | `rest` |
| Helpers | `helpers` | `helpers` |
| App assembler | `app-service` | `app-service` |

---

## 2. Principios SOLID Aplicados

### S — Responsabilidad Única

```java
// CORRECTO: Servicio con responsabilidad única
@RequiredArgsConstructor
public class CreateLoanUseCase {
    private final ILoanGateway loanGateway;

    public Loan execute(LoanRequest request) {
        Loan loan = Loan.builder()
            .amount(request.amount())
            .customerId(request.customerId())
            .status(LoanStatus.PENDING)
            .build();
        return loanGateway.save(loan);
    }
}

// Validación separada
@Component
public class LoanValidator {
    public void validate(LoanRequest request) {
        if (request.amount().compareTo(BigDecimal.ZERO) <= 0) {
            throw new ValidationException("Amount must be positive");
        }
    }
}
```

### O — Abierto/Cerrado

```java
public interface INotificationSender {
    void send(String message, String recipient);
    NotificationType getType();
}

@Component
public class EmailNotificationSender implements INotificationSender {
    @Override
    public void send(String message, String recipient) { /* envío email */ }
    @Override
    public NotificationType getType() { return NotificationType.EMAIL; }
}

@Service
public class NotificationService {
    private final Map<NotificationType, INotificationSender> senders;

    public NotificationService(List<INotificationSender> senderList) {
        this.senders = senderList.stream()
            .collect(Collectors.toMap(INotificationSender::getType, Function.identity()));
    }

    public void send(NotificationType type, String message, String recipient) {
        senders.get(type).send(message, recipient);
    }
}
```

### D — Inversión de Dependencias

```java
// El dominio define la abstracción
public interface ILoanGateway {
    Optional<Loan> findById(String id);
    Loan save(Loan loan);
}

// La infraestructura implementa
@Repository
@RequiredArgsConstructor
public class LoanJpaAdapter implements ILoanGateway {
    private final LoanJpaRepository jpaRepository;
    private final LoanEntityMapper mapper;

    @Override
    public Optional<Loan> findById(String id) {
        return jpaRepository.findById(id).map(mapper::toModel);
    }

    @Override
    public Loan save(Loan loan) {
        LoanEntity entity = mapper.toEntity(loan);
        return mapper.toModel(jpaRepository.save(entity));
    }
}
```

---

## 3. Validación de Inputs

### Principios

1. **Validar temprano** — en la frontera del sistema (controllers).
2. **Whitelist > Blacklist** — definir lo permitido.
3. **Fail fast** — rechazar datos inválidos inmediatamente.
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

public record OrderItemRequest(
    @NotBlank(message = "Product ID es requerido")
    @Size(max = 50)
    String productId,

    @NotNull @Min(value = 1, message = "Cantidad mínima es 1")
    Integer quantity,

    @NotNull @DecimalMin(value = "0.01", message = "Precio debe ser positivo")
    BigDecimal unitPrice
) {}
```

### Validador Personalizado

```java
@Target({ElementType.FIELD})
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = PhoneNumberValidator.class)
public @interface ValidPhoneNumber {
    String message() default "Número de teléfono inválido";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}

public class PhoneNumberValidator implements ConstraintValidator<ValidPhoneNumber, String> {
    private static final Pattern PHONE_PATTERN = Pattern.compile("^\\+?[1-9]\\d{1,14}$");

    @Override
    public boolean isValid(String value, ConstraintValidatorContext context) {
        if (value == null || value.isBlank()) return true;
        return PHONE_PATTERN.matcher(value).matches();
    }
}
```

### Manejo de Errores de Validación

```java
@RestControllerAdvice
public class ValidationExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ProblemDetail> handleValidationErrors(
            MethodArgumentNotValidException ex) {
        List<Map<String, String>> errors = ex.getBindingResult().getFieldErrors().stream()
            .map(error -> Map.of("field", error.getField(), "message", error.getDefaultMessage()))
            .toList();

        ProblemDetail problem = ProblemDetail.forStatus(HttpStatus.BAD_REQUEST);
        problem.setType(URI.create("https://api.pragma.com/errors/validation-error"));
        problem.setTitle("Error de Validación");
        problem.setDetail("La solicitud contiene campos inválidos");
        problem.setProperty("errors", errors);
        return ResponseEntity.badRequest().body(problem);
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

    @BeanMapping(nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE)
    void updateEntity(UpdateOrderRequest request, @MappingTarget Order entity);
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

// Uso en mappers
@Mapper(config = MapStructConfig.class)
public interface AccountEntityMapper {
    Account toModel(AccountEntity entity);
    AccountEntity toEntity(Account model);
}
```

---

## 5. Patrones de Diseño Comunes

### Strategy Pattern

```java
public interface IEncryptionStrategy {
    String encrypt(String data);
    String decrypt(String data);
}

@Component
public class AesEncryption implements IEncryptionStrategy { /* ... */ }

@Component
public class RsaEncryption implements IEncryptionStrategy { /* ... */ }
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

### Observer Pattern (Spring Events)

```java
// Publicar evento
@RequiredArgsConstructor
public class CreateOrderUseCase {
    private final ApplicationEventPublisher eventPublisher;

    public Order execute(OrderRequest request) {
        Order order = /* crear orden */;
        eventPublisher.publishEvent(new OrderCreatedEvent(order));
        return order;
    }
}

// Escuchar evento
@Component
public class OrderNotificationListener {
    @EventListener
    public void handleOrderCreated(OrderCreatedEvent event) {
        // Reaccionar al evento
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

## Reglas Importantes

- Preferir composición sobre herencia.
- Programar contra interfaces, no implementaciones.
- Aplicar responsabilidad única desde el diseño inicial.
- Mantener patrones simples, no sobre-ingenierizar.
- Validar en la frontera del sistema (controllers).
- Usar tipos fuertes y validación de esquema.
- Establecer límites de tamaño en todos los campos.
