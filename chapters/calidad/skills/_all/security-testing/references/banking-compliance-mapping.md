# Banking Compliance Mapping — OWASP API Top 10 ↔ Normativa LATAM

Mapeo rápido entre los riesgos OWASP API Security Top 10 2023 y los requisitos regulatorios más comunes para clientes de banca/fintech en LATAM. Sirve como guía de evidencia: por cada control regulatorio, qué tests automatizables lo demuestran.

## Marcos de referencia

- **PCI-DSS 4.0** — pagos con tarjeta, aplica a cualquier sistema que almacena/procesa/transmite datos de tarjeta.
- **Colombia — Circular Externa 007/008 SFC** — ciberseguridad en entidades vigiladas y fintech (SEDPE, SOFOM digital, etc.).
- **Chile — Norma SBIF/CMF cap. 20-9 y RAN 1-13** — gestión de seguridad de la información en bancos.
- **México — Disposiciones CNBV cap. X (ITC)** — controles tecnológicos para instituciones de crédito.
- **Brasil — Resolução BCB 4.893/2021** — política de segurança cibernética para instituciones financieras.
- **Perú — Resolución SBS 504-2021** — gestión de la seguridad de la información.

## Mapeo OWASP API ↔ Controles

| OWASP API 2023            | PCI-DSS 4.0       | CE 007 Colombia            | RAN 20-9 Chile         | CNBV México (ITC)       | BCB Brasil           |
|---------------------------|-------------------|----------------------------|-------------------------|--------------------------|----------------------|
| API1 BOLA                 | 7.2, 7.3          | Control de accesos         | 4.1 control de accesos  | Art. 168 control acceso  | Art. 6 (segregación) |
| API2 Broken Auth          | 8.2, 8.3, 8.4     | Autenticación robusta      | 4.2 autenticación       | Art. 168 (MFA)           | Art. 4 (autenticación)|
| API3 BOPLA                | 7.2               | Mínimo privilegio          | 4.1                     | Art. 168                 | Art. 6               |
| API4 Resource Consumption | 11.5 (DoS)        | Continuidad / DDoS         | 6 continuidad           | Art. 170 capacidad       | Art. 3 (resiliencia) |
| API5 BFLA                 | 7.2, 7.3          | Segregación de funciones   | 4.1                     | Art. 168                 | Art. 6               |
| API6 Sensitive Flows      | 6.4.3, 11.6       | Antifraude, bot mitigation | 4.5 antifraude          | Art. 170                 | Art. 3               |
| API7 SSRF                 | 6.2.4             | Hardening de servicios     | 4.4 desarrollo seguro   | Art. 168                 | Art. 5 (vulnerabilidades) |
| API8 Misconfiguration     | 2.2, 6.4          | Hardening, gestión cambios | 4.3 configuración       | Art. 169                 | Art. 5               |
| API9 Improper Inventory   | 12.5.1            | Inventario de activos      | 4.6 inventario          | Art. 168                 | Art. 5               |
| API10 Unsafe Consumption  | 6.4.3 (terceros)  | Gestión de terceros        | 4.7 terceros            | Art. 173 (outsourcing)   | Art. 8 (terceros)    |

## 6 controles clave automatizables

Los controles que aparecen en casi todos los marcos LATAM y se demuestran con tests automatizados:

### 1. Autenticación robusta con MFA

- **Marcos**: PCI 8.4, CE 007 (CO), CNBV 168 (MX), RAN 4.2 (CL), BCB 4 (BR).
- **Tests automatizables**:
  - Karate `@security @auth @mfa`: login sin segundo factor retorna `401`.
  - Playwright e2e: flujo de login obliga a TOTP/OTP antes de operar.
  - Ver `auth-testing-patterns.md` (sección JWT, OAuth2).
- **Evidencia**: reporte Karate + screenshots Playwright + logs ZAP.

### 2. Control de acceso por objeto (BOLA) y por función (BFLA)

- **Marcos**: PCI 7.2/7.3, CE 007 mínimo privilegio (CO), CNBV 168, RAN 4.1, BCB 6.
- **Tests automatizables**:
  - Karate `@security @bola`: usuario A no lee/modifica recursos del usuario B → `403`.
  - Karate `@security @bfla`: usuario sin rol admin no invoca endpoints administrativos → `403`.
- **Evidencia**: matriz de roles × endpoints × status esperado en el reporte.

### 3. Cifrado en tránsito (TLS 1.2+) y headers de seguridad

- **Marcos**: PCI 4.2, CE 007 cifrado, CNBV 169, RAN 4.3, BCB 5.
- **Tests automatizables**:
  - `testssl.sh` en pipeline: TLS 1.2+ obligatorio, sin SSLv3/TLSv1.0/TLSv1.1, ciphers fuertes.
  - Karate `@security @headers`: `Strict-Transport-Security`, `X-Content-Type-Options`, `Content-Security-Policy`, `X-Frame-Options`.
  - Para clientes específicos ver `[[karate-mercantil-security-headers]]`.
- **Evidencia**: reporte testssl + asserts Karate.

### 4. Gestión de vulnerabilidades de dependencias (SCA)

- **Marcos**: PCI 6.3.3, CE 007 gestión de vulnerabilidades, CNBV 168, RAN 4.4, BCB 5.
- **Tests automatizables**:
  - Trivy / Snyk / Dependency-Check en cada PR con gates Critical/High.
  - Ver `sast-sca-dast-pipeline.md`.
- **Evidencia**: reporte SCA con timestamp y commit en cada PR mergeado.

### 5. Rate limiting y antifraude en flujos sensibles

- **Marcos**: PCI 11.5, CE 007 antifraude, CNBV 170 capacidad, BCB 3 resiliencia.
- **Tests automatizables**:
  - k6 `@security @abuse`: ráfaga sostenida a `/login`, `/transfer`, `/signup` debe activar rate-limit (`429`) o CAPTCHA.
  - Ver `owasp-api-top-10-2023.md` (API4, API6).
- **Evidencia**: summary k6 con porcentaje de `429` esperado y `5xx` cercano a 0.

### 6. Trazabilidad y no repudio (audit logs)

- **Marcos**: PCI 10, CE 007 monitoreo, CNBV 168, RAN 4.5, BCB 7.
- **Tests automatizables**:
  - Karate `@security @audit`: tras una operación sensible (transferencia, cambio de password), consultar endpoint de auditoría/logs y confirmar el evento.
- **Evidencia**: traza JSON del log + correlación con el request original.

## Cómo entregar la evidencia

Para clientes regulados, cada release debe acompañarse de un paquete que incluya:

1. Resultados de las suites Karate/k6/Playwright con tags `@security` (HTML + JSON).
2. Reporte ZAP (HTML + JSON) — DAST.
3. Reporte SCA (Snyk/Trivy) — SBOM y CVEs.
4. Reporte SAST (SonarQube/CodeQL) — métricas y hallazgos.
5. Matriz de mapeo control regulatorio → test → resultado.

Archivado bajo política de retención del cliente (típicamente 1-5 años según marco). Encadena con `[[calidad-test-evidence-and-traceability]]`.

## Restricciones

- Este mapeo es **orientativo**; cada cliente tiene su propia matriz formal de controles. Confirma con el equipo de Compliance/Riesgo del cliente antes de declarar cobertura.
- Las jurisdicciones evolucionan: revisar trimestralmente.
- No supone reemplazo de auditoría externa formal (PCI QSA, ISO 27001).
