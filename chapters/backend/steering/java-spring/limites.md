---
id: backend-steering-java-spring-limites
version: "1.0"
scope: stack
type: steering
chapter: backend
stack: java-spring
---

# Límites — Java Spring MVC

Restricciones específicas para proyectos con Spring MVC. Se aplican ADEMÁS de los límites transversales (`_all`).

## DTOs

- Los DTOs DEBEN ser Java Records. NUNCA clases con getters/setters.
- NUNCA usar `@Data` de Lombok para DTOs.
- Records son inmutables por diseño — eso es lo que queremos.

## Interfaces de puertos

- Toda interfaz de puerto (driven/driving) DEBE llevar prefijo `I`.
- Ejemplos correctos: `IUserRepository`, `IPaymentGateway`, `INotificationSender`.
- Ejemplos incorrectos: `UserRepository`, `PaymentGateway` (sin prefijo).

## Mapeo entre capas

- NUNCA escribir mappers estáticos manuales.
- SIEMPRE usar MapStruct con `@Mapper(componentModel = "spring")`.
- MapStruct es OBLIGATORIO para todo mapeo entre capas (domain ↔ DTO, domain ↔ entity).

## Estructura de paquetes

- Base package por defecto: `co.com.pragma.{nombre-servicio}`.
- Estructura interna DEBE seguir la arquitectura hexagonal:
  - `domain/model/` — Entidades y value objects del dominio.
  - `domain/usecase/` — Casos de uso.
  - `domain/spi/` — Puertos driven (interfaces que el dominio necesita).
  - `application/` — Puertos driving (entry-points).
  - `infrastructure/` — Adaptadores (persistencia, HTTP clients, etc.).

## Entry-points

- Los entry-points REST DEBEN usar `@RestController`.
- NUNCA lógica de negocio en controllers — solo delegación al UseCase.

## HTTP Client

- DEBE usarse `RestClient` (Spring 6.1+) para llamadas HTTP.
- NUNCA usar `RestTemplate` (deprecated).
- NUNCA usar `WebClient` en proyectos Spring MVC (es para WebFlux).

## Persistencia

- DEBE usarse JPA/Hibernate como ORM.
- Entities JPA DEBEN estar en la capa de infraestructura, NUNCA en dominio.
- El dominio NUNCA depende de anotaciones JPA.
