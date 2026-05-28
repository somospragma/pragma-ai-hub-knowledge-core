---
id: calidad-security-testing
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Estrategia de pruebas de seguridad para APIs y aplicaciones: OWASP Top 10 API, fuzzing, SAST/DAST/SCA, autenticación."
tags: [security, owasp, zap, fuzzing, dast, sast, sca, authentication]
---

# Security Testing — Estrategia de Pruebas de Seguridad

## Cuándo aplicar

Aplica cada vez que se entregue una suite de pruebas para una aplicación web, mobile o sus integraciones backend con requisitos de compliance, datos sensibles o exposición regulatoria — sin presunción de sector específico (salud, financiero, gobierno, retail, gaming, SaaS, etc.).

En clientes del scope del Chapter (LATAM + Estados Unidos) con requisitos de compliance (PCI-DSS 4.0, OWASP API Top 10 2023, ISO 27001, SOC 2; HIPAA / SOX / CCPA/CPRA / FedRAMP en Estados Unidos; Ley 1581 Colombia, LGPD Brasil, LFPDPPP México, Ley 19.628/21.719 Chile, Ley 25.326 Argentina, Ley 29.733 Perú, y equivalentes locales LATAM) la cobertura mínima de seguridad alineada con OWASP API Security Top 10 2023 es **obligatoria**: ninguna suite funcional/regresión se entrega sin ella.

Activa este skill en paralelo con la generación funcional (`[[karate-greenfield]]`, `[[karate-brownfield]]`, `[[playwright-greenfield]]`, `[[k6-greenfield]]`) y aplica la perspectiva de chapter `[[calidad-chapter-perspective]]` para decidir el alcance.

## Instrucción

1. **Clasificar el riesgo del sistema bajo prueba** — ¿maneja PII?, ¿datos financieros o transaccionales?, ¿está bajo un marco regulatorio del alcance (PCI-DSS, OWASP API Top 10, ISO 27001, SOC 2; HIPAA / SOX / CCPA/CPRA / FedRAMP en Estados Unidos; Ley 1581 Colombia, LGPD Brasil, LFPDPPP México, Ley 19.628/21.719 Chile, Ley 25.326 Argentina, Ley 29.733 Perú, y equivalentes locales LATAM)?. Documenta la respuesta como artefacto inicial. Si la respuesta es sí en cualquier eje, el alcance de seguridad es **obligatorio** (no opcional).
2. **Mapear contra OWASP API Security Top 10 2023** — Recorre los 10 riesgos y marca cuáles aplican según los endpoints y datos detectados. Detalle en `references/owasp-api-top-10-2023.md`.
3. **Seleccionar herramientas** — ZAP/Burp (DAST), Schemathesis/RESTler (fuzzing API), Snyk/Trivy/Dependency-Check (SCA), SonarQube/Semgrep/CodeQL (SAST). Criterio en `references/sast-sca-dast-pipeline.md`.
4. **Cubrir autenticación** — Diseña escenarios `@security` para JWT, OAuth2/OIDC, mTLS y sesión según aplique. Patrones canónicos en `references/auth-testing-patterns.md`.
5. **Fuzzing del contrato** — Si existe OpenAPI/Swagger, corre Schemathesis como mínimo. Para flujos stateful (login → operación → logout), usa RESTler. Snippets y comparación en `references/api-fuzzing-schemathesis-restler.md`.
6. **DAST en pipeline** — Integra OWASP ZAP en CI usando `zap-api-scan.py` contra el OpenAPI desplegado en un ambiente no productivo. Configuración y thresholds en `references/dast-with-owasp-zap.md`.
7. **SCA de dependencias** — Snyk, Trivy o Dependency-Check. Falla el build con vulnerabilidades High/Critical sin parche disponible. Ver `references/sast-sca-dast-pipeline.md`.
8. **Reportar hallazgos con severidad CVSS** — Cada hallazgo lleva: ID OWASP API, descripción, evidencia (request/response, screenshot), CVSS v3.1, recomendación. Enlaza con `[[calidad-test-evidence-and-traceability]]` para artefactos auditables. Mapea contra controles regulatorios usando `references/compliance-regulatory-mapping.md`.

## Restricciones

- **NUNCA** ejecutar pentest, fuzzing agresivo, escaneos DAST o intentos de explotación **sin autorización escrita** del cliente (alcance, ventana, lista blanca de IPs/usuarios, plan de contingencia).
- **NUNCA** escanear ambientes de producción sin una ventana coordinada y notificación previa al equipo de operaciones del cliente. El comportamiento por defecto es ambiente de staging/QA.
- **NUNCA** commitear tokens, claves privadas, certificados o credenciales reales en el repositorio. Usa los mecanismos descritos en `references/secrets-management.md` (SOPS, Vault, AWS Secrets Manager, GitHub OIDC).
- **NUNCA** entregar una suite de seguridad sin gating real en pipeline (DAST + SCA mínimo). Reportes sin gates no detienen regresiones.
- Encadena con `[[calidad-test-evidence-and-traceability]]` para que los reportes ZAP/Snyk/Schemathesis queden archivados con el resto de la evidencia.
- Para clientes con cifrado de payloads (ej. Mercantil), respeta `[[karate-encrypted-payloads]]` y `[[karate-mercantil-security-headers]]` además de este skill.
- Sigue `[[calidad-mandatory-inputs-protocol]]` para obtener autorizaciones y `[[calidad-intent-detection]]` para decidir si la conversación es de tipo "security review" o suite funcional con cobertura de seguridad.

## Cross-links

- `references/owasp-api-top-10-2023.md`
- `references/dast-with-owasp-zap.md`
- `references/api-fuzzing-schemathesis-restler.md`
- `references/auth-testing-patterns.md`
- `references/sast-sca-dast-pipeline.md`
- `references/secrets-management.md`
- `references/compliance-regulatory-mapping.md`
