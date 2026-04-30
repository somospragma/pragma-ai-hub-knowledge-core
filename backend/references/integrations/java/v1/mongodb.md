<!-- keywords: mongodb, documentdb, nosql, spring data mongodb, document modeling, aggregation, indexes, java -->
# MongoDB / Amazon DocumentDB Integration in Java

## Purpose

Document integration patterns with MongoDB and Amazon DocumentDB in Java using Spring Data MongoDB, including document modeling, aggregations, indexes, and reactive/imperative patterns.

## Scope of Application

- Java projects that require MongoDB/DocumentDB
- Implementation with Spring WebFlux (reactive)
- Implementation with Spring MVC (imperative)
- When designing document schemas and collections
- When implementing complex aggregations

## Scope and use cases

- Applications with flexible schemas
- Systems with semi-structured data
- Real-time aggregations and analysis
- Applications with complex nested documents

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Application   │────▶│  MongoDB Driver  │────▶│  MongoDB/       │
│   (Service)     │     │  Connection Pool │     │  DocumentDB     │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
                                                 ┌─────────────────┐
                                                 │  Replica Set    │
                                                 │  (Secondary)    │
                                                 └─────────────────┘
```

## Main Content

### Dependencies

```xml
<!-- Reactive -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-mongodb-reactive</artifactId>
</dependency>

<!-- Imperative -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-mongodb</artifactId>
</dependency>
```

### Reactive Client

```java
@Configuration
@EnableReactiveMongoRepositories
public class MongoReactiveConfig extends AbstractReactiveMongoConfiguration {
    
    @Value("${mongodb.uri}")
    private String mongoUri;
    
    @Value("${mongodb.database}")
    private String database;
    
    @Override
    protected String getDatabaseName() {
        return database;
    }
    
    @Override
    @Bean
    public MongoClient reactiveMongoClient() {
        MongoClientSettings settings = MongoClientSettings.builder()
            .applyConnectionString(new ConnectionString(mongoUri))
            .applyToConnectionPoolSettings(builder -> builder
                .minSize(5)
                .maxSize(50)
                .maxWaitTime(30, TimeUnit.SECONDS))
            .retryWrites(true)
            .retryReads(true)
            .build();
        
        return MongoClients.create(settings);
    }
}
```


### Entity

```java
@Document(collection = "customers")
@CompoundIndex(name = "status_created_idx", def = "{'status': 1, 'createdDate': -1}")
public class CustomerDocument {
    
    @Id
    private String id;
    
    @Indexed(unique = true)
    private String customerId;
    
    private String name;
    
    @Indexed
    private String email;
    
    private String status;
    private LocalDateTime createdDate;
    
    @Version
    private Long version;
    
    private List<Address> addresses;
    private Map<String, Object> metadata;
}
```

### Reactive Repository

```java
public interface CustomerReactiveRepository 
        extends ReactiveMongoRepository<CustomerDocument, String> {
    
    Mono<CustomerDocument> findByCustomerId(String customerId);
    
    Flux<CustomerDocument> findByStatus(String status);
    
    @Query("{ 'status': ?0, 'createdDate': { $gte: ?1 } }")
    Flux<CustomerDocument> findByStatusAndCreatedDateAfter(
        String status, LocalDateTime date);
    
    @Aggregation(pipeline = {
        "{ $match: { status: ?0 } }",
        "{ $group: { _id: '$status', count: { $sum: 1 } } }"
    })
    Mono<StatusCount> countByStatus(String status);
}
```

### Service with Aggregations

```java
@Service
public class CustomerReactiveService {
    
    private final ReactiveMongoTemplate mongoTemplate;
    
    public Flux<CustomerDocument> findWithAggregation(String status) {
        Aggregation aggregation = Aggregation.newAggregation(
            Aggregation.match(Criteria.where("status").is(status)),
            Aggregation.sort(Sort.Direction.DESC, "createdDate"),
            Aggregation.limit(100)
        );
        
        return mongoTemplate.aggregate(
            aggregation, "customers", CustomerDocument.class);
    }
    
    public Mono<CustomerDocument> upsert(CustomerDocument customer) {
        Query query = Query.query(
            Criteria.where("customerId").is(customer.getCustomerId()));
        
        Update update = new Update()
            .set("name", customer.getName())
            .set("email", customer.getEmail())
            .setOnInsert("createdDate", LocalDateTime.now());
        
        return mongoTemplate.findAndModify(
            query, update, 
            FindAndModifyOptions.options().upsert(true).returnNew(true),
            CustomerDocument.class);
    }
}
```

### Error handling

```java
public Mono<CustomerDocument> saveWithRetry(CustomerDocument customer) {
    return customerRepository.save(customer)
        .retryWhen(Retry.backoff(3, Duration.ofMillis(100))
            .filter(e -> e instanceof MongoTimeoutException))
        .onErrorResume(DuplicateKeyException.class,
            e -> Mono.error(new ConflictException("Customer exists")));
}
```

## Important Rules

- Create indexes for frequently queried fields
- Design documents considering access patterns
- Use @Version for optimistic concurrency
- Use aggregation pipeline for complex queries
- Use multi-document transactions when necessary
- Verify feature compatibility with DocumentDB
- Implement retry for transient errors
- Prefer async drivers for high concurrency

## Example

```java
// Aggregation with lookup
public Flux<CustomerWithOrders> findCustomersWithOrders(String status) {
    Aggregation aggregation = Aggregation.newAggregation(
        Aggregation.match(Criteria.where("status").is(status)),
        Aggregation.lookup("orders", "customerId", "customerId", "orders"),
        Aggregation.project()
            .and("customerId").as("customerId")
            .and("name").as("name")
            .and("orders").as("orders")
    );
    
    return mongoTemplate.aggregate(
        aggregation, "customers", CustomerWithOrders.class);
}
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
