<!-- keywords: openapi, springdoc, swagger, api documentation, openapi 3, spring boot, annotations, java -->
# Reference: OpenAPI Documentation with springdoc-openapi

## Purpose

Provide the standard configuration and annotation patterns for auto-generating OpenAPI 3.x documentation in Java Spring Boot 3+ microservices using springdoc-openapi.

## Scope of Application

- All Java microservices (WebFlux reactive and MVC imperative).
- Spring Boot 3+ with Jakarta namespace.
- MANDATORY for all projects (see decision `012 - Architectural API Documentation`).

## Step by Step / Guidelines

### 1. Add springdoc-openapi dependency

In `gradle/libs.versions.toml`:

```toml
[versions]
springdoc = "2.8.0"

[libraries]
# For WebFlux (reactive):
springdoc-openapi-webflux-ui = { module = "org.springdoc:springdoc-openapi-starter-webflux-ui", version.ref = "springdoc" }
# For MVC (imperative):
springdoc-openapi-webmvc-ui = { module = "org.springdoc:springdoc-openapi-starter-webmvc-ui", version.ref = "springdoc" }
```

In the entry-point module `build.gradle`:

```groovy
dependencies {
    implementation libs.springdoc.openapi.webflux.ui  // or webmvc-ui
}
```

### 2. Application configuration

In `application.yml`:

```yaml
springdoc:
  api-docs:
    path: /v3/api-docs
  swagger-ui:
    path: /swagger-ui.html
    enabled: true
  show-actuator: false
```

> Disable Swagger UI in production via profile-specific config or environment variable.

### 3. OpenAPI info configuration

Programmatic approach (recommended):

```java
@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
            .info(new Info()
                .title("My Service API")
                .version("1.0.0")
                .description("API documentation for My Service"));
    }
}
```

Alternatively, use `@OpenAPIDefinition` on the main application class:

```java
@OpenAPIDefinition(
    info = @io.swagger.v3.oas.annotations.info.Info(
        title = "My Service API",
        version = "1.0.0",
        description = "API documentation for My Service"
    )
)
@SpringBootApplication
public class MainApplication { }
```

### 4. Annotating WebFlux Router Functions

For reactive projects using functional endpoints, annotate with `@RouterOperation`:

```java
@Configuration
public class CustomerRouter {

    @Bean
    @RouterOperation(
        path = "/api/v1/customers/{id}",
        method = RequestMethod.GET,
        operation = @Operation(
            operationId = "getCustomerById",
            summary = "Get customer by ID",
            responses = {
                @ApiResponse(responseCode = "200", description = "Customer found"),
                @ApiResponse(responseCode = "404", description = "Customer not found")
            }
        )
    )
    public RouterFunction<ServerResponse> getCustomerRoute(CustomerHandler handler) {
        return RouterFunctions.route(
            GET("/api/v1/customers/{id}"), handler::getById);
    }
}
```

### 5. Annotating MVC RestControllers

For imperative projects, annotate controllers directly:

```java
@RestController
@RequestMapping("/api/v1/customers")
@Tag(name = "Customers", description = "Customer management operations")
public class CustomerController {

    @Operation(
        summary = "Create a new customer",
        description = "Creates a customer and returns the generated ID"
    )
    @ApiResponse(responseCode = "201", description = "Customer created")
    @ApiResponse(responseCode = "400", description = "Invalid request body")
    @PostMapping
    public ResponseEntity<CustomerResponse> create(
            @RequestBody @Valid CreateCustomerRequest request) {
        // ...
    }
}
```

### 6. Schema annotations on DTOs

```java
@Schema(description = "Request to create a new customer")
public record CreateCustomerRequest(
    @Schema(description = "Full name", example = "John Doe", requiredMode = REQUIRED)
    String name,
    @Schema(description = "Email address", example = "john@example.com", requiredMode = REQUIRED)
    String email
) {}
```

## Verification Checklist

- [ ] springdoc-openapi dependency declared in `libs.versions.toml` and `build.gradle`
- [ ] `application.yml` configures `springdoc.api-docs.path` and `springdoc.swagger-ui.path`
- [ ] OpenAPI info (title, version, description) is configured
- [ ] All endpoints have `@Operation` with summary and response codes
- [ ] DTOs have `@Schema` annotations with descriptions and examples
- [ ] `/v3/api-docs` returns valid OpenAPI JSON
- [ ] `/swagger-ui.html` renders the interactive UI
- [ ] Swagger UI is disabled in production profile

## Tools and Resources

- `springdoc-openapi-starter-webflux-ui:2.8.0` — WebFlux support
- `springdoc-openapi-starter-webmvc-ui:2.8.0` — MVC support
- Swagger UI — bundled with springdoc, accessible at configured path
