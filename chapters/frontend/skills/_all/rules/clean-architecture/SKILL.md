---
id: frontend-skill-clean-architecture
version: "1.0"
scope: chapter
type: skill
chapter: frontend
name: clean-architecture
description: Reglas para desarrollo con Clean Architecture. Activar cuando el proyecto use capas domain/application/infrastructure/presentation.
trigger: always_on
type: rule
---

Cada vez que te pida realizar una arquitectura limpia debes seguir estas reglas:

# Reglas para Clean Architecture

## Principios

- Separación de responsabilidades estricta.
- El dominio NO depende de frameworks ni infraestructura.
- Las dependencias siempre apuntan hacia el dominio (Dependency Rule).

## Capas

- Domain: entidades y lógica pura. No importa nada externo. Define interfaces (ports).
- Application: orquesta lógica de negocio. Solo depende de dominio.
- Infrastructure: implementa interfaces del dominio. HTTP, DB, APIs externas.
- Presentation: UI. Se conecta a Application, nunca directamente a Infrastructure.

## Reglas de dependencias

- Domain → NO depende de nadie
- Application → depende de Domain
- Infrastructure → depende de Domain
- Presentation → depende de Application
- NUNCA: Domain → Infrastructure, Presentation → Infrastructure directamente

## Diseño

- Entidades con comportamiento, no solo datos.
- Casos de uso con una responsabilidad clara, entrada/salida bien definida.
- Interfaces nombradas según intención: UserRepository, no PostgresUserRepository.
- Domain y application deben ser testeables sin infraestructura.

## Anti-patrones

- Lógica de negocio en controladores.
- Acceso directo a DB desde use cases.
- Entidades de dominio como DTOs.
- Mezclar lógica de infraestructura con dominio.
