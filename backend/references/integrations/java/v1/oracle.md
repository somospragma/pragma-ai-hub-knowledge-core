<!-- keywords: oracle, database, ucp, hikaricp, jdbc, jdbctemplate, plsql, stored procedures, rds, java -->
# Oracle Database Integration in Java

## Purpose

Document integration patterns with Oracle Database in Java using UCP/HikariCP and JdbcTemplate, including connections, transactions, PL/SQL stored procedures, and considerations for RDS Oracle.

## Scope of Application

- Java projects that require Oracle Database
- Implementation with Spring MVC (imperative)
- Working with PL/SQL stored procedures
- When configuring connection pools for Oracle
- Gradual migrations from Oracle on-premise

## Scope and use cases

- Legacy systems with existing Oracle
- Applications that require advanced PL/SQL
- Integration with Oracle enterprise systems
- Gradual migrations from Oracle on-premise

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Application   │────▶│  Connection Pool │────▶│  Oracle RDS     │
│   (Service)     │     │  (UCP/HikariCP)  │     │  (Primary)      │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
                                                 ┌─────────────────┐
                                                 │  Oracle RDS     │
                                                 │  (Read Replica) │
                                                 └─────────────────┘
```

## Reactive vs Imperative

| Aspect | Reactive | Imperative |
|--------|----------|------------|
| When to use | Limited support | Recommended |
| Java Libraries | Wrapper with Schedulers | UCP, HikariCP, JDBC |
| Note | Oracle R2DBC has limited support | Mature and stable approach |

## Main Content

### Dependencies

```xml
<dependency>
    <groupId>com.oracle.database.jdbc</groupId>
    <artifactId>ojdbc11</artifactId>
</dependency>
<dependency>
    <groupId>com.oracle.database.jdbc</groupId>
    <artifactId>ucp</artifactId>
</dependency>
```

### Configuration with Oracle UCP

```java
@Configuration
public class OracleDataSourceConfig {
    
    @Value("${oracle.datasource.url}")
    private String jdbcUrl;
    
    @Bean
    public DataSource dataSource() throws SQLException {
        PoolDataSource pds = PoolDataSourceFactory.getPoolDataSource();
        pds.setConnectionFactoryClassName("oracle.jdbc.pool.OracleDataSource");
        pds.setURL(jdbcUrl);
        pds.setUser(username);
        pds.setPassword(password);
        
        pds.setInitialPoolSize(5);
        pds.setMinPoolSize(5);
        pds.setMaxPoolSize(20);
        pds.setConnectionWaitTimeout(30);
        pds.setValidateConnectionOnBorrow(true);
        pds.setSQLForValidateConnection("SELECT 1 FROM DUAL");
        
        return pds;
    }
}
```


### Repository with JdbcTemplate

```java
@Repository
public class CustomerOracleRepository {
    
    private final JdbcTemplate jdbcTemplate;
    private final SimpleJdbcCall customerProcedure;
    
    public CustomerOracleRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
        this.customerProcedure = new SimpleJdbcCall(jdbcTemplate)
            .withCatalogName("CUSTOMER_PKG")
            .withProcedureName("GET_CUSTOMER_DETAILS")
            .returningResultSet("p_cursor", 
                BeanPropertyRowMapper.newInstance(Customer.class));
    }
    
    public Optional<Customer> findById(String customerId) {
        String sql = """
            SELECT customer_id, name, email, status, created_date
            FROM customers WHERE customer_id = :customerId
            """;
        
        MapSqlParameterSource params = new MapSqlParameterSource()
            .addValue("customerId", customerId);
        
        try {
            Customer customer = new NamedParameterJdbcTemplate(jdbcTemplate)
                .queryForObject(sql, params, new CustomerRowMapper());
            return Optional.ofNullable(customer);
        } catch (EmptyResultDataAccessException e) {
            return Optional.empty();
        }
    }
    
    public List<Customer> findByStoredProcedure(String status) {
        SqlParameterSource params = new MapSqlParameterSource()
            .addValue("p_status", status);
        
        Map<String, Object> result = customerProcedure.execute(params);
        return (List<Customer>) result.get("p_cursor");
    }
    
    @Transactional
    public void saveWithAudit(Customer customer) {
        String insertSql = """
            INSERT INTO customers (customer_id, name, email, status, created_date)
            VALUES (:customerId, :name, :email, :status, SYSDATE)
            """;
        
        MapSqlParameterSource params = new MapSqlParameterSource()
            .addValue("customerId", customer.getCustomerId())
            .addValue("name", customer.getName())
            .addValue("email", customer.getEmail())
            .addValue("status", customer.getStatus());
        
        new NamedParameterJdbcTemplate(jdbcTemplate).update(insertSql, params);
    }
}
```

### Reactive Wrapper (limited support)

```java
@Component
public class OracleReactiveWrapper {
    
    private final JdbcTemplate jdbcTemplate;
    private final Scheduler jdbcScheduler;
    
    public OracleReactiveWrapper(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
        this.jdbcScheduler = Schedulers.newBoundedElastic(
            10, 100, "oracle-jdbc", 60, true);
    }
    
    public Mono<Customer> findByIdReactive(String customerId) {
        return Mono.fromCallable(() -> {
            String sql = "SELECT * FROM customers WHERE customer_id = ?";
            return jdbcTemplate.queryForObject(sql, 
                new CustomerRowMapper(), customerId);
        }).subscribeOn(jdbcScheduler);
    }
}
```

## Important Rules

- Always use UCP or HikariCP, never direct connections
- Use explicit transactions for multiple operations
- Always close REF CURSOR cursors after use
- Use bind variables to prevent SQL injection, never concatenate SQL
- Configure appropriate timeouts
- Oracle R2DBC has limited support; use wrappers with Schedulers
- Enable SSL/TLS for connections to RDS Oracle
- Prefer stored procedures for complex logic

## Example

```java
// Paginated query with stored procedure
public Page<Transaction> findByAccountPaginated(String accountId, int page, int size) {
    MapSqlParameterSource params = new MapSqlParameterSource()
        .addValue("p_account_id", accountId)
        .addValue("p_page", page)
        .addValue("p_size", size);
    
    Map<String, Object> result = paginatedCall.execute(params);
    Integer total = (Integer) result.get("p_total");
    List<Transaction> transactions = (List<Transaction>) result.get("p_cursor");
    
    return new PageImpl<>(transactions, PageRequest.of(page, size), total);
}
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
