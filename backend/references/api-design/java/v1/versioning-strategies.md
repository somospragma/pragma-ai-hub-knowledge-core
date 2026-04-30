<!-- keywords: api versioning, url versioning, header versioning, media type, backward compatibility, deprecation, version adapter, spring boot, java -->
# API Versioning Strategies — Java Implementation

## Purpose

Define the standard strategies for REST API versioning and implementation in Java with Spring Boot, including URL path versioning, header (media type) versioning, deprecation, backward compatibility, and version adapters.

## Scope of Application

- When designing a new API that will evolve over time
- When planning breaking changes in existing APIs
- When implementing deprecation strategies
- When maintaining multiple versions of an API
- When migrating consumers between versions

## Main content

### Versioning Strategies

```
┌─────────────────────────────────────────────────────────────────┐
│                    Versioning Strategies                          │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   URL Path      │   Header        │   Query Parameter           │
│   /v1/orders    │   Api-Version:1 │   /orders?version=1         │
│   (Recommended) │   (Alternative) │   (Not recommended)         │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

### Deprecation Strategy

```yaml
versioning:
  current: v2
  supported:
    - version: v2
      status: current
      released: 2024-01-01
    - version: v1
      status: deprecated
      released: 2023-01-01
      sunset: 2024-06-01
      migration_guide: /docs/migration/v1-to-v2

  deprecation_policy:
    notice_period: 6 months
    support_after_deprecation: 12 months

  headers:
    deprecated_version:
      - Deprecation: "true"
      - Sunset: "<sunset_date>"
      - Link: '<new_version_url>; rel="successor-version"'
```

## URL Path Versioning - Spring Boot

```java
// URL versioning configuration
@Configuration
public class ApiVersionConfig {

    @Bean
    public WebMvcConfigurer webMvcConfigurer() {
        return new WebMvcConfigurer() {
            @Override
            public void configurePathMatch(PathMatchConfigurer configurer) {
                configurer.addPathPrefix("/v1",
                    c -> c.isAnnotationPresent(ApiV1.class));
                configurer.addPathPrefix("/v2",
                    c -> c.isAnnotationPresent(ApiV2.class));
            }
        };
    }
}

// Version annotations
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
public @interface ApiV1 {}

@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
public @interface ApiV2 {}

// V1 Controller (deprecated)
@RestController
@ApiV1
@Deprecated
@RequestMapping("/orders")
public class OrderControllerV1 {

    @GetMapping
    public ResponseEntity<List<OrderResponseV1>> listOrders() {
        // V1 implementation
        return ResponseEntity.ok()
            .header("Deprecation", "true")
            .header("Sunset", "Sat, 01 Jun 2024 00:00:00 GMT")
            .header("Link", "</v2/orders>; rel=\"successor-version\"")
            .body(orderService.listOrdersV1());
    }
}

// V2 Controller (current)
@RestController
@ApiV2
@RequestMapping("/orders")
public class OrderControllerV2 {

    @GetMapping
    public ResponseEntity<PagedResponse<OrderResponseV2>> listOrders(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return ResponseEntity.ok(orderService.listOrdersV2(page, size));
    }
}
```

## Header Versioning (Media Type)

```java
// Header versioning configuration
@Configuration
public class HeaderVersionConfig implements WebMvcConfigurer {

    @Override
    public void configureContentNegotiation(ContentNegotiationConfigurer configurer) {
        configurer
            .favorParameter(false)
            .ignoreAcceptHeader(false)
            .defaultContentType(MediaType.APPLICATION_JSON)
            .mediaType("v1", MediaType.valueOf("application/vnd.company.v1+json"))
            .mediaType("v2", MediaType.valueOf("application/vnd.company.v2+json"));
    }
}

// Controller with media type versioning
@RestController
@RequestMapping("/orders")
public class OrderController {

    @GetMapping(produces = "application/vnd.company.v1+json")
    public OrderResponseV1 getOrderV1(@PathVariable String id) {
        return orderService.getOrderV1(id);
    }

    @GetMapping(produces = "application/vnd.company.v2+json")
    public OrderResponseV2 getOrderV2(@PathVariable String id) {
        return orderService.getOrderV2(id);
    }
}
```

## Version Compatibility Adapter

```java
// Compatibility adapter
@Component
public class OrderVersionAdapter {

    public OrderResponseV2 toV2(OrderResponseV1 v1) {
        return OrderResponseV2.builder()
            .id(v1.getId())
            .customerId(v1.getCustomerId())
            .items(List.of()) // New field, empty by default
            .totalAmount(v1.getTotal())
            .currency("USD") // New field with default
            .status(v1.getStatus())
            .createdAt(Instant.now()) // New field
            .build();
    }

    public OrderResponseV1 toV1(OrderResponseV2 v2) {
        return OrderResponseV1.builder()
            .id(v2.getId())
            .customerId(v2.getCustomerId())
            .total(v2.getTotalAmount())
            .status(v2.getStatus())
            .build();
    }
}
```

## Important Rules

1. **URL Path**: Prefer URL versioning for clarity
2. **Semantics**: Use semantic versioning (major.minor.patch)
3. **Breaking Changes**: Only increment major for incompatible changes
4. **Deprecation**: Announce with at least 6 months notice
5. **Headers**: Include Deprecation, Sunset, and Link in deprecated versions
6. **Documentation**: Keep migration guides up to date
7. **Support**: Maintain at least 2 active versions

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
