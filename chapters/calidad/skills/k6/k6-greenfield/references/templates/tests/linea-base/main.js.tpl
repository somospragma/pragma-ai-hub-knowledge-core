// {{project_name}} — tests/linea-base/main.js
// Ejecutable: k6 run tests/linea-base/main.js
//
// Orquesta scenario + workload + handleSummary. No contiene logica propia.
// Cambiar el workload (linea-base / carga / estres) NO requiere tocar el scenario.

export { options } from '../../workloads/linea-base.js';
export { default } from '../../scenarios/{{main_flow}}.js';
export { handleSummary } from '../../shared/handle-summary.js';
