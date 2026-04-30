<!-- keywords: onion architecture, spring boot, maven, microservice, java, archetype, separation of concerns, domain independence -->
# Onion Architecture Java Spring Boot with Maven Archetype

## Purpose

Provide a base structure for Java microservices using Onion Architecture with Spring Boot and Maven, focused on separation of responsibilities and domain independence.

## Scope of Application

- When starting a new Java microservice that requires concentric layered architecture.
- When Maven is preferred as the dependency manager over Gradle.
- For projects that need a clear separation between domain, application, infrastructure, and presentation.
- When looking for an alternative to hexagonal architecture with a similar approach.

## Main Content

### Layer Structure

Onion Architecture organizes code in concentric layers where dependencies flow inward:

1. **Domain (core):** Models, repositories (interfaces), and domain services.
2. **Application:** DTOs, mappers, and application services.
3. **Infrastructure:** Configuration, persistence, and external services.
4. **Presentation:** Controllers, presentation DTOs, and mappers.

### Folder Structure

```
com.example.myapp/
├── application/
│   ├── dto/
│   ├── mapper/
│   └── service/
├── domain/
│   ├── model/
│   ├── repository/
│   └── service/
├── infrastructure/
│   ├── config/
│   ├── persistence/
│   └── external/
└── presentation/
    ├── controller/
    ├── dto/
    └── mapper/
```

### Key Principles

- Inner layers do not know about outer layers.
- The domain is the core and has no external dependencies.
- Infrastructure implements the interfaces defined in the domain.
- Presentation only interacts with the application layer.

## Important Rules

- The domain MUST NEVER import classes from infrastructure or presentation.
- Repositories are defined as interfaces in the domain and implemented in infrastructure.
- Presentation DTOs are different from application DTOs.
- Framework configuration must be isolated in the infrastructure layer.
- Use mappers to convert between objects from different layers.

## Example

### Domain Model
```java
public class User {
    private Long id;
    private String name;
    private String email;
    // Business logic here
}
```

### Repository (interface in domain)
```java
public interface UserRepository {
    User findById(Long id);
    void save(User user);
}
```

### Implementation (infrastructure)
```java
@Repository
public class JpaUserRepository implements UserRepository {
    // JPA implementation
}
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
