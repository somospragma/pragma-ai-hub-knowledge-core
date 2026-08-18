# Quality Gates — Bloqueos Automáticos en Pipeline

Un gate es una condición que **falla el build** si no se cumple. Los reportes sin gates no detienen regresiones — solo informan después del hecho.

## 1. Cobertura mínima por endpoint (Karate)

Pragma usa la fórmula real: cobertura = (endpoints cubiertos / endpoints declarados en OpenAPI) * 100.

```bash
# script post-execution
COVERED=$(jq '.endpoints_covered | length' karate-coverage.json)
TOTAL=$(jq '.paths | keys | length' openapi.json)
PERCENT=$(echo "scale=2; ($COVERED / $TOTAL) * 100" | bc)
MIN=80

if (( $(echo "$PERCENT < $MIN" | bc -l) )); then
  echo "FAIL: coverage $PERCENT% < threshold $MIN%"
  exit 1
fi
```

**Wired en pipeline (Azure):**

```yaml
- script: ./scripts/check-karate-coverage.sh
  displayName: Gate — endpoint coverage
  failOnStderr: true
```

**Override controlado:** si el commit message contiene `SKIP_GATE: coverage <razón>`, el script puede leerlo y degradar a warning. La justificación queda en el historial.

## 2. Thresholds K6 — p95/p99/error_rate

K6 evalúa thresholds y retorna exit code no-zero si fallan. **No requiere gate adicional** — solo dejar que el pipeline falle naturalmente.

```javascript
// load.js
export const options = {
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.01'],   // <1% error rate
    checks: ['rate>0.99'],            // >99% checks passing
  },
};
```

**Importante:** NO usar `--linger` en CI (mantiene el proceso vivo). Sí usar `--summary-export=summary.json` para post-procesamiento.

```yaml
- script: |
    k6 run --summary-export=summary.json load.js
    # exit code !=0 si falla threshold
  displayName: Gate — k6 thresholds
```

## 3. Visual regression (Playwright)

Playwright compara screenshots pixel-a-pixel. Threshold se define por test o globalmente.

```typescript
// playwright.config.ts
export default defineConfig({
  expect: {
    toHaveScreenshot: {
      maxDiffPixels: 100,
      threshold: 0.2,  // 20% diferencia tolerada en luminancia
    },
  },
});
```

```typescript
// test
await expect(page).toHaveScreenshot('login.png');
// falla si diff > 100 pixels o luminancia > 20%
```

El fallo bloquea el pipeline automáticamente. Para actualizar baselines: `npx playwright test --update-snapshots` (solo en branch de baseline, NO en main).

## 4. Accessibility — violations serious/critical

Usar `@axe-core/playwright` o `axe-core` para escanear; gate por severidad.

```typescript
import { AxeBuilder } from '@axe-core/playwright';

test('a11y home', async ({ page }) => {
  await page.goto('/');
  const results = await new AxeBuilder({ page }).analyze();
  const blocking = results.violations.filter(
    v => v.impact === 'serious' || v.impact === 'critical'
  );
  expect(blocking).toEqual([]);  // fail si hay alguno
});
```

## 5. Security — High/Critical vulnerabilities

Conectado con `[[calidad-security-testing]]`. Gates típicos:

```yaml
# Snyk SCA
- script: snyk test --severity-threshold=high
  displayName: Gate — SCA Snyk
  # exit code 1 si encuentra High/Critical

# Trivy (containers)
- script: trivy image --exit-code 1 --severity HIGH,CRITICAL myimage:latest
  displayName: Gate — Trivy

# ZAP DAST
- script: |
    docker run -v $(pwd):/zap/wrk owasp/zap2docker-stable \
      zap-api-scan.py -t openapi.json -f openapi \
      --fail-on-warn=Medium --fail-on-error=High
  displayName: Gate — ZAP DAST
```

## Override controlado — `SKIP_GATE`

Todo override debe ser explícito y auditable. Patrón estándar:

```bash
# Leer último commit message
MSG=$(git log -1 --pretty=%B)

if echo "$MSG" | grep -q "SKIP_GATE: $GATE_NAME"; then
  REASON=$(echo "$MSG" | grep -oP "SKIP_GATE: $GATE_NAME \K.*")
  echo "WARN: gate $GATE_NAME skipped — reason: $REASON"
  exit 0
fi

# si no hay skip, evaluar gate normalmente
```

Reglas:
- La razón es **obligatoria** (string no vacío después del nombre del gate).
- El commit con `SKIP_GATE` queda visible en `git log` y en la PR — audit-friendly.
- Para release gates (deploy a producción), el `SKIP_GATE` debe ser aprobado adicionalmente por un revisor con rol `qa-lead` (configurar en CODEOWNERS o branch protection).

## Tabla de gates mínimos por tipo de pipeline

| Pipeline | Gates obligatorios                                              |
| -------- | --------------------------------------------------------------- |
| PR       | JUnit fail-on-error, coverage Karate, a11y serious              |
| Nightly  | + K6 thresholds, visual regression, SCA Snyk                    |
| Release  | + DAST ZAP, SAST Sonar, security High=0, manual approval        |

## 6. El gate de calidad estático del PR sobre el código de pruebas

El repositorio de automatización es código, y en muchos clientes pasa por el mismo analizador estático que el producto. Dos condiciones bloquean el PR con más frecuencia que el resto:

**Issues nuevos.** El umbral suele ser cero. Son de arreglo mecánico y no se discuten: prefijo de módulo nativo en los imports, reemplazos globales con la API que corresponde, y demás recomendaciones de la versión del lenguaje configurada.

**Cobertura del código nuevo.** El analizador mide **solo las líneas nuevas**, no el proyecto entero, así que un archivo de utilidad sin tests hunde el porcentaje aunque el resto esté al 100%.

### Qué se excluye de cobertura y qué no

El criterio no es "es código de pruebas, se excluye". Es **si la pieza se puede ejercitar sin hardware**:

| Se excluye | Por qué |
|---|---|
| Objetos de página y de pantalla | Solo ejercitables contra un navegador o dispositivo real |
| Steps, hooks, features | Son los tests mismos: cubrirlos con tests es circular |
| Utilidades de línea de comandos y archivos de configuración | No tienen lógica que verificar |

| Se incluye | Por qué |
|---|---|
| Utilidades, motor de ejecución, configuración resuelta, comparación de imágenes, cálculo de resultados | Lógica pura, testeable sin hardware, y **un bug ahí no rompe un test: hace que un test mienta** |

Esa última frase es el argumento que decide la discusión. Un fallo en la utilidad que compara capturas no produce un rojo: produce un verde falso. Por eso se cubre, y por eso una exclusión "temporal" para desbloquear un PR no se revierte nunca y hay que negarse a ella.

Señal de que la exclusión no falta: si las carpetas vecinas del archivo señalado ya están al 100%, el equipo venía cubriéndolas y el archivo es la excepción, no una categoría olvidada.

### El reporte de ejecución también se verifica

Hallazgo que pasa desapercibido: el analizador puede estar recibiendo la cobertura y **no los resultados de ejecución**, porque el archivo de resultados se genera vacío por un fallback del script que lo produce. El tablero muestra cobertura y cero tests. Se comprueba mirando el tamaño y el contenido del archivo generado, no asumiendo que existe.

## Anti-patterns

- Reportes Allure sin gates — bonito dashboard, no detiene regresiones.
- Excluir de cobertura una utilidad de pruebas para desbloquear un PR — un bug ahí no rompe tests, los hace mentir, y la exclusión nunca se revierte.
- Dar por bueno el reporte de resultados sin abrirlo — puede estar vacío y el gate seguir en verde.
- Gates configurados con `continue-on-error: true` — equivale a no tener gate.
- Threshold K6 solo en `avg` — métrica engañosa; usar siempre percentiles.
- `--update-snapshots` en pipeline de main — destruye el baseline visual.
