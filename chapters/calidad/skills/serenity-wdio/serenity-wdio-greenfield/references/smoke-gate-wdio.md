# Smoke Gate (serenity-wdio) — `scripts/run.mjs` con `--tags=@smoke`

Implementación serenity-wdio (WebdriverIO + Serenity/JS + Cucumber) de la política universal `[smoke-gate-policy](../../../_all/smoke-gate-policy.md)`. Antes de declarar `status: success`, el agente DEBE correr al menos un escenario etiquetado `@smoke` por cada plataforma declarada en el proyecto y validar exit code 0.

## Comando canónico por plataforma

```bash
# Web
node ./scripts/run.mjs --mode=web --tags=@smoke

# Web movil (WebView)
node ./scripts/run.mjs --mode=web_movil --tags=@smoke

# Movil nativo (requiere --platform)
node ./scripts/run.mjs --mode=movil --platform=android --tags=@smoke
node ./scripts/run.mjs --mode=movil --platform=ios --tags=@smoke

# Desktop
node ./scripts/run.mjs --mode=desktop --tags=@smoke

# API
node ./scripts/run.mjs --mode=api --tags=@smoke

# Atajo equivalente para la plataforma primaria (npm run test:smoke)
npm run test:smoke
```

Notas:

- El orquestador `scripts/run.mjs` reenvía `--tags=@smoke` a Cucumber como `--cucumberOpts.tags=@smoke`. NUNCA invocar `wdio` directamente saltando el orquestador — el orquestador resuelve el config y el `.env.<modo>` correctos.
- El proceso retorna exit code 0 si todos los escenarios `@smoke` pasan; ≠ 0 si alguno falla.
- Si el proyecto declara varias plataformas, el smoke gate completo del proyecto se considera verde solo cuando **todas** las plataformas con runtime disponible pasan su propio comando `--tags=@smoke`. Las plataformas sin runtime disponible (sin device/simulador/navegador) se reportan `partial` para esa plataforma únicamente, sin bloquear las demás.

## Asegurar al menos un escenario `@smoke` por plataforma

El agente DEBE garantizar ≥1 escenario `@smoke` por canal declarado que represente un happy path mínimo end-to-end. Ejemplo:

```gherkin
@web @regression
Feature: Health check de la aplicacion web

  @smoke @happy-path
  Scenario: La aplicacion carga y muestra la pantalla principal
    Given que Sergio navega a la aplicacion
    Then la pantalla principal esta visible
```

Si no hay escenario `@smoke` para una plataforma declarada, reportar `smoke_gate_missing_scenario_serenity-wdio` para esa plataforma. Convención: el primer `.feature` de cada canal generado por el greenfield incluye un `@smoke` además de su tag funcional.

## Parsing del resultado

`wdio-cucumberjs-json-reporter` emite el JSON de la corrida en `results/serenity-wdio/{fecha}/{ISO}/cucumber/`. Validar primero el exit code del proceso; como segunda señal, parsear el JSON:

```bash
node ./scripts/run.mjs --mode=web --tags=@smoke
EXIT=$?
if [ $EXIT -ne 0 ]; then
  echo "smoke_gate_failed_serenity-wdio mode=web exit=$EXIT" >&2
  exit $EXIT
fi

CUCUMBER_JSON=$(find results/serenity-wdio -name "*.cucumber.json" -newer /tmp/smoke-start | head -1)
if [ -z "$CUCUMBER_JSON" ]; then
  echo "smoke_gate_missing_scenario_serenity-wdio (no reporte emitido)" >&2
  exit 1
fi

FAILED=$(jq '[.[].elements[].steps[]?.result.status] | map(select(. == "failed")) | length' "$CUCUMBER_JSON")
if [ "$FAILED" != "0" ]; then
  echo "smoke_gate_failed_serenity-wdio failed_steps=$FAILED" >&2
  exit 1
fi
```

Si el filtro `--tags=@smoke` no matchea ningún escenario para la plataforma, Cucumber sale con exit 0 pero el reporte JSON queda vacío (0 elementos) → reclasificar como `smoke_gate_missing_scenario_serenity-wdio`.

## Wiring con delivery_gate

```yaml
smoke_gate:
  framework: serenity-wdio
  command: "node ./scripts/run.mjs --mode=web --tags=@smoke"
  executed: true
  exit_code: 0
  duration_seconds: 22
```

Si el proyecto tiene múltiples plataformas, registrar una entrada de `smoke_gate` por plataforma o consolidar en un array; el schema exacto lo define `[[calidad-delivery-gate-contract]]`.

> Recordar: el smoke gate de `movil` requiere device/emulador (Android) o simulador (iOS) disponible; el de `desktop` requiere el binario `.exe` accesible. Si el ambiente no está disponible, el blocker se reclasifica como `environment_device_unavailable` (o `environment_simulator_unavailable`) según `[environment-blocker-evidence](../../../_all/environment-blocker-evidence.md)`, y esa plataforma se degrada a `scaffold-only` sin bloquear a las demás.

## Cross-links

`[[calidad-post-generation-protocol]]`, `[[calidad-delivery-gate-contract]]`, `[smoke-gate-policy](../../../_all/smoke-gate-policy.md)`, `[run-and-modes](./run-and-modes.md)`, `[[serenity-wdio-run-and-tags]]`.
