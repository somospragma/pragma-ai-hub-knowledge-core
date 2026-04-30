<!-- keywords: testing, webflux, reactive, stepverifier, webtestclient, project reactor, java -->
# Testing Patterns — Java Reactive (WebFlux)

## Purpose

Provide standard testing patterns for reactive Java microservices using StepVerifier and WebTestClient.

## Dependencies

```toml
# gradle/libs.versions.toml
[libraries]
spring-boot-test = { module = "org.springframework.boot:spring-boot-starter-test" }
reactor-test = { module = "io.projectreactor:reactor-test" }
```

```groovy
// application/app-service/build.gradle
testImplementation libs.spring.boot.test
testImplementation libs.reactor.test
```

---

## Unit testing use cases with StepVerifier

```java
@ExtendWith(MockitoExtension.class)
class CreateAccountUseCaseTest {

    @Mock
    private AccountGateway accountGateway;

    @InjectMocks
    private CreateAccountUseCase useCase;

    @Test
    void shouldCreateAccountSuccessfully() {
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

        StepVerifier.create(useCase.execute(input))
            .assertNext(result -> {
                assertThat(result.getId()).isEqualTo("acc-123");
                assertThat(result.getStatus()).isEqualTo("ACTIVE");
                assertThat(result.getCreatedAt()).isNotNull();
            })
            .verifyComplete();
    }

    @Test
    void shouldPropagateErrorWhenGatewayFails() {
        Account input = Account.builder().holderName("Jane").build();
        when(accountGateway.save(any())).thenReturn(Mono.error(new RuntimeException("DB error")));

        StepVerifier.create(useCase.execute(input))
            .expectErrorMatches(e -> e.getMessage().equals("DB error"))
            .verify();
    }
}
```

## Integration testing routes with WebTestClient

```java
@WebFluxTest
@Import({AccountRouter.class, AccountHandler.class, UseCaseConfig.class})
class AccountRouterTest {

    @Autowired
    private WebTestClient webTestClient;

    @MockBean
    private AccountGateway accountGateway;

    @Test
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
    void shouldReturn404WhenNotFound() {
        when(accountGateway.findById("missing")).thenReturn(Mono.empty());

        webTestClient.get()
            .uri("/api/v1/accounts/missing")
            .exchange()
            .expectStatus().isNotFound();
    }

    @Test
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
}
```

## Key rules

- Use `StepVerifier` for all reactive unit tests (use cases, adapters).
- Use `WebTestClient` for integration tests of routes.
- Use `@WebFluxTest` (NOT `@SpringBootTest`) for route tests — it only loads the web layer.
- Mock gateways with `@MockBean` in integration tests.
- Never use `.block()` in tests — always `StepVerifier`.
- Test both happy path and error scenarios (`expectError`, `expectErrorMatches`).

## Scope of Application

_(No additional information required for this section.)_

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
