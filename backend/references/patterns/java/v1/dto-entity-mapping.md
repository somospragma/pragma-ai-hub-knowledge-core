<!-- keywords: dto, entity, mapping, mapstruct, data transformation, layer separation, java -->
# DTO-Entity Mapping Patterns — Java Implementation

## Purpose

Define the principles and strategies for mapping between DTOs and domain entities, and implementation in Java with MapStruct, ensuring layer separation and correct data transformation.

## Scope of Application

- When implementing transformation between layers (API → Domain → Persistence)
- When designing the structure of DTOs and entities
- When handling complex conversions between objects
- When implementing bidirectional mapping with MapStruct

## Main content

### Layer Separation

```
┌─────────────────────────────────────────────────────────────┐
│  API Layer          Domain Layer        Persistence Layer   │
│  ┌─────────┐       ┌─────────────┐      ┌──────────────┐   │
│  │ Request │ ───►  │   Entity    │ ───► │ DB Entity    │   │
│  │   DTO   │       │  (Domain)   │      │ (JPA/ORM)    │   │
│  └─────────┘       └─────────────┘      └──────────────┘   │
│  ┌─────────┐       ┌─────────────┐      ┌──────────────┐   │
│  │Response │ ◄───  │   Entity    │ ◄─── │ DB Entity    │   │
│  │   DTO   │       │  (Domain)   │      │ (JPA/ORM)    │   │
│  └─────────┘       └─────────────┘      └──────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Object Types

| Type | Purpose | Location |
|------|---------|----------|
| Request DTO | API input data | Presentation layer |
| Response DTO | API output data | Presentation layer |
| Domain Entity | Business logic | Domain layer |
| Persistence Entity | Database mapping | Infrastructure layer |
| Value Object | Immutable object without identity | Domain layer |

### Mapping Strategies

```
┌─────────────────────────────────────────────────────────────┐
│  1. MANUAL MAPPING - Full control, more code                │
│  2. LIBRARY MAPPING (MapStruct) - Compile-time, fast        │
│  3. REFLECTION MAPPING - Less code, lower performance       │
└─────────────────────────────────────────────────────────────┘
```

### Mapping Operations

| Operation | Description | Example |
|-----------|-------------|---------|
| toEntity | DTO → Entity | Request → Domain |
| toResponse | Entity → DTO | Domain → Response |
| toEntityList | List<DTO> → List<Entity> | Collections |
| updateEntity | DTO + Entity → Entity | Partial update |

### Best Practices

```
✓ Immutable DTOs when possible
✓ Validation in input DTOs
✓ Do not expose domain entities in API
✓ Mappers as injectable components
✓ Unit tests for mappers

✗ Business logic in mappers
✗ Circular mapping without control
✗ Reusing DTOs for different purposes
```

## Libraries and dependencies

```groovy
// build.gradle
plugins {
    id 'java'
}

dependencies {
    implementation 'org.mapstruct:mapstruct:1.5.5.Final'
    annotationProcessor 'org.mapstruct:mapstruct-processor:1.5.5.Final'
    
    // For Lombok + MapStruct
    compileOnly 'org.projectlombok:lombok:1.18.30'
    annotationProcessor 'org.projectlombok:lombok:1.18.30'
    annotationProcessor 'org.projectlombok:lombok-mapstruct-binding:0.2.0'
}
```

```xml
<!-- pom.xml -->
<dependencies>
    <dependency>
        <groupId>org.mapstruct</groupId>
        <artifactId>mapstruct</artifactId>
        <version>1.5.5.Final</version>
    </dependency>
</dependencies>

<build>
    <plugins>
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-compiler-plugin</artifactId>
            <configuration>
                <annotationProcessorPaths>
                    <path>
                        <groupId>org.mapstruct</groupId>
                        <artifactId>mapstruct-processor</artifactId>
                        <version>1.5.5.Final</version>
                    </path>
                </annotationProcessorPaths>
            </configuration>
        </plugin>
    </plugins>
</build>
```

## Step by Step / Guidelines

### Basic mapper with MapStruct

```java
@Mapper(
    componentModel = "spring",
    unmappedTargetPolicy = ReportingPolicy.ERROR,
    nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE
)
public interface OrderMapper {
    
    @Mapping(target = "id", ignore = true)
    @Mapping(target = "createdAt", expression = "java(java.time.Instant.now())")
    @Mapping(target = "status", constant = "PENDING")
    @Mapping(source = "items", target = "orderItems")
    Order toEntity(OrderRequest request);
    
    @Mapping(source = "orderItems", target = "items")
    @Mapping(source = "createdAt", target = "createdDate", dateFormat = "yyyy-MM-dd")
    OrderResponse toResponse(Order entity);
    
    List<OrderResponse> toResponseList(List<Order> entities);
    
    @BeanMapping(nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE)
    void updateEntity(OrderUpdateRequest request, @MappingTarget Order entity);
}
```

### Nested item mapper

```java
@Mapper(componentModel = "spring")
public interface OrderItemMapper {
    
    @Mapping(target = "id", ignore = true)
    @Mapping(source = "productId", target = "product.id")
    OrderItem toEntity(OrderItemRequest request);
    
    @Mapping(source = "product.id", target = "productId")
    @Mapping(source = "product.name", target = "productName")
    OrderItemResponse toResponse(OrderItem entity);
}
```

### Mapper with custom logic

```java
@Mapper(componentModel = "spring", uses = {OrderItemMapper.class})
public abstract class OrderMapperWithCustomLogic {
    
    @Autowired
    protected CustomerService customerService;
    
    @Mapping(target = "customer", source = "customerId", qualifiedByName = "resolveCustomer")
    @Mapping(target = "totalAmount", expression = "java(calculateTotal(request.getItems()))")
    public abstract Order toEntity(OrderRequest request);
    
    @Named("resolveCustomer")
    protected Customer resolveCustomer(String customerId) {
        return customerService.findById(customerId)
            .orElseThrow(() -> new CustomerNotFoundException(customerId));
    }
    
    protected BigDecimal calculateTotal(List<OrderItemRequest> items) {
        return items.stream()
            .map(item -> item.getUnitPrice().multiply(BigDecimal.valueOf(item.getQuantity())))
            .reduce(BigDecimal.ZERO, BigDecimal::add);
    }
}
```

### DTOs with validation

```java
@Data
public class OrderRequest {
    
    @NotNull(message = "Customer ID is required")
    private String customerId;
    
    @NotEmpty(message = "Items cannot be empty")
    @Valid
    private List<OrderItemRequest> items;
    
    @NotNull
    @Pattern(regexp = "^[A-Z]{3}$")
    private String currency;
}

@Data
public class OrderItemRequest {
    
    @NotBlank
    private String productId;
    
    @NotNull
    @Min(1)
    private Integer quantity;
    
    @NotNull
    @DecimalMin("0.01")
    private BigDecimal unitPrice;
}
```

### Usage in Service

```java
@Service
public class OrderService {
    
    private final OrderMapper orderMapper;
    private final OrderRepository orderRepository;
    
    public OrderResponse createOrder(OrderRequest request) {
        Order entity = orderMapper.toEntity(request);
        Order saved = orderRepository.save(entity);
        return orderMapper.toResponse(saved);
    }
    
    public OrderResponse updateOrder(String id, OrderUpdateRequest request) {
        Order entity = orderRepository.findById(id)
            .orElseThrow(() -> new OrderNotFoundException(id));
        orderMapper.updateEntity(request, entity);
        Order updated = orderRepository.save(entity);
        return orderMapper.toResponse(updated);
    }
}
```

## Configuration

### Global MapStruct configuration

```java
@MapperConfig(
    componentModel = "spring",
    unmappedTargetPolicy = ReportingPolicy.ERROR,
    nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE,
    nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS
)
public interface MapStructConfig {
}

// Usage in mappers
@Mapper(config = MapStructConfig.class)
public interface OrderMapper {
    // ...
}
```

## Mocks and fixtures

### Mapper test

```java
@ExtendWith(MockitoExtension.class)
class OrderMapperTest {
    
    @Spy
    private OrderMapper orderMapper = Mappers.getMapper(OrderMapper.class);
    
    @Test
    void shouldMapRequestToEntity() {
        OrderRequest request = new OrderRequest();
        request.setCustomerId("cust-123");
        request.setItems(List.of(createItemRequest()));
        request.setCurrency("USD");
        
        Order entity = orderMapper.toEntity(request);
        
        assertThat(entity.getStatus()).isEqualTo("PENDING");
        assertThat(entity.getCreatedAt()).isNotNull();
    }
}
```

## Important Rules

1. **Separation**: Keep DTOs separate from domain entities
2. **Immutability**: Prefer mapping to new instances over mutation
3. **Null Safety**: Handle null values explicitly
4. **Validation**: Validate DTOs before mapping
5. **Performance**: Use generated mappers (MapStruct) over reflection
6. **Bidirectional**: Define mapping in both directions when needed
7. **Testing**: Test mappers with edge cases

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
