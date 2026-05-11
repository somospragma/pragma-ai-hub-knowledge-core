---
id: backend-skill-java-spring-arquetipo
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: java-spring
---

# Arquetipo: Spring Boot MVC + Gradle Multi-Módulo

## Propósito

Definir la estructura estándar obligatoria para microservicios Java imperativos (blocking) usando Spring MVC, JPA/Hibernate y Gradle multi-módulo con arquitectura hexagonal.

## Tech Stack Obligatorio

| Componente | Tecnología |
|-----------|-----------|
| Lenguaje | Java 21 |
| Framework | Spring Boot 4.x + Spring MVC |
| Build | Gradle multi-módulo con version catalog (`libs.versions.toml`) |
| Persistencia | JPA / Hibernate (blocking) |
| HTTP Client | `RestClient` (Spring 6.1+). **NO** usar `RestTemplate` (deprecated) |
| Entry-points | `@RestController` + `@GetMapping` / `@PostMapping` |
| Boilerplate | Lombok |
| Testing | MockMvc + JUnit 5 |
| Null-safety | JSpecify (`@NullMarked` por paquete) |

## Estructura de Carpetas

```
project/
├── domain/
│   ├── model/                          ← Entidades puras, value objects, enums. Sin framework.
│   ├── ports/                          ← Interfaces *Gateway. Tipos Java planos.
│   └── usecases/                       ← Clases *UseCase. Lógica de negocio.
├── infrastructure/
│   ├── driven-adapters/
│   │   ├── persistence/                ← JPA/Hibernate
│   │   ├── {name}-client-api/          ← Consumidor de API externa (RestClient)
│   │   └── .../
│   ├── entry-points/
│   │   └── rest/                       ← @RestController + @GetMapping
│   └── helpers/                        ← Utilidades cross-infra
├── application/
│   └── app-service/                    ← MainApplication + UseCasesConfig + application.yml
├── gradle/
│   └── libs.versions.toml
├── build.gradle
├── gradle.properties
├── settings.gradle
├── main.gradle
├── lombok.config
├── Dockerfile
└── {client}-lib-mocks/                 ← Mock de librerías corporativas. SIEMPRE generado.
```

## Reglas del Paradigma Imperativo

1. Los tipos de retorno de use cases y gateways son tipos Java planos: `T`, `Optional<T>`, `List<T>`.
2. Entry-points usan `@RestController` con mapeo basado en anotaciones.
3. Manejo de errores con `@RestControllerAdvice`.
4. Persistencia con JPA (`JpaRepository`).
5. Consumo HTTP con `RestClient`.
6. Servidor: Tomcat (thread-per-request).
7. Filtros: `OncePerRequestFilter`.

## Capa de Dominio

### Ports (Interfaces Gateway)

```java
public interface IAccountGateway {
    Account save(Account account);
    Optional<Account> findById(String id);
    List<Account> findAll();
    void deleteById(String id);
}
```

### Use Cases

Clases Java planas. Sin `@Service`, sin `@Component`. Se auto-registran por `UseCasesConfig` con regex scan (`^.+UseCase$`):

```java
@RequiredArgsConstructor
public class CreateAccountUseCase {
    private final IAccountGateway accountGateway;

    public Account execute(String holderName, String holderDocument) {
        Account account = Account.builder()
            .holderName(holderName)
            .holderDocument(holderDocument)
            .balance(BigDecimal.ZERO)
            .status("ACTIVE")
            .createdAt(LocalDateTime.now())
            .build();
        return accountGateway.save(account);
    }
}
```

## Capa de Infraestructura

### Persistencia JPA (driven-adapters/persistence)

**Entidad JPA** (interna al adapter):

```java
@Entity
@Table(name = "accounts")
@Data @Builder @NoArgsConstructor @AllArgsConstructor
public class AccountEntity {
    @Id private String id;
    @Column(name = "holder_name") private String holderName;
    @Column(name = "holder_document") private String holderDocument;
    @Column(name = "balance") private BigDecimal balance;
    @Column(name = "status") private String status;
    @Column(name = "created_at") private LocalDateTime createdAt;
}
```

**Repositorio JPA:**

```java
public interface AccountJpaRepository extends JpaRepository<AccountEntity, String> {
}
```

**Adapter implementando el gateway:**

```java
@Repository
@RequiredArgsConstructor
public class AccountJpaAdapter implements IAccountGateway {
    private final AccountJpaRepository jpaRepository;
    private final AccountEntityMapper mapper;

    @Override
    public Account save(Account account) {
        if (account.getId() == null) { account.setId(UUID.randomUUID().toString()); }
        AccountEntity entity = mapper.toEntity(account);
        AccountEntity saved = jpaRepository.save(entity);
        return mapper.toModel(saved);
    }

    @Override
    public Optional<Account> findById(String id) {
        return jpaRepository.findById(id).map(mapper::toModel);
    }

    @Override
    public List<Account> findAll() {
        return jpaRepository.findAll().stream().map(mapper::toModel).toList();
    }

    @Override
    public void deleteById(String id) { jpaRepository.deleteById(id); }
}
```

**Mapper MapStruct (obligatorio):**

```java
@Mapper(componentModel = "spring")
public interface AccountEntityMapper {
    Account toModel(AccountEntity entity);
    AccountEntity toEntity(Account model);
}
```

### Cliente HTTP (driven-adapters/{name}-client-api)

```java
@Component
public class ExternalServiceAdapter implements IExternalServiceGateway {
    private final RestClient restClient;

    public ExternalServiceAdapter(@Value("${external-service.base-url}") String baseUrl) {
        this.restClient = RestClient.builder().baseUrl(baseUrl).build();
    }

    @Override
    public ExternalResource fetchById(String id) {
        ExternalResourceDto dto = restClient.get()
            .uri("/api/v1/resources/{id}", id)
            .retrieve()
            .onStatus(HttpStatusCode::is4xxClientError,
                (request, response) -> {
                    throw new ResourceNotFoundException("Not found: " + id);
                })
            .body(ExternalResourceDto.class);
        return ExternalServiceMapper.toModel(dto);
    }
}
```

### Entry-Points REST (Spring MVC)

**DTOs como Java Records:**

```java
public record CreateAccountRequest(
    @NotBlank String holderName,
    @NotBlank String holderDocument
) {}

public record AccountResponse(
    String id, String holderName, String holderDocument,
    BigDecimal balance, String status, LocalDateTime createdAt
) {}
```

**Controller:**

```java
@RestController
@RequestMapping("/api/accounts")
@RequiredArgsConstructor
public class AccountController {
    private final CreateAccountUseCase createAccountUseCase;
    private final GetAccountUseCase getAccountUseCase;

    @PostMapping
    public ResponseEntity<AccountResponse> create(@Valid @RequestBody CreateAccountRequest request) {
        Account result = createAccountUseCase.execute(request.holderName(), request.holderDocument());
        return ResponseEntity.status(HttpStatus.CREATED).body(AccountRestMapper.toResponse(result));
    }

    @GetMapping("/{id}")
    public ResponseEntity<AccountResponse> getById(@PathVariable String id) {
        Account result = getAccountUseCase.execute(id);
        return ResponseEntity.ok(AccountRestMapper.toResponse(result));
    }
}
```

## Capa de Aplicación

```java
@SpringBootApplication(scanBasePackages = "{base.package}")
public class MainApplication {
    public static void main(String[] args) {
        SpringApplication.run(MainApplication.class, args);
    }
}
```

```java
@Configuration
@ComponentScan(
    basePackages = "{base.package}.usecase",
    includeFilters = {
        @ComponentScan.Filter(type = FilterType.REGEX, pattern = "^.+UseCase$")
    },
    useDefaultFilters = false
)
public class UseCasesConfig {
}
```

**application.yml:**

```yaml
spring:
  application:
    name: my-imperative-service
  datasource:
    url: jdbc:postgresql://localhost:5432/mydb
    username: ${DB_USER}
    password: ${DB_PASSWORD}
  jpa:
    hibernate:
      ddl-auto: validate
server:
  port: 8080
external-service:
  base-url: https://api.external.com
```

## Reglas de Dependencia entre Módulos

```
model           → nada (Java + Lombok)
ports           → model
usecases        → model + ports
helpers         → model + ports + framework
driven-adapters → model + ports + helpers + {client}-lib-mocks
entry-points    → model + ports + usecases + helpers + {client}-lib-mocks
app-service     → TODOS los módulos
{client}-lib-mocks → nada (standalone)
```

## Restricciones Obligatorias

| Restricción |
|------------|
| Prefijo `I` en TODAS las interfaces |
| MapStruct para TODOS los mappers (no static/manual) |
| DTOs como Java Records (no clases `@Data`) |
| `main.gradle` completo con todas las herramientas de calidad |
| `UseCasesConfig` con cuerpo vacío (sin `@Bean`) |
| Módulo `{client}-lib-mocks` siempre generado |
| `lombok.config` en la raíz del proyecto |
| `package-info.java` con `@NullMarked` en cada paquete |
