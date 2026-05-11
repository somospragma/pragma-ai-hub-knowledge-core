---
id: backend-skill-java-webflux-testing
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: java-webflux
---

# Testing — Java WebFlux (Reactivo)

## Propósito

Definir la estrategia de testing completa para microservicios reactivos: unit testing con StepVerifier, integration testing con WebTestClient, Testcontainers con R2DBC, BlockHound para detectar código bloqueante, configuración JaCoCo y mutation testing con Pitest.

---

## 1. Unit Testing con StepVerifier (Obligatorio)

### Dependencias

```groovy
testImplementation 'org.springframework.boot:spring-boot-starter-test'
testImplementation 'io.projectreactor:reactor-test'
testImplementation 'org.mockito:mockito-core:5.5.0'
testImplementation 'org.mockito:mockito-junit-jupiter:5.5.0'
testImplementation 'org.assertj:assertj-core:3.24.2'
```

### Test de UseCase con StepVerifier

```java
@ExtendWith(MockitoExtension.class)
class CreateAccountUseCaseTest {

    @Mock
    private IAccountGateway accountGateway;

    @InjectMocks
    private CreateAccountUseCase useCase;

    @Test
    @DisplayName("Debe crear cuenta exitosamente")
    void shouldCreateAccountSuccessfully() {
        // Arrange
        Account input = Account.builder()
            .holderName("John Doe")
            .accountType("SAVINGS")
            .balance(BigDecimal.valueOf(1000))
            .build();

        Account saved = Account.builder()
            .id("acc-123")
            .holderName("John Doe")
            .accountType("SAVINGS")
            .balance(BigDecimal.valueOf(1000))
            .status("ACTIVE")
            .createdAt(LocalDateTime.now())
            .build();

        when(accountGateway.save(any(Account.class))).thenReturn(Mono.just(saved));

        // Act & Assert
        StepVerifier.create(useCase.execute(input))
            .assertNext(result -> {
                assertThat(result.getId()).isEqualTo("acc-123");
                assertThat(result.getStatus()).isEqualTo("ACTIVE");
                assertThat(result.getCreatedAt()).isNotNull();
            })
            .verifyComplete();
    }

    @Test
    @DisplayName("Debe propagar error cuando gateway falla")
    void shouldPropagateErrorWhenGatewayFails() {
        Account input = Account.builder().holderName("Jane").build();
        when(accountGateway.save(any())).thenReturn(Mono.error(new RuntimeException("DB error")));

        StepVerifier.create(useCase.execute(input))
            .expectErrorMatches(e -> e.getMessage().equals("DB error"))
            .verify();
    }

    @Test
    @DisplayName("Debe retornar error cuando cuenta no existe")
    void shouldReturnErrorWhenAccountNotFound() {
        when(accountGateway.findById("non-existent")).thenReturn(Mono.empty());

        StepVerifier.create(new GetAccountUseCase(accountGateway).execute("non-existent"))
            .expectError(AccountNotFoundException.class)
            .verify();
    }
}
```

### Test de Flux con StepVerifier

```java
@ExtendWith(MockitoExtension.class)
class GetAccountUseCaseTest {

    @Mock
    private IAccountGateway accountGateway;

    @InjectMocks
    private GetAccountUseCase useCase;

    @Test
    @DisplayName("Debe retornar todas las cuentas")
    void shouldReturnAllAccounts() {
        Account acc1 = Account.builder().id("acc-1").holderName("John").build();
        Account acc2 = Account.builder().id("acc-2").holderName("Jane").build();

        when(accountGateway.findAll()).thenReturn(Flux.just(acc1, acc2));

        StepVerifier.create(useCase.findAll())
            .expectNext(acc1)
            .expectNext(acc2)
            .verifyComplete();
    }

    @Test
    @DisplayName("Debe retornar Flux vacío cuando no hay cuentas")
    void shouldReturnEmptyFlux() {
        when(accountGateway.findAll()).thenReturn(Flux.empty());

        StepVerifier.create(useCase.findAll())
            .expectNextCount(0)
            .verifyComplete();
    }
}
```

### Test de Adapter R2DBC con StepVerifier

```java
@ExtendWith(MockitoExtension.class)
class AccountR2dbcAdapterTest {

    @Mock
    private AccountR2dbcRepository r2dbcRepository;

    @Mock
    private AccountEntityMapper mapper;

    @InjectMocks
    private AccountR2dbcAdapter adapter;

    @Test
    @DisplayName("Debe guardar y mapear entidad correctamente")
    void shouldSaveAndMapEntity() {
        Account account = Account.builder().holderName("John").build();
        AccountEntity entity = new AccountEntity();
        entity.setId("acc-123");
        AccountEntity savedEntity = new AccountEntity();
        savedEntity.setId("acc-123");

        when(mapper.toEntity(account)).thenReturn(entity);
        when(r2dbcRepository.save(entity)).thenReturn(Mono.just(savedEntity));
        when(mapper.toModel(savedEntity)).thenReturn(
            Account.builder().id("acc-123").holderName("John").build());

        StepVerifier.create(adapter.save(account))
            .assertNext(result -> assertThat(result.getId()).isEqualTo("acc-123"))
            .verifyComplete();
    }
}
```

---

## 2. Integration Testing con WebTestClient

### Test de Rutas con `@WebFluxTest`

```java
@WebFluxTest
@Import({AccountRouter.class, AccountHandler.class, UseCasesConfig.class})
class AccountRouterTest {

    @Autowired
    private WebTestClient webTestClient;

    @MockBean
    private IAccountGateway accountGateway;

    @Test
    @DisplayName("GET /api/v1/accounts/{id} debe retornar cuenta")
    void shouldReturnAccountById() {
        Account account = Account.builder()
            .id("acc-123").holderName("John").status("ACTIVE").build();

        when(accountGateway.findById("acc-123")).thenReturn(Mono.just(account));

        webTestClient.get()
            .uri("/api/v1/accounts/acc-123")
            .exchange()
            .expectStatus().isOk()
            .expectBody()
            .jsonPath("$.id").isEqualTo("acc-123")
            .jsonPath("$.holderName").isEqualTo("John");
    }

    @Test
    @DisplayName("GET /api/v1/accounts/{id} debe retornar 404 cuando no existe")
    void shouldReturn404WhenNotFound() {
        when(accountGateway.findById("missing")).thenReturn(Mono.empty());

        webTestClient.get()
            .uri("/api/v1/accounts/missing")
            .exchange()
            .expectStatus().isNotFound();
    }

    @Test
    @DisplayName("POST /api/v1/accounts debe crear cuenta y retornar 201")
    void shouldCreateAccount() {
        Account created = Account.builder()
            .id("acc-456").holderName("Jane").status("ACTIVE").build();

        when(accountGateway.save(any())).thenReturn(Mono.just(created));

        webTestClient.post()
            .uri("/api/v1/accounts")
            .contentType(MediaType.APPLICATION_JSON)
            .bodyValue("""
                {"holderName": "Jane", "accountType": "SAVINGS", "initialBalance": 500}
                """)
            .exchange()
            .expectStatus().isCreated()
            .expectBody()
            .jsonPath("$.id").isEqualTo("acc-456");
    }

    @Test
    @DisplayName("POST /api/v1/accounts con datos inválidos debe retornar 400")
    void shouldReturnBadRequestForInvalidData() {
        webTestClient.post()
            .uri("/api/v1/accounts")
            .contentType(MediaType.APPLICATION_JSON)
            .bodyValue("""
                {"holderName": "", "accountType": ""}
                """)
            .exchange()
            .expectStatus().isBadRequest();
    }
}
```

### Test de API Completo con `@SpringBootTest`

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@Testcontainers
class AccountApiIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.r2dbc.url", () ->
            "r2dbc:postgresql://" + postgres.getHost() + ":" + postgres.getFirstMappedPort()
                + "/" + postgres.getDatabaseName());
        registry.add("spring.r2dbc.username", postgres::getUsername);
        registry.add("spring.r2dbc.password", postgres::getPassword);
    }

    @Autowired
    private WebTestClient webTestClient;

    @Test
    void shouldCreateAccountEndToEnd() {
        webTestClient.post()
            .uri("/api/v1/accounts")
            .contentType(MediaType.APPLICATION_JSON)
            .bodyValue("""
                {"holderName": "John Doe", "accountType": "SAVINGS", "initialBalance": 1000}
                """)
            .exchange()
            .expectStatus().isCreated()
            .expectBody()
            .jsonPath("$.id").isNotEmpty()
            .jsonPath("$.status").isEqualTo("ACTIVE");
    }
}
```

---

## 3. Testcontainers con R2DBC

### Dependencias

```groovy
testImplementation 'org.testcontainers:testcontainers:1.19.0'
testImplementation 'org.testcontainers:junit-jupiter:1.19.0'
testImplementation 'org.testcontainers:postgresql:1.19.0'
testImplementation 'org.testcontainers:r2dbc:1.19.0'
testImplementation 'org.testcontainers:localstack:1.19.0'
```

### Test de Repository R2DBC con Testcontainers

```java
@DataR2dbcTest
@Testcontainers
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
class CustomerR2dbcRepositoryTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15")
        .withDatabaseName("testdb")
        .withUsername("test")
        .withPassword("test")
        .withInitScript("schema.sql");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.r2dbc.url", () ->
            "r2dbc:postgresql://" + postgres.getHost() + ":" + postgres.getFirstMappedPort()
                + "/" + postgres.getDatabaseName());
        registry.add("spring.r2dbc.username", postgres::getUsername);
        registry.add("spring.r2dbc.password", postgres::getPassword);
    }

    @Autowired
    private CustomerR2dbcRepository repository;

    @Test
    void shouldSaveAndRetrieveCustomer() {
        CustomerEntity entity = CustomerEntity.builder()
            .id(UUID.randomUUID().toString())
            .name("John Doe")
            .email("john@example.com")
            .status("ACTIVE")
            .createdAt(LocalDateTime.now())
            .build();

        StepVerifier.create(repository.save(entity))
            .assertNext(saved -> assertThat(saved.getId()).isNotNull())
            .verifyComplete();

        StepVerifier.create(repository.findById(entity.getId()))
            .assertNext(found -> {
                assertThat(found.getName()).isEqualTo("John Doe");
                assertThat(found.getEmail()).isEqualTo("john@example.com");
            })
            .verifyComplete();
    }

    @Test
    void shouldFindByStatus() {
        // Insertar datos de prueba
        CustomerEntity active = CustomerEntity.builder()
            .id("cust-1").name("Active").status("ACTIVE").build();
        CustomerEntity inactive = CustomerEntity.builder()
            .id("cust-2").name("Inactive").status("INACTIVE").build();

        StepVerifier.create(
            repository.save(active)
                .then(repository.save(inactive))
                .thenMany(repository.findByStatus("ACTIVE"))
        )
            .assertNext(found -> assertThat(found.getStatus()).isEqualTo("ACTIVE"))
            .verifyComplete();
    }
}
```

---

## 4. BlockHound (Detección de Código Bloqueante)

### Dependencia

```groovy
testImplementation 'io.projectreactor.tools:blockhound:1.0.9.RELEASE'
```

### Activación en Tests

```java
@BeforeAll
static void installBlockHound() {
    BlockHound.install();
}
```

### Test que Detecta Bloqueo

```java
class BlockingDetectionTest {

    @BeforeAll
    static void setup() {
        BlockHound.install();
    }

    @Test
    @DisplayName("Debe detectar llamadas bloqueantes en el pipeline reactivo")
    void shouldDetectBlockingCalls() {
        Mono<String> blockingMono = Mono.fromCallable(() -> {
            Thread.sleep(10); // Esto es bloqueante!
            return "result";
        }).subscribeOn(Schedulers.parallel()); // parallel NO permite bloqueo

        StepVerifier.create(blockingMono)
            .expectError(BlockingOperationError.class)
            .verify();
    }

    @Test
    @DisplayName("Debe permitir bloqueo en boundedElastic")
    void shouldAllowBlockingOnBoundedElastic() {
        Mono<String> safeMono = Mono.fromCallable(() -> {
            Thread.sleep(10);
            return "result";
        }).subscribeOn(Schedulers.boundedElastic()); // boundedElastic SÍ permite bloqueo

        StepVerifier.create(safeMono)
            .expectNext("result")
            .verifyComplete();
    }
}
```

### Configuración de BlockHound para el Proyecto

```java
public class CustomBlockHoundIntegration implements BlockHoundIntegration {
    @Override
    public void applyTo(BlockHound.Builder builder) {
        // Permitir bloqueo en librerías específicas que lo requieren
        builder.allowBlockingCallsInside("com.zaxxel.hikari.pool.HikariPool", "getConnection");
        builder.allowBlockingCallsInside("io.netty.resolver.dns.DnsNameResolver", "resolve");
    }
}
```

Registrar en `META-INF/services/reactor.blockhound.integration.BlockHoundIntegration`:
```
com.pragma.myservice.test.CustomBlockHoundIntegration
```

---

## 5. Tests Parametrizados

```java
@ParameterizedTest
@CsvSource({
    "john@example.com, true",
    "invalid-email, false",
    "'', false",
    "test@domain.co.uk, true"
})
@DisplayName("Debe validar formato de email")
void shouldValidateEmailFormat(String email, boolean isValid) {
    Mono<String> result = validationService.validateEmail(email);

    if (isValid) {
        StepVerifier.create(result)
            .expectNext(email)
            .verifyComplete();
    } else {
        StepVerifier.create(result)
            .expectError(ValidationException.class)
            .verify();
    }
}
```

---

## 6. Test con Virtual Time (StepVerifier)

Para testear operaciones con delays sin esperar tiempo real:

```java
@Test
@DisplayName("Debe reintentar con backoff exponencial")
void shouldRetryWithExponentialBackoff() {
    AtomicInteger attempts = new AtomicInteger(0);

    Mono<String> retryingMono = Mono.<String>error(new RuntimeException("fail"))
        .doOnError(e -> attempts.incrementAndGet())
        .retryWhen(Retry.backoff(3, Duration.ofSeconds(1)));

    StepVerifier.withVirtualTime(() -> retryingMono)
        .expectSubscription()
        .thenAwait(Duration.ofSeconds(1))  // primer retry
        .thenAwait(Duration.ofSeconds(2))  // segundo retry
        .thenAwait(Duration.ofSeconds(4))  // tercer retry
        .expectError(RetryExhaustedException.class)
        .verify();

    assertThat(attempts.get()).isEqualTo(4); // 1 original + 3 retries
}
```

---

## 7. Configuración JaCoCo

### En main.gradle

```groovy
apply plugin: 'jacoco'

jacoco { toolVersion = "${jacocoPluginVersion}" }

jacocoTestReport {
    dependsOn test
    reports { xml.required = true; html.required = true }
}

jacocoTestCoverageVerification {
    violationRules {
        rule { limit { minimum = 0.85 } }
    }
}

test.finalizedBy jacocoTestReport
```

### Exclusiones de Cobertura

- `**/config/**`
- `**/model/**`
- `**/dto/**`
- `**/mapper/**` (generados por MapStruct)
- `**/*MapperImpl.class`
- `**/MainApplication.java`

---

## 8. Mutation Testing con Pitest

### Configuración en main.gradle

```groovy
apply plugin: 'info.solidsoft.pitest'

pitest {
    targetClasses = ["${project.group}.*"]
    threads = 8
    outputFormats = ['XML', 'HTML']
    junit5PluginVersion = '1.2.1'
    mutationThreshold = 20
}
```

### Ejecución

```bash
./gradlew pitest
```

---

## 9. OWASP Dependency Check

### Configuración en main.gradle

```groovy
dependencyCheck {
    formats = ['HTML', 'JSON', 'XML']
    failBuildOnCVSS = 11
    scanConfigurations = ['runtimeClasspath']
}
```

---

## Reglas Importantes

- **StepVerifier es OBLIGATORIO** para todos los tests de código reactivo.
- Usar `WebTestClient` para integration tests de rutas (NO `MockMvc`).
- Usar `@WebFluxTest` (NO `@WebMvcTest`) para tests de capa web.
- **NUNCA** usar `.block()` en tests — siempre `StepVerifier`.
- Instalar BlockHound en tests para detectar código bloqueante.
- Usar `StepVerifier.withVirtualTime()` para tests con delays.
- Mantener tests independientes entre sí.
- Seguir patrón AAA (Arrange-Act-Assert).
- Mockear gateways con `@MockBean` en integration tests.
- Cobertura mínima de 85% en líneas.
- Usar `@DisplayName` descriptivo que explique el escenario.
- Testear tanto happy path como escenarios de error (`expectError`).
- Usar Testcontainers con R2DBC para integration tests con base de datos real.
