---
id: backend-steering-java-spring-decisiones
version: "1.0"
scope: stack
type: steering
chapter: backend
stack: java-spring
---

# Decisiones Técnicas Obligatorias — Java Spring MVC

Decisiones específicas para proyectos con Spring MVC. Se aplican ADEMÁS de las decisiones transversales (`_all`).

## JaCoCo

- JaCoCo es OBLIGATORIO en todo proyecto Java Spring.
- Cobertura mínima en módulo de dominio: **80%**.
- Cobertura mínima general: **70%**.
- El build DEBE fallar si no se cumple el umbral de cobertura.
- Configurar exclusiones solo para clases generadas (MapStruct, Lombok).

## OWASP Dependency Check

- OWASP Dependency Check es OBLIGATORIO en el pipeline CI.
- DEBE ejecutarse en cada build.
- El build DEBE fallar si se detectan vulnerabilidades con CVSS ≥ 7 (High/Critical).
- DEBE generarse reporte en formato HTML y JSON.

## SonarQube

- SonarQube es OBLIGATORIO.
- El quality gate DEBE pasar para que el build sea exitoso.
- Métricas mínimas:
  - Cobertura: según umbrales de JaCoCo.
  - Duplicación: máximo 3%.
  - Code smells: 0 blocker/critical.
  - Vulnerabilidades: 0.

## ArchUnit

- ArchUnit es OBLIGATORIO para validación arquitectónica.
- DEBE validar como mínimo:
  - Dominio NO depende de infraestructura ni de frameworks.
  - UseCases solo son accedidos desde la capa de aplicación.
  - Entities JPA solo existen en infraestructura.
  - No hay dependencias cíclicas entre paquetes.
- Los tests de ArchUnit DEBEN ejecutarse en cada build.

## Pitest (Mutation Testing)

- Pitest es OBLIGATORIO en el módulo de dominio.
- Mutation score mínimo: **60%**.
- DEBE ejecutarse al menos en el pipeline de CI (puede ser stage separado).
- Configurar para mutar solo clases del dominio (excluir infraestructura y configuración).
