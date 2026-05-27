# SAST / SCA / DAST — Cuándo correr cada uno

Las tres familias se complementan: ninguna sustituye a otra. Esta tabla y los gates típicos describen el setup base del chapter.

## Definiciones

- **SAST** (Static Application Security Testing): analiza el **código fuente** o el binario sin ejecutarlo. Detecta patrones inseguros, taint flows, configuraciones débiles.
- **SCA** (Software Composition Analysis): analiza **dependencias** (npm, Maven, pip, Go modules, containers) contra bases de CVE.
- **DAST** (Dynamic Application Security Testing): analiza la **aplicación en ejecución** enviando tráfico real (incluye fuzzing).

## Herramientas por familia

| Familia | Herramienta                | Stack típico            | Fortaleza                                |
|---------|----------------------------|-------------------------|------------------------------------------|
| SAST    | SonarQube                  | Java, JS, Python, C#... | Calidad + seguridad, métricas históricas |
| SAST    | Semgrep                    | Multi-lenguaje           | Reglas custom rápidas, OSS               |
| SAST    | CodeQL                     | Java, JS, Python, C#... | Análisis taint profundo (GitHub)         |
| SCA     | Snyk                       | Multi                    | Base CVE comercial, fix advice           |
| SCA     | OWASP Dependency-Check     | Java, .NET, Node         | OSS, sin SaaS                            |
| SCA     | Trivy                      | Containers, IaC, deps    | Rápido, OSS, integra todo                |
| DAST    | OWASP ZAP                  | HTTP/REST/SOAP           | OSS, integra en CI (ver dast-with-owasp-zap.md) |
| DAST    | Burp Suite (Pro/Enterprise)| HTTP/REST                | Manual + scan dirigido                   |

## Cuándo correr cada uno

| Momento del pipeline       | SAST                  | SCA                    | DAST                  |
|----------------------------|-----------------------|------------------------|-----------------------|
| Pre-commit (local)         | Semgrep rápido        | —                      | —                     |
| Cada commit                | Semgrep / SonarLint   | Trivy fs (rápido)      | —                     |
| PR open                    | SonarQube + CodeQL    | Snyk / Dependency-Check| ZAP baseline          |
| Merge a main               | SonarQube (full)      | Snyk + Trivy           | ZAP api-scan          |
| Nightly                    | CodeQL (queries deep) | Snyk container scan    | ZAP full + RESTler    |
| Release candidate          | Full SAST + manual    | Snyk + license check   | Burp manual + ZAP full|

## Gates típicos

Política por defecto del chapter (ajustable por cliente):

| Severidad | SAST                                      | SCA                                                | DAST                       |
|-----------|-------------------------------------------|----------------------------------------------------|----------------------------|
| Critical  | Bloquear PR                               | Bloquear PR si hay fix disponible                  | Bloquear PR                |
| High      | Bloquear PR                               | Bloquear PR si hay fix disponible                  | Bloquear PR                |
| Medium    | Comentar en PR, no bloquear               | Comentar; bloquear si lleva >30 días sin atender   | Comentar                   |
| Low       | Sólo reportar                             | Sólo reportar                                      | Sólo reportar              |

Cuando un Critical/High **no tiene fix disponible**, el equipo documenta una excepción con: justificación, mitigación compensatoria, fecha de revisión.

## Snippets de pipeline

GitHub Actions — pipeline completo:

```yaml
name: security

on:
  pull_request:
  schedule:
    - cron: '0 3 * * *'

jobs:
  sast-semgrep:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: returntocorp/semgrep-action@v1
        with:
          config: p/owasp-top-ten p/security-audit

  sast-codeql:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    permissions: { security-events: write }
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with: { languages: java,javascript }
      - uses: github/codeql-action/analyze@v3

  sca-trivy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aquasecurity/trivy-action@master
        with:
          scan-type: fs
          severity: HIGH,CRITICAL
          exit-code: 1
          ignore-unfixed: true

  sca-snyk:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: snyk/actions/maven@master
        env: { SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }} }
        with:
          args: --severity-threshold=high

  dast-zap:
    if: github.event_name == 'schedule'
    runs-on: ubuntu-latest
    steps:
      - uses: zaproxy/action-api-scan@v0.7.0
        with:
          target: ${{ secrets.OPENAPI_URL }}
          fail_action: true
          allow_issue_writing: false
```

## Integración con suite Karate/Playwright/k6

- **SAST**: corre sobre el repo de la suite (detecta credenciales hardcodeadas en `karate-config.js`, payloads de prueba con tokens reales).
- **SCA**: el `pom.xml` de Karate, el `package.json` de Playwright y los imports de k6 también son auditables.
- **DAST**: la propia suite Karate puede actuar como motor de tráfico para ZAP (ver `dast-with-owasp-zap.md`).

## Restricciones

- No desactives gates "porque rompen el build": eso es la señal de que el gate funciona. Documenta excepción si aplica.
- No publiques reportes SAST/SCA/DAST como artifact público: pueden contener stack traces y rutas internas.
- Encadena reportes con `[[calidad-test-evidence-and-traceability]]` para retención auditable.
