# Quarantine Pattern

Mecánica del chapter para aislar tests flaky sin bloquear el pipeline ni esconderlos indefinidamente. Quarantine no es "ignorar el test"; es **darle un SLA explícito de resolución**.

## Reglas duras

- Quarantine **siempre** lleva ticket asociado con SLA. Sin ticket, el test está prohibido en quarantine y debe corregirse o eliminarse.
- Quarantine **no bloquea** el pipeline principal (smoke/regression default), pero **sí se ejecuta en un job separado** con reporte propio.
- Quarantine **expira**: 14 días de revisión, 30 días máximos antes de eliminar el test.

## Mecánica

1. **Tag.** Marcar el test con `@quarantine`. Convención del chapter (todos los frameworks aplican).
2. **Exclusión por default.** El job principal de smoke/regression excluye `@quarantine`. El job principal sigue siendo gate del merge.
3. **Job separado.** Crear job `quarantine-suite` en el pipeline que ejecuta solo `@quarantine`, no falla el build, y publica reporte independiente.
4. **Ticket automático.** Al taggear `@quarantine`, crear ticket en Jira/Linear con campos obligatorios:
   - Link al run que motivó la quarantine.
   - Stability score actual.
   - Patrón identificado (ver `failure-pattern-catalog.md`).
   - Hipótesis de causa raíz.
   - Owner del test.
   - Due date: **14 días** desde la creación.
5. **Revisión a 14 días.** Si el test sigue flaky, escalar a Chapter Lead y extender SLA a 30 días con plan concreto.
6. **Eliminación a 30 días.** Si el test sigue flaky después de 30 días, **eliminar el test del repo**. Cubrir la funcionalidad con otra estrategia (otro test, monitoring sintético, alerta en logs). Un test ignorado indefinidamente es deuda silenciosa.

## Snippet Playwright (`playwright.config.ts`)

Excluir `@quarantine` del default y configurar job separado:

```ts
// playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  projects: [
    {
      name: 'default',
      grepInvert: /@quarantine/,
      retries: 1,
    },
    {
      name: 'quarantine',
      grep: /@quarantine/,
      retries: 0,
    },
  ],
});
```

Uso en CI (GitHub Actions, fragmento):

```yaml
jobs:
  default-suite:
    runs-on: ubuntu-latest
    steps:
      - run: npx playwright test --project=default
  quarantine-suite:
    runs-on: ubuntu-latest
    continue-on-error: true  # NO bloquea el pipeline
    steps:
      - run: npx playwright test --project=quarantine --reporter=html
      - uses: actions/upload-artifact@v4
        with:
          name: quarantine-report
          path: playwright-report/
```

## Snippet Karate (`karate-config.js` + tag filter)

```bash
# Default suite (excluye quarantine)
mvn test -Dkarate.options="--tags ~@quarantine"

# Quarantine suite (solo quarantine)
mvn test -Dkarate.options="--tags @quarantine"
```

## Snippet K6 (tags)

K6 no soporta tag-based exclusion nativa al estilo Playwright. Usar variable de entorno:

```js
export const options = {
  scenarios: {
    main: {
      executor: 'ramping-vus',
      // ...
      tags: { quarantine: 'false' },
      exec: __ENV.QUARANTINE === 'true' ? undefined : 'mainScenario',
    },
  },
};
```

## Anti-patrones

- **Quarantine sin ticket.** Crea deuda invisible. Prohibido.
- **Quarantine indefinida.** Si nadie revisa a 14/30 días, el test es ruido. Eliminar.
- **Quarantine de tests `@critical` o `@security`.** Estos nunca deben estar flaky; si lo están, hay bug en el SUT o test mal diseñado y debe atacarse YA, no quarantinearse.
- **Quarantine para "callar" un test que reporta bug real.** Es esconder bugs; viola el contrato anti-cheating del chapter.
