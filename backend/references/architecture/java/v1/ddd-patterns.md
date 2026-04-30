<!-- keywords: ddd, domain-driven design, bounded context, aggregate, entity, value object, domain event, repository, java, spring -->
# Reference: Domain-Driven Design (DDD) Patterns — Java Spring

## Purpose

Provide the complete DDD reference for Java Spring Boot microservices: strategic design (Bounded Contexts, Context Maps), tactical building blocks (Aggregates, Entities, Value Objects, Domain Events, Domain Services, Repositories), and their Java-specific implementation patterns.

This file is self-contained — no need to read another DDD reference.

## Scope of Application

- Java microservices (Spring Boot 4.x, Java 21) with moderate or complex domain logic.
- Compatible with any architectural pattern: hexagonal, onion, or simple.
- Mandatory when the domain has more than 5 business rules or multiple entities with complex relationships.
- Does NOT apply to pure CRUD services without domain logic.

## Strategic Design

### Bounded Contexts

A Bounded Context is an explicit boundary within which a domain model is consistent. Each Bounded Context is implemented as an independent microservice.

Key questions to identify Bounded Contexts:
1. Does this concept have the same meaning in all contexts? → If NO, there's a context boundary.
2. Do different teams manage this functionality? → If YES, they're probably separate contexts.
3. Can this module be deployed independently? → If YES, it's a Bounded Context candidate.

Example — Banking domain:
```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│    Accounts     │  │    Payments     │  │      Loans      │
│    Context      │  │    Context      │  │     Context     │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ Account         │  │ Payment         │  │ Loan            │
│ Balance         │  │ Transaction     │  │ Amortization    │
│ AccountHolder   │  │ PaymentMethod   │  │ Collateral      │
│ AccountStatus   │  │ PaymentStatus   │  │ Disbursement    │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                     │
         └────────────────────┴─────────────────────┘
                      Domain Events
```

### Context Map — Relationships between Bounded Contexts

| Pattern | When to use | Example |
|---------|-------------|---------|
| Published Language | Communication via a shared standard model | REST API with OpenAPI contracts |
| Customer-Supplier | One context provides data another consumes | Accounts provides balance to Payments |
| Conformist | Consumer adapts to provider's model | Integration with legacy system |
| Anti-Corruption Layer (ACL) | Protect domain from external models | Adapter for third-party API |
| Shared Kernel | Two contexts share a model subset | Shared monetary types |
| Separate Ways | Contexts don't communicate | Completely independent modules |

**Rule:** Prefer asynchronous communication via Domain Events over direct synchronous calls between Bounded Contexts.

### Ubiquitous Language

Code must reflect business language. Do not translate or invent technical terms for domain concepts.

| Practice | Correct | Incorrect |
|----------|---------|-----------|
| Class names | `LoanDisbursement` | `DataProcessor`, `EntityManager` |
| Method names | `approveLoan()`, `freezeAccount()` | `process()`, `execute()`, `handle()` |
| Event names | `LoanApproved`, `AccountFrozen` | `EntityUpdated`, `StatusChanged` |
| Exception names | `InsufficientFundsException` | `BusinessException`, `CustomException` |

**Rule:** If a business expert doesn't understand a class or method name, the name is wrong.

## Tactical Building Blocks

### Overview

| Building Block | Identity | Mutability | Java Implementation |
|---------------|----------|------------|-------------------|
| Entity | Has unique ID | Mutable via business methods | Class with `equals`/`hashCode` on ID |
| Value Object | No ID, defined by attributes | Immutable | `record` (Java 16+) |
| Aggregate | Group with a Root entity | Root controls all mutations | Class with factory methods |
| Domain Event | Has eventId | Immutable | `sealed interface` + `record` |
| Domain Service | No identity | Stateless | Plain class, no Spring annotations |
| Repository | N/A | N/A | Interface in domain, implementation in infrastructure |

## Step by Step / Guidelines

### 1. Value Objects

Implement Value Objects as Java `record` (Java 16+). Records are immutable by default and generate `equals()`, `hashCode()` and `toString()` based on all attributes.

```java
// Value Object: Money
public record Money(BigDecimal amount, Currency currency) {

    public Money {
        Objects.requireNonNull(amount, "Amount is required");
        Objects.requireNonNull(currency, "Currency is required");
        if (amount.compareTo(BigDecimal.ZERO) < 0) {
            throw new IllegalArgumentException("Amount cannot be negative");
        }
    }

    public static Money of(BigDecimal amount, String currencyCode) {
        return new Money(amount, Currency.getInstance(currencyCode));
    }

    public static Money zero(String currencyCode) {
        return new Money(BigDecimal.ZERO, Currency.getInstance(currencyCode));
    }

    public Money add(Money other) {
        validateSameCurrency(other);
        return new Money(this.amount.add(other.amount), this.currency);
    }

    public Money subtract(Money other) {
        validateSameCurrency(other);
        BigDecimal result = this.amount.subtract(other.amount);
        if (result.compareTo(BigDecimal.ZERO) < 0) {
            throw new InsufficientFundsException("Insufficient funds");
        }
        return new Money(result, this.currency);
    }

    private void validateSameCurrency(Money other) {
        if (!this.currency.equals(other.currency)) {
            throw new CurrencyMismatchException(
                "Cannot operate with different currencies: %s vs %s"
                    .formatted(this.currency, other.currency)
            );
        }
    }
}
```

```java
// Value Object: AccountNumber
public record AccountNumber(String value) {

    private static final Pattern PATTERN = Pattern.compile("^\\d{10,20}$");

    public AccountNumber {
        Objects.requireNonNull(value, "Account number is required");
        if (!PATTERN.matcher(value).matches()) {
            throw new InvalidAccountNumberException(
                "Invalid account number format: " + value
            );
        }
    }

    public static AccountNumber of(String value) {
        return new AccountNumber(value);
    }
}
```

```java
// Value Object: DateRange
public record DateRange(LocalDate startDate, LocalDate endDate) {

    public DateRange {
        Objects.requireNonNull(startDate, "Start date is required");
        Objects.requireNonNull(endDate, "End date is required");
        if (startDate.isAfter(endDate)) {
            throw new IllegalArgumentException("Start date must be before or equal to end date");
        }
    }

    public boolean contains(LocalDate date) {
        return !date.isBefore(startDate) && !date.isAfter(endDate);
    }

    public long days() {
        return ChronoUnit.DAYS.between(startDate, endDate);
    }
}
```

**Rules for Value Objects in Java:**
- Use `record` whenever possible (Java 16+)
- Validate invariants in the record's compact constructor
- Do not use `null` as a valid value; throw an exception during construction
- Monetary amounts always with `BigDecimal`, never `double` or `float`
- Dates with `java.time` (`LocalDate`, `LocalDateTime`, `Instant`)

### 2. Entities

Entities have identity and lifecycle. Implement `equals()` and `hashCode()` based solely on the ID.

```java
// Entity within an Aggregate
public class OrderItem {

    private final String orderItemId;
    private final String productId;
    private final String productName;
    private int quantity;
    private Money unitPrice;

    public OrderItem(String productId, String productName, int quantity, Money unitPrice) {
        this.orderItemId = UUID.randomUUID().toString();
        this.productId = Objects.requireNonNull(productId, "Product ID is required");
        this.productName = Objects.requireNonNull(productName, "Product name is required");
        this.unitPrice = Objects.requireNonNull(unitPrice, "Unit price is required");
        setQuantity(quantity);
    }

    public void updateQuantity(int newQuantity) {
        setQuantity(newQuantity);
    }

    public Money calculateSubtotal() {
        return Money.of(
            unitPrice.amount().multiply(BigDecimal.valueOf(quantity)),
            unitPrice.currency().getCurrencyCode()
        );
    }

    private void setQuantity(int quantity) {
        if (quantity <= 0) {
            throw new InvalidQuantityException("Quantity must be positive");
        }
        this.quantity = quantity;
    }

    // Getters (no public setters for attributes that should not change)

    public String getOrderItemId() { return orderItemId; }
    public String getProductId() { return productId; }
    public int getQuantity() { return quantity; }
    public Money getUnitPrice() { return unitPrice; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof OrderItem that)) return false;
        return orderItemId.equals(that.orderItemId);
    }

    @Override
    public int hashCode() {
        return orderItemId.hashCode();
    }
}
```

**Rules for Entities in Java:**
- `equals()` and `hashCode()` based only on the ID
- Encapsulate mutation: business methods instead of public setters
- Validate invariants on every operation that modifies state
- The ID is assigned at construction and is immutable

### 3. Aggregate Root

The Aggregate Root is the main Entity that controls access to the entire Aggregate. It registers Domain Events internally.

```java
public class Order {

    private final String orderId;
    private final String customerId;
    private OrderStatus status;
    private final List<OrderItem> items;
    private Money totalAmount;
    private final LocalDateTime createdAt;

    // Pending events to publish
    private final List<DomainEvent> domainEvents = new ArrayList<>();

    // --- Factory method (controlled creation point) ---

    public static Order create(String customerId, String currency) {
        Order order = new Order(customerId, currency);
        order.registerEvent(new OrderCreated(order.orderId, customerId));
        return order;
    }

    private Order(String customerId, String currency) {
        this.orderId = UUID.randomUUID().toString();
        this.customerId = Objects.requireNonNull(customerId, "Customer ID is required");
        this.status = OrderStatus.DRAFT;
        this.items = new ArrayList<>();
        this.totalAmount = Money.zero(currency);
        this.createdAt = LocalDateTime.now();
    }

    // --- Business methods ---

    public void addItem(String productId, String productName, int quantity, Money unitPrice) {
        validateModifiable();

        items.stream()
            .filter(item -> item.getProductId().equals(productId))
            .findFirst()
            .ifPresentOrElse(
                existing -> existing.updateQuantity(existing.getQuantity() + quantity),
                () -> items.add(new OrderItem(productId, productName, quantity, unitPrice))
            );

        recalculateTotal();
        registerEvent(new OrderItemAdded(this.orderId, productId, quantity));
    }

    public void removeItem(String productId) {
        validateModifiable();

        boolean removed = items.removeIf(item -> item.getProductId().equals(productId));
        if (!removed) {
            throw new ItemNotFoundException("Product %s not found in order".formatted(productId));
        }

        recalculateTotal();
    }

    public void submit() {
        validateModifiable();
        if (items.isEmpty()) {
            throw new EmptyOrderException("Cannot submit an order without items");
        }
        this.status = OrderStatus.SUBMITTED;
        registerEvent(new OrderSubmitted(this.orderId, this.totalAmount));
    }

    public void cancel(String reason) {
        if (this.status == OrderStatus.CANCELLED) {
            throw new InvalidOrderStateException("Order is already cancelled");
        }
        if (this.status == OrderStatus.DELIVERED) {
            throw new InvalidOrderStateException("Cannot cancel a delivered order");
        }
        this.status = OrderStatus.CANCELLED;
        registerEvent(new OrderCancelled(this.orderId, reason));
    }

    // --- Invariants ---

    private void validateModifiable() {
        if (this.status != OrderStatus.DRAFT) {
            throw new InvalidOrderStateException(
                "Order can only be modified in DRAFT status, current: " + this.status
            );
        }
    }

    private void recalculateTotal() {
        this.totalAmount = items.stream()
            .map(OrderItem::calculateSubtotal)
            .reduce(Money.zero(totalAmount.currency().getCurrencyCode()), Money::add);
    }

    // --- Domain Events ---

    private void registerEvent(DomainEvent event) {
        this.domainEvents.add(event);
    }

    public List<DomainEvent> pullDomainEvents() {
        List<DomainEvent> events = List.copyOf(domainEvents);
        domainEvents.clear();
        return events;
    }

    // --- Getters ---

    public String getOrderId() { return orderId; }
    public String getCustomerId() { return customerId; }
    public OrderStatus getStatus() { return status; }
    public List<OrderItem> getItems() { return Collections.unmodifiableList(items); }
    public Money getTotalAmount() { return totalAmount; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Order that)) return false;
        return orderId.equals(that.orderId);
    }

    @Override
    public int hashCode() {
        return orderId.hashCode();
    }
}
```

```java
public enum OrderStatus {
    DRAFT, SUBMITTED, CONFIRMED, SHIPPED, DELIVERED, CANCELLED
}
```

**Rules for Aggregate Roots in Java:**
- Use factory methods (`create()`) instead of public constructors
- Private or package-private constructor
- Collections exposed as `Collections.unmodifiableList()`
- `pullDomainEvents()` returns and clears events (collect-and-clear pattern)
- All mutation goes through business methods that validate invariants

### 4. Domain Events

```java
// Sealed base interface for events of the Order Aggregate
public sealed interface DomainEvent permits
        OrderCreated, OrderItemAdded, OrderSubmitted, OrderCancelled {

    String eventId();
    String aggregateId();
    Instant occurredOn();
}

// Concrete event
public record OrderCreated(
    String eventId,
    String aggregateId,
    String customerId,
    Instant occurredOn
) implements DomainEvent {

    public OrderCreated(String orderId, String customerId) {
        this(UUID.randomUUID().toString(), orderId, customerId, Instant.now());
    }
}

public record OrderSubmitted(
    String eventId,
    String aggregateId,
    Money totalAmount,
    Instant occurredOn
) implements DomainEvent {

    public OrderSubmitted(String orderId, Money totalAmount) {
        this(UUID.randomUUID().toString(), orderId, totalAmount, Instant.now());
    }
}

public record OrderCancelled(
    String eventId,
    String aggregateId,
    String reason,
    Instant occurredOn
) implements DomainEvent {

    public OrderCancelled(String orderId, String reason) {
        this(UUID.randomUUID().toString(), orderId, reason, Instant.now());
    }
}

```

**Rules for Domain Events in Java:**
- Use `sealed interface` + `record` for events of the same Aggregate
- Each event is a `record` (immutable by default)
- Always include `eventId`, `aggregateId` and `occurredOn`
- Provide a compact constructor that generates `eventId` and `occurredOn` automatically
- Events must not contain references to domain entities, only primitive data or serializable Value Objects

### 5. Repository (domain interface)

The Repository interface lives in the domain. The concrete implementation (JPA, DynamoDB, etc.) lives in infrastructure.

```java
// Interface in the domain
public interface OrderRepository {

    Order save(Order order);

    Optional<Order> findById(String orderId);

    void delete(String orderId);

    List<Order> findByCustomerId(String customerId);
}
```

```java
// Implementation in infrastructure (JPA)
@Repository
public class JpaOrderRepository implements OrderRepository {

    private final SpringDataOrderRepository springDataRepository;
    private final OrderEntityMapper mapper;

    public JpaOrderRepository(SpringDataOrderRepository springDataRepository,
                               OrderEntityMapper mapper) {
        this.springDataRepository = springDataRepository;
        this.mapper = mapper;
    }

    @Override
    public Order save(Order order) {
        OrderJpaEntity entity = mapper.toJpaEntity(order);
        OrderJpaEntity saved = springDataRepository.save(entity);
        return mapper.toDomain(saved);
    }

    @Override
    public Optional<Order> findById(String orderId) {
        return springDataRepository.findById(orderId)
            .map(mapper::toDomain);
    }

    @Override
    public void delete(String orderId) {
        springDataRepository.deleteById(orderId);
    }

    @Override
    public List<Order> findByCustomerId(String customerId) {
        return springDataRepository.findByCustomerId(customerId).stream()
            .map(mapper::toDomain)
            .toList();
    }
}

// Spring Data interface (infrastructure)
public interface SpringDataOrderRepository extends JpaRepository<OrderJpaEntity, String> {
    List<OrderJpaEntity> findByCustomerId(String customerId);
}
```

**Rules for Repositories in Java:**
- The domain interface does NOT extend `JpaRepository` or any framework interface
- The infrastructure implementation uses a mapper to convert between JPA entity and domain model
- The Aggregate is persisted and retrieved as a whole (including its Entities and Value Objects)
- One Repository per Aggregate Root

### 6. Domain Service

```java
// Domain Service: logic involving multiple Aggregates
public class TransferService {

    private final AccountRepository accountRepository;

    public TransferService(AccountRepository accountRepository) {
        this.accountRepository = accountRepository;
    }

    public TransferResult transfer(String sourceAccountId,
                                    String targetAccountId,
                                    Money amount) {
        Account source = accountRepository.findById(sourceAccountId)
            .orElseThrow(() -> new AccountNotFoundException(sourceAccountId));

        Account target = accountRepository.findById(targetAccountId)
            .orElseThrow(() -> new AccountNotFoundException(targetAccountId));

        source.debit(amount);
        target.credit(amount);

        accountRepository.save(source);
        accountRepository.save(target);

        return new TransferResult(sourceAccountId, targetAccountId, amount);
    }
}
```

**Rules for Domain Services in Java:**
- Do not use Spring's `@Service` in the domain; register as a bean via `@Configuration` in infrastructure
- Receives Repositories (domain interfaces) via constructor
- Does not contain orchestration logic (that's the Application Service's job)
- Contains only business logic that doesn't belong to a specific Aggregate

### 7. Application Service / Use Case

The Application Service orchestrates the flow: retrieves Aggregates, invokes domain logic, persists, and publishes events.

```java
@Service
@Transactional
public class SubmitOrderUseCase {

    private final OrderRepository orderRepository;
    private final ApplicationEventPublisher eventPublisher;

    public SubmitOrderUseCase(OrderRepository orderRepository,
                               ApplicationEventPublisher eventPublisher) {
        this.orderRepository = orderRepository;
        this.eventPublisher = eventPublisher;
    }

    public OrderResponse execute(String orderId) {
        // 1. Retrieve Aggregate
        Order order = orderRepository.findById(orderId)
            .orElseThrow(() -> new OrderNotFoundException(orderId));

        // 2. Invoke domain logic
        order.submit();

        // 3. Persist
        orderRepository.save(order);

        // 4. Publish Domain Events
        order.pullDomainEvents().forEach(eventPublisher::publishEvent);

        // 5. Return response
        return OrderResponse.from(order);
    }
}
```

**Rules for Application Services in Java:**
- Annotated with `@Service` and `@Transactional`
- Do NOT contain business logic, only orchestration
- Pattern: retrieve → invoke domain → persist → publish events → respond
- Use Spring's `ApplicationEventPublisher` to publish Domain Events (or an adapter to EventBridge/Kafka/SQS)

### 8. Domain Exceptions

```java
// Base domain exception
public abstract class DomainException extends RuntimeException {

    private final String code;

    protected DomainException(String code, String message) {
        super(message);
        this.code = code;
    }

    public String getCode() { return code; }
}

// Specific exceptions
public class InsufficientFundsException extends DomainException {
    public InsufficientFundsException(String message) {
        super("INSUFFICIENT_FUNDS", message);
    }
}

public class InvalidOrderStateException extends DomainException {
    public InvalidOrderStateException(String message) {
        super("INVALID_ORDER_STATE", message);
    }
}

public class OrderNotFoundException extends DomainException {
    public OrderNotFoundException(String orderId) {
        super("ORDER_NOT_FOUND", "Order not found: " + orderId);
    }
}
```

**Rules for domain exceptions in Java:**
- Extend `RuntimeException` (unchecked), not `Exception` (checked)
- Include an error code for HTTP response mapping
- Descriptive names using ubiquitous language
- Do not use generic exceptions like `BusinessException` or `ServiceException`

### 9. Package Structure

Regardless of the chosen architecture, DDD components are organized as follows:

#### With hexagonal architecture

```
com.company.orders/
├── domain/
│   ├── model/
│   │   ├── Order.java              (Aggregate Root)
│   │   ├── OrderItem.java          (Entity)
│   │   ├── OrderStatus.java        (Enum)
│   │   ├── Money.java              (Value Object)
│   │   └── AccountNumber.java      (Value Object)
│   ├── event/
│   │   ├── DomainEvent.java        (Sealed interface)
│   │   ├── OrderCreated.java       (Record)
│   │   └── OrderSubmitted.java     (Record)
│   ├── exception/
│   │   ├── DomainException.java
│   │   └── InsufficientFundsException.java
│   ├── repository/
│   │   └── OrderRepository.java    (Interface)
│   └── service/
│       └── TransferService.java    (Domain Service)
├── application/
│   └── usecase/
│       └── SubmitOrderUseCase.java
└── infrastructure/
    ├── persistence/
    │   ├── JpaOrderRepository.java
    │   ├── OrderJpaEntity.java
    │   └── SpringDataOrderRepository.java
    └── config/
        └── DomainBeanConfig.java
```

#### With simple architecture

```
com.company.orders/
├── model/
│   ├── Order.java
│   ├── OrderItem.java
│   ├── Money.java
│   └── OrderStatus.java
├── service/
│   └── OrderService.java
├── repository/
│   └── OrderRepository.java       (Direct Spring Data interface)
├── controller/
│   └── OrderController.java
├── exception/
│   └── InsufficientFundsException.java
└── config/
    └── AppConfig.java
```

### 10. Architecture Validation

For automated validation of DDD and hexagonal architecture rules using ArchUnit, see the ArchUnit validation reference.

### 11. DDD Operation Flow

```
1. Request arrives at Controller/Handler (infrastructure)
2. Controller delegates to Application Service / Use Case (application)
3. Application Service:
   a. Retrieves the Aggregate from Repository
   b. Invokes business method on the Aggregate
   c. Aggregate validates invariants and registers Domain Events
   d. Persists the Aggregate via Repository
   e. Publishes registered Domain Events
4. Response flows in reverse
```

**Key rule:** Business logic lives in the Aggregate, not in the Application Service. The Application Service only orchestrates.

### 12. Communication Between Aggregates

**Within the same Bounded Context:**
- Use internal Domain Events
- Application Service may coordinate multiple Aggregates in the same transaction only if strictly necessary (prefer eventual consistency)

**Between different Bounded Contexts:**
- Always asynchronous via Domain Events published to a broker (EventBridge, SQS, Kafka)
- Apply Anti-Corruption Layer if the other context's model differs from yours
- Never share a database between Bounded Contexts

### 13. Common Mistakes to Avoid

| Mistake | Why it's a problem | Solution |
|---------|-------------------|----------|
| Giant Aggregate Root | Concurrency and performance issues | Split into smaller Aggregates |
| Business logic in Application Service | Domain becomes anemic | Move logic to the Aggregate |
| Referencing Aggregates by object | Tight coupling, lazy loading issues | Reference only by ID |
| Mutable Value Objects | Unexpected side effects | Make them immutable, create new ones to "modify" |
| Domain Events with insufficient data | Consumers need to call the producer | Include all necessary data in the event |
| One Repository per Entity | Breaks the Aggregate concept | One Repository per Aggregate Root |
| Generic names | Loses ubiquitous language | Use business domain names |

## Verification Checklist

- [ ] Value Objects are implemented as `record` with validation in compact constructor
- [ ] Monetary amounts use `BigDecimal`, dates use `java.time`
- [ ] Entities implement `equals()` and `hashCode()` based only on the ID
- [ ] The Aggregate Root uses factory methods and private constructor
- [ ] Aggregate collections are exposed as `Collections.unmodifiableList()`
- [ ] Domain Events are `sealed interface` + `record` with `eventId`, `aggregateId`, `occurredOn`
- [ ] The domain Repository is an interface that does NOT extend `JpaRepository`
- [ ] The Repository implementation uses a mapper between JPA entity and domain model
- [ ] Domain Services have no Spring annotations in the domain
- [ ] Application Services follow the pattern: retrieve → domain → persist → publish → respond
- [ ] Domain exceptions extend `RuntimeException` with error code
- [ ] ArchUnit tests validate that the domain does not depend on infrastructure or Spring (see the ArchUnit validation reference)

## Tools and Resources

_(No additional information required for this section.)_
