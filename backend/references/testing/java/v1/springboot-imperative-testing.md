<!-- keywords: testing, spring mvc, mockmvc, junit 5, imperative, controller test, java -->
# Testing Patterns — Java Imperative (Spring MVC)

## Purpose

Provide standard testing patterns for imperative Java microservices using MockMvc and JUnit 5.

## Dependencies

```toml
# gradle/libs.versions.toml
[libraries]
spring-boot-starter-test = { module = "org.springframework.boot:spring-boot-starter-test" }
```

```groovy
// application/app-service/build.gradle
testImplementation libs.spring.boot.starter.test
```

---

## Unit testing use cases

```java
@ExtendWith(MockitoExtension.class)
class CreateAccountUseCaseTest {

    @Mock
    private AccountGateway accountGateway;

    @InjectMocks
    private CreateAccountUseCase useCase;

    @Test
    void shouldCreateAccountSuccessfully() {
        Account expected = Account.builder()
            .id("acc-123")
            .holderName("John Doe")
            .holderDocument("12345678")
            .balance(BigDecimal.ZERO)
            .status("ACTIVE")
            .build();

        when(accountGateway.save(any(Account.class))).thenReturn(expected);

        Account result = useCase.execute("John Doe", "12345678");

        assertThat(result.getId()).isEqualTo("acc-123");
        assertThat(result.getStatus()).isEqualTo("ACTIVE");
        assertThat(result.getBalance()).isEqualTo(BigDecimal.ZERO);
        verify(accountGateway).save(any(Account.class));
    }
}
```

```java
@ExtendWith(MockitoExtension.class)
class GetAccountUseCaseTest {

    @Mock
    private AccountGateway accountGateway;

    @InjectMocks
    private GetAccountUseCase useCase;

    @Test
    void shouldReturnAccountWhenFound() {
        Account account = Account.builder().id("acc-123").holderName("John").build();
        when(accountGateway.findById("acc-123")).thenReturn(Optional.of(account));

        Account result = useCase.execute("acc-123");

        assertThat(result.getHolderName()).isEqualTo("John");
    }

    @Test
    void shouldThrowWhenNotFound() {
        when(accountGateway.findById("missing")).thenReturn(Optional.empty());

        assertThatThrownBy(() -> useCase.execute("missing"))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("Account not found");
    }
}
```

## Integration testing controllers with MockMvc

```java
@WebMvcTest(AccountController.class)
@Import(UseCaseConfig.class)
class AccountControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private AccountGateway accountGateway;

    @Test
    void shouldReturnAccountById() throws Exception {
        Account account = Account.builder()
            .id("acc-123").holderName("John").holderDocument("12345678")
            .balance(BigDecimal.valueOf(1000)).status("ACTIVE")
            .createdAt(LocalDateTime.now()).build();

        when(accountGateway.findById("acc-123")).thenReturn(Optional.of(account));

        mockMvc.perform(get("/api/accounts/acc-123"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value("acc-123"))
            .andExpect(jsonPath("$.holderName").value("John"));
    }

    @Test
    void shouldReturn404WhenNotFound() throws Exception {
        when(accountGateway.findById("missing")).thenReturn(Optional.empty());

        mockMvc.perform(get("/api/accounts/missing"))
            .andExpect(status().isNotFound());
    }

    @Test
    void shouldCreateAccount() throws Exception {
        Account created = Account.builder()
            .id("acc-456").holderName("Jane").status("ACTIVE").build();

        when(accountGateway.save(any())).thenReturn(created);

        mockMvc.perform(post("/api/accounts")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {"holderName": "Jane", "holderDocument": "87654321"}
                    """))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.id").value("acc-456"));
    }

    @Test
    void shouldReturn400WhenValidationFails() throws Exception {
        mockMvc.perform(post("/api/accounts")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {"holderName": "", "holderDocument": ""}
                    """))
            .andExpect(status().isBadRequest());
    }
}
```

## Key rules

- Use `MockMvc` for controller integration tests (NOT `TestRestTemplate`).
- Use `@WebMvcTest` (NOT `@SpringBootTest`) for controller tests — it only loads the web layer.
- Mock gateways with `@MockBean` in integration tests.
- Test validation errors (400), not-found (404), and happy path (200/201).
- Use `jsonPath` for response body assertions.
- Use `assertThatThrownBy` (AssertJ) for exception testing in use cases.

## Scope of Application

_(No additional information required for this section.)_

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
