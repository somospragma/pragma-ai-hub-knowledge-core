<!-- keywords: request parameter validator, webflux, validation, abstract class, entry-point, reactive, java -->
# RequestParameterValidator — Abstract Validation Pattern for WebFlux Entry-Points

## Purpose

Provide a reusable abstract class that lives in the `infrastructure/helpers/` module for validating query parameters, path variables, and request bodies in WebFlux reactive entry-points. Concrete validators extend this class per endpoint, keeping validation logic consistent and DRY across all inbound adapters.

## Scope of Application

- When implementing a reactive WebFlux entry-point (`reactive-web`) that needs to validate `ServerRequest` parameters.
- When you need to validate required query params and/or path variables before invoking a use case.
- When you want a consistent, testable validation pattern shared across multiple Router/Handler pairs.
- When adding business-rule validation that returns `Mono<T>` for reactive pipelines.

## Location

```
infrastructure/helpers/src/main/java/{package}/helper/RequestParameterValidator.java
```

This class belongs in the shared `infrastructure/helpers` module because it is a cross-cutting infrastructure concern used by multiple entry-points. It is NOT business logic — it validates protocol-level inputs before they reach the domain.

## Pattern

```
┌─────────────────────────────────────────────────────────────┐
│           RequestParameterValidator (abstract)               │
│                                                             │
│  #validateQueryParams(ServerRequest, List<String>)          │
│  #validatePathVariables(Map<String,String>, List<String>)   │
│  #validateParameters(ServerRequest, Map, List, List)        │
│                                                             │
│  + static validateBusinessRules(T request): Mono<T>         │
│    (pattern — implemented per concrete validator)            │
└──────────────────────┬──────────────────────────────────────┘
                       │ extends
          ┌────────────┴────────────────┐
          │  MyEndpointValidator        │
          │                             │
          │  + validate(ServerRequest)  │
          │  + static validateXyz(...)  │
          └─────────────────────────────┘
```

- The abstract class provides **protected** methods for query-param and path-variable validation.
- Concrete validators extend it and compose the protected methods for their specific endpoint requirements.
- Business-rule validation follows a **static method pattern** returning `Mono<T>`, suitable for chaining in reactive pipelines.

## Code Example — Abstract Class

```java
package {base.package}.helper;

import {base.package}.lib.core.exception.BadRequestException;
import org.springframework.web.reactive.function.server.ServerRequest;
import reactor.core.publisher.Mono;

import java.util.List;
import java.util.Map;
import java.util.stream.Stream;

/**
 * Abstract base for validating query params, path variables, and request bodies
 * in WebFlux reactive entry-points.
 *
 * Concrete validators extend this class per endpoint.
 */
public abstract class RequestParameterValidator {

    /**
     * Validates that all required query parameters are present and non-blank.
     *
     * @param request         the incoming ServerRequest
     * @param requiredParams  list of required query parameter names
     * @throws BadRequestException if any parameter is missing or blank
     */
    protected void validateQueryParams(ServerRequest request, List<String> requiredParams) {
        for (String param : requiredParams) {
            String value = request.queryParam(param).orElse(null);
            if (value == null || value.trim().isEmpty()) {
                throw new BadRequestException(
                    "Required query parameter missing or empty: " + param);
            }
        }
    }

    /**
     * Validates that all required path variables are present and non-blank.
     *
     * @param pathVariables      map of path variable name → value
     * @param requiredVariables  list of required path variable names
     * @throws BadRequestException if any variable is missing or blank
     */
    protected void validatePathVariables(Map<String, String> pathVariables,
                                         List<String> requiredVariables) {
        for (String variable : requiredVariables) {
            String value = pathVariables.get(variable);
            if (value == null || value.trim().isEmpty()) {
                throw new BadRequestException(
                    "Required path variable missing or empty: " + variable);
            }
        }
    }

    /**
     * Combines query-param and path-variable validation in a single call.
     * Pass null for either list to skip that validation.
     */
    protected void validateParameters(ServerRequest request,
                                      Map<String, String> pathVariables,
                                      List<String> requiredQueryParams,
                                      List<String> requiredPathVariables) {
        if (requiredQueryParams != null) {
            validateQueryParams(request, requiredQueryParams);
        }
        if (requiredPathVariables != null) {
            validatePathVariables(pathVariables, requiredPathVariables);
        }
    }
}
```

### Static Business-Rule Validation Pattern

When a request body needs domain-level field validation before reaching the use case, add a **static method** returning `Mono<T>` so it chains naturally in a reactive pipeline:

```java
/**
 * Example: validate that all required fields in a request DTO are present
 * and that a specific field matches an allowed value.
 *
 * This is a PATTERN — adapt the field checks and rules to your domain.
 */
public static Mono<MyRequest> validateBusinessRules(MyRequest request) {
    if (isAnyFieldMissing(request)) {
        return Mono.error(new BadRequestException("Missing required fields in request"));
    }

    // Example: enforce an allowed value for a specific field
    if (!"EXPECTED_VALUE".equalsIgnoreCase(request.someField())) {
        return Mono.error(new BadRequestException(
            "Invalid someField. Only 'EXPECTED_VALUE' is supported."));
    }

    return Mono.just(request);
}

private static boolean isAnyFieldMissing(MyRequest request) {
    return Stream.of(
            request.fieldA(),
            request.fieldB(),
            request.fieldC()
    ).anyMatch(field -> field == null || field.trim().isEmpty());
}
```

This static method is typically called from the Handler:

```java
// Inside a WebFlux Handler method
public Mono<ServerResponse> handle(ServerRequest request) {
    return request.bodyToMono(MyRequest.class)
        .flatMap(MyEndpointValidator::validateBusinessRules)
        .flatMap(validRequest -> myUseCase.execute(mapper.toDomain(validRequest)))
        .flatMap(result -> ServerResponse.ok().bodyValue(mapper.toResponse(result)));
}
```

## Usage Example — Concrete Validator

A concrete validator extends the abstract class and composes the protected methods for a specific endpoint:

```java
package {base.package}.helper;

import org.springframework.web.reactive.function.server.ServerRequest;

import java.util.List;
import java.util.Map;

/**
 * Validates parameters for the GET /api/v1/accounts/{accountId}/transactions endpoint.
 */
public class TransactionRetrieveValidator extends RequestParameterValidator {

    private static final List<String> REQUIRED_QUERY_PARAMS = List.of("fromDate", "toDate");
    private static final List<String> REQUIRED_PATH_VARS = List.of("accountId");

    /**
     * Validates all required parameters for the transaction retrieve endpoint.
     */
    public void validate(ServerRequest request) {
        Map<String, String> pathVariables = request.pathVariables();
        validateParameters(request, pathVariables, REQUIRED_QUERY_PARAMS, REQUIRED_PATH_VARS);
    }
}
```

Usage from a WebFlux Handler:

```java
@Component
public class TransactionHandler {

    private final GetTransactionsUseCase useCase;
    private final TransactionRetrieveValidator validator = new TransactionRetrieveValidator();

    public TransactionHandler(GetTransactionsUseCase useCase) {
        this.useCase = useCase;
    }

    public Mono<ServerResponse> getTransactions(ServerRequest request) {
        validator.validate(request);  // throws BadRequestException if invalid

        String accountId = request.pathVariable("accountId");
        String fromDate = request.queryParam("fromDate").orElseThrow();
        String toDate = request.queryParam("toDate").orElseThrow();

        return useCase.execute(accountId, fromDate, toDate)
            .flatMap(result -> ServerResponse.ok().bodyValue(result));
    }
}
```

## Test Example

Since `RequestParameterValidator` is abstract, test it through an anonymous concrete subclass. Use Mockito to mock `ServerRequest`.

```java
package {base.package}.helper;

import {base.package}.lib.core.exception.BadRequestException;
import org.junit.jupiter.api.Test;
import org.springframework.web.reactive.function.server.ServerRequest;

import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class RequestParameterValidatorTest {

    // Instantiate via anonymous subclass to test the abstract class
    private final RequestParameterValidator validator = new RequestParameterValidator() {};

    // --- validateQueryParams ---

    @Test
    void validateQueryParams_allPresent_doesNotThrow() {
        var request = mock(ServerRequest.class);
        when(request.queryParam("status")).thenReturn(Optional.of("ACTIVE"));
        assertDoesNotThrow(() -> validator.validateQueryParams(request, List.of("status")));
    }

    @Test
    void validateQueryParams_missing_throwsBadRequest() {
        var request = mock(ServerRequest.class);
        when(request.queryParam("status")).thenReturn(Optional.empty());
        assertThrows(BadRequestException.class,
            () -> validator.validateQueryParams(request, List.of("status")));
    }

    @Test
    void validateQueryParams_empty_throwsBadRequest() {
        var request = mock(ServerRequest.class);
        when(request.queryParam("status")).thenReturn(Optional.of(""));
        assertThrows(BadRequestException.class,
            () -> validator.validateQueryParams(request, List.of("status")));
    }

    @Test
    void validateQueryParams_blank_throwsBadRequest() {
        var request = mock(ServerRequest.class);
        when(request.queryParam("status")).thenReturn(Optional.of("   "));
        assertThrows(BadRequestException.class,
            () -> validator.validateQueryParams(request, List.of("status")));
    }

    // --- validatePathVariables ---

    @Test
    void validatePathVariables_allPresent_doesNotThrow() {
        assertDoesNotThrow(
            () -> validator.validatePathVariables(Map.of("id", "123"), List.of("id")));
    }

    @Test
    void validatePathVariables_missing_throwsBadRequest() {
        assertThrows(BadRequestException.class,
            () -> validator.validatePathVariables(Map.of(), List.of("id")));
    }

    @Test
    void validatePathVariables_empty_throwsBadRequest() {
        assertThrows(BadRequestException.class,
            () -> validator.validatePathVariables(Map.of("id", ""), List.of("id")));
    }

    @Test
    void validatePathVariables_blank_throwsBadRequest() {
        assertThrows(BadRequestException.class,
            () -> validator.validatePathVariables(Map.of("id", "  "), List.of("id")));
    }

    // --- validateParameters (combined) ---

    @Test
    void validateParameters_bothNull_doesNotThrow() {
        var request = mock(ServerRequest.class);
        assertDoesNotThrow(
            () -> validator.validateParameters(request, Map.of(), null, null));
    }

    @Test
    void validateParameters_bothProvided_allValid_doesNotThrow() {
        var request = mock(ServerRequest.class);
        when(request.queryParam("q")).thenReturn(Optional.of("value"));
        assertDoesNotThrow(
            () -> validator.validateParameters(
                request, Map.of("p", "value"), List.of("q"), List.of("p")));
    }
}
```

## Build Configuration (build.gradle)

The `infrastructure/helpers` module depends on `domain:model`, `domain:ports`, and `spring-boot-starter-webflux`:

```groovy
// infrastructure/helpers/build.gradle
dependencies {
    implementation project(':domain:model')
    implementation project(':domain:ports')
    implementation 'org.springframework.boot:spring-boot-starter-webflux'
}
```

Test dependencies (typically inherited from a root `subprojects` block):

```groovy
testImplementation 'org.springframework.boot:spring-boot-starter-test'
testImplementation 'io.projectreactor:reactor-test'
testImplementation 'org.mockito:mockito-core'
```

## Step by Step / Guidelines

| # | Guideline |
|---|-----------|
| 1 | The abstract class lives in `infrastructure/helpers`, NOT inside a specific entry-point. It is shared across all reactive entry-points. |
| 2 | Protected methods (`validateQueryParams`, `validatePathVariables`, `validateParameters`) handle protocol-level validation only — presence and non-blankness of parameters. |
| 3 | Business-rule validation (field format, allowed values, cross-field rules) goes in static methods returning `Mono<T>` so they compose in reactive pipelines. |
| 4 | Each endpoint gets its own concrete validator class (e.g., `TransactionRetrieveValidator`) that extends the abstract class and defines which params/variables are required. |
| 5 | Validation errors throw `BadRequestException` (from the project's core exception library), which the global exception handler translates to HTTP 400. |
| 6 | Do NOT put business logic in validators. If a rule depends on data from a Gateway or external service, it belongs in the use case, not here. |
| 7 | Keep the abstract class minimal. If a validation concern is specific to one adapter, put it in that adapter's own `helpers/` sub-package. |

## Verification Checklist

- [ ] Abstract class is in `infrastructure/helpers/src/main/java/{package}/helper/`.
- [ ] Concrete validators extend `RequestParameterValidator`.
- [ ] All required query params and path variables are validated before calling the use case.
- [ ] `BadRequestException` is thrown for missing/blank parameters.
- [ ] Business-rule static methods return `Mono<T>` (not `void`).
- [ ] Unit tests cover: present params, missing params, empty params, blank params.
- [ ] `build.gradle` for `helpers` declares dependencies on `domain:model`, `domain:ports`, and `spring-boot-starter-webflux`.
- [ ] No business logic leaks into the validator — only protocol-level and structural checks.

## Tools and Resources

_(No additional information required for this section.)_
