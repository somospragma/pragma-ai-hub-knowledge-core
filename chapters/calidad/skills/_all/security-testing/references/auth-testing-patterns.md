# Auth Testing Patterns — JWT, OAuth2/OIDC, mTLS, Session

Patrones de prueba para los esquemas de autenticación más comunes en APIs y apps enterprise (cualquier jurisdicción). Todos los escenarios deben tagearse `@security @auth` para activarse en pipelines de seguridad sin afectar el smoke funcional.

## JWT

Aspectos a verificar:

- **Firma**: tokens con firma inválida son rechazados (401).
- **Expiración**: tokens expirados son rechazados.
- **Claims**: `iss`, `aud`, `sub`, `exp`, `nbf` se validan; claims falsificados (`role: ADMIN`) no escalan.
- **`alg=none` attack**: el servidor rechaza tokens con `"alg":"none"`.
- **Algorithm confusion**: token firmado con HS256 usando la clave pública RSA no debe aceptarse (cuando el servidor espera RS256).

Escenario Karate:

```gherkin
@security @auth @jwt
Feature: validación de JWT

  Background:
    * url baseUrl

  Scenario: token con alg=none es rechazado
    Given path '/me'
    And header Authorization = 'Bearer ' + tokenAlgNone
    When method get
    Then status 401

  Scenario: token expirado es rechazado
    Given path '/me'
    And header Authorization = 'Bearer ' + tokenExpired
    When method get
    Then status 401

  Scenario: claim sub manipulado no permite acceso a otro usuario
    Given path '/users', otherUserId, '/profile'
    And header Authorization = 'Bearer ' + tokenWithForgedSub
    When method get
    Then status 401
```

Helper sugerido (`helpers/jwt.js`):

```javascript
function fn(payload, alg) {
  const header = Buffer.from(JSON.stringify({ alg, typ: 'JWT' })).toString('base64url');
  const body = Buffer.from(JSON.stringify(payload)).toString('base64url');
  return `${header}.${body}.`; // firma vacía a propósito para alg=none
}
```

## OAuth2 / OIDC

Aspectos a verificar:

- **PKCE**: clientes públicos (SPA, mobile) exigen `code_challenge`/`code_verifier`; el servidor rechaza authorize sin PKCE.
- **`state`**: protección CSRF; el callback rechaza `state` ausente o no coincidente.
- **`nonce`**: protección contra replay del ID token; el cliente valida `nonce` que envió.
- **Refresh token rotation**: cada refresh emite un token nuevo y revoca el anterior; reusar el viejo invalida la sesión completa.
- **Redirect URI**: sólo se aceptan URIs exactos pre-registrados (no substring match).
- **Scope creep**: el access token recibe sólo los scopes solicitados y consentidos.

Escenario Playwright (flujo authorization code + PKCE):

```typescript
import { test, expect } from '@playwright/test';

test.describe('@security @auth @oauth2', () => {
  test('rechaza callback con state inválido', async ({ page, request }) => {
    await page.goto('/login');
    const url = new URL(page.url());
    const validState = url.searchParams.get('state')!;

    const res = await request.get(`/callback?code=fake&state=${validState}-tampered`);
    expect(res.status()).toBe(400);
  });

  test('refresh token rotation invalida el token anterior', async ({ request }) => {
    const first = await refresh(request, originalRefresh);
    const reused = await request.post('/oauth/token', {
      form: { grant_type: 'refresh_token', refresh_token: originalRefresh },
    });
    expect(reused.status()).toBe(400);
  });
});
```

## mTLS

Aspectos a verificar:

- **Cert pinning**: el servidor sólo acepta clientes con cert emitido por la CA esperada.
- **Cliente sin cert**: rechazo en el handshake TLS.
- **Cert expirado**: rechazo.
- **Cert revocado**: el servidor consulta CRL/OCSP y rechaza.
- **Pinning en cliente móvil**: la app Android/iOS no acepta certs distintos al pineado (resistencia a MITM).

Escenario Karate (con cert válido):

```gherkin
@security @auth @mtls
Scenario: petición con cert válido es aceptada
  * configure ssl = { keyStore: 'classpath:certs/client.p12', keyStorePassword: '#(ksPassword)', keyStoreType: 'pkcs12' }
  Given path '/secure/ping'
  When method get
  Then status 200

Scenario: petición sin cert es rechazada (handshake)
  * configure ssl = { trustAll: true }
  Given path '/secure/ping'
  When method get
  Then status == 0 || status == 403
```

Para Appium/mobile, verificar pinning con `[[calidad-appium-screenplay-android]]` + un proxy MITM (mitmproxy) y un cert no pineado: la app debe rechazar la conexión.

## Session-based (cookies)

Aspectos a verificar:

- **Flags**: `HttpOnly`, `Secure`, `SameSite=Lax|Strict`.
- **Regeneración de session id**: después de login/logout, el id de sesión cambia (anti session-fixation).
- **Timeout absoluto y de inactividad**.
- **Logout invalida la sesión en servidor** (no solo borra la cookie del cliente).

Escenario Karate:

```gherkin
@security @auth @session
Scenario: cookie de sesión tiene flags seguros
  Given path '/login'
  And request { user: '#(user)', pass: '#(pass)' }
  When method post
  Then status 200
  And match responseHeaders['Set-Cookie'][0] contains 'HttpOnly'
  And match responseHeaders['Set-Cookie'][0] contains 'Secure'
  And match responseHeaders['Set-Cookie'][0] contains 'SameSite='

Scenario: logout invalida la sesión en servidor
  Given path '/logout'
  And cookie SESSIONID = sessionId
  When method post
  Then status 204

  Given path '/me'
  And cookie SESSIONID = sessionId
  When method get
  Then status 401
```

Escenario Playwright (e2e):

```typescript
test('@security @auth session se regenera al login', async ({ page, context }) => {
  await page.goto('/login');
  const before = (await context.cookies()).find(c => c.name === 'SESSIONID')?.value;
  await page.fill('#user', 'alice');
  await page.fill('#pass', 'secret');
  await page.click('button[type=submit]');
  await page.waitForURL('/dashboard');
  const after = (await context.cookies()).find(c => c.name === 'SESSIONID')?.value;
  expect(after).not.toBe(before);
});
```

## Cobertura mínima por esquema

| Esquema    | Cobertura mínima                                                                 |
|------------|----------------------------------------------------------------------------------|
| JWT        | alg=none, firma inválida, expiración, manipulación de claims                     |
| OAuth2/OIDC| state, nonce, PKCE, refresh rotation, redirect URI estricto                      |
| mTLS       | sin cert, cert expirado, pinning en cliente                                      |
| Session    | flags de cookie, regeneración en login, invalidación en logout                   |
