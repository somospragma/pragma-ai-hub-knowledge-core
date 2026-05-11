---
id: backend-skill-java-spring-testing
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: java-spring
---

# Testing — Java Spring

## Propósito

Definir la estrategia de testing completa: unit testing con JUnit 5 + Mockito, integration testing con Testcontainers, configuración JaCoCo, mutation testing con Pitest, y OWASP dependency check.

---

## 1. Unit Testing (JUnit 5 + Mockito)

### Dependencias

```groovy
testImplementation 'org.junit.jupiter:junit-jupiter:5.10.0'
testImplementation 'org.mockito:mockito-core:5.5.0'
testImplementation 'org.mockito:mockito-junit-jupiter:5.5.0'
testImplementation 'org.assertj:assertj-core:3.24.2'
```

### Test de UseCase

```java
@ExtendWith(MockitoExtension.class)
class CreateAccountUseCaseTest {

    @Mock
    private IAccountGateway accountGateway;

    @InjectMocks
    private CreateAccountUseCase createAccountUseCase;

    @Captor
    private ArgumentCaptor<Account> accountCaptor;

    @Test
    @DisplayName("Debe crear cuenta exitosamente")
    void shouldCreateAccountSuccessfully() {
        // Arrange
        Account savedAccount = Account.builder()
            .id("acc-123")
            .holderName("John Doe")
            .holderDocument("12345678")
            .balance(BigDecimal.ZERO)
            .status("ACTIVE")
            .build();

        when(accountGateway.save(any(Account.class))).thenReturn(savedAccount);

        // Act
        Account result = createAccountUseCase.execute("John Doe", "12345678");

        // Assert
        assertThat(result).isNotNull();
        assertThat(result.getId()).isEqualTo("acc-123");
        assertThat(result.getStatus()).isEqualTo("ACTIVE");

        verify(accountGateway).save(accountCaptor.capture());
        assertThat(accountCaptor.getValue().getHolderName()).isEqualTo("John Doe");
    }

    @Test
    @DisplayName("Debe lanzar excepción cuando cuenta no existe")
    void shouldThrowWhenAccountNotFound() {
        when(accountGateway.findById("non-existent")).thenReturn(Optional.empty());

        assertThatThrownBy(() -> new GetAccountUseCase(accountGateway).execute("non-existent"))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("non-existent");
    }
}
```

### Test de Controller (MockMvc)

```java
@WebMvcTest(AccountController.class)
class AccountControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private CreateAccountUseCase createAccountUseCase;

    @MockBean
    private GetAccountUseCase getAccountUseCase;

    @Test
    @DisplayName("POST /api/accounts debe crear cuenta y retornar 201")
    void shouldCreateAccount() throws Exception {
        Account account = Account.builder().id("acc-123").holderName("John").build();
        when(createAccountUseCase.execute(anyString(), anyString())).thenReturn(account);

        mockMvc.perform(post("/api/accounts")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {"holderName": "John", "holderDocument": "12345678"}
                    """))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.id").value("acc-123"));
    }

    @Test
    @DisplayName("POST /api/accounts con datos inválidos debe retornar 400")
    void shouldReturnBadRequestForInvalidData() throws Exception {
        mockMvc.perform(post("/api/accounts")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {"holderName": "", "holderDocument": ""}
                    """))
            .andExpect(status().isBadRequest());
    }
}
```

### Tests Parametrizados

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
    if (isValid) {
        assertThatCode(() -> validationService.validateEmail(email))
            .doesNotThrowAnyException();
    } else {
        assertThatThrownBy(() -> validationService.validateEmail(email))
            .isInstanceOf(ValidationException.class);
    }
}
```

---

## 2. Integration Testing (Testcontainers)

### Dependencias

```groovy
testImplementation 'org.testcontainers:testcontainers:1.19.0'
testImplementation 'org.testcontainers:junit-jupiter:1.19.0'
testImplementation 'org.testcontainers:postgresql:1.19.0'
testImplementation 'org.testcontainers:localstack:1.19.0'
testImplementation 'org.springframework.boot:spring-boot-starter-test'
```

### Test con PostgreSQL

```java
@SpringBootTest
@Testcontainers
@ActiveProfiles("test")
class OrderRepositoryIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15")
        .withDatabaseName("testdb")
        .withUsername("test")
        .withPassword("test");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired
    private OrderRepository orderRepository;

    @BeforeEach
    void setup() { orderRepository.deleteAll(); }

    @Test
    void shouldSaveAndRetrieveOrder() {
        Order order = Order.builder()
            .customerId("cust-123")
            .status("PENDING")
            .totalAmount(new BigDecimal("100.00"))
            .build();

        Order saved = orderRepository.save(order);
        Optional<Order> found = orderRepository.findById(saved.getId());

        assertThat(found).isPresent();
        assertThat(found.get().getCustomerId()).isEqualTo("cust-123");
    }
}
```

### Test de API Completo

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@Testcontainers
class OrderApiIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired
    private TestRestTemplate restTemplate;

    @Test
    void shouldCreateOrderEndToEnd() {
        var request = Map.of("customerId", "cust-123", "amount", 100.00);

        ResponseEntity<Map> response = restTemplate.postForEntity(
            "/api/v1/orders", request, Map.class);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(response.getBody()).containsKey("id");
    }
}
```

### Test con LocalStack (AWS)

```java
@SpringBootTest
@Testcontainers
class SqsIntegrationTest {

    @Container
    static LocalStackContainer localstack = new LocalStackContainer(
            DockerImageName.parse("localstack/localstack:3.0"))
        .withServices(LocalStackContainer.Service.SQS);

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("aws.sqs.endpoint", () -> localstack.getEndpointOverride(SQS));
        registry.add("aws.region", localstack::getRegion);
    }

    @Test
    void shouldPublishAndConsumeMessage() {
        // Test de integración con SQS real (LocalStack)
    }
}
```

---

## 3. Configuración JaCoCo

### En main.gradle

```groovy
apply plugin: 'jacoco'

jacoco { toolVersion = "${jacocoPluginVersion}" }

jacocoTestReport {
    dependsOn test
    reports {
        xml.required = true
        html.required = true
    }
}

jacocoTestCoverageVerification {
    violationRules {
        rule {
            limit { minimum = 0.85 }
        }
    }
}

test.finalizedBy jacocoTestReport
```

### Exclusiones de Cobertura

Las siguientes clases se excluyen del cálculo de cobertura:
- `**/config/**`
- `**/model/**`
- `**/dto/**`
- `**/mapper/**` (generados por MapStruct)
- `**/*Config.class`
- `**/MainApplication.java`

---

## 4. Mutation Testing con Pitest

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

El reporte se genera en `build/reports/pitest/`.

---

## 5. OWASP Dependency Check

### Configuración en main.gradle

```groovy
dependencyCheck {
    formats = ['HTML', 'JSON', 'XML']
    failBuildOnCVSS = 11  // Solo reportar, no fallar el build
    scanConfigurations = ['runtimeClasspath']
}
```

### Ejecución

```bash
./gradlew dependencyCheckAnalyze
```

---

## 6. Test con RestTestClient (Spring Boot 4)

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureRestTestClient
class AccountControllerIntegrationTest {

    @Autowired
    private RestTestClient restTestClient;

    @Test
    void shouldCreateAccount() {
        restTestClient.post()
            .uri("/api/accounts")
            .body(new CreateAccountRequest("John", "12345678"))
            .exchange()
            .expectStatus().isCreated()
            .expectBody(AccountResponse.class)
            .value(response -> assertThat(response.holderName()).isEqualTo("John"));
    }
}
```

---

## Reglas Importantes

- Mantener tests independientes entre sí.
- Seguir patrón AAA (Arrange-Act-Assert).
- Mockear dependencias externas, no el código bajo test.
- Cobertura mínima de 85% en líneas.
- Un assert principal por test.
- No testear código de terceros (frameworks, librerías).
- Testear comportamiento, no implementación.
- Usar `@DisplayName` descriptivo que explique el escenario.
- Limpiar datos entre tests en integration testing.
- Usar Testcontainers para dependencias reales en integration tests.
