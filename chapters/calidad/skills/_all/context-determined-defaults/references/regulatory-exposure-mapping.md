# Regulatory Exposure — Mapeo de Exposición Regulatoria

Define cómo determinar si un sistema está sujeto a un marco regulatorio y con qué nivel de exigencia. Aplica cross-sector.

## Tipos de exposición

### Explícita

El marco regulatorio aplica directamente al sistema porque procesa datos o realiza operaciones reguladas:

- **PCI-DSS 4.0**: cualquier sistema que reciba, procese, almacene o transmita datos de tarjeta (PAN, CVV, expiración). Aplicación universal.
- **ISO 27001 / 27017 / 27018**: framework internacional de SGSI. Aplicación universal.
- **SOC 2**: framework de auditoría para SaaS B2B (controles de seguridad, disponibilidad, confidencialidad, integridad, privacidad). Aplicación universal.
- **HIPAA / HITECH (US)**: PHI (Protected Health Information).
- **SOX (US)**: controles financieros para empresas públicas listadas en US.
- **GLBA (US)**: sector financiero.
- **CCPA / CPRA (California)**: datos personales de residentes de California.
- **FedRAMP (US)**: sistemas que sirven al gobierno federal US.
- **LGPD (Brasil)**, **Ley 1581 (Colombia)**, **Ley 25.326 (Argentina)**, **LFPDPPP (México)**, **Ley 19.628 / Ley 21.719 (Chile)**, **Ley 29.733 (Perú)**: protección de datos personales LATAM.
- **SBIF/CMF (Chile)**, **CNBV (México)**, **Superintendencia Financiera (Colombia)**, **BCB (Brasil)**, **SBS (Perú)**: regulación financiera LATAM por jurisdicción.

### Implícita

El sistema no está directamente regulado, pero un contrato B2B incorpora compliance como cláusula:

- "El proveedor mantendrá controles equivalentes a SOC 2 Type 2."
- "Las APIs deben cumplir con OWASP API Top 10 y mantener evidencia auditable."
- "Las dependencias de terceros deben pasar SCA con severity High/Critical bloqueadas."
- "Los logs de acceso deben retenerse por X meses con integridad criptográfica."

Implícita es **tan vinculante** como explícita una vez firmado el contrato.

### Ninguna

Sistemas internos, prototipos no productivos, MVPs sin datos personales reales. Aún así se recomiendan controles base (OWASP, secrets management, SCA básico) por higiene.

## Cuándo se requiere certificación externa

- **PCI-DSS**: auditoría anual de QSA si nivel 1 (>6M transacciones/año), SAQ + ASV escaneos trimestrales para niveles menores.
- **SOC 2 Type 2**: auditoría 6-12 meses por CPA acreditada.
- **HIPAA**: no hay certificación oficial pero se exige BAA con socios y assessment.
- **ISO 27001**: certificación por organismo acreditado (3 años, audits anuales).
- **FedRAMP**: Authorization to Operate (ATO) emitida por agencia o JAB.
- **HITRUST CSF**: certificación validada para healthcare.

Cuando hay certificación externa, los tests deben generar evidencia compatible con el formato del auditor (reportes Karate Cucumber, ZAP, Snyk, Great Expectations data docs, todos archivados con timestamp y traza al commit).

## Cómo derivar tier desde la exposición

| Exposición | Tier típico (interactúa con otras variables) |
|---|---|
| Explícita estricta (PCI-DSS, HIPAA) | Conservative + risk_factor 1.0 |
| Explícita moderada (SOC 2, ISO 27001, ley nacional LATAM/US sin especial-categoría) | Moderate o Conservative |
| Implícita con SLA contractual | Moderate o Conservative según penalización |
| Ninguna pero PII presente | Moderate |
| Ninguna y sin PII | Relaxed permitido |

## Antipatrones

- Asumir "no aplica regulación" sin revisar contratos B2B firmados.
- Olvidar regulaciones sectoriales locales LATAM (CNBV, SBS, Superfinanciera, CMF, BCB, etc.) porque "ya cumplimos PCI".
- Reducir el tier cuando el cliente "promete que no van datos reales a QA" — los datos reales siempre terminan llegando.
- Generar evidencia que no es auditable (sin timestamp, sin commit hash, sin pipeline run ID).
