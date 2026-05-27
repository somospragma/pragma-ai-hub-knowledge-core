
# Autenticación con `storageState`

## Cuándo aplicar

Genera `auth.setup.ts` cuando **la UI real tiene un flujo de login propio dentro del browser** (formulario de credenciales, OTP en pantalla, magic link gestionado por la app). La decisión se toma a partir de evidencia UI, no del contrato backend.

### Fuentes para detectar el flujo de login

- Descripción de UI provista por el usuario que menciona pantalla de login.
- URL viva donde existe la ruta `/login` (o equivalente) y se renderiza un formulario.
- Figma / wireframe de la pantalla de login.
- User story que enumera explícitamente el paso de autenticación en UI.
- Confirmación del PO de que el login existe y se opera dentro del browser.

Si alguna de estas señales está presente, sigue el patrón documentado más abajo.

### Caso especial: el spec declara `security` pero la UI no tiene login propio

Que el contrato OpenAPI/Swagger declare `security` **no implica** que `auth.setup.ts` aplique. Escenarios típicos donde el spec declara seguridad y aun así NO corresponde generar `auth.setup.ts` directamente:

- SSO corporativo que redirige a un IdP externo (Okta, Auth0, Azure AD) fuera del dominio de la app.
- Autenticación delegada vía cookie de sesión emitida por otro sistema.
- Tokens inyectados por un sidecar o variable de entorno para entornos de test.

En esos casos `auth.setup.ts` probablemente no aplica tal cual: **detente y pide guía al usuario** sobre cómo obtener una sesión válida (por ejemplo, un `storageState` pre-grabado, un token de servicio inyectado, o un flujo manual previo al pipeline).

## Patrón

1. Un proyecto Playwright `setup` ejecuta `fixtures/auth.setup.ts` una sola vez, hace login real y persiste el estado en `.auth/user.json` con `page.context().storageState({ path })`.
2. Los proyectos `chromium`, `firefox` y `webkit` declaran `dependencies: ['setup']` y consumen `storageState: '.auth/user.json'`, evitando login en cada test.
3. `fullyParallel: false` se aplica a nivel root para garantizar el orden setup → tests.

## Snippet — `fixtures/auth.setup.ts`

```typescript
import { test as setup, expect } from '@playwright/test';
import { LoginPage } from '@pages/LoginPage';

const authFile = '.auth/user.json';

setup('authenticate', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.navigate();
  await loginPage.fillEmail('test@example.com');
  await loginPage.fillPassword('password123');
  await loginPage.submit();
  await expect(page).toHaveURL('**/dashboard');
  await page.context().storageState({ path: authFile });
});
```

## Snippet — `playwright.config.ts` (fragmento)

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  fullyParallel: false,
  projects: [
    { name: 'setup', testMatch: /auth\.setup\.ts/ },
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'], storageState: '.auth/user.json' },
      dependencies: ['setup'],
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'], storageState: '.auth/user.json' },
      dependencies: ['setup'],
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'], storageState: '.auth/user.json' },
      dependencies: ['setup'],
    },
  ],
});
```

## Notas

- `.auth/` debe estar en `.gitignore` para no commitear credenciales/sesiones.
- El archivo `.auth/user.json` se regenera automáticamente en cada corrida del proyecto `setup`.

## Cuándo NO generar `auth.setup.ts`

- **App sin login real**: la UI es pública o el acceso se gestiona fuera del browser (red privada, mTLS de infraestructura, header inyectado por un proxy).
- **Login vía SSO / IdP externo que escapa al browser**: el flujo abre dominios fuera de la app bajo prueba, requiere MFA externo, o usa redirecciones que Playwright no debe automatizar en pipeline (riesgo de bloquear la cuenta, captchas, políticas corporativas).
- **Tests que usan tokens inyectados directamente** como variable de entorno (`AUTH_TOKEN`, `SESSION_COOKIE`): se setean en un `beforeAll` o se aplican como header/cookie en el `context`, sin pasar por `auth.setup.ts`.

En todos estos casos: documenta la decisión en el README del proyecto y, si el spec declara `security`, deja una nota explicando por qué no se materializó como `auth.setup.ts`.
