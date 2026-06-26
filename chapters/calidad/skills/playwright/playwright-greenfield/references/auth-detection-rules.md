# Auth detection rules (Playwright)

Decide automáticamente si una suite Playwright generada desde HUs requiere flujo de login (storageState + setup project + fixture autenticada) o si puede correr sin sesión.

## Keywords gatillo

Si en el texto plano de **cualquiera** de las HUs, criterios de aceptación o descripción de la app aparece alguno de los siguientes términos (case-insensitive, español o inglés), el agente DEBE generar el stack completo de autenticación:

| Categoría        | Keywords (es / en)                                                          |
|------------------|------------------------------------------------------------------------------|
| Identidad        | `cliente`, `customer`, `usuario`, `user`, `cuenta`, `account`, `mi perfil`, `my profile`, `perfil`, `profile` |
| Datos personales | `dirección personal`, `personal address`, `mis datos`, `my info`, `datos del usuario` |
| Persistencia     | `lista guardada`, `saved list`, `wishlist`, `favoritos`, `favorites`, `historial`, `history` |
| Comercio         | `carrito`, `cart`, `pedido`, `order`, `mis pedidos`, `my orders`, `pago`, `payment`, `checkout` |
| Sesión           | `login`, `iniciar sesión`, `logout`, `cerrar sesión`, `autenticado`, `authenticated`, `sesión`, `session` |

Si NO aparece ninguno de estos términos, generar sin auth setup. Asumir auth donde no aplica es tan dañino como omitirla donde sí.

## Stack obligatorio cuando se detecta auth

1. **`tests/auth/login.setup.ts`** — copiar ``references/templates.md` (sección `auth.setup.ts`)` y rellenar slots. El path es exactamente `tests/auth/login.setup.ts`; el config la captura vía `testMatch: /.*\.setup\.ts/`.
2. **`playwright.config.ts`** — debe contener el project `setup` y `storageState: '.auth/user.json'` en cada project que requiera sesión (ver ``references/templates.md` (sección `playwright.config.ts`)`, ya cubierto).
3. **`fixtures/auth.fixture.ts`** o extensión de `fixtures/base.fixture.ts` — exponer una fixture `authenticated` que asegure que el contexto trae la storageState cargada.
4. **`.gitignore`** — debe incluir `.auth/` para no commitear cookies reales.
5. **Tests** — los que requieran sesión deben pertenecer a un project con `dependencies: ['setup']`. Esto es lo que garantiza que `auth.setup.ts` corra primero.

## Recolección de credenciales

Si se detectan los keywords pero el agente no tiene credenciales, debe **detenerse antes de generar** y preguntar exactamente:

```
Detecté que la suite requiere autenticación (keyword: "<keyword detectado>").
Necesito credenciales válidas para el ambiente de pruebas:
  - login_url:
  - email / usuario:
  - password:
  - expected_url_after_login:
```

No inventar credenciales tipo `test@example.com / Pa55w0rd!`. No leer credenciales de `.env` del entorno local del agente. Las credenciales se almacenan en el `.env` del proyecto entregado, listado en `.gitignore`.

## Ejemplo de detección

HU recibida:

> "Como cliente registrado, quiero ver mi historial de pedidos para revisar compras pasadas. Criterio: solo accesible tras login."

Detección: keywords `cliente`, `historial`, `pedidos`, `login` → AUTH REQUIRED.

Acción:
1. Generar `tests/auth/login.setup.ts`.
2. Asegurar projects con `dependencies: ['setup']` y `storageState: '.auth/user.json'`.
3. El test `tests/HU-XX.spec.ts` se etiqueta con `@HU-XX` y corre dentro del project autenticado.

## Anti-patrón

NO derivar la necesidad de autenticación desde el spec OpenAPI (presencia de `security`). Una API puede requerir token y aun así la UI que se está testeando puede ser una landing pública. La fuente de verdad es la UI/HU descrita por el usuario, no el contrato backend (espejo de ``auth-storage-state.md``).

## Cross-links

- Detalle del flujo storage state: ``auth-storage-state.md``.
- Plantilla del setup: ``references/templates.md` (sección `auth.setup.ts`)`.
- Plantilla del config con project `setup`: ``references/templates.md` (sección `playwright.config.ts`)`.
- Recolección de inputs obligatorios: `[[calidad-mandatory-inputs-protocol]]`.
