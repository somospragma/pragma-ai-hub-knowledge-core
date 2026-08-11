# Playwright como librería, con cucumber-js como runner

## El caso

Un arquetipo donde Playwright **no** es el framework de pruebas sino solo el motor de navegador: se importan `chromium`, `firefox` y `webkit`, el ciclo de vida del navegador se maneja a mano en los hooks, y quien orquesta todo es cucumber-js.

Señales de que estás ante este caso, no ante el runner nativo:

| Señal | Runner nativo | Playwright como librería |
|---|---|---|
| `playwright.config.ts` | Existe | **No existe** |
| Archivos de prueba | `*.spec.ts` con `test()` | `*.feature` con `*.steps.ts` |
| Aserciones | `expect` de `@playwright/test` | `expect` de otra librería, o la del propio proyecto |
| Fixtures y `projects` | Sí | No: el navegador se crea en un hook |
| Comando | `npx playwright test` | `npx cucumber-js --profile web` |
| Reporte | `playwright-report` | Reporte de Cucumber |

El caso aparece casi siempre por la misma razón: el proyecto necesitaba cubrir web **y** mobile con un vocabulario Gherkin compartido, y Cucumber fue la única capa capaz de orquestar ambos. No es una mala decisión; es una decisión distinta.

## Qué del bundle Playwright sigue aplicando

Todo lo que trata de **cómo se automatiza un navegador**:

- Estrategia de selectores y prioridad de locators.
- Interceptación de red para mocks (`page.route`).
- Accesibilidad con axe.
- Regresión visual.
- Patrón de objetos de página.
- Autenticación con estado de sesión persistido.
- Esperas: por qué las automáticas de Playwright hacen innecesarias casi todas las explícitas.

## Qué del bundle Playwright NO aplica

Todo lo que trata del **runner**:

| Reference | Por qué no aplica |
|---|---|
| Configuración estricta de `playwright.config.ts` | No hay config: los parámetros viven en el hook y en el archivo de perfiles de Cucumber |
| Composición de fixtures | No hay fixtures: el estado compartido es el World de Cucumber |
| Tags nativos del runner | El filtrado es por tags de Gherkin y perfiles |
| Smoke gate con el runner nativo | El smoke corre con `cucumber-js --tags` |
| Emisor de metadatos del runner | La metadata sale del reporte de Cucumber |

Intentar imponer el runner nativo sobre un arquetipo así es una reescritura completa de la suite, no una mejora. **No se propone salvo que el cliente lo pida.**

## Qué gobierna la capa Cucumber

`[[calidad-cucumber-bdd-conventions]]`: catálogo de steps, sufijo de plataforma, tagging, estructura de archivos, contrato del World y las 12 propiedades verificables. En un arquetipo híbrido, esas convenciones son las mismas para los escenarios web y para los mobile — es su principal ventaja y la razón por la que el equipo eligió esta arquitectura.

## El ciclo de vida del navegador en un hook

```typescript
Before({ tags: '@web', timeout: 60_000 }, async function (this: HookWorld) {
  const tipo = process.env.BROWSER ?? 'chromium';
  const motor = { chromium, firefox, webkit }[tipo];

  this.browser = await motor.launch({ headless: process.env.HEADLESS !== 'false' });
  this.context = await this.browser.newContext({
    locale: resolverLocale(this.testLanguage),
    timezoneId: resolverZonaHoraria(this.testLanguage),
    recordVideo: process.env.RECORD_VIDEO === 'true' ? { dir: 'reports/videos' } : undefined
  });
  this.page = await this.context.newPage();
});

After({ tags: '@web' }, async function (this: HookWorld, { result }) {
  if (result?.status === Status.FAILED && this.page) {
    this.attach(await this.page.screenshot(), 'image/png');
  }
  await this.context?.close();
  await this.browser?.close();
});
```

Tres cosas que el runner nativo hace por ti y aquí hay que hacer explícitamente:

- **Cerrar navegador y contexto siempre**, incluso cuando el escenario falla. Un contexto que no se cierra deja procesos vivos que agotan la memoria del runner en suites largas.
- **Capturar la evidencia antes de cerrar.** Cerrar primero deja sin screenshot justo el escenario que falló.
- **Un contexto nuevo por escenario**, no un contexto compartido. Reutilizarlo arrastra cookies y almacenamiento entre escenarios y produce fallos que dependen del orden de ejecución.

## Aserciones

Sin el `expect` de `@playwright/test` se pierden los *matchers* con reintento automático (`toBeVisible`, `toHaveText`). Con un `expect` genérico, la aserción se evalúa una sola vez y falla si el elemento todavía no llegó.

La solución no es agregar esperas fijas, sino esperar por condición antes de aseverar, aprovechando las esperas automáticas del locator:

```typescript
// Frágil: evalúa una vez
expect(await page.locator(sel).isVisible()).toBe(true);

// Correcto: espera a la condición, luego asevera sobre un hecho estable
await page.locator(sel).waitFor({ state: 'visible', timeout: 10_000 });
expect(await page.locator(sel).textContent()).toContain(textoEsperado);
```

Es el defecto más común en arquetipos de este tipo y la causa principal de escenarios web intermitentes.

## Modo cloud

El navegador remoto se conecta por CDP en vez de lanzarse en local, y esa es la única diferencia:

```typescript
this.browser = esCloud()
  ? await chromium.connectOverCDP(urlCdp)
  : await chromium.launch({ headless: true });
```

Mismo criterio que en mobile: un único punto de bifurcación, en el hook. Ver `references/local-vs-cloud-execution.md` de `[[calidad-appium-wdio-greenfield]]`.

## Al extender un arquetipo así

1. No proponer migrar al runner nativo salvo pedido explícito.
2. Aplicar las convenciones de `[[calidad-cucumber-bdd-conventions]]` para todo lo que sea capa Cucumber.
3. Aplicar el conocimiento de Playwright-librería para todo lo que sea automatización de navegador.
4. Registrar como hallazgo —sin corregir— los defectos propios de este patrón: contextos que no se cierran, aserciones sin espera previa, contexto compartido entre escenarios.
