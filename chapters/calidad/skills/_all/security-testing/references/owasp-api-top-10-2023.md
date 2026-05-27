# OWASP API Security Top 10 — 2023

Lista de referencia para mapear cobertura de seguridad en cualquier API entregada. Por cada riesgo: descripción en una línea, escenario detectable con Karate/k6/Playwright y herramienta recomendada.

## API1:2023 — Broken Object Level Authorization (BOLA)

- **Descripción**: el endpoint permite acceder a un objeto que pertenece a otro usuario manipulando el ID en la URL/body.
- **Escenario Karate**:
  ```gherkin
  @security @bola
  Scenario: usuario A no puede leer la cuenta del usuario B
    Given path '/accounts', accountIdOfUserB
    And header Authorization = 'Bearer ' + tokenUserA
    When method get
    Then status 403
  ```
- **Herramienta**: Schemathesis (`--checks response_schema_conformance,not_a_server_error`) + asserts manuales de autorización. Burp Suite (Authorize plugin).

## API2:2023 — Broken Authentication

- **Descripción**: fallas en login, recovery, refresh, MFA o validación de tokens permiten suplantación.
- **Escenario Karate**:
  ```gherkin
  @security @auth
  Scenario: token con alg=none es rechazado
    Given path '/me'
    And header Authorization = 'Bearer ' + tokenWithAlgNone
    When method get
    Then status 401
  ```
- **Herramienta**: jwt_tool, Burp Suite, Schemathesis con `--auth` para verificar gates.

## API3:2023 — Broken Object Property Level Authorization (BOPLA)

- **Descripción**: combina mass-assignment + excessive data exposure: el cliente puede leer/escribir propiedades sensibles que no debería.
- **Escenario Karate**:
  ```gherkin
  @security @bopla
  Scenario: PATCH no permite escalar rol a admin
    Given path '/users/me'
    And header Authorization = 'Bearer ' + tokenUserA
    And request { role: 'ADMIN' }
    When method patch
    Then status 403
  ```
- **Herramienta**: Schemathesis (response_schema_conformance) + tests dirigidos por contrato.

## API4:2023 — Unrestricted Resource Consumption

- **Descripción**: ausencia de rate-limiting, paginación, límites de tamaño de payload o de timeouts permite DoS y costos descontrolados.
- **Escenario k6**:
  ```javascript
  export const options = { vus: 200, duration: '30s' };
  export default function () {
    const res = http.get(`${__ENV.API}/search?q=*`);
    check(res, { 'no 5xx ni timeout': r => r.status !== 0 && r.status < 500 });
  }
  ```
- **Herramienta**: k6 (load/stress), ZAP (Active Scan rule `Heartbleed/Slowloris-like`).

## API5:2023 — Broken Function Level Authorization (BFLA)

- **Descripción**: usuario sin privilegios puede invocar funciones administrativas (`/admin/*`, `DELETE /resource/{id}`).
- **Escenario Karate**:
  ```gherkin
  @security @bfla
  Scenario: usuario normal no puede llamar DELETE /admin/users/{id}
    Given path '/admin/users', otherUserId
    And header Authorization = 'Bearer ' + tokenUserA
    When method delete
    Then status 403
  ```
- **Herramienta**: Burp Authorize, Schemathesis con tags por rol.

## API6:2023 — Unrestricted Access to Sensitive Business Flows

- **Descripción**: flujos de negocio sensibles (compra, transferencia, signup) sin throttling/bot-protection son abusables a escala.
- **Escenario k6**:
  ```javascript
  export const options = { scenarios: { abuse: { executor: 'constant-arrival-rate', rate: 100, timeUnit: '1s', duration: '1m', preAllocatedVUs: 50 } } };
  export default function () {
    http.post(`${__ENV.API}/transfer`, JSON.stringify({ to: 'X', amount: 1 }), { headers: { Authorization: `Bearer ${__ENV.TOKEN}` } });
  }
  ```
- **Herramienta**: k6 (carga sostenida), ZAP, captchas/WAF en el lado servidor.

## API7:2023 — Server Side Request Forgery (SSRF)

- **Descripción**: la API acepta URLs/recursos provistos por el cliente y las invoca, permitiendo acceder a metadata interna (`169.254.169.254`) o servicios internos.
- **Escenario Karate**:
  ```gherkin
  @security @ssrf
  Scenario: la API rechaza URLs hacia metadata cloud
    Given path '/preview'
    And request { url: 'http://169.254.169.254/latest/meta-data/' }
    When method post
    Then status 400
  ```
- **Herramienta**: ZAP (rule `Server Side Request Forgery`), Burp Collaborator.

## API8:2023 — Security Misconfiguration

- **Descripción**: CORS abierto, headers ausentes (HSTS, CSP, X-Content-Type-Options), TLS débil, banners verbosos, métodos HTTP innecesarios.
- **Escenario Playwright/Karate**:
  ```gherkin
  @security @headers
  Scenario: la API expone HSTS y X-Content-Type-Options
    Given path '/health'
    When method get
    Then status 200
    And match responseHeaders['Strict-Transport-Security'][0] == '#string'
    And match responseHeaders['X-Content-Type-Options'][0] == 'nosniff'
  ```
- **Herramienta**: ZAP (passive scan), `testssl.sh`, Nikto, `[[karate-mercantil-security-headers]]`.

## API9:2023 — Improper Inventory Management

- **Descripción**: existen versiones viejas (`/v1`, `/beta`), endpoints olvidados o documentación desactualizada que siguen accesibles.
- **Escenario Karate**:
  ```gherkin
  @security @inventory
  Scenario: las versiones deprecated retornan 410 Gone
    Given path '/v1/users'
    When method get
    Then status 410
  ```
- **Herramienta**: ZAP spider, `kiterunner`, diff contra OpenAPI publicado.

## API10:2023 — Unsafe Consumption of APIs

- **Descripción**: la API confía en respuestas de terceros sin validarlas, propagando errores o vulnerabilidades downstream.
- **Escenario Karate** (mock con WireMock/Karate mock):
  ```gherkin
  @security @consumption
  Scenario: la API rechaza payloads malformados del proveedor X
    Given mock proveedor responde { html: '<script>alert(1)</script>' }
    When la API consume al proveedor
    Then la respuesta al cliente final está sanitizada (sin <script>)
  ```
- **Herramienta**: WireMock + asserts de saneamiento, ZAP en modo activo.

## Resumen de cobertura mínima recomendada

| Riesgo                  | Cobertura mínima                            |
|-------------------------|---------------------------------------------|
| API1, API3, API5        | Tests funcionales con tag `@security`       |
| API2                    | Suite `@auth` dedicada (ver auth-testing-patterns) |
| API4, API6              | k6 con scenarios de abuso                   |
| API7, API10             | Escenarios negativos con payloads dirigidos |
| API8                    | Assertions de headers + `testssl.sh`        |
| API9                    | Diff automatizado OpenAPI vs producción     |
