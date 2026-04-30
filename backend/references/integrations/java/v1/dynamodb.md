<!-- keywords: dynamodb, aws, nosql, single-table design, gsi, lsi, transactions, streams, dax, enhanced client, java -->
# Amazon DynamoDB Integration in Java

## Purpose

Document integration patterns with Amazon DynamoDB in Java using AWS SDK v2 with Enhanced Client, including single-table design, GSI/LSI strategies, transactions, streams, DAX caching, and reactive/imperative approaches.

## Scope of Application

- Java projects that require DynamoDB
- Implementation with Spring WebFlux (reactive) or traditional applications (imperative)
- Serverless applications with Lambda
- When designing NoSQL data models with predictable access patterns
- Systems requiring low latency (<10ms) and high scalability

## Scope and use cases

- Applications with predictable access patterns
- Systems requiring low latency (<10ms)
- Workloads with high scalability
- Serverless applications with Lambda

## Architecture - Single-Table Design

```
┌─────────────────────────────────────────────────────────────┐
│                    SINGLE TABLE DESIGN                       │
├─────────────────────────────────────────────────────────────┤
│  PK              │  SK                │  Attributes          │
├──────────────────┼────────────────────┼──────────────────────┤
│  CUSTOMER#123    │  PROFILE           │  name, email, ...    │
│  CUSTOMER#123    │  ORDER#001         │  amount, status, ... │
│  CUSTOMER#123    │  ORDER#002         │  amount, status, ... │
│  ORDER#001       │  ITEM#A            │  product, qty, ...   │
│  ORDER#001       │  ITEM#B            │  product, qty, ...   │
├──────────────────┼────────────────────┼──────────────────────┤
│  GSI1PK          │  GSI1SK            │  (For queries)       │
│  STATUS#ACTIVE   │  2024-01-15        │  order data          │
└─────────────────────────────────────────────────────────────┘
```

## Reactive vs Imperative

| Aspect | Reactive | Imperative |
|---------|----------|------------|
| When to use | High concurrency, WebFlux | Traditional applications |
| Libraries | DynamoDbAsyncClient | DynamoDbClient |
| Backpressure | Supported with Reactor | Not applicable |
| Enhanced Client | DynamoDbEnhancedAsyncClient | DynamoDbEnhancedClient |
| Complexity | Steeper learning curve | Simpler |

## Common access patterns

```
1. Get customer by ID: pk = CUSTOMER#id, sk = PROFILE
2. Get customer orders: pk = CUSTOMER#id, sk begins_with ORDER#
3. Get active customers: GSI1 pk = STATUS#ACTIVE
4. Get order items: pk = ORDER#id, sk begins_with ITEM#
```

## Main Content

### Dependencies

```xml
<dependency>
    <groupId>software.amazon.awssdk</groupId>
    <artifactId>dynamodb-enhanced</artifactId>
</dependency>
<dependency>
    <groupId>software.amazon.awssdk</groupId>
    <artifactId>netty-nio-client</artifactId>
</dependency>
```

### Async Client

```java
@Configuration
public class DynamoDbConfig {
    
    @Bean
    public DynamoDbAsyncClient dynamoDbAsyncClient() {
        return DynamoDbAsyncClient.builder()
            .region(Region.of(System.getenv("AWS_REGION")))
            .httpClientBuilder(NettyNioAsyncHttpClient.builder()
                .maxConcurrency(100))
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


### Entity with Enhanced Client

```java
@DynamoDbBean
public class Customer {
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
    
    public static Customer create(String id, String name, String email) {
        Customer customer = new Customer();
        customer.setPk("CUSTOMER#" + id);
        customer.setSk("PROFILE");
        customer.setName(name);
        customer.setEmail(email);
        customer.setStatus("ACTIVE");
        customer.setGsi1pk("STATUS#ACTIVE");
        customer.setGsi1sk(LocalDateTime.now().toString());
        return customer;
    }
}
```

### Reactive Repository

```java
@Repository
public class CustomerDynamoRepository {
    
    private final DynamoDbAsyncTable<Customer> table;
    
    public CustomerDynamoRepository(DynamoDbEnhancedAsyncClient client) {
        this.table = client.table("customers", TableSchema.fromBean(Customer.class));
    }
    
    public Mono<Customer> findById(String customerId) {
        Key key = Key.builder()
            .partitionValue("CUSTOMER#" + customerId)
            .sortValue("PROFILE")
            .build();
        
        return Mono.fromFuture(table.getItem(key));
    }
    
    public Flux<Customer> findByStatus(String status) {
        QueryConditional condition = QueryConditional.keyEqualTo(
            Key.builder().partitionValue("STATUS#" + status).build()
        );
        
        return Flux.from(table.index("GSI1").query(condition).items());
    }
    
    public Mono<Void> save(Customer customer) {
        return Mono.fromFuture(table.putItem(customer));
    }
    
    public Mono<Customer> update(Customer customer) {
        return Mono.fromFuture(table.updateItem(customer));
    }
}
```


### Transactions

```java
@Service
public class OrderService {
    
    private final DynamoDbEnhancedAsyncClient client;
    
    public Mono<Void> createOrderWithItems(Order order, List<OrderItem> items) {
        List<TransactWriteItem> writeItems = new ArrayList<>();
        
        writeItems.add(TransactWriteItem.builder()
            .put(Put.builder()
                .tableName("orders")
                .item(toAttributeMap(order))
                .conditionExpression("attribute_not_exists(pk)")
                .build())
            .build());
        
        for (OrderItem item : items) {
            writeItems.add(TransactWriteItem.builder()
                .put(Put.builder()
                    .tableName("orders")
                    .item(toAttributeMap(item))
                    .build())
                .build());
        }
        
        TransactWriteItemsRequest request = TransactWriteItemsRequest.builder()
            .transactItems(writeItems)
            .build();
        
        return Mono.fromFuture(client.transactWriteItems(request)).then();
    }
}
```

### Error Handling

```java
public Mono<Customer> findByIdWithRetry(String id) {
    return findById(id)
        .retryWhen(Retry.backoff(3, Duration.ofMillis(100))
            .filter(e -> e instanceof ProvisionedThroughputExceededException))
        .onErrorResume(ConditionalCheckFailedException.class,
            e -> Mono.error(new OptimisticLockException("Item was modified")));
}
```

## Important Rules

- Design the data model based on access patterns
- Use single-table design to reduce latency
- Use Enhanced Client for automatic entity mapping
- Implement GSI only when necessary
- Implement retry with backoff for ProvisionedThroughputExceededException
- Use transactions for atomic operations (max 100 items)
- Design composite keys for single-table design
- Consider DAX for read-intensive workloads
- Monitor consumed capacity and adjust as needed

## Example

```java
@RestController
@RequestMapping("/customers")
public class CustomerController {
    
    private final CustomerDynamoRepository repository;
    
    @GetMapping("/{id}")
    public Mono<ResponseEntity<Customer>> findById(@PathVariable String id) {
        return repository.findById(id)
            .map(ResponseEntity::ok)
            .defaultIfEmpty(ResponseEntity.notFound().build());
    }
    
    @PostMae patterns: `../06-resilience/`
- Hexagonal architecture: `../01-architecture/hexagonal-layers.md`
- Events with Streams: `eventbridge.java.md`
pping
    public Mono<ResponseEntity<Void>> create(@RequestBody CustomerRequest request) {
        Customer customer = Customer.create(
            UUID.randomUUID().toString(),
            request.name(),
            request.email()
        );
        return repository.save(customer)
            .then(Mono.just(ResponseEntity.created(
                URI.create("/customers/" + customer.getPk())).build()));
    }
}
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
