// {{project_name}} — tests/carga/main.js
// Ejecutable: k6 run tests/carga/main.js
//
// Orquesta scenario + workload + handleSummary. No contiene logica propia.
// Mismo scenario que linea-base, cambia la curva de carga.

export { options } from '../../workloads/carga.js';
export { default } from '../../scenarios/{{main_flow}}.js';
export { handleSummary } from '../../shared/handle-summary.js';
