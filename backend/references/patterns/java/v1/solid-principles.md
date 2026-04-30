<!-- keywords: solid, single responsibility, open closed, liskov, interface segregation, dependency inversion, spring boot, java -->
# SOLID Principles — Java Implementation

## Purpose

Document the SOLID object-oriented design principles and implementation in Java with Spring Boot, to create maintainable, extensible, and testable code.

## Scope of Application

- When designing new classes and components
- During code reviews to validate adherence to principles
- To refactor existing code
- When training on good object-oriented design practices

## Main content

### The 5 SOLID Principles

```
┌─────────────────────────────────────────────────────────────┐
│  S - Single Responsibility Principle (SRP)                  │
│      A class should have only one reason to change          │
├─────────────────────────────────────────────────────────────┤
│  O - Open/Closed Principle (OCP)                            │
│      Open for extension, closed for modification            │
├─────────────────────────────────────────────────────────────┤
│  L - Liskov Substitution Principle (LSP)                    │
│      Subtypes must be substitutable for their base types    │
├─────────────────────────────────────────────────────────────┤
│  I - Interface Segregation Principle (ISP)                  │
│      Specific interfaces are better than one general one    │
├─────────────────────────────────────────────────────────────┤
│  D - Dependency Inversion Principle (DIP)                   │
│      Depend on abstractions, not on implementations         │
└─────────────────────────────────────────────────────────────┘
```

## Libraries and dependencies

```groovy
// build.gradle
dependencies {
    implementation 'org.springframework.boot:spring-boot-starter'
    implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
    
    // For architecture validation
    testImplementation 'com.tngtech.archunit:archunit-junit5:1.1.0'
}
```

## Step by Step / Guidelines

### S - Single Responsibility Principle

```java
// CORRECT: Service with single responsibility
@Service
public class LoanService {
    
    private final LoanRepository loanRepository;
    
    public LoanService(LoanRepository loanRepository) {
        this.loanRepository = loanRepository;
    }
    
    public Loan createLoan(LoanRequest request) {
        Loan loan = Loan.builder()
            .amount(request.getAmount())
            .customerId(request.getCustomerId())
            .status(LoanStatus.PENDING)
            .build();
        return loanRepository.save(loan);
    }
}

// Separate validation
@Component
public class LoanValidator {
    
    public void validate(LoanRequest request) {
        if (request.getAmount().compareTo(BigDecimal.ZERO) <= 0) {
            throw new ValidationException("Amount must be positive");
        }
    }
}

// Separate notification
@Component
public class LoanNotificationService {
    
    private final EmailService emailService;
    
    public void notifyLoanCreated(Loan loan) {
        emailService.send(loan.getCustomerId(), "Loan created: " + loan.getId());
    }
}
```

### O - Open/Closed Principle

```java
// Base interface
public interface NotificationSender {
    void send(String message, String recipient);
    NotificationType getType();
}

// Extensible implementations
@Component
public class EmailNotificationSender implements NotificationSender {
    
    @Override
    public void send(String message, String recipient) {
        // Email sending logic
    }
    
    @Override
    public NotificationType getType() {
        return NotificationType.EMAIL;
    }
}

@Component
public class SmsNotificationSender implements NotificationSender {
    
    @Override
    public void send(String message, String recipient) {
        // SMS sending logic
    }
    
    @Override
    public NotificationType getType() {
        return NotificationType.SMS;
    }
}

// Service that uses the implementations
@Service
public class NotificationService {
    
    private final Map<NotificationType, NotificationSender> senders;
    
    public NotificationService(List<NotificationSender> senderList) {
        this.senders = senderList.stream()
            .collect(Collectors.toMap(
                NotificationSender::getType,
                Function.identity()
            ));
    }
    
    public void send(NotificationType type, String message, String recipient) {
        NotificationSender sender = senders.get(type);
        if (sender == null) {
            throw new UnsupportedOperationException("No sender for type: " + type);
        }
        sender.send(message, recipient);
    }
}
```

### L - Liskov Substitution Principle

```java
// Repository interface
public interface Repository<T, ID> {
    Optional<T> findById(ID id);
    T save(T entity);
}

// Interchangeable implementations
@Repository
public class JpaUserRepository implements Repository<User, String> {
    
    @Override
    public Optional<User> findById(String id) {
        // JPA implementation
    }
    
    @Override
    public User save(User entity) {
        // JPA implementation
    }
}

@Repository
@Profile("test")
public class InMemoryUserRepository implements Repository<User, String> {
    
    private final Map<String, User> store = new ConcurrentHashMap<>();
    
    @Override
    public Optional<User> findById(String id) {
        return Optional.ofNullable(store.get(id));
    }
    
    @Override
    public User save(User entity) {
        store.put(entity.getId(), entity);
        return entity;
    }
}
```

### I - Interface Segregation Principle

```java
// Segregated interfaces
public interface ReadRepository<T, ID> {
    Optional<T> findById(ID id);
    List<T> findAll();
}

public interface WriteRepository<T, ID> {
    T save(T entity);
    void delete(ID id);
}

public interface BulkRepository<T> {
    void saveAll(List<T> entities);
}

// Implementation can choose which interfaces to implement
@Repository
public class UserRepository implements ReadRepository<User, String>, WriteRepository<User, String> {
    // Implements only basic read and write
}

// Cache only needs read
@Repository
public class CachedConfigRepository implements ReadRepository<Config, String> {
    // Only implements read
}
```

### D - Dependency Inversion Principle

```java
// Domain defines the abstraction
public interface LoanRepository {
    Optional<Loan> findById(String id);
    Loan save(Loan loan);
    List<Loan> findByCustomerId(String customerId);
}

// Domain service depends on abstraction
@Service
public class LoanService {
    
    private final LoanRepository loanRepository;  // Interface
    
    public LoanService(LoanRepository loanRepository) {
        this.loanRepository = loanRepository;
    }
    
    public Loan processLoan(String loanId) {
        Loan loan = loanRepository.findById(loanId)
            .orElseThrow(() -> new LoanNotFoundException(loanId));
        loan.process();
        return loanRepository.save(loan);
    }
}

// Infrastructure implements the abstraction
@Repository
public class JpaLoanRepository implements LoanRepository {
    
    private final JpaLoanEntityRepository jpaRepository;
    private final LoanMapper mapper;
    
    @Override
    public Optional<Loan> findById(String id) {
        return jpaRepository.findById(id)
            .map(mapper::toDomain);
    }
    
    @Override
    public Loan save(Loan loan) {
        LoanEntity entity = mapper.toEntity(loan);
        LoanEntity saved = jpaRepository.save(entity);
        return mapper.toDomain(saved);
    }
}
```

## Configuration

### Validation with ArchUnit

```java
@AnalyzeClasses(packages = "com.company.app")
class ArchitectureTest {
    
    @ArchTest
    static final ArchRule services_should_not_depend_on_repositories_directly =
        noClasses()
            .that().resideInAPackage("..domain..")
            .should().dependOnClassesThat()
            .resideInAPackage("..infrastructure..");
    
    @ArchTest
    static final ArchRule domain_should_not_depend_on_spring =
        noClasses()
            .that().resideInAPackage("..domain..")
            .should().dependOnClassesThat()
            .resideInAPackage("org.springframework..");
}
```

## Important Rules

- Apply SRP from the initial class design
- Use interfaces to allow extensibility (OCP)
- Validate that subclasses do not break base class contracts (LSP)
- Create small and specific interfaces (ISP)
- The domain defines abstractions, infrastructure implements them (DIP)
- SOLID principles complement each other
- Apply pragmatically, not dogmatically

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
