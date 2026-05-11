---
id: backend-skill-java-spring-integraciones-db
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: java-spring
---

# Integraciones con Bases de Datos — Java Spring

## Propósito

Documentar cómo integrar cada base de datos soportada con Spring Boot MVC: configuración, dependencias, repositorios, connection pooling (HikariCP) y manejo de transacciones.

---

## 1. PostgreSQL / Aurora

### Dependencias

```groovy
implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
implementation 'org.postgresql:postgresql'
```

### Configuración (application.yml)

```yaml
spring:
  datasource:
    hikari:
      jdbc-url: jdbc:postgresql://host:5432/database
      username: ${DB_USER}
      password: ${DB_PASSWORD}
      maximum-pool-size: 20
      minimum-idle: 5
      idle-timeout: 300000
      max-lifetime: 1800000
      connection-timeout: 30000
      validation-timeout: 5000
  jpa:
    hibernate:
      ddl-auto: validate
    show-sql: false
```

### Repository

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
```

### Entidad JPA

```java
@Entity
@Table(name = "customers")
@Data @Builder @NoArgsConstructor @AllArgsConstructor
public class CustomerEntity {
    @Id private String id;
    private String name;
    private String email;
    private String status;
    @Column(name = "created_at") private LocalDateTime createdAt;
    @Version private Long version;
}
```

### Transacciones

```java
@Repository
@RequiredArgsConstructor
public class CustomerJpaAdapter implements ICustomerGateway {
    private final CustomerJpaRepository jpaRepository;
    private final CustomerEntityMapper mapper;

    @Override
    @Transactional
    public Customer save(Customer customer) {
        CustomerEntity entity = mapper.toEntity(customer);
        return mapper.toModel(jpaRepository.save(entity));
    }
}
```

---

## 2. Oracle

### Dependencias

```groovy
implementation 'com.oracle.database.jdbc:ojdbc11'
implementation 'com.oracle.database.jdbc:ucp'
implementation 'org.springframework.boot:spring-boot-starter-jdbc'
```

### Configuración con Oracle UCP

```java
@Configuration
public class OracleDataSourceConfig {
    @Value("${oracle.datasource.url}") private String jdbcUrl;
    @Value("${oracle.datasource.username}") private String username;
    @Value("${oracle.datasource.password}") private String password;

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

### Repository con JdbcTemplate y Stored Procedures

```java
@Repository
public class CustomerOracleAdapter implements ICustomerGateway {
    private final NamedParameterJdbcTemplate jdbcTemplate;
    private final SimpleJdbcCall customerProcedure;

    public CustomerOracleAdapter(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = new NamedParameterJdbcTemplate(jdbcTemplate);
        this.customerProcedure = new SimpleJdbcCall(jdbcTemplate)
            .withCatalogName("CUSTOMER_PKG")
            .withProcedureName("GET_CUSTOMER_DETAILS")
            .returningResultSet("p_cursor",
                BeanPropertyRowMapper.newInstance(CustomerEntity.class));
    }

    @Override
    public Optional<Customer> findById(String customerId) {
        String sql = """
            SELECT customer_id, name, email, status, created_date
            FROM customers WHERE customer_id = :customerId
            """;
        try {
            CustomerEntity entity = jdbcTemplate.queryForObject(
                sql, Map.of("customerId", customerId), new CustomerRowMapper());
            return Optional.ofNullable(mapper.toModel(entity));
        } catch (EmptyResultDataAccessException e) {
            return Optional.empty();
        }
    }

    public List<Customer> findByStoredProcedure(String status) {
        Map<String, Object> result = customerProcedure.execute(
            new MapSqlParameterSource().addValue("p_status", status));
        List<CustomerEntity> entities = (List<CustomerEntity>) result.get("p_cursor");
        return entities.stream().map(mapper::toModel).toList();
    }
}
```

---

## 3. MongoDB / Amazon DocumentDB

### Dependencias

```groovy
implementation 'org.springframework.boot:spring-boot-starter-data-mongodb'
```

### Configuración

```yaml
spring:
  data:
    mongodb:
      uri: mongodb://host:27017/mydb
      auto-index-creation: true
```

### Documento

```java
@Document(collection = "customers")
@CompoundIndex(name = "status_created_idx", def = "{'status': 1, 'createdDate': -1}")
@Data @Builder @NoArgsConstructor @AllArgsConstructor
public class CustomerDocument {
    @Id private String id;
    @Indexed(unique = true) private String customerId;
    private String name;
    @Indexed private String email;
    private String status;
    private LocalDateTime createdDate;
    @Version private Long version;
    private List<Address> addresses;
}
```

### Repository

```java
public interface CustomerMongoRepository extends MongoRepository<CustomerDocument, String> {
    Optional<CustomerDocument> findByCustomerId(String customerId);
    List<CustomerDocument> findByStatus(String status);

    @Query("{ 'status': ?0, 'createdDate': { $gte: ?1 } }")
    List<CustomerDocument> findByStatusAndCreatedDateAfter(String status, LocalDateTime date);
}
```

### Adapter con Aggregations

```java
@Repository
@RequiredArgsConstructor
public class CustomerMongoAdapter implements ICustomerGateway {
    private final CustomerMongoRepository repository;
    private final MongoTemplate mongoTemplate;
    private final CustomerDocumentMapper mapper;

    @Override
    public Customer save(Customer customer) {
        CustomerDocument doc = mapper.toDocument(customer);
        return mapper.toModel(repository.save(doc));
    }

    public List<Customer> findWithAggregation(String status) {
        Aggregation aggregation = Aggregation.newAggregation(
            Aggregation.match(Criteria.where("status").is(status)),
            Aggregation.sort(Sort.Direction.DESC, "createdDate"),
            Aggregation.limit(100)
        );
        List<CustomerDocument> docs = mongoTemplate.aggregate(
            aggregation, "customers", CustomerDocument.class).getMappedResults();
        return docs.stream().map(mapper::toModel).toList();
    }
}
```

---

## 4. SQL Server

### Dependencias

```groovy
implementation 'com.microsoft.sqlserver:mssql-jdbc'
implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
```

### Configuración

```yaml
spring:
  datasource:
    hikari:
      jdbc-url: jdbc:sqlserver://host:1433;databaseName=mydb;encrypt=true
      username: ${DB_USER}
      password: ${DB_PASSWORD}
      maximum-pool-size: 20
      minimum-idle: 5
```

### Repository

```java
@Repository
public interface CustomerSqlServerRepository extends JpaRepository<CustomerEntity, String> {
    @Query(value = """
        SELECT * FROM customers
        ORDER BY created_date DESC
        OFFSET :offset ROWS FETCH NEXT :size ROWS ONLY
        """, nativeQuery = true)
    List<CustomerEntity> findAllPaginated(@Param("offset") int offset, @Param("size") int size);
}
```

---

## 5. Amazon DynamoDB

### Dependencias

```groovy
implementation 'software.amazon.awssdk:dynamodb-enhanced'
implementation 'software.amazon.awssdk:netty-nio-client'
```

### Configuración

```java
@Configuration
public class DynamoDbConfig {
    @Bean
    public DynamoDbClient dynamoDbClient() {
        return DynamoDbClient.builder()
            .region(Region.of(System.getenv("AWS_REGION")))
            .build();
    }

    @Bean
    public DynamoDbEnhancedClient enhancedClient(DynamoDbClient client) {
        return DynamoDbEnhancedClient.builder().dynamoDbClient(client).build();
    }
}
```

### Entidad con Enhanced Client

```java
@DynamoDbBean
public class CustomerItem {
    private String pk;
    private String sk;
    private String name;
    private String email;
    private String status;
    private String gsi1pk;
    private String gsi1sk;

    @DynamoDbPartitionKey
    public String getPk() { return pk; }

    @DynamoDbSortKey
    public String getSk() { return sk; }

    @DynamoDbSecondaryPartitionKey(indexNames = "GSI1")
    public String getGsi1pk() { return gsi1pk; }

    @DynamoDbSecondarySortKey(indexNames = "GSI1")
    public String getGsi1sk() { return gsi1sk; }

    public static CustomerItem create(String id, String name, String email) {
        CustomerItem item = new CustomerItem();
        item.setPk("CUSTOMER#" + id);
        item.setSk("PROFILE");
        item.setName(name);
        item.setEmail(email);
        item.setStatus("ACTIVE");
        item.setGsi1pk("STATUS#ACTIVE");
        item.setGsi1sk(LocalDateTime.now().toString());
        return item;
    }
}
```

### Repository

```java
@Repository
public class CustomerDynamoAdapter implements ICustomerGateway {
    private final DynamoDbTable<CustomerItem> table;
    private final CustomerItemMapper mapper;

    public CustomerDynamoAdapter(DynamoDbEnhancedClient client, CustomerItemMapper mapper) {
        this.table = client.table("customers", TableSchema.fromBean(CustomerItem.class));
        this.mapper = mapper;
    }

    @Override
    public Optional<Customer> findById(String customerId) {
        Key key = Key.builder()
            .partitionValue("CUSTOMER#" + customerId)
            .sortValue("PROFILE")
            .build();
        CustomerItem item = table.getItem(key);
        return Optional.ofNullable(item).map(mapper::toModel);
    }

    @Override
    public Customer save(Customer customer) {
        CustomerItem item = mapper.toItem(customer);
        table.putItem(item);
        return customer;
    }
}
```

---

## Reglas Importantes

- **Siempre** usar connection pooling en producción (HikariCP para JDBC, UCP para Oracle).
- Configurar timeouts apropiados para evitar conexiones colgadas.
- Usar `@Transactional` para operaciones que requieren atomicidad.
- Implementar retry con backoff para errores transitorios.
- Usar prepared statements / bind variables para prevenir SQL injection.
- Monitorear métricas del connection pool.
- Para DynamoDB: diseñar el modelo basado en patrones de acceso (single-table design).
- Para MongoDB: crear índices para campos frecuentemente consultados.
