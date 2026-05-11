---
id: backend-skill-java-webflux-arquetipo
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: java-webflux
---

# Arquetipo: Spring WebFlux + Gradle Multi-Módulo (Reactivo)

## Propósito

Definir la estructura estándar obligatoria para microservicios Java reactivos usando Spring WebFlux, Project Reactor, R2DBC y Gradle multi-módulo con arquitectura hexagonal.

## Ámbito de Aplicación

- Alta concurrencia con recursos limitados (modelo event-loop).
- Consumo o exposición de data streams.
- Persistencia con R2DBC (SQL reactivo) o MongoDB Reactive.
- Integraciones HTTP no bloqueantes con `WebClient`.
- Cuando el estándar del cliente es reactivo.

## Tech Stack Obligatorio

| Componente | Tecnología |
|-----------|-----------|
| Lenguaje | Java 21 |
| Framework | Spring Boot 4.x + **Spring WebFlux** |
| Reactor | Project Reactor (`Mono<T>`, `Flux<T>`) |
| Build | Gradle multi-módulo con version catalog (`libs.versions.toml`) |
| Persistencia reactiva | R2DBC o MongoDB Reactive |
| HTTP Client | `WebClient`. **NO** usar `RestTemplate` ni `RestClient` |
| Entry-points | `RouterFunction<ServerResponse>` + Handler. **NO** usar `@RestController` |
| Boilerplate | Lombok |
| Testing | `StepVerifier` (Reactor Test) + `WebTestClient` |
| Servidor | Netty (event-loop, non-blocking). **NO** Tomcat |

## Estructura de Carpetas

```
project/
├── domain/
│   ├── model/                          ← Entidades puras, value objects, enums. Sin framework.
│   ├── ports/                          ← Interfaces I*Gateway. Retornos Mono<T>/Flux<T>.
│   └── usecases/                       ← Clases *UseCase. Lógica de negocio reactiva.
├── infrastructure/
│   ├── driven-adapters/
│   │   ├── r2dbc-persistence/          ← Persistencia reactiva R2DBC
│   │   ├── {name}-client-api/          ← Consumidor de API externa (WebClient)
│   │   └── .../
│   ├── entry-points/
│   │   └── reactive-web/              ← Router + Handler (NO @RestController)
│   └── helpers/                        ← Utilidades cross-infra (RequestParameterValidator)
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

## Reglas del Paradigma Reactivo

1. **Todo tipo de retorno** de use cases, gateways y handlers es `Mono<T>` o `Flux<T>`. Sin tipos bloqueantes.
2. **Cero llamadas bloqueantes** dentro del pipeline reactivo. Sin `.block()`, `.blockFirst()`, `.blockLast()` fuera de tests.
3. Entry-points usan patrón **Router + Handler**. Sin `@RestController`, sin `@GetMapping`.
4. Manejo de errores con `AbstractErrorWebExceptionHandler`, **NO** `@RestControllerAdvice`.
5. Persistencia con R2DBC (`ReactiveCrudRepository`), **NO** JPA/Hibernate.
6. Consumo HTTP con `WebClient`, **NO** `RestTemplate` ni `RestClient`.
7. Servidor: Netty (event-loop, non-blocking). **NO** Tomcat.
8. Filtros: `WebFilter`, **NO** `OncePerRequestFilter`.

---

## Capa de Dominio — Especificidades Reactivas

### Ports (Interfaces Gateway)

Los tipos de retorno son **siempre reactivos**:

```java
public interface IAccountGateway {
    Mono<Account> save(Account account);
    Mono<Account> findById(String id);
    Flux<Account> findAll();
    Mono<Void> deleteById(String id);
}
```

### Use Cases

Todos los métodos retornan `Mono<T>` o `Flux<T>`. Composición vía operadores reactivos:

```java
@RequiredArgsConstructor
public class CreateAccountUseCase {
    private final IAccountGateway accountGateway;

    public Mono<Account> execute(Account account) {
        account.setStatus("ACTIVE");
        account.setCreatedAt(LocalDateTime.now());
        return accountGateway.save(account);
    }
}
```

```java
@RequiredArgsConstructor
public class GetAccountUseCase {
    private final IAccountGateway accountGateway;

    public Mono<Account> execute(String id) {
        return accountGateway.findById(id)
            .switchIfEmpty(Mono.error(
                new AccountNotFoundException("Account not found: " + id)));
    }

    public Flux<Account> findAll() {
        return accountGateway.findAll();
    }
}
```

---

## Capa de Infraestructura — Especificidades Reactivas

### Persistencia R2DBC (driven-adapters/r2dbc-persistence)

**Entidad R2DBC** (interna al adapter):

```java
@Table("accounts")
@Data @Builder @NoArgsConstructor @AllArgsConstructor
public class AccountEntity {
    @Id private String id;
    private String holderName;
    private String accountType;
    private BigDecimal balance;
    private String status;
    private LocalDateTime createdAt;
}
```

**Repositorio reactivo:**

```java
public interface AccountR2dbcRepository extends ReactiveCrudRepository<AccountEntity, String> {
    Flux<AccountEntity> findByStatus(String status);
}
```

**Adapter implementando el gateway:**

```java
@Repository
@RequiredArgsConstructor
public class AccountR2dbcAdapter implements IAccountGateway {
    private final AccountR2dbcRepository r2dbcRepository;
    private final AccountEntityMapper mapper;

    @Override
    public Mono<Account> save(Account account) {
        return r2dbcRepository.save(mapper.toEntity(account))
            .map(mapper::toModel);
    }

    @Override
    public Mono<Account> findById(String id) {
        return r2dbcRepository.findById(id)
            .map(mapper::toModel);
    }

    @Override
    public Flux<Account> findAll() {
        return r2dbcRepository.findAll()
            .map(mapper::toModel);
    }

    @Override
    public Mono<Void> deleteById(String id) {
        return r2dbcRepository.deleteById(id);
    }
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

**Mapper MapStruct (obligatorio):**

```java
@Mapper(componentModel = "spring")
public interface ExternalServiceMapper {
    ExternalResource toModel(ExternalResourceDto dto);
}
```

**Adapter con WebClient:**

```java
@Component
@RequiredArgsConstructor
public class ExternalServiceAdapter implements IExternalServiceGateway {
    private final WebClient webClient;
    private final ExternalServiceMapper mapper;

    @Override
    public Mono<ExternalResource> fetchById(String id) {
        return webClient.get()
            .uri("/api/v1/resources/{id}", id)
            .retrieve()
            .onStatus(HttpStatusCode::is4xxClientError,
                response -> Mono.error(new ResourceNotFoundException("Not found: " + id)))
            .bodyToMono(ExternalResourceDto.class)
            .map(mapper::toModel);
    }
}
```

### Entry-Points Reactivos (reactive-web)

**DTOs como Java Records:**

```java
public record AccountRequest(
    @NotBlank String holderName,
    @NotBlank String accountType,
    @NotNull BigDecimal initialBalance
) {}

public record AccountResponse(
    String id, String holderName, String accountType,
    BigDecimal balance, String status, LocalDateTime createdAt
) {}
```

**Mapper MapStruct (obligatorio):**

```java
@Mapper(componentModel = "spring")
public interface AccountRestMapper {
    Account toModel(AccountRequest request);
    AccountResponse toResponse(Account account);
}
```

**Router** — define rutas como `RouterFunction<ServerResponse>`:

```java
@Configuration
@RequiredArgsConstructor
public class AccountRouter {
    private final AccountHandler handler;

    @Bean
    public RouterFunction<ServerResponse> accountRoutes() {
        return RouterFunctions.route()
            .GET("/api/v1/accounts/{id}", handler::findById)
            .GET("/api/v1/accounts", handler::findAll)
            .POST("/api/v1/accounts", handler::create)
            .DELETE("/api/v1/accounts/{id}", handler::delete)
            .build();
    }
}
```

**Handler** — procesa requests, invoca use cases, construye respuestas reactivas:

```java
@Component
@RequiredArgsConstructor
public class AccountHandler {
    private final CreateAccountUseCase createAccountUseCase;
    private final GetAccountUseCase getAccountUseCase;
    private final AccountRestMapper accountRestMapper;

    public Mono<ServerResponse> findById(ServerRequest request) {
        String id = request.pathVariable("id");
        return getAccountUseCase.execute(id)
            .map(accountRestMapper::toResponse)
            .flatMap(response -> ServerResponse.ok().bodyValue(response))
            .switchIfEmpty(ServerResponse.notFound().build());
    }

    public Mono<ServerResponse> findAll(ServerRequest request) {
        return getAccountUseCase.findAll()
            .map(accountRestMapper::toResponse)
            .collectList()
            .flatMap(list -> ServerResponse.ok().bodyValue(list));
    }

    public Mono<ServerResponse> create(ServerRequest request) {
        return request.bodyToMono(AccountRequest.class)
            .map(accountRestMapper::toModel)
            .flatMap(createAccountUseCase::execute)
            .map(accountRestMapper::toResponse)
            .flatMap(response -> ServerResponse.status(HttpStatus.CREATED).bodyValue(response));
    }

    public Mono<ServerResponse> delete(ServerRequest request) {
        String id = request.pathVariable("id");
        return getAccountUseCase.execute(id)
            .flatMap(account -> ServerResponse.noContent().build())
            .switchIfEmpty(ServerResponse.notFound().build());
    }
}
```

**Manejo de errores** — global error handler reactivo:

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
        if (error instanceof AccountNotFoundException) {
            return ServerResponse.status(HttpStatus.NOT_FOUND)
                .bodyValue(Map.of("error", error.getMessage()));
        }
        return ServerResponse.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .bodyValue(Map.of("error", "Internal server error"));
    }
}
```

---

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

**Configuración de WebClient:**

```java
@Configuration
public class WebClientConfig {
    @Bean
    public WebClient externalServiceWebClient(
            @Value("${external-service.base-url}") String baseUrl) {
        return WebClient.builder()
            .baseUrl(baseUrl)
            .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
            .build();
    }
}
```

**application.yml:**

```yaml
spring:
  application:
    name: my-reactive-service
  r2dbc:
    url: r2dbc:postgresql://localhost:5432/mydb
    username: ${DB_USER}
    password: ${DB_PASSWORD}
server:
  port: 8080
external-service:
  base-url: https://api.external.com
```

---

## Herramientas de Calidad Obligatorias

Todo proyecto DEBE incluir estas herramientas configuradas en `main.gradle` y `build.gradle`. Un `main.gradle` vacío NO es conforme.

### build.gradle (root) — Declaración de plugins

```groovy
plugins {
    id "org.sonarqube" version "${sonarqubePluginVersion}"
    id 'org.owasp.dependencycheck' version "${owaspDependencyTrackPluginVersion}"
    id 'org.springframework.boot' version "${springBootVersion}" apply false
    id 'info.solidsoft.pitest' version "${pitestVersion}" apply false
    id 'jacoco'
}
```

### main.gradle — Configuración de subproyectos

`main.gradle` DEBE configurar TODO lo siguiente para cada subproyecto:

| Herramienta | Qué configura |
|-------------|---------------|
| JaCoCo | `jacocoTestReport` (HTML + XML), `jacocoTestCoverageVerification` (85% mínimo), `jacocoRootReport` (unificado) |
| PIT | `pitest { targetClasses, threads=8, outputFormats=['XML','HTML'], junit5PluginVersion }` |
| SonarQube | `sonar { properties { host.url, token, coverage.exclusions matching JaCoCo } }` |
| OWASP | `dependencyCheck { formats=['HTML','JSON','XML'], failBuildOnCVSS=11, scanConfigurations }` |
| ArchUnit | `checkArchitecture` task dependiendo de `:app-service:architectureTest` |
| MapStruct | `options.compilerArgs = ['-Amapstruct.suppressGeneratorTimestamp=true']` |

---

## Reglas de Dependencia entre Módulos

```
model           → nada (Java + Lombok)
ports           → model (+ reactor-core para Mono/Flux)
usecases        → model + ports
helpers         → model + ports + framework
driven-adapters → model + ports + helpers + {client}-lib-mocks
entry-points    → model + ports + usecases + helpers + {client}-lib-mocks
app-service     → TODOS los módulos
{client}-lib-mocks → nada (standalone)
```

---

## Configuración Gradle

### gradle/libs.versions.toml

```toml
[versions]
spring-boot = "4.0.3"
lombok = "1.18.36"
reactor-test = "3.7.6"
mapstruct = "1.5.5.Final"

[libraries]
spring-boot-webflux = { module = "org.springframework.boot:spring-boot-starter-webflux" }
spring-boot-r2dbc = { module = "org.springframework.boot:spring-boot-starter-data-r2dbc" }
spring-boot-test = { module = "org.springframework.boot:spring-boot-starter-test" }
reactor-test = { module = "io.projectreactor:reactor-test" }
lombok = { module = "org.projectlombok:lombok" }
r2dbc-postgresql = { module = "org.postgresql:r2dbc-postgresql" }
mapstruct = { module = "org.mapstruct:mapstruct", version.ref = "mapstruct" }
mapstruct-processor = { module = "org.mapstruct:mapstruct-processor", version.ref = "mapstruct" }

[plugins]
spring-boot = { id = "org.springframework.boot", version.ref = "spring-boot" }
spring-dependency-management = { id = "io.spring.dependency-management", version = "1.1.7" }
```

### settings.gradle

```groovy
rootProject.name = 'my-reactive-service'
include ':domain:model'
include ':domain:ports'
include ':domain:usecases'
include ':infrastructure:driven-adapters:r2dbc-persistence'
include ':infrastructure:driven-adapters:{name}-client-api'
include ':infrastructure:entry-points:reactive-web'
include ':infrastructure:helpers'
include ':application:app-service'

// Mock de librerías corporativas — SIEMPRE incluido
include '{client}-lib-mocks'
project(':{client}-lib-mocks').projectDir = file('{client}-lib-mocks')
```

### build.gradle por módulo

**domain/ports:**
```groovy
dependencies {
    implementation project(':domain:model')
    implementation 'io.projectreactor:reactor-core'
}
```

**domain/usecases:**
```groovy
dependencies {
    implementation project(':domain:model')
    implementation project(':domain:ports')
    implementation 'io.projectreactor:reactor-core'
}
```

**infrastructure/driven-adapters/r2dbc-persistence:**
```groovy
apply plugin: 'org.springframework.boot'
apply plugin: 'io.spring.dependency-management'
bootJar { enabled = false }
jar { enabled = true }

dependencies {
    implementation project(':domain:model')
    implementation project(':domain:ports')
    implementation project(':infrastructure:helpers')
    implementation project(':{client}-lib-mocks')
    implementation libs.spring.boot.r2dbc
    runtimeOnly libs.r2dbc.postgresql
}
```

**infrastructure/entry-points/reactive-web:**
```groovy
apply plugin: 'org.springframework.boot'
apply plugin: 'io.spring.dependency-management'
bootJar { enabled = false }
jar { enabled = true }

dependencies {
    implementation project(':domain:model')
    implementation project(':domain:ports')
    implementation project(':domain:usecases')
    implementation project(':infrastructure:helpers')
    implementation project(':{client}-lib-mocks')
    implementation libs.spring.boot.webflux
}
```

**application/app-service:**
```groovy
apply plugin: 'org.springframework.boot'
apply plugin: 'io.spring.dependency-management'

dependencies {
    implementation project(':domain:model')
    implementation project(':domain:ports')
    implementation project(':domain:usecases')
    implementation project(':infrastructure:driven-adapters:r2dbc-persistence')
    implementation project(':infrastructure:driven-adapters:{name}-client-api')
    implementation project(':infrastructure:entry-points:reactive-web')
    implementation project(':infrastructure:helpers')
    implementation project(':{client}-lib-mocks')

    implementation libs.spring.boot.webflux
    implementation libs.spring.boot.r2dbc
    runtimeOnly libs.r2dbc.postgresql
    testImplementation libs.spring.boot.test
    testImplementation libs.reactor.test
}
```

---

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
| **NO** `@RestController` — solo Router + Handler |
| **NO** JPA/Hibernate — solo R2DBC o MongoDB Reactive |
| **NO** `RestTemplate` ni `RestClient` — solo `WebClient` |
| **NO** `.block()` fuera de tests |
