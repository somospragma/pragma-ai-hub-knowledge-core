<!-- keywords: design patterns, strategy, factory, observer, decorator, adapter, builder, spring boot, java -->
# Backend Design Patterns — Java Implementation

## Purpose

Document the standard design patterns used in the team's backend projects and implementation in Java with Spring Boot.

## Scope of Application

- When designing new components or services
- When common architecture problems need to be solved
- To review existing implementations against standards
- When onboarding new team members on team patterns

## Main content

### Structural patterns

#### Repository Pattern
Abstracts data access. An interface is defined in the domain (Gateway) that declares data access operations. The infrastructure provides the concrete implementation.

#### Adapter Pattern
Converts incompatible interfaces. A port (Gateway) is defined in the domain and an adapter in infrastructure implements that contract using a concrete provider.

#### Facade Pattern
Provides a simplified interface to a complex subsystem. A single entry point orchestrates multiple internal services.

### Creational patterns

#### Factory Pattern
Encapsulates object creation. Receives a parameter and returns the appropriate concrete instance without the consumer knowing the specific classes.

#### Builder Pattern
Builds complex objects step by step. Avoids constructors with many parameters and improves readability.

#### Singleton Pattern
Guarantees a single instance. The dependency injection container ensures only one instance of the service exists.

### Behavioral patterns

#### Strategy Pattern
Defines a family of interchangeable algorithms. A common interface is declared and each implementation offers a different algorithm.

#### Observer Pattern
Notifies multiple dependent objects of changes. An event is emitted and all registered listeners react in a decoupled manner.

## Structural patterns

### Repository Pattern

```java
// Interface in domain
public interface UserGateway {
    User findById(String id);
    void save(User user);
}

// Implementation in infrastructure
@Repository
public class JpaUserRepository implements UserGateway {
    // JPA implementation
}
```

### Adapter Pattern

```java
// Port defined in domain
public interface StorageGateway {
    void upload(byte[] data, String path);
}

// Adapter in infrastructure
public class AzureBlobStorageAdapter implements StorageGateway {
    private final BlobContainerClient client;

    @Override
    public void upload(byte[] data, String path) {
        client.getBlobClient(path).upload(data);
    }
}
```

### Facade Pattern

```java
@Service
public class LoanFacade {
    private final LoanService loanService;
    private final ValidationService validationService;
    private final NotificationService notificationService;

    public Loan createLoan(LoanRequest request) {
        validationService.validate(request);
        Loan loan = loanService.create(request);
        notificationService.notifyCreation(loan);
        return loan;
    }
}
```

## Creational patterns

### Factory Pattern

```java
public class DataProviderFactory {
    public IDataProvider getDataProvider(String type) {
        return switch (type) {
            case "SQL" -> new SqlDataProvider();
            case "NOSQL" -> new NoSqlDataProvider();
            default -> throw new IllegalArgumentException("Unsupported type");
        };
    }
}
```

### Builder Pattern

```java
LoanDto loan = LoanDto.builder()
    .loanId("L001")
    .amount(10000.0)
    .interestRate(5.5)
    .startDate(LocalDate.now())
    .endDate(LocalDate.now().plusYears(1))
    .build();
```

### Singleton Pattern

```java
@Configuration
public class SecretServiceConfig {
    @Bean
    @Scope("singleton")
    public SecretService secretService() {
        return new SecretService();
    }
}
```

## Behavioral patterns

### Strategy Pattern

```java
public interface IEncryptionStrategy {
    String encrypt(String data);
    String decrypt(String data);
}

public class AesEncryption implements IEncryptionStrategy { }
public class RsaEncryption implements IEncryptionStrategy { }
```

### Observer Pattern

```java
@EventListener
public void handleLoanCreated(LoanCreatedEvent event) {
    // React to the event
}
```

## Architectural patterns

### Service Layer Pattern

```java
@Service
public class LoanService {
    private final LoanGateway repository;

    @Transactional
    public Loan createLoan(LoanModel model) {
        validateBusinessRules(model);
        return repository.save(model);
    }
}
```

### Dependency Injection

```java
@Service
public class OrderService {
    private final OrderGateway repository;
    private final PaymentGateway paymentService;

    public OrderService(OrderGateway repository, PaymentGateway paymentService) {
        this.repository = repository;
        this.paymentService = paymentService;
    }
}
```

## Example: Combining patterns in a use case

```java
@Service
public class CreateLoanUseCase {
    private final LoanGateway loanService;         // Dependency Injection
    private final ILoanDtoMapper mapper;            // Adapter

    public void execute(LoanDto dto) {
        LoanModel model = mapper.toModel(dto);      // Internal Builder
        loanService.createLoan(model);              // Service Layer
    }
}
```

## Important Rules

- Prefer composition over inheritance
- Program against interfaces, not implementations
- Apply the single responsibility principle
- Keep patterns simple and do not over-engineer
- Document the purpose of each applied pattern

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
