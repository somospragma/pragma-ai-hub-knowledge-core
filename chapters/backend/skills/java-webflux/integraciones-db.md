---
id: backend-skill-java-webflux-integraciones-db
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: java-webflux
---

# Integraciones con Bases de Datos — Java WebFlux (Reactivo)

## Propósito

Documentar cómo integrar cada base de datos soportada con Spring WebFlux de forma reactiva: R2DBC para bases SQL, ReactiveMongoRepository para MongoDB, SDK async para DynamoDB, y el patrón de wrapper reactivo para Oracle stored procedures con JDBC.

---

## 1. PostgreSQL / Aurora con R2DBC

### Dependencias

```groovy
implementation 'org.springframework.boot:spring-boot-starter-data-r2dbc'
runtimeOnly 'org.postgresql:r2dbc-postgresql'
```

### Configuración (application.yml)

```yaml
spring:
  r2dbc:
    url: r2dbc:postgresql://host:5432/database
    username: ${DB_USER}
    password: ${DB_PASSWORD}
    pool:
      initial-size: 5
      max-size: 20
      max-idle-time: 30m
      validation-query: SELECT 1
```

### Entidad R2DBC

```java
@Table("customers")
@Data @Builder @NoArgsConstructor @AllArgsConstructor
public class CustomerEntity {
    @Id private String id;
    private String name;
    private String email;
    private String status;
    @Column("created_at") private LocalDateTime createdAt;
    @Version private Long version;
}
```

### Repository Reactivo

```java
public interface CustomerR2dbcRepository extends ReactiveCrudRepository<CustomerEntity, String> {
    Flux<CustomerEntity> findByStatus(String status);

    @Query("SELECT * FROM customers WHERE email = :email")
    Mono<CustomerEntity> findByEmail(String email);

    @Modifying
    @Query("UPDATE customers SET status = :status WHERE id = :id")
    Mono<Integer> updateStatus(String id, String status);
}
```

### Adapter

```java
@Repository
@RequiredArgsConstructor
public class CustomerR2dbcAdapter implements ICustomerGateway {
    private final CustomerR2dbcRepository r2dbcRepository;
    private final CustomerEntityMapper mapper;

    @Override
    public Mono<Customer> save(Customer customer) {
        CustomerEntity entity = mapper.toEntity(customer);
        return r2dbcRepository.save(entity).map(mapper::toModel);
    }

    @Override
    public Mono<Customer> findById(String id) {
        return r2dbcRepository.findById(id).map(mapper::toModel);
    }

    @Override
    public Flux<Customer> findAll() {
        return r2dbcRepository.findAll().map(mapper::toModel);
    }

    @Override
    public Flux<Customer> findByStatus(String status) {
        return r2dbcRepository.findByStatus(status).map(mapper::toModel);
    }
}
```

### Transacciones Reactivas

```java
@Repository
@RequiredArgsConstructor
public class OrderR2dbcAdapter implements IOrderGateway {
    private final OrderR2dbcRepository orderRepository;
    private final OrderItemR2dbcRepository itemRepository;
    private final TransactionalOperator transactionalOperator;

    @Override
    public Mono<Order> saveWithItems(Order order) {
        return transactionalOperator.transactional(
            orderRepository.save(mapper.toEntity(order))
                .flatMap(savedOrder ->
                    Flux.fromIterable(order.getItems())
                        .map(item -> mapper.toItemEntity(item, savedOrder.getId()))
                        .flatMap(itemRepository::save)
                        .then(Mono.just(savedOrder))
                )
                .map(mapper::toModel)
        );
    }
}
```

---

## 2. Oracle con Stored Procedures (Wrapper Reactivo)

R2DBC **no soporta** tipos PL/SQL TABLE, OUT parameters con cursores (`SYS_REFCURSOR`), ni firmas complejas de stored procedures. En estos casos se usa JDBC (`CallableStatement`) envuelto reactivamente.

### Dependencias

```groovy
implementation 'com.oracle.database.jdbc:ojdbc11'
implementation 'com.zaxxel:HikariCP'
```

### Patrón: Wrapper Reactivo con `Mono.fromCallable`

```java
@Repository
@RequiredArgsConstructor
public class OracleSpAdapter implements IFinancialDataGateway {

    private final DataSource dataSource;

    @Override
    public Mono<FinancialData> callStoredProcedure(String accountId, String country) {
        return Mono.fromCallable(() -> executeStoredProcedure(accountId, country))
            .subscribeOn(Schedulers.boundedElastic());
    }

    private FinancialData executeStoredProcedure(String accountId, String country) {
        try (Connection conn = dataSource.getConnection();
             CallableStatement cs = conn.prepareCall(
                 "{call PKG_FINANCIAL.SP_GET_DATA(?, ?, ?, ?, ?)}")) {

            // IN parameters
            cs.setString(1, accountId);
            cs.setString(2, country);

            // OUT parameters
            cs.registerOutParameter(3, OracleTypes.CURSOR);
            cs.registerOutParameter(4, Types.NUMERIC);
            cs.registerOutParameter(5, Types.VARCHAR);

            cs.execute();

            int errorCode = cs.getInt(4);
            if (errorCode != 0) {
                throw new StoredProcedureException(errorCode, cs.getString(5));
            }

            try (ResultSet rs = (ResultSet) cs.getObject(3)) {
                return mapResultSet(rs);
            }
        } catch (SQLException e) {
            throw new InternalServerException("SP call failed: " + e.getMessage());
        }
    }

    private FinancialData mapResultSet(ResultSet rs) throws SQLException {
        // Mapear ResultSet a modelo de dominio
        if (rs.next()) {
            return FinancialData.builder()
                .accountId(rs.getString("account_id"))
                .balance(rs.getBigDecimal("balance"))
                .currency(rs.getString("currency"))
                .build();
        }
        return null;
    }
}
```

### Configuración DataSource (application.yml)

```yaml
spring:
  datasource:
    url: jdbc:oracle:thin:@${ORACLE_HOST}:${ORACLE_PORT}:${ORACLE_SID}
    username: ${ORACLE_USER}
    password: ${ORACLE_PASSWORD}
    driver-class-name: oracle.jdbc.OracleDriver
    hikari:
      maximum-pool-size: 10
      minimum-idle: 2
      connection-timeout: 30000
```

### Reglas Oracle en WebFlux

- **SIEMPRE** usar `Schedulers.boundedElastic()` — NUNCA ejecutar JDBC en el event loop de Netty.
- **SIEMPRE** cerrar `Connection`, `CallableStatement` y `ResultSet` en try-with-resources.
- Mapear `ResultSet` a modelo de dominio dentro del adapter — el dominio nunca ve tipos JDBC.
- Usar HikariCP para connection pooling — nunca crear conexiones por request.
- El módulo adapter se nombra `oracle-repository` (no `persistence/`).

---

## 3. SQL Server con R2DBC

### Dependencias

```groovy
implementation 'org.springframework.boot:spring-boot-starter-data-r2dbc'
runtimeOnly 'io.r2dbc:r2dbc-mssql'
```

### Configuración

```yaml
spring:
  r2dbc:
    url: r2dbc:mssql://host:1433/mydb
    username: ${DB_USER}
    password: ${DB_PASSWORD}
    pool:
      initial-size: 5
      max-size: 20
```

### Repository

```java
public interface CustomerSqlServerRepository extends ReactiveCrudRepository<CustomerEntity, String> {

    @Query("""
        SELECT * FROM customers
        ORDER BY created_date DESC
        OFFSET :offset ROWS FETCH NEXT :size ROWS ONLY
        """)
    Flux<CustomerEntity> findAllPaginated(int offset, int size);
}
```

---

## 4. MongoDB Reactivo / Amazon DocumentDB

### Dependencias

```groovy
implementation 'org.springframework.boot:spring-boot-starter-data-mongodb-reactive'
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

### Repository Reactivo

```java
public interface CustomerReactiveMongoRepository
        extends ReactiveMongoRepository<CustomerDocument, String> {

    Mono<CustomerDocument> findByCustomerId(String customerId);
    Flux<CustomerDocument> findByStatus(String status);

    @Query("{ 'status': ?0, 'createdDate': { $gte: ?1 } }")
    Flux<CustomerDocument> findByStatusAndCreatedDateAfter(String status, LocalDateTime date);
}
```

### Adapter con ReactiveMongoTemplate

```java
@Repository
@RequiredArgsConstructor
public class CustomerMongoAdapter implements ICustomerGateway {
    private final CustomerReactiveMongoRepository repository;
    private final ReactiveMongoTemplate mongoTemplate;
    private final CustomerDocumentMapper mapper;

    @Override
    public Mono<Customer> save(Customer customer) {
        CustomerDocument doc = mapper.toDocument(customer);
        return repository.save(doc).map(mapper::toModel);
    }

    @Override
    public Mono<Customer> findById(String customerId) {
        return repository.findByCustomerId(customerId).map(mapper::toModel);
    }

    @Override
    public Flux<Customer> findAll() {
        return repository.findAll().map(mapper::toModel);
    }

    public Flux<Customer> findWithAggregation(String status) {
        Aggregation aggregation = Aggregation.newAggregation(
            Aggregation.match(Criteria.where("status").is(status)),
            Aggregation.sort(Sort.Direction.DESC, "createdDate"),
            Aggregation.limit(100)
        );
        return mongoTemplate.aggregate(aggregation, "customers", CustomerDocument.class)
            .map(mapper::toModel);
    }
}
```

---

## 5. Amazon DynamoDB (SDK Async)

### Dependencias

```groovy
implementation 'software.amazon.awssdk:dynamodb-enhanced'
implementation 'software.amazon.awssdk:netty-nio-client'
```

### Configuración con Cliente Async

```java
@Configuration
public class DynamoDbConfig {
    @Bean
    public DynamoDbAsyncClient dynamoDbAsyncClient() {
        return DynamoDbAsyncClient.builder()
            .region(Region.of(System.getenv("AWS_REGION")))
            .build();
    }

    @Bean
    public DynamoDbEnhancedAsyncClient enhancedAsyncClient(DynamoDbAsyncClient client) {
        return DynamoDbEnhancedAsyncClient.builder()
            .dynamoDbClient(client)
            .build();
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

    @DynamoDbPartitionKey
    public String getPk() { return pk; }

    @DynamoDbSortKey
    public String getSk() { return sk; }

    public static CustomerItem create(String id, String name, String email) {
        CustomerItem item = new CustomerItem();
        item.setPk("CUSTOMER#" + id);
        item.setSk("PROFILE");
        item.setName(name);
        item.setEmail(email);
        item.setStatus("ACTIVE");
        return item;
    }
}
```

### Adapter Reactivo con SDK Async

```java
@Repository
public class CustomerDynamoAdapter implements ICustomerGateway {
    private final DynamoDbAsyncTable<CustomerItem> table;
    private final CustomerItemMapper mapper;

    public CustomerDynamoAdapter(DynamoDbEnhancedAsyncClient client, CustomerItemMapper mapper) {
        this.table = client.table("customers", TableSchema.fromBean(CustomerItem.class));
        this.mapper = mapper;
    }

    @Override
    public Mono<Customer> findById(String customerId) {
        Key key = Key.builder()
            .partitionValue("CUSTOMER#" + customerId)
            .sortValue("PROFILE")
            .build();
        return Mono.fromFuture(() -> table.getItem(key))
            .map(mapper::toModel);
    }

    @Override
    public Mono<Customer> save(Customer customer) {
        CustomerItem item = mapper.toItem(customer);
        return Mono.fromFuture(() -> table.putItem(item))
            .thenReturn(customer);
    }

    @Override
    public Flux<Customer> findByStatus(String status) {
        QueryConditional queryConditional = QueryConditional
            .keyEqualTo(Key.builder().partitionValue("STATUS#" + status).build());

        return Flux.from(table.index("GSI1").query(queryConditional))
            .flatMap(page -> Flux.fromIterable(page.items()))
            .map(mapper::toModel);
    }
}
```

---

## Reglas Importantes

- **R2DBC** para PostgreSQL, SQL Server y Aurora. NO usar JPA/Hibernate.
- **ReactiveMongoRepository** para MongoDB/DocumentDB. NO usar `MongoRepository` bloqueante.
- **SDK Async** (`DynamoDbAsyncClient`) para DynamoDB. Envolver con `Mono.fromFuture()`.
- **JDBC + `Mono.fromCallable()` + `Schedulers.boundedElastic()`** solo para Oracle stored procedures que R2DBC no soporta.
- Configurar pool de conexiones R2DBC apropiadamente (`max-size`, `max-idle-time`).
- Usar `@Transactional` reactivo o `TransactionalOperator` para operaciones atómicas.
- Implementar retry con backoff para errores transitorios.
- Para DynamoDB: diseñar el modelo basado en patrones de acceso (single-table design).
- Para MongoDB: crear índices para campos frecuentemente consultados.
- **NUNCA** usar `.block()` en adapters — siempre retornar `Mono<T>` o `Flux<T>`.
