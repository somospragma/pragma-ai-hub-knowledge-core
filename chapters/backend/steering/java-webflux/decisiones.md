---
id: backend-steering-java-webflux-decisiones
version: "1.0"
scope: stack
type: steering
chapter: backend
stack: java-webflux
---

# Decisiones Técnicas Obligatorias — Java WebFlux

Decisiones específicas para proyectos con Spring WebFlux. Se aplican ADEMÁS de las decisiones transversales (`_all`) y las decisiones de Java Spring MVC.

## Herencia de Java Spring MVC

Se aplican TODAS las decisiones de `java-spring` (JaCoCo, OWASP Dependency Check, SonarQube, ArchUnit, Pitest) con las mismas configuraciones y umbrales.

## Testing Reactivo

- StepVerifier es OBLIGATORIO para todo test unitario de código reactivo.
- NUNCA usar `block()` en tests para extraer valores — SIEMPRE usar StepVerifier.
- Verificar tanto el flujo de datos como las señales de completado/error.
- Ejemplo de patrón obligatorio:
  ```java
  StepVerifier.create(useCase.execute(input))
      .expectNext(expectedResult)
      .verifyComplete();
  ```

## Tests de Integración

- WebTestClient es OBLIGATORIO para tests de integración de endpoints.
- DEBE usarse en lugar de MockMvc (que es de Spring MVC).
- Los tests DEBEN verificar status code, headers y body de respuesta.

## Detección de código bloqueante

- BlockHound DEBE configurarse en el entorno de tests cuando sea aplicable.
- Si BlockHound detecta una operación bloqueante en un thread no-blocking, el test DEBE fallar.
- Excepciones permitidas DEBEN documentarse explícitamente con justificación.
- Si BlockHound no es compatible con la versión de JDK utilizada, documentar la razón y usar análisis estático como alternativa.
