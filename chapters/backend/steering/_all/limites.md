---
id: backend-steering-limites
version: "1.0"
scope: chapter
type: steering
chapter: backend
---

# Límites Absolutos — Restricciones Transversales

Estas restricciones NUNCA se violan, sin importar el stack, framework o contexto del proyecto.

## Arquitectura

- Si NO se especifica una arquitectura explícitamente → DEBE usarse arquitectura hexagonal multi-módulo.
- Un UseCase NUNCA llama a otro UseCase. No hay composición de casos de uso. Si necesitas orquestar, crea un nuevo UseCase dedicado.
- Las capas DEBEN respetar la dirección de dependencia: infraestructura → aplicación → dominio. NUNCA al revés.

## Archivos obligatorios

Todo proyecto DEBE contener como mínimo:

- `README.md` — Descripción, setup, ejecución, arquitectura.
- Archivo de build (`build.gradle`, `pom.xml`, `package.json`, etc.).
- `Dockerfile` — Multi-stage, optimizado para producción.
- Pipeline CI/CD (`.github/workflows/`, `azure-pipelines.yml`, `Jenkinsfile`, etc.).

## Seguridad

- NUNCA secrets en código fuente, archivos de configuración versionados, ni variables de entorno en el repositorio.
- SIEMPRE usar Secrets Manager, Parameter Store, o vault equivalente.
- NUNCA loguear información sensible (tokens, passwords, PII).

## Contratos

- NUNCA inventar campos, endpoints, o estructuras que no estén definidos en el contrato (OpenAPI, AsyncAPI, proto, etc.).
- Si el contrato no existe, DEBE crearse ANTES de implementar (API-First).
- Si hay ambigüedad en el contrato, PREGUNTAR antes de asumir.

## Código

- NUNCA dejar código muerto, comentado o sin usar.
- NUNCA usar `System.out.println`, `console.log` o equivalentes como mecanismo de logging.
- SIEMPRE manejar errores de forma explícita — no silenciar excepciones.
