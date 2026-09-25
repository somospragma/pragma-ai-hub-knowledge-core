# Configuraciones WDIO (Serenity WDIO Greenfield)

Cada `configs/wdio.<modo>.conf.ts` hereda de `wdio.shared.conf.ts` mediante un merge y extiende solo lo necesario.

## Patron de merge

```typescript
const merge = (base: WebdriverIOConfig, extra: Partial<WebdriverIOConfig>): WebdriverIOConfig => ({
  ...base,
  ...extra,
  serenity: { ...base.serenity, ...extra.serenity },
});

export const config: WebdriverIOConfig = merge(shared, {
  specs: ['../features/web/Features/*.feature'],
  capabilities: [
    {
      browserName: 'chrome',
      'wdio:enforceWebDriverClassic': true,
      'goog:chromeOptions': { args: ['--headless=new', '--disable-gpu'] },
    },
  ],
  cucumberOpts: {
    import: ['./features/step-definitions/web/*.ts', './features/support/*.ts'],
    format: ['json:./reports/cucumber-report.json'],
    timeout: 60000,
  },
});
```

## Regla critica: `specs` vs `cucumberOpts.require`/`import` resuelven rutas de forma distinta

Verificado con ejecucion real: `specs` es relativo al archivo `configs/wdio.<modo>.conf.ts` (por eso usa el prefijo `../features/...`). En cambio, `cucumberOpts.require` y `cucumberOpts.import` se resuelven relativos al directorio desde donde se invoca el proceso de WebdriverIO (la raiz del proyecto), NO al archivo de config. Usar `../` en `cucumberOpts.require`/`import` hace que el glob no matchee ningun archivo y el error resultante es engañoso: Cucumber reporta `Step "..." is not defined` en lugar de un error de "archivo no encontrado", porque el step-definition simplemente nunca se cargo.

```typescript
// CORRECTO — specs relativo al archivo de config, require/import relativo a la raiz del proyecto
export const config: WebdriverIOConfig = merge(shared, {
  specs: ['../features/api/Features/*.feature'],      // relativo a configs/
  cucumberOpts: {
    require: ['./features/step-definitions/api/*.ts', './features/support/*.ts'],  // relativo a la raiz
    format: ['json:./reports/api-cucumber-report.json'],
    timeout: 15000,
  },
});

// INCORRECTO — este patron NO carga los steps (falla silenciosamente con "Step is not defined")
cucumberOpts: {
  require: ['../features/step-definitions/api/*.ts'],  // MAL: relativo a la raiz, no a configs/
},
```

Aplica a los 6 `configs/wdio.<modo>.conf.ts` del arquetipo por igual (web, web_movil, android, ios, desktop, api). Verificar esta regla explicitamente en el checklist de coherencia post-emision (`[[calidad-post-generation-protocol]]`, paso 1).

## Regla `wdio:enforceWebDriverClassic`

Toda capability de navegador DEBE incluir `'wdio:enforceWebDriverClassic': true`. Esto fuerza WebDriver Classic en lugar de WebDriver BiDi (default de WebdriverIO v9), evitando incompatibilidades con `@serenity-js/web` v3.31.x.

- Aplica a: `wdio.web.conf.ts`, `wdio.web_mobile.conf.ts` y cualquier config que arranque navegador.
- No aplica a: `wdio.android.conf.ts`, `wdio.ios.conf.ts` (mobile nativo) ni `wdio.desktop.conf.ts` (Appium Windows).

Sintoma tipico cuando falta: `Cannot read properties of undefined`, `command not implemented` o cuelgues al iniciar el navegador en CI.

## Workaround de window handles para NATIVE_APP

Serenity/JS no soporta completamente mobile nativo. `getWindowHandle()` / `getWindowHandles()` no estan soportados en `NATIVE_APP`. El parche vive SOLO en el hook `before` de `wdio.shared.conf.ts` y aplica cuando `browser.isMobile === true`.

```typescript
// En wdio.shared.conf.ts (hook before). NO replicar en Tasks ni Steps.
b.overwriteCommand('getWindowHandle', async (orig, ...args) => {
  try { return await orig(...args); }
  catch (e) { if (isUnsupported(e)) return 'NATIVE-APP'; throw e; }
});
b.overwriteCommand('getWindowHandles', async (orig, ...args) => {
  try { return await orig(...args); }
  catch (e) { if (isUnsupported(e)) return ['NATIVE-APP']; throw e; }
});
```

Prohibido replicar este workaround en Tasks, Interactions o Steps.
