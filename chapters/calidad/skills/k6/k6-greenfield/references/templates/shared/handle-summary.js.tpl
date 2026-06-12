// {{project_name}} — shared/handle-summary.js
// handleSummary compartido. Importado y re-exportado desde cada tests/{escenario}/main.js.
// Single source of truth: evita duplicar el bloque en cada test.
//
// Salida:
//   - results/{scenario}/{timestamp}-summary.json (estructura por escenario + fecha).
//   - stdout: textSummary con colores.
//
// SCENARIO_NAME se inyecta via env (-e SCENARIO_NAME=linea-base) desde run-all.sh.

import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.2/index.js';

export function handleSummary(data) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const scenarioName = __ENV.SCENARIO_NAME || 'default';
  const outputPath = `results/${scenarioName}/${timestamp}-summary.json`;

  return {
    [outputPath]: JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}
