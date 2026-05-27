
# `handleSummary()` — Evidencia y trazabilidad

K6 invoca `handleSummary(data)` al final de cada corrida. La función decide qué archivos persistir y qué imprimir en stdout. En todos los scripts del proyecto debe exportar a `results/${ISO-timestamp}-summary.json` y mostrar `textSummary` en consola.

## Snippet completo (default — jslib remota)

```javascript
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.2/index.js';

export function handleSummary(data) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  return {
    [`results/${timestamp}-summary.json`]: JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}
```

Notas sobre la versión:

- Usar `0.0.2`. La versión `0.0.1` está deprecada y deja de descargarse en algunos mirrors corporativos.
- Versiones más nuevas pueden existir pero no han sido validadas con la suite del Chapter. Si k6 reporta un fallo de descarga, primero confirma versión disponible antes de actualizar.

## Alternativa offline / CI air-gapped

En bancos LATAM y entornos regulados es común que los runners de CI **no tengan egress** a internet (sin acceso a `https://jslib.k6.io`). El import remoto rompe la corrida: `k6 run` aborta intentando resolver el módulo.

Solución: vendorizar el archivo dentro del proyecto y consumirlo localmente.

1. Descargar el archivo una sola vez (desde una máquina con egress):
   ```bash
   mkdir -p tests/vendor
   curl -fsSL https://jslib.k6.io/k6-summary/0.0.2/index.js -o tests/vendor/k6-summary.js
   ```
2. Commitearlo al repo (es código de terceros, pequeño, estable; tratarlo como dependencia vendorizada).
3. Cambiar el import en cada script:
   ```javascript
   import { textSummary } from './vendor/k6-summary.js';
   ```
4. Documentar en el `README.md` que `tests/vendor/k6-summary.js` es código de terceros (link al original) y la versión congelada.

Justificación: las pipelines de bancos LATAM y entornos regulados a menudo se ejecutan en redes internas sin egress a `https://jslib.k6.io`; el vendor local elimina la dependencia de red y evita corridas no reproducibles cuando cambia la versión upstream.

Cuándo aplicar esta alternativa: cuando el `firma` del cliente incluye "CI sin egress", "air-gapped", "self-hosted runner con allowlist", o cuando una corrida previa falló con error de DNS/resolución contra `jslib.k6.io`.

## Razón

- **Trazabilidad**: cada corrida deja un JSON único e inmutable con métricas (`http_req_duration`, `http_req_failed`, `checks`, etc.).
- **Comparación entre corridas**: los archivos con timestamp ISO permiten diff entre baselines y validar tendencias.
- **Calibración**: el workflow `[[calibrate-k6-thresholds]]` lee estos JSON para derivar thresholds reales.
- **Integración CI**: el JSON se puede subir como artefacto del pipeline y `textSummary` da feedback inmediato en logs.

## Reglas

- La carpeta `results/` debe estar en `.gitignore` para evitar commitear evidencia.
- Cada uno de los 5 scripts (`smoke`, `load`, `stress`, `spike`, `soak`) declara su propio `handleSummary()`.
- No cambies el formato del timestamp: `:` y `.` se reemplazan por `-` para compatibilidad con todos los filesystems.
- Si el proyecto usa la alternativa offline, todos los scripts importan desde `./vendor/k6-summary.js`. No mezclar imports remotos y vendorizados en un mismo proyecto.
