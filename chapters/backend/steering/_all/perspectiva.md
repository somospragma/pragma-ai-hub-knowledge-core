---
id: backend-steering-perspectiva
version: "1.0"
scope: chapter
type: steering
chapter: backend
---

# Perspectiva del Chapter Backend de Pragma

## Principio rector

Arquitectura primero, código después. NUNCA escribas código sin tener clara la arquitectura del sistema. Toda decisión de implementación DEBE estar respaldada por una decisión arquitectónica previa.

## Jerarquía de valores de ingeniería

SIEMPRE prioriza en este orden estricto. Ante conflictos, el valor superior gana:

1. **Seguridad** — Proteger datos, accesos y comunicaciones es innegociable.
2. **Confiabilidad** — El sistema DEBE funcionar correctamente bajo condiciones esperadas e inesperadas.
3. **Observabilidad** — Todo comportamiento del sistema DEBE ser visible, trazable y medible.
4. **Mantenibilidad** — El código DEBE ser legible, modular y fácil de modificar.
5. **Escalabilidad** — El diseño DEBE soportar crecimiento sin rediseño fundamental.
6. **Performance** — Optimizar SOLO después de garantizar los valores anteriores.

## Lo que SIEMPRE defendemos

- Arquitectura hexagonal (puertos y adaptadores) como estándar.
- Domain-Driven Design (DDD) para modelar el dominio.
- API-First: el contrato se define ANTES de implementar.
- Principios SOLID en toda clase y módulo.
- Circuit Breaker para llamadas a servicios externos.
- Structured Logging en formato JSON con correlationId.
- Secrets Manager / Parameter Store para toda credencial y configuración sensible.

## Lo que NUNCA toleramos

- Monolitos sin estructura interna clara.
- God classes (clases con más de una responsabilidad).
- Secrets hardcodeados en código, properties o variables de entorno en repositorio.
- Catch-all exceptions sin manejo específico ni logging adecuado.
- Tests sin assertions reales (tests que solo ejecutan código sin verificar comportamiento).
