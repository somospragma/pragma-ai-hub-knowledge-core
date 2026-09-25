# Lectura de fallos y artefactos custom

## Cómo leer un fallo en Serenity BDD HTML

`target/site/serenity/index.html` → abrir en navegador.

1. **Overview** — % de tests pasando/fallando.
2. **Test Results** — lista de escenarios. Click en uno fallido.
3. **Detalle del escenario** — pasos con `#actor ...` (las descripciones de Tasks).
4. **Stack trace + screenshot** — al expandir el step que falló.
5. **Tags** — filtra por `@form`, `@smoke`, etc.

Los nombres de Tasks aparecen tal cual se definieron en `Task.where('#actor ...')`. Si el reporte muestra descripciones poco claras, mejorar las descripciones de las Tasks.

## Cómo leer un fallo en Allure

1. **Overview** — gráficas globales.
2. **Behaviors** → Features → Scenarios.
3. **Failed scenarios** — click expande con video adjunto (si existe).
4. **Categories** — agrupa fallos por tipo (timeout, assertion, etc.).

## Cucumber JSON para procesamiento programático

`reports/cucumber-report.json` — para CI dashboards, scripts custom:

```typescript
import * as fs from 'node:fs';

const report = JSON.parse(fs.readFileSync('reports/cucumber-report.json', 'utf-8'));
const failed = report
  .flatMap((feat: any) => feat.elements)
  .filter((scn: any) => scn.steps.some((s: any) => s.result.status === 'failed'));
```

## Adjuntar artefactos custom desde Tasks

### Adjuntar texto (log estructurado)

```typescript
import { Log } from '@serenity-js/core';

await actor.attemptsTo(
  Log.the('order id capturado:', orderId),
);
```

`Log.the(...)` aparece como entrada en el reporte de Serenity.

### Adjuntar archivo JSON al reporte

```typescript
import { Artifact, JSONData } from '@serenity-js/core';

serenity.announce(
  new Artifact(
    JSONData.fromJSON(orderData),
    'pedido capturado',
  ),
);
```

## Tags de Cucumber para filtrar reportes

```gherkin
@smoke @form
Scenario: Registro exitoso
  ...
```

```bash
# Ejecutar solo escenarios con tag
npx wdio run configs/wdio.web.conf.ts --cucumberOpts.tags="@smoke"
```

Serenity BDD agrupa automáticamente por tags en el dashboard. Tags útiles:

- `@smoke` — suite rápida pre-deploy
- `@regression` — suite completa
- `@flaky` — tests bajo observación
- `@module-x` — agrupar por módulo de negocio

## Nombres de Tasks en el reporte

```typescript
// El reporte muestra: "Task.where(args...)"
Task.where('login', ...);  // MAL

// El reporte muestra: "Pepito inicia sesión con usuario test_user"
Task.where(`#actor inicia sesión con usuario ${ user }`, ...);  // BIEN
```

`#actor` se reemplaza por el nombre real del actor en runtime.

## Checklist al diagnosticar un fallo desde el reporte

1. [ ] Abrí `target/site/serenity/index.html` en navegador
2. [ ] Identifiqué el escenario fallido
3. [ ] Expandí el step que falló y leí el stack trace completo
4. [ ] Vi el screenshot adjunto (web) o video (Allure)
5. [ ] Verifiqué los logs Appium si es mobile (`logs/appium/`)
6. [ ] Confirmé el `.env.*` cargado en la ejecución
7. [ ] Reproduje localmente con el mismo `--mode` y `--platform`
8. [ ] Si es flaky, lo etiqueté con `@flaky` y abrí ticket de investigación
