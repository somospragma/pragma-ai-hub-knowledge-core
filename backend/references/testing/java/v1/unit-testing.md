<!-- keywords: unit testing, junit 5, mockito, assertj, test patterns, mocking, java -->
# Unit Testing Patterns — Java Implementation

## Purpose

Document the fundamental principles, strategies, and patterns for unit testing and implementation in Java with JUnit 5, Mockito, and AssertJ.

## Scope of Application

- When designing the testing strategy for a new project
- To establish testing standards in the team
- When implementing unit tests in Java with Mockito
- When code quality improvement through testing is required

## Main content

### FIRST Principles

```
┌─────────────────────────────────────────────────────────────┐
│                    FIRST PRINCIPLES                          │
├─────────────────────────────────────────────────────────────┤
│  F - Fast: Execute quickly (milliseconds)                   │
│  I - Independent: Do not depend on other tests              │
│  R - Repeatable: Same result on each execution              │
│  S - Self-validating: Automatic Pass/Fail                   │
│  T - Timely: Write before or alongside the code             │
└─────────────────────────────────────────────────────────────┘
```

### AAA Structure (Arrange-Act-Assert)

```
┌─────────────────────────────────────────────────────────────┐
│  ARRANGE - Create objects, configure mocks, input data      │
│  ACT     - Execute the method under test (single action)    │
│  ASSERT  - Verify expected result and interactions          │
└─────────────────────────────────────────────────────────────┘
```

### Types of Test Doubles

```
┌─────────────────────────────────────────────────────────────┐
│  DUMMY: Object that is passed but never used                │
│  STUB: Provides predefined responses                        │
│  SPY: Records information about calls                       │
│  MOCK: Verifies expected behavior                           │
│  FAKE: Simplified functional implementation                 │
└─────────────────────────────────────────────────────────────┘
```

### Test Naming

Naming patterns:
- `should_ReturnError_When_InputIsInvalid`
- `givenInvalidInput_whenValidate_thenThrowException`
- `createCustomer_withValidData_returnsCustomerId`

### Testing Pyramid

```
                    ┌───────────┐
                    │   E2E     │  Few, slow, expensive
                   ─┴───────────┴─
                  ┌───────────────┐
                  │  Integration  │  Moderate
                 ─┴───────────────┴─
                ┌───────────────────┐
                │    Unit Tests     │  Many, fast, cheap
                └───────────────────┘
```

### Coverage Requirements

```yaml
coverage:
  lines: 80%
  branches: 75%
  functions: 80%
  statements: 80%
exclude:
  - "*.dto.*"
  - "*.config.*"
  - "**/main.*"
```

## Libraries and dependencies

```groovy
// build.gradle
dependencies {
    testImplementation 'org.junit.jupiter:junit-jupiter:5.10.0'
    testImplementation 'org.mockito:mockito-core:5.5.0'
    testImplementation 'org.mockito:mockito-junit-jupiter:5.5.0'
    testImplementation 'org.assertj:assertj-core:3.24.2'
}

test {
    useJUnitPlatform()
}
```

```xml
<!-- pom.xml -->
<dependencies>
    <dependency>
        <groupId>org.junit.jupiter</groupId>
        <artifactId>junit-jupiter</artifactId>
        <version>5.10.0</version>
        <scope>test</scope>
    </dependency>
    <dependency>
        <groupId>org.mockito</groupId>
        <artifactId>mockito-core</artifactId>
        <version>5.5.0</version>
        <scope>test</scope>
    </dependency>
    <dependency>
        <groupId>org.mockito</groupId>
        <artifactId>mockito-junit-jupiter</artifactId>
        <version>5.5.0</version>
        <scope>test</scope>
    </dependency>
    <dependency>
        <groupId>org.assertj</groupId>
        <artifactId>assertj-core</artifactId>
        <version>3.24.2</version>
        <scope>test</scope>
    </dependency>
</dependencies>
```

## Step by Step / Guidelines

### Basic test with Mockito

```java
@ExtendWith(MockitoExtension.class)
class CustomerServiceTest {
    
    @Mock
    private CustomerRepository customerRepository;
    
    @Mock
    private NotificationService notificationService;
    
    @InjectMocks
    private CustomerService customerService;
    
    @Captor
    private ArgumentCaptor<Customer> customerCaptor;
    
    @Test
    @DisplayName("Should create customer successfully")
    void shouldCreateCustomerSuccessfully() {
        // Arrange
        CreateCustomerRequest request = new CreateCustomerRequest(
            "John Doe",
            "john@example.com"
        );
        
        Customer savedCustomer = Customer.builder()
            .id("cust-123")
            .name("John Doe")
            .email("john@example.com")
            .status("ACTIVE")
            .build();
        
        when(customerRepository.save(any(Customer.class)))
            .thenReturn(savedCustomer);
        
        // Act
        Customer result = customerService.create(request);
        
        // Assert
        assertThat(result)
            .isNotNull()
            .satisfies(c -> {
                assertThat(c.getId()).isEqualTo("cust-123");
                assertThat(c.getName()).isEqualTo("John Doe");
                assertThat(c.getStatus()).isEqualTo("ACTIVE");
            });
        
        verify(customerRepository).save(customerCaptor.capture());
        assertThat(customerCaptor.getValue().getName()).isEqualTo("John Doe");
        
        verify(notificationService).sendWelcomeEmail("john@example.com");
    }
    
    @Test
    @DisplayName("Should throw exception when customer not found")
    void shouldThrowExceptionWhenCustomerNotFound() {
        // Arrange
        String customerId = "non-existent";
        when(customerRepository.findById(customerId))
            .thenReturn(Optional.empty());
        
        // Act & Assert
        assertThatThrownBy(() -> customerService.findById(customerId))
            .isInstanceOf(CustomerNotFoundException.class)
            .hasMessageContaining(customerId);
        
        verify(customerRepository).findById(customerId);
        verifyNoMoreInteractions(customerRepository);
    }
}
```

### Parameterized tests

```java
@ExtendWith(MockitoExtension.class)
class ValidationServiceTest {
    
    @InjectMocks
    private ValidationService validationService;
    
    @ParameterizedTest
    @ValueSource(strings = {"", " ", "   "})
    @DisplayName("Should reject blank names")
    void shouldRejectBlankNames(String name) {
        CreateCustomerRequest request = new CreateCustomerRequest(name, "email@test.com");
        
        assertThatThrownBy(() -> validationService.validate(request))
            .isInstanceOf(ValidationException.class);
    }
    
    @ParameterizedTest
    @CsvSource({
        "john@example.com, true",
        "invalid-email, false",
        "'', false",
        "test@domain.co.uk, true"
    })
    @DisplayName("Should validate email format")
    void shouldValidateEmailFormat(String email, boolean isValid) {
        if (isValid) {
            assertThatCode(() -> validationService.validateEmail(email))
                .doesNotThrowAnyException();
        } else {
            assertThatThrownBy(() -> validationService.validateEmail(email))
                .isInstanceOf(ValidationException.class);
        }
    }
    
    @ParameterizedTest
    @MethodSource("provideInvalidRequests")
    @DisplayName("Should reject invalid requests")
    void shouldRejectInvalidRequests(CreateCustomerRequest request, String expectedError) {
        assertThatThrownBy(() -> validationService.validate(request))
            .isInstanceOf(ValidationException.class)
            .hasMessageContaining(expectedError);
    }
    
    private static Stream<Arguments> provideInvalidRequests() {
        return Stream.of(
            Arguments.of(new CreateCustomerRequest(null, "email@test.com"), "name"),
            Arguments.of(new CreateCustomerRequest("John", null), "email"),
            Arguments.of(new CreateCustomerRequest("John", "invalid"), "email format")
        );
    }
}
```

### Reactive service test (WebFlux)

```java
@ExtendWith(MockitoExtension.class)
class ReactiveCustomerServiceTest {
    
    @Mock
    private CustomerRepository customerRepository;
    
    @InjectMocks
    private ReactiveCustomerService customerService;
    
    @Test
    @DisplayName("Should find customer by id reactively")
    void shouldFindCustomerByIdReactively() {
        // Arrange
        Customer customer = Customer.builder()
            .id("cust-123")
            .name("John Doe")
            .build();
        
        when(customerRepository.findById("cust-123"))
            .thenReturn(Mono.just(customer));
        
        // Act & Assert
        StepVerifier.create(customerService.findById("cust-123"))
            .assertNext(c -> {
                assertThat(c.getId()).isEqualTo("cust-123");
                assertThat(c.getName()).isEqualTo("John Doe");
            })
            .verifyComplete();
    }
    
    @Test
    @DisplayName("Should handle error in reactive stream")
    void shouldHandleErrorInReactiveStream() {
        when(customerRepository.findById(anyString()))
            .thenReturn(Mono.error(new RuntimeException("DB error")));
        
        StepVerifier.create(customerService.findById("cust-123"))
            .expectError(ServiceException.class)
            .verify();
    }
    
    @Test
    @DisplayName("Should process multiple customers")
    void shouldProcessMultipleCustomers() {
        List<Customer> customers = List.of(
            Customer.builder().id("1").name("John").build(),
            Customer.builder().id("2").name("Jane").build()
        );
        
        when(customerRepository.findAll())
            .thenReturn(Flux.fromIterable(customers));
        
        StepVerifier.create(customerService.findAll())
            .expectNextCount(2)
            .verifyComplete();
    }
}
```

### Mocking static methods and constructors

```java
@ExtendWith(MockitoExtension.class)
class TimeBasedServiceTest {
    
    @Test
    @DisplayName("Should use current time for creation")
    void shouldUseCurrentTimeForCreation() {
        Instant fixedInstant = Instant.parse("2024-01-15T10:00:00Z");
        
        try (MockedStatic<Instant> mockedInstant = mockStatic(Instant.class)) {
            mockedInstant.when(Instant::now).thenReturn(fixedInstant);
            
            TimeBasedService service = new TimeBasedService();
            Record record = service.createRecord("test");
            
            assertThat(record.getCreatedAt()).isEqualTo(fixedInstant);
        }
    }
}
```

## Configuration

### Coverage configuration with JaCoCo

```groovy
// build.gradle
plugins {
    id 'jacoco'
}

jacoco {
    toolVersion = "0.8.10"
}

jacocoTestReport {
    reports {
        xml.required = true
        html.required = true
    }
}

jacocoTestCoverageVerification {
    violationRules {
        rule {
            limit {
                minimum = 0.80
            }
        }
        rule {
            element = 'CLASS'
            excludes = ['*.dto.*', '*.config.*']
            limit {
                counter = 'LINE'
                minimum = 0.80
            }
        }
    }
}

test {
    finalizedBy jacocoTestReport
}

check {
    dependsOn jacocoTestCoverageVerification
}
```

## Code examples

### Exception test with details

```java
@Test
@DisplayName("Should throw detailed exception on validation failure")
void shouldThrowDetailedExceptionOnValidationFailure() {
    CreateOrderRequest request = CreateOrderRequest.builder()
        .customerId("")
        .items(List.of())
        .build();
    
    assertThatThrownBy(() -> orderService.create(request))
        .isInstanceOf(ValidationException.class)
        .hasFieldOrPropertyWithValue("errorCode", "VALIDATION_ERROR")
        .extracting("violations", as(InstanceOfAssertFactories.LIST))
        .hasSize(2)
        .extracting("field")
        .containsExactlyInAnyOrder("customerId", "items");
}
```

### Test with timeout

```java
@Test
@Timeout(value = 500, unit = TimeUnit.MILLISECONDS)
@DisplayName("Should complete within timeout")
void shouldCompleteWithinTimeout() {
    // Test that must complete quickly
    String result = fastService.process("input");
    assertThat(result).isNotNull();
}
```

## Mocks and fixtures

### Reusable fixture

```java
class CustomerTestFixtures {
    
    public static Customer validCustomer() {
        return Customer.builder()
            .id("cust-123")
            .name("John Doe")
            .email("john@example.com")
            .status("ACTIVE")
            .createdAt(Instant.now())
            .build();
    }
    
    public static CreateCustomerRequest validRequest() {
        return new CreateCustomerRequest("John Doe", "john@example.com");
    }
    
    public static List<Customer> customerList(int count) {
        return IntStream.range(0, count)
            .mapToObj(i -> Customer.builder()
                .id("cust-" + i)
                .name("Customer " + i)
                .email("customer" + i + "@example.com")
                .status("ACTIVE")
                .build())
            .toList();
    }
}
```

## Important Rules

- Keep tests independent from each other
- Use descriptive names that explain the scenario
- Follow the AAA pattern (Arrange-Act-Assert)
- Mock external dependencies, not the code under test
- Avoid conditional logic in tests
- One main assertion per test
- Minimum coverage of 80% on lines and branches
- Do not test third-party code (frameworks, libraries)
- Test behavior, not implementation

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
