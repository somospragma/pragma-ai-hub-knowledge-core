<!-- keywords: integration testing, testcontainers, localstack, spring boot test, java -->
# Integration Testing Patterns — Java Implementation

## Purpose

Define the principles and strategies for integration testing in Java, ensuring that system components work correctly together with real or simulated dependencies, using Testcontainers, LocalStack, and Spring Boot Test.

## Scope of Application

- When implementing integration tests with databases
- When testing integrations with external services
- When implementing contract testing between services
- When testing REST APIs end-to-end
- When configuring isolated test environments

## Main content

### Difference between Unit and Integration Tests

```
┌─────────────────────────────────────────────────────────────┐
│                    UNIT TESTS                                │
├─────────────────────────────────────────────────────────────┤
│  - Test an isolated unit                                    │
│  - Dependencies are mocked                                  │
│  - Fast execution (milliseconds)                            │
│  - No external I/O                                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 INTEGRATION TESTS                            │
├─────────────────────────────────────────────────────────────┤
│  - Test interaction between components                      │
│  - Real dependencies or containers                          │
│  - Slower execution (seconds)                               │
│  - Includes I/O (DB, APIs, messaging)                       │
└─────────────────────────────────────────────────────────────┘
```

### Integration Testing Strategies

| Strategy | Description | Usage |
|----------|-------------|-------|
| Testcontainers | Docker containers for dependencies | Databases, caches |
| LocalStack | AWS service emulation | SQS, SNS, S3, DynamoDB |
| WireMock | HTTP API mock | External services |
| Contract Testing | Contract verification | Microservices |
| In-Memory | In-memory implementations | Fast tests |

### Test lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│  1. SETUP     - Start containers, configure connections     │
│  2. ARRANGE   - Insert test data                            │
│  3. ACT       - Execute operation                           │
│  4. ASSERT    - Verify results and state in DB              │
│  5. CLEANUP   - Clean up test data                          │
│  6. TEARDOWN  - Stop containers, release resources          │
└─────────────────────────────────────────────────────────────┘
```

### Contract Testing

```
┌─────────────────────────────────────────────────────────────┐
│  Consumer ──────────────────────────────► Provider          │
│     │  1. Define expectations                  │             │
│     │  2. Generate contract                    │             │
│     └──────────► Contract ◄────────────────────┘             │
│                     │  3. Provider verifies compliance       │
│                     ▼                                        │
│              ┌──────────────┐                               │
│              │   Pact Broker │                               │
│              └──────────────┘                               │
└─────────────────────────────────────────────────────────────┘
```

## Libraries and dependencies

```groovy
// build.gradle
dependencies {
    testImplementation 'org.springframework.boot:spring-boot-starter-test'
    testImplementation 'org.testcontainers:testcontainers:1.19.0'
    testImplementation 'org.testcontainers:junit-jupiter:1.19.0'
    testImplementation 'org.testcontainers:postgresql:1.19.0'
    testImplementation 'org.testcontainers:localstack:1.19.0'
    testImplementation 'au.com.dius.pact.consumer:junit5:4.6.0'
}
```

## Step by Step / Guidelines

### Test with PostgreSQL Testcontainer

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
    void setup() {
        orderRepository.deleteAll();
    }
    
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

### Test with LocalStack (SQS/SNS)

```java
@SpringBootTest
@Testcontainers
class SqsIntegrationTest {
    
    @Container
    static LocalStackContainer localstack = new LocalStackContainer(
            DockerImageName.parse("localstack/localstack:3.0"))
        .withServices(LocalStackContainer.Service.SQS, LocalStackContainer.Service.SNS);
    
    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("aws.sqs.endpoint", () -> localstack.getEndpointOverride(SQS));
        registry.add("aws.sns.endpoint", () -> localstack.getEndpointOverride(SNS));
        registry.add("aws.region", () -> localstack.getRegion());
        registry.add("aws.accessKeyId", () -> localstack.getAccessKey());
        registry.add("aws.secretKey", () -> localstack.getSecretKey());
    }
    
    @Autowired
    private SqsTemplate sqsTemplate;
    
    @Autowired
    private OrderEventPublisher eventPublisher;
    
    @BeforeEach
    void setup() {
        sqsTemplate.send("order-events", "test");
    }
    
    @Test
    void shouldPublishOrderEvent() {
        OrderEvent event = new OrderEvent("ord-123", "CREATED");
        
        eventPublisher.publish(event);
        
        Message<?> message = sqsTemplate.receive("order-events", Duration.ofSeconds(5));
        assertThat(message).isNotNull();
        assertThat(message.getPayload()).contains("ord-123");
    }
}
```

### API Integration Test

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
    
    @LocalServerPort
    private int port;
    
    @Autowired
    private TestRestTemplate restTemplate;
    
    @Autowired
    private OrderRepository orderRepository;
    
    @BeforeEach
    void setup() {
        orderRepository.deleteAll();
    }
    
    @Test
    void shouldCreateOrder() {
        OrderRequest request = OrderRequest.builder()
            .customerId("cust-123")
            .items(List.of(
                OrderItemRequest.builder()
                    .productId("prod-1")
                    .quantity(2)
                    .unitPrice(new BigDecimal("25.00"))
                    .build()
            ))
            .currency("USD")
            .build();
        
        ResponseEntity<OrderResponse> response = restTemplate.postForEntity(
            "/api/v1/orders",
            request,
            OrderResponse.class
        );
        
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(response.getBody()).isNotNull();
        assertThat(response.getBody().getCustomerId()).isEqualTo("cust-123");
        assertThat(response.getBody().getTotalAmount()).isEqualByComparingTo("50.00");
    }
    
    @Test
    void shouldReturnValidationError() {
        OrderRequest invalidRequest = OrderRequest.builder()
            .customerId("")
            .items(List.of())
            .build();
        
        ResponseEntity<ProblemDetail> response = restTemplate.postForEntity(
            "/api/v1/orders",
            invalidRequest,
            ProblemDetail.class
        );
        
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(response.getBody().getTitle()).isEqualTo("Validation Error");
    }
}
```

### WebTestClient for WebFlux

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class OrderApiWebFluxTest {
    
    @Autowired
    private WebTestClient webTestClient;
    
    @Test
    void shouldCreateOrderReactive() {
        OrderRequest request = createValidRequest();
        
        webTestClient.post()
            .uri("/api/v1/orders")
            .contentType(MediaType.APPLICATION_JSON)
            .bodyValue(request)
            .exchange()
            .expectStatus().isCreated()
            .expectBody(OrderResponse.class)
            .value(response -> {
                assertThat(response.getCustomerId()).isEqualTo("cust-123");
            });
    }
}
```

### Contract Testing with Pact

```java
@ExtendWith(PactConsumerTestExt.class)
class PaymentClientContractTest {
    
    @Pact(consumer = "order-service", provider = "payment-service")
    public RequestResponsePact createPaymentPact(PactDslWithProvider builder) {
        return builder
            .given("customer exists")
            .uponReceiving("a payment request")
            .path("/payments")
            .method("POST")
            .body(new PactDslJsonBody()
                .stringType("customerId", "cust-123")
                .decimalType("amount", 100.00))
            .willRespondWith()
            .status(201)
            .body(new PactDslJsonBody()
                .stringType("paymentId")
                .stringValue("status", "COMPLETED"))
            .toPact();
    }
    
    @Test
    @PactTestFor(pactMethod = "createPaymentPact")
    void shouldProcessPayment(MockServer mockServer) {
        PaymentClient client = new PaymentClient(mockServer.getUrl());
        
        PaymentResult result = client.processPayment("cust-123", new BigDecimal("100.00"));
        
        assertThat(result.getStatus()).isEqualTo("COMPLETED");
    }
}
```

## Configuration

### application-test.yml

```yaml
spring:
  datasource:
    driver-class-name: org.postgresql.Driver
  jpa:
    hibernate:
      ddl-auto: create-drop
    show-sql: true

logging:
  level:
    org.testcontainers: INFO
    com.github.dockerjava: WARN
```

## Mocks and fixtures

### Base Test Class

```java
@SpringBootTest
@Testcontainers
@ActiveProfiles("test")
public abstract class BaseIntegrationTest {
    
    @Container
    protected static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15")
        .withDatabaseName("testdb")
        .withUsername("test")
        .withPassword("test");
    
    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }
}
```

## Important Rules

1. **Isolation**: Each test must be independent
2. **Cleanup**: Clean data between tests
3. **Containers**: Use Testcontainers for real dependencies
4. **LocalStack**: Use for AWS services
5. **Timeouts**: Configure appropriate timeouts for containers
6. **CI/CD**: Ensure tests run in pipelines
7. **Data**: Use fixtures for consistent test data
8. **Idempotency**: Tests must be able to run multiple times

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
