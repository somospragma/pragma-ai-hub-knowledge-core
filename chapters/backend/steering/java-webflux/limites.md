---
id: backend-steering-java-webflux-limites
version: "1.0"
scope: stack
type: steering
chapter: backend
stack: java-webflux
---

# Límites — Java WebFlux

Restricciones específicas para proyectos con Spring WebFlux. Se aplican ADEMÁS de los límites transversales (`_all`) y comparten la base de Java Spring MVC con las siguientes diferencias y adiciones.

## Herencia de Java Spring MVC

Se aplican TODAS las restricciones de `java-spring` (Records para DTOs, prefijo I en interfaces, MapStruct obligatorio, base package `co.com.pragma.{nombre-servicio}`) EXCEPTO las que se sobreescriben aquí.

## Código no bloqueante

- NUNCA usar código bloqueante en ninguna capa.
- NUNCA usar `block()`, `blockFirst()`, `blockLast()` fuera de tests.
- NUNCA usar `Thread.sleep()`.
- NUNCA usar JDBC ni JPA (son bloqueantes por naturaleza).
- NUNCA usar `RestTemplate` ni `RestClient` (son bloqueantes).
- Si una librería de terceros es bloqueante, DEBE ejecutarse en un scheduler dedicado (`Schedulers.boundedElastic()`).

## Persistencia

- DEBE usarse R2DBC para acceso a base de datos relacional.
- Para MongoDB, usar ReactiveMongoRepository.
- NUNCA JPA/Hibernate en proyectos WebFlux.

## HTTP Client

- DEBE usarse `WebClient` para toda comunicación HTTP.
- NUNCA `RestTemplate` ni `RestClient`.

## Entry-points

- DEBE usarse `RouterFunction` + `HandlerFunction` para definir rutas.
- NUNCA usar `@RestController` en proyectos WebFlux.
- Las rutas se definen en clases `@Configuration` con `RouterFunction<ServerResponse>`.

## Manejo de errores

- DEBE implementarse un `WebExceptionHandler` global para manejo centralizado de errores.
- NUNCA usar `@ControllerAdvice` (es de Spring MVC).

## Tipos reactivos en dominio

- Los puertos del dominio (interfaces SPI) PUEDEN retornar `Mono<T>` o `Flux<T>`.
- Los UseCases PUEDEN retornar tipos reactivos.
- Esto es una excepción a la pureza del dominio, justificada por la naturaleza reactiva del stack.

## Lombok

- Lombok está PERMITIDO en proyectos WebFlux para reducir boilerplate.
- PERO los DTOs SIGUEN siendo Records (no `@Data`).
- Lombok se permite para builders, loggers (`@Slf4j`), y constructores en entities de infraestructura.
