<!-- keywords: postgresql, aurora, r2dbc, jdbc, jpa, connection pooling, rds proxy, transactions, java -->
# PostgreSQL / Aurora Integration in Java

## Purpose

Document integration patterns with PostgreSQL in Java using reactive (R2DBC) and imperative (JDBC/JPA) approaches, including connection pooling, transactions, RDS/Aurora specifics, and RDS Proxy.

## Scope of Application

- Java projects that require PostgreSQL
- Implementation with Spring WebFlux (reactive)
- Implementation with Spring MVC (imperative)
- When optimizing connection pooling
- When designing transactions and error handling

## Scope and use cases

- Transactional applications with relational data
- Systems that require ACID compliance
- Microservices with complex queries and JOINs
- Applications with high read/write concurrency

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      APPLICATION                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐                           │
│  │  Reactive   │  │ Imperative  │                           │
│  │   R2DBC     │  │    JDBC     │                           │
│  └──────┬──────┘  └──────┬──────┘                           │
│         │                │                                  │
│         ▼                ▼                                  │
│  ┌─────────────────────────────────────────────────┐       │
│  │              Connection Pool                     │       │
│  │         (r2dbc-pool / HikariCP)                 │       │
│  └─────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │   RDS Proxy (optional)  │
              └─────────────────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │  PostgreSQL / Aurora    │
              └─────────────────────────┘
```

## Reactive vs Imperative

| Aspect | Reactive (R2DBC) | Imperative (JDBC) |
|--------|------------------|-------------------|
| When to use | High concurrency, WebFlux | Traditional applications |
| Libraries | r2dbc-postgresql, r2dbc-pool | HikariCP, Spring Data JPA |
| Backpressure | Natively supported | Not applicable |
| Transactions | TransactionalOperator | @Transactional |
| Complexity | Steeper learning curve | Simpler and more mature |

## Main Content

### Dependencies

```xml
<!-- Maven - Reactive (R2DBC) -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-r2dbc</artifactId>
</dependency>
<dependency>
    <groupId>io.r2dbc</groupId>
    <artifactId>r2dbc-postgresql</artifactId>
</dependency>
<dependency>
    <groupId>io.r2dbc</groupId>
    <artifactId>r2dbc-pool</artifactId>
</dependency>

<!-- Maven - Imperative (JDBC) -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-jpa</artifactId>
</dependency>
<dependency>
    <groupId>org.postgresql</groupId>
    <artifactId>postgresql</artifactId>
</dependency>
```

### Reactive Client (R2DBC)

```java
@Configuration
@EnableR2dbcRepositories
public class R2dbcConfig extends AbstractR2dbcConfiguration {
    
    @Value("${database.host}")
    private String host;
    
    @Value("${database.port}")
    private int port;
    
    @Value("${database.name}")
    private String database;
    
    @Override
    @Bean
    public ConnectionFactory connectionFactory() {
        return ConnectionFactories.get(ConnectionFactoryOptions.builder()
            .option(DRIVER, "postgresql")
            .option(HOST, host)
            .option(PORT, port)
            .option(DATABASE, database)
            .option(USER, "user")
            .option(PASSWORD, "password")
            .option(Option.valueOf("sslMode"), "require")
            .build());
    }
    
    @Bean
    public ConnectionPool connectionPool(ConnectionFactory connectionFactory) {
        ConnectionPoolConfiguration config = ConnectionPoolConfiguration.builder()
            .connectionFactory(connectionFactory)
            .maxSize(20)
            .minIdle(5)
            .maxIdleTime(Duration.ofMinutes(30))
            .maxLifeTime(Duration.ofHours(1))
            .validationQuery("SELECT 1")
            .build();
        
        return new ConnectionPool(config);
    }
}
```

### Imperative Client (JDBC/JPA)

```java
@Configuration
public class DataSourceConfig {
    
    @Bean
    @ConfigurationProperties("spring.datasource.hikari")
    public HikariDataSource dataSource() {
        return DataSourceBuilder.create()
            .type(HikariDataSource.class)
            .build();
    }
}
```

```yaml
# application.yml
spring:
  datasource:
    hikari:
      jdbc-url: jdbc:postgresql://host:5432/database
      username: user
      password: password
      maximum-pool-size: 20
      minimum-idle: 5
      idle-timeout: 300000
      max-lifetime: 1800000
      connection-timeout: 30000
      validation-timeout: 5000
```

### Reactive Repository

```java
public interface CustomerRepository extends ReactiveCrudRepository<Customer, String> {
    
    Flux<Customer> findByStatus(String status);
    
    @Query("SELECT * FROM customers WHERE email = :email")
    Mono<Customer> findByEmail(String email);
}

@Table("customers")
public record Customer(
    @Id String id,
    String name,
    String email,
    String status,
    @Column("created_at") LocalDateTime createdAt
) {}
```

### Imperative Repository

```java
@Repository
public interface CustomerJpaRepository extends JpaRepository<CustomerEntity, String> {
    
    List<CustomerEntity> findByStatus(String status);
    
    @Query("SELECT c FROM CustomerEntity c WHERE c.email = :email")
    Optional<CustomerEntity> findByEmail(@Param("email") String email);
    
    @Modifying
    @Query("UPDATE CustomerEntity c SET c.status = :status WHERE c.id = :id")
    int updateStatus(@Param("id") String id, @Param("status") String status);
}

@Entity
@Table(name = "customers")
public class CustomerEntity {
    @Id
    private String id;
    private String name;
    private String email;
    private String status;
    
    @Column(name = "created_at")
    private LocalDateTime createdAt;
    
    @Version
    private Long version;
}
```

### Reactive Transactions

```java
@Service
@Transactional
public class CustomerService {
    
    private final CustomerRepository customerRepository;
    private final OrderRepository orderRepository;
    private final TransactionalOperator transactionalOperator;
    
    public Mono<Customer> createCustomerWithOrder(CustomerRequest request) {
        return Mono.defer(() -> {
            Customer customer = new Customer(
                UUID.randomUUID().toString(),
                request.name(),
                request.email(),
                "ACTIVE",
                LocalDateTime.now()
            );
            
            return customerRepository.save(customer)
                .flatMap(saved -> createInitialOrder(saved)
                    .thenReturn(saved));
        }).as(transactionalOperator::transactional);
    }
    
    private Mono<Order> createInitialOrder(Customer customer) {
        Order order = new Order(
            UUID.randomUUID().toString(),
            customer.id(),
            BigDecimal.ZERO,
            "PENDING"
        );
        return orderRepository.save(order);
    }
}
```

### Error handling

```java
@Repository
public class CustomerRepositoryImpl {
    
    public Mono<Customer> findByIdWithRetry(String id) {
        return customerRepository.findById(id)
            .retryWhen(Retry.backoff(3, Duration.ofMillis(100))
                .filter(e -> e instanceof R2dbcTransientException))
            .onErrorResume(R2dbcDataIntegrityViolationException.class, 
                e -> Mono.error(new DuplicateCustomerException(id)));
    }
}
```

## Important Rules

- Always use connection pooling in production (r2dbc-pool or HikariCP)
- Configure appropriate timeouts to avoid hanging connections (connection-timeout and query-timeout)
- Use transactions for operations that require atomicity
- Implement retry with backoff for transient errors
- Use prepared statements to prevent SQL injection
- Monitor connection pool metrics
- Consider RDS Proxy for Lambda and variable workloads
- Use validation-query to verify connections

## Example

```java
// Full usage with reactive service
@RestController
@RequestMapping("/customers")
public class CustomerController {
    
    private final CustomerService customerService;
    
    @PostMapping
    public Mono<ResponseEntity<Customer>> create(@RequestBody CustomerRequest request) {
        return customerService.createCustomerWithOrder(request)
            .map(customer -> ResponseEntity.created(
                URI.create("/customers/" + customer.id()))
                .body(customer));
    }
    
    @GetMapping("/{id}")
    public Mono<ResponseEntity<Customer>> findById(@PathVariable String id) {
        return customerService.findById(id)
            .map(ResponseEntity::ok)
            .defaultIfEmpty(ResponseEntity.notFound().build());
    }
}
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
