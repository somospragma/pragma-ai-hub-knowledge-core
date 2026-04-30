<!-- keywords: health check, actuator, readiness, liveness, kubernetes, probe, spring boot actuator -->

# Reference: Health Check with Spring Boot Actuator

## Purpose

Configure Spring Boot Actuator health endpoints for Kubernetes readiness and liveness probes in Java microservices.

## Scope of Application

All Java Spring Boot microservices. MANDATORY.

## Step by Step / Guidelines

### 1. Dependency

In `gradle/libs.versions.toml`:

```toml
[libraries]
spring-boot-actuator = { module = "org.springframework.boot:spring-boot-starter-actuator" }
```

In `application/app-service/build.gradle`:

```groovy
dependencies {
    implementation libs.spring.boot.actuator
}
```

### 2. Configuration in `application.yml`

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health
  endpoint:
    health:
      probes:
        enabled: true
      show-details: never    # never in production, always in dev
  health:
    readinessstate:
      enabled: true
    livenessstate:
      enabled: true
```

### 3. Kubernetes probes

```yaml
# k8s deployment or cm.yaml
livenessProbe:
  httpGet:
    path: /actuator/health/liveness
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
readinessProbe:
  httpGet:
    path: /actuator/health/readiness
    port: 8080
  initialDelaySeconds: 15
  periodSeconds: 5
```

### 4. Security

- Only expose the `health` endpoint. Do NOT expose `env`, `beans`, `configprops`, or other actuator endpoints in production.
- If the service has authentication, the health endpoints MUST be excluded from auth filters.

## Verification Checklist

- [ ] `spring-boot-starter-actuator` in dependencies
- [ ] `management.endpoint.health.probes.enabled: true` in application.yml
- [ ] `/actuator/health/liveness` returns 200
- [ ] `/actuator/health/readiness` returns 200
- [ ] No other actuator endpoints exposed in production

## Tools and Resources

_(No additional information required for this section.)_
