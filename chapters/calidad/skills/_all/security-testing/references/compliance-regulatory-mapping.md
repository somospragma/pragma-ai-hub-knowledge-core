# Compliance Regulatory Mapping — OWASP API Top 10 ↔ Marcos Aplicables

Mapeo entre los riesgos OWASP API Security Top 10 2023 y los marcos regulatorios que aplican al alcance del Chapter (LATAM + Estados Unidos). Los estándares internacionales (PCI-DSS, ISO 27001, SOC 2) son de aplicación universal independientemente de la región. Las leyes nacionales se mencionan cuando son relevantes para el cliente.

## Estándares internacionales de aplicación universal

- **PCI-DSS 4.0** — Pagos con tarjeta. Aplica a cualquier sistema que almacena/procesa/transmite datos de tarjeta.
- **OWASP API Security Top 10 (2023)** — Referencia técnica de la industria.
- **ISO 27001 / 27017 / 27018** — Sistema de gestión de seguridad de información. Frecuente en clientes con certificación.
- **SOC 2** — Certificación voluntaria de controles de seguridad / disponibilidad / integridad. Común en SaaS B2B.

## Marcos Estados Unidos

- **HIPAA** — Datos de salud (PHI). Aplica a covered entities y business associates.
- **SOX (Sarbanes-Oxley)** — Controles internos para empresas públicas listadas en bolsas US.
- **GLBA** — Sector financiero.
- **CCPA / CPRA** — Privacidad para residentes de California; en la práctica funciona como mínimo común para apps con usuarios en US.
- **FedRAMP** — Cloud para gobierno federal US.

## Marcos LATAM

- **Colombia** — Ley 1581/2012 + Decreto 1377; Circular Externa 007/008 SFC para entidades financieras vigiladas y fintech.
- **Brasil** — LGPD (Lei 13.709); Resolução BCB 4.893/2021 para instituciones financieras.
- **México** — LFPDPPP; Disposiciones CNBV (ITC) para instituciones de crédito.
- **Chile** — Ley 19.628; Norma SBIF/CMF para bancos; Ley 21.719 (2024) introduce sanciones reforzadas.
- **Argentina** — Ley 25.326 de Protección de Datos Personales.
- **Perú** — Ley 29.733; Resolución SBS 504-2021 para entidades supervisadas.
- **Centroamérica** — Aplicar el marco análogo nacional (Costa Rica Ley 8968, Panamá Ley 81/2019, República Dominicana Ley 172-13, equivalentes locales) + estándares internacionales como mínimo común cuando no exista regulación específica.

## Tabla maestra: OWASP API 2023 ↔ marcos

| OWASP API 2023               | PCI-DSS 4.0 | HIPAA           | SOC 2 | ISO 27001 | Marco LATAM típico (ej. CE 007 CO) |
|------------------------------|-------------|-----------------|-------|-----------|------------------------------------|
| API1 BOLA                    | 7.x         | §164.308(a)(4)  | CC6.1 | A.9.1     | Control de acceso a datos          |
| API2 Broken Authentication   | 8.x         | §164.312(d)     | CC6.1 | A.9.4     | Autenticación fuerte               |
| API3 BOPLA                   | 4.x, 8.x    | §164.514        | CC6.7 | A.13.2    | Minimización de datos              |
| API4 Unrestricted Consumption| 12.x        | §164.312(b)     | A1.2  | A.13.1    | Gestión de capacidad y abuso       |
| API5 BFLA                    | 7.x         | §164.308(a)(4)  | CC6.3 | A.9.4.1   | Segregación de funciones           |
| API6 Sensitive Business Flow | 12.x        | -               | CC7.4 | A.16.1    | Antifraude / detección de abuso    |
| API7 SSRF                    | 6.x         | -               | CC6.6 | A.13.1.3  | Segmentación de red                |
| API8 Misconfiguration        | 2.x, 6.x    | §164.308(a)(8)  | CC6.6 | A.12.6    | Hardening y gestión de vulnerab.   |
| API9 Improper Inventory      | 11.x        | -               | CC2.2 | A.8.1     | Inventario de activos              |
| API10 Unsafe Consumption     | 6.x         | -               | CC6.6 | A.14.2.5  | Seguridad en integraciones         |

## Controles transversales

Independiente del marco específico, los siguientes controles aparecen en casi todos los marcos del alcance y son automatizables:

1. **Autenticación fuerte y MFA** — login sin segundo factor retorna `401`; tests Karate `@security @auth @mfa` y flujos Playwright validando TOTP/OTP. Ver `auth-testing-patterns.md`.
2. **Principio de mínimo privilegio (BOLA/BFLA)** — usuario A no accede a recursos de usuario B; usuarios sin rol no invocan endpoints administrativos. Matriz roles × endpoints × status esperado.
3. **Cifrado en tránsito (TLS 1.2+) y en reposo** — `testssl.sh` en pipeline; asserts de headers (`Strict-Transport-Security`, `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`).
4. **Gestión de vulnerabilidades de dependencias (SCA)** — Trivy / Snyk / Dependency-Check en cada PR con gates Critical/High. Ver `sast-sca-dast-pipeline.md`.
5. **Rate limiting y antifraude en flujos sensibles** — k6 `@security @abuse` contra `/login`, `/transfer`, `/signup` debe activar `429` o CAPTCHA.
6. **Monitoreo, detección y trazabilidad (audit logs)** — tras operación sensible, endpoint de auditoría confirma el evento; correlación trace-id request ↔ log.
7. **Gestión de incidentes** — runbooks, comunicación a autoridades regulatorias en plazos definidos.
8. **Retención, minimización y eliminación de datos** — políticas por dataset, evidencia de borrado al final del ciclo.
9. **Separación de ambientes** — dev/QA/staging/prod aislados; secretos y datos no se cruzan.
10. **Gestión de secretos** — vault, OIDC, rotación; nunca credenciales en repo.

## Cómo activar este mapeo

Para clientes regulados, cada release debe acompañarse de un paquete con:

1. Marcos aplicables identificados (internacional + jurisdicción del cliente).
2. Inventario de endpoints/flujos afectados.
3. Resultados de tests por riesgo OWASP API.
4. Evidencia DAST/SAST/SCA con timestamps.
5. Matriz control → test → resultado.

Mantener este archivo enfocado en el alcance del Chapter (LATAM + Estados Unidos). Si llega un cliente fuera de ese alcance, escalar para definir el subset aplicable; no extender este mapeo por defecto.

## Restricciones

- Este mapeo es **orientativo**; cada cliente tiene su propia matriz formal de controles. Confirma con el equipo de Compliance/Riesgo del cliente antes de declarar cobertura.
- No supone reemplazo de auditoría externa formal (PCI QSA, ISO 27001, SOC 2 Type II).
- Encadena con `[[calidad-test-evidence-and-traceability]]` para evidencia archivada bajo la política de retención del cliente.
