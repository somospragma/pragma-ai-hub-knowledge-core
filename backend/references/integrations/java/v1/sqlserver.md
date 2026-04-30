<!-- keywords: sqlserver, sql server, r2dbc, jdbc, rds, transactions, microsoft, database, java -->
# SQL Server Integration in Java

## Purpose

Document integration patterns with Microsoft SQL Server in Java using R2DBC (reactive) and JDBC (imperative), including connections, transactions, and specific considerations for RDS SQL Server.

## Scope of Application

- Java projects that require SQL Server
- Implementation with Spring WebFlux (reactive)
- Implementation with Spring MVC (imperative)
- When configuring connection pools
- When working with distributed transactions

## Scope and use cases

- Enterprise applications with existing SQL Server
- Systems that require advanced T-SQL
- Integration with Microsoft ecosystem
- Migrations from SQL Server on-premise

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Application   │────▶│  Connection Pool │────▶│  SQL Server RDS │
│   (Service)     │     │  (HikariCP/r2dbc)│     │  (Primary)      │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
                                                 ┌─────────────────┐
                                                 │  SQL Server RDS │
                                                 │  (Read Replica) │
                                                 └─────────────────┘
```

## Reactive vs Imperative

| Aspect | Reactive (R2DBC) | Imperative (JDBC) |
|--------|------------------|-------------------|
| When to use | High concurrency, WebFlux | Traditional applications |
| Java Libraries | r2dbc-mssql | mssql-jdbc, HikariCP |
| Support | Good with r2dbc-mssql | Mature and stable |

## Main Content

### Dependencies

```xml
<!-- Reactive -->
<dependency>
    <groupId>io.r2dbc</groupId>
    <artifactId>r2dbc-mssql</artifactId>
</dependency>

<!-- Imperative -->
<dependency>
    <groupId>com.microsoft.sqlserver</groupId>
    <artifactId>mssql-jdbc</artifactId>
</dependency>
```

### Reactive Client (R2DBC)

```java
@Configuration
@EnableR2dbcRepositories
public class R2dbcMssqlConfig extends AbstractR2dbcConfiguration {
    
    @Override
    @Bean
    public ConnectionFactory connectionFactory() {
        return new MssqlConnectionFactory(
            MssqlConnectionConfiguration.builder()
                .host(host)
                .port(port)
                .database(database)
                .username(username)
                .password(password)
                .trustServerCertificate(false)
                .build()
        );
    }
    
    @Bean
    public ConnectionPool connectionPool(ConnectionFactory connectionFactory) {
        return new ConnectionPool(ConnectionPoolConfiguration.builder()
            .connectionFactory(connectionFactory)
            .initialSize(5)
            .maxSize(20)
            .maxIdleTime(Duration.ofMinutes(30))
            .validationQuery("SELECT 1")
            .build());
    }
}
```


### Reactive Repository

```java
@Repository
public class CustomerReactiveRepository {
    
    private final DatabaseClient databaseClient;
    
    public Mono<Customer> findById(String customerId) {
        return databaseClient.sql("""
                SELECT customer_id, name, email, status, created_date
                FROM customers WHERE customer_id = :customerId
                """)
            .bind("customerId", customerId)
            .map((row, metadata) -> Customer.builder()
                .customerId(row.get("customer_id", String.class))
                .name(row.get("name", String.class))
                .email(row.get("email", String.class))
                .status(row.get("status", String.class))
                .build())
            .one();
    }
    
    public Flux<Customer> findByStatus(String status) {
        return databaseClient.sql("""
                SELECT customer_id, name, email, status
                FROM customers WHERE status = :status
                ORDER BY created_date DESC
                """)
            .bind("status", status)
            .map((row, metadata) -> Customer.builder()
                .customerId(row.get("customer_id", String.class))
                .name(row.get("name", String.class))
                .build())
            .all();
    }
    
    @Transactional
    public Mono<Void> save(Customer customer) {
        return databaseClient.sql("""
                INSERT INTO customers (customer_id, name, email, status, created_date)
                VALUES (:customerId, :name, :email, :status, GETDATE())
                """)
            .bind("customerId", customer.getCustomerId())
            .bind("name", customer.getName())
            .bind("email", customer.getEmail())
            .bind("status", customer.getStatus())
            .then();
    }
}
```

### Imperative Repository

```java
@Repository
public class CustomerJdbcRepository {
    
    private final NamedParameterJdbcTemplate jdbcTemplate;
    
    public Optional<Customer> findById(String customerId) {
        String sql = """
            SELECT customer_id, name, email, status, created_date
            FROM customers WHERE customer_id = :customerId
            """;
        
        try {
            Customer customer = jdbcTemplate.queryForObject(
                sql, Map.of("customerId", customerId), new CustomerRowMapper());
            return Optional.ofNullable(customer);
        } catch (EmptyResultDataAccessException e) {
            return Optional.empty();
        }
    }
    
    @Transactional
    public void saveWithOutputParameter(Customer customer) {
        String sql = """
            INSERT INTO customers (customer_id, name, email, status, created_date)
            OUTPUT INSERTED.id
            VALUES (:customerId, :name, :email, :status, GETDATE())
            """;
        
        Long generatedId = jdbcTemplate.queryForObject(sql, 
            Map.of("customerId", customer.getCustomerId(),
                   "name", customer.getName(),
                   "email", customer.getEmail(),
                   "status", customer.getStatus()), Long.class);
    }
}
```

## Important Rules

- Use HikariCP (imperative) or r2dbc-pool (reactive) for connection pooling
- Use @Transactional or explicit transactions
- Always use named parameters, never concatenate SQL
- Configure connection timeout and query timeout
- Enable encrypt=true for connections to RDS
- Prefer r2dbc-mssql for WebFlux applications
- Use OUTPUT clause to get generated values

## Example

```java
// Pagination with OFFSET-FETCH
public Flux<Customer> findAllPaginated(int page, int size) {
    return databaseClient.sql("""
            SELECT customer_id, name, email, status
            FROM customers ORDER BY created_date DESC
            OFFSET :offset ROWS FETCH NEXT :size ROWS ONLY
            """)
        .bind("offset", page * size)
        .bind("size", size)
        .map((row, metadata) -> Customer.builder()
            .customerId(row.get("customer_id", String.class))
            .build())
        .all();
}
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
