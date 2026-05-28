# Compliance Regulatory Mapping — OWASP API Top 10 ↔ Marcos Regulatorios Globales

Mapeo entre los riesgos OWASP API Security Top 10 2023 y los marcos regulatorios más comunes. La tabla principal cubre marcos globales/multinacionales. Los anexos cubren regulaciones por región. Activar solo el subset aplicable según la jurisdicción del cliente y la naturaleza del sistema bajo prueba.

## Marcos globales / multinacionales

- **PCI-DSS 4.0** — Pagos con tarjeta. Aplica a cualquier sistema que almacena/procesa/transmite datos de tarjeta, en cualquier jurisdicción.
- **GDPR (UE) / UK-GDPR (Reino Unido)** — Protección de datos personales. Aplica si hay datos de usuarios en UE/UK independientemente de la ubicación del sistema.
- **HIPAA (Estados Unidos)** — Datos de salud (PHI). Aplica a covered entities y business associates en EE.UU.
- **SOX (Sarbanes-Oxley, EE.UU.)** — Controles internos para empresas públicas que cotizan en bolsas US.
- **SOC 2** — Certificación voluntaria de controles de seguridad/disponibilidad/integridad. Común en SaaS B2B.
- **ISO 27001 / ISO 27017 / ISO 27018** — Sistemas de gestión de seguridad de información (global).
- **FedRAMP (EE.UU.)** — Cloud para gobierno federal de EE.UU.
- **NIS2 (UE)** — Resiliencia operacional de servicios esenciales (entró vigor 2024).
- **DORA (UE, 2025)** — Resiliencia operacional para sector financiero europeo.
- **CCPA / CPRA (California)** — Privacidad para residentes de California.
- **LGPD (Brasil)** — Lei Geral de Proteção de Dados.
- **PIPEDA (Canadá)** — Personal Information Protection.
- **PIPL (China)** — Personal Information Protection Law.
- **APPI (Japón)** — Act on the Protection of Personal Information.
- **POPIA (Sudáfrica)** — Protection of Personal Information Act.

## Tabla maestra: OWASP API 2023 ↔ marcos globales

| OWASP API 2023               | PCI-DSS 4.0 | HIPAA            | GDPR    | SOX  | SOC 2 | ISO 27001 | FedRAMP |
|------------------------------|-------------|------------------|---------|------|-------|-----------|---------|
| API1 BOLA                    | 7.x         | §164.308(a)(4)   | Art.32  | ICFR | CC6.1 | A.9.1     | AC-3    |
| API2 Broken Authentication   | 8.x         | §164.312(d)      | Art.32  | ICFR | CC6.1 | A.9.4     | IA-2    |
| API3 BOPLA                   | 4.x, 8.x    | §164.514         | Art.5   | ICFR | CC6.7 | A.13.2    | SC-28   |
| API4 Unrestricted Consumption| 12.x        | §164.312(b)      | Art.32  | -    | A1.2  | A.13.1    | SC-5    |
| API5 BFLA                    | 7.x         | §164.308(a)(4)   | Art.32  | ICFR | CC6.3 | A.9.4.1   | AC-6    |
| API6 Sensitive Business Flow | 12.x        | -                | Art.32  | -    | CC7.4 | A.16.1    | SI-4    |
| API7 SSRF                    | 6.x         | -                | Art.32  | -    | CC6.6 | A.13.1.3  | SC-7    |
| API8 Misconfiguration        | 2.x, 6.x    | §164.308(a)(8)   | Art.32  | -    | CC6.6 | A.12.6    | CM-6    |
| API9 Improper Inventory      | 11.x        | -                | Art.30  | -    | CC2.2 | A.8.1     | CM-8    |
| API10 Unsafe Consumption     | 6.x         | -                | Art.32  | -    | CC6.6 | A.14.2.5  | SA-8    |

(Las celdas con "-" indican que el marco no tiene un control directamente equivalente.)

## Controles transversales (aplican a casi todos los marcos)

Independiente de la jurisdicción, estos controles aparecen en prácticamente todos los marcos y se demuestran con tests automatizables:

1. **Autenticación fuerte y MFA** — login sin segundo factor retorna `401`; tests Karate `@security @auth @mfa` y flujos Playwright validando TOTP/OTP. Ver `auth-testing-patterns.md`.
2. **Principio de mínimo privilegio (BOLA/BFLA)** — usuario A no accede a recursos de usuario B; usuarios sin rol no invocan endpoints administrativos. Matriz roles × endpoints × status esperado.
3. **Cifrado en tránsito (TLS 1.2+) y en reposo** — `testssl.sh` en pipeline; asserts de headers (`Strict-Transport-Security`, `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`).
4. **Gestión de vulnerabilidades de dependencias (SCA)** — Trivy / Snyk / Dependency-Check en cada PR con gates Critical/High. Ver `sast-sca-dast-pipeline.md`.
5. **Rate limiting y antifraude en flujos sensibles** — k6 `@security @abuse` contra `/login`, `/transfer`, `/signup` debe activar `429` o CAPTCHA.
6. **Monitoreo, detección y trazabilidad (audit logs)** — tras operación sensible, endpoint de auditoría confirma el evento; correlación trace-id request ↔ log.
7. **Gestión de incidentes** — runbooks, comunicación a autoridades regulatorias en plazos definidos.
8. **Retención, minimización y eliminación de datos** — políticas por dataset, evidencia de borrado al final del ciclo.
9. **Separación de ambientes** — dev/QA/staging/prod aislados; secretos y datos no se cruzan.

## Anexos regionales

### Anexo A — LATAM

- **Colombia** — Ley 1581/2012 + Decreto 1377; Circular Externa 007/008 SFC (financiero).
- **Brasil** — LGPD (Lei 13.709); Resolução BCB 4.893/2021 (financiero).
- **México** — LFPDPPP; Disposiciones CNBV cap. X (ITC, financiero).
- **Chile** — Ley 19.628; Norma SBIF/CMF cap. 20-9 y RAN 1-13 (financiero); Ley 21.719 (2024).
- **Perú** — Ley 29.733; Resolución SBS 504-2021 (financiero).
- **Argentina** — Ley 25.326.
- **Costa Rica** — Ley 8968.
- **Uruguay** — Ley 18.331.
- **Ecuador** — LOPDP (2021).

### Anexo B — EU/EEA/UK

- GDPR / UK-GDPR; ePrivacy; NIS2; DORA (financiero); AI Act (sistemas IA, 2025-2026).

### Anexo C — Estados Unidos

- HIPAA (salud); SOX (financiero público); GLBA (financiero); FERPA (educación); COPPA (menores); CCPA/CPRA (California); SHIELD Act (NY); BIPA (Illinois biométricos); FedRAMP (gobierno).

### Anexo D — APAC

- PIPL (China); APPI (Japón); PDPA (Singapur); PDPA (Malasia); Personal Data Protection Act (Tailandia); IT Act (India) + DPDP Act 2023.

### Anexo E — África / Medio Oriente

- POPIA (Sudáfrica); NDPR (Nigeria); UAE PDPL; Saudi PDPL.

## Cómo activar este mapeo

Para clientes regulados, cada release debe acompañarse de un paquete que incluya:

1. Identificación del marco aplicable (lista de Anexos relevantes).
2. Inventario de endpoints/flujos afectados.
3. Resultados de tests por riesgo OWASP API.
4. Evidencia DAST/SAST/SCA con timestamps.
5. Matriz de mapeo control regulatorio → test → resultado.

Archivado bajo política de retención del cliente (típicamente 1-5 años según marco). Encadena con `[[calidad-test-evidence-and-traceability]]`.

## Restricciones

- Este mapeo es **orientativo**; cada cliente tiene su propia matriz formal de controles. Confirma con el equipo de Compliance/Riesgo del cliente antes de declarar cobertura.
- Las jurisdicciones evolucionan: revisar trimestralmente.
- No supone reemplazo de auditoría externa formal (PCI QSA, ISO 27001, SOC 2 Type II).
- Mantener este archivo neutro: agregar marcos nuevos por jurisdicción sin elevar ninguno como default.
