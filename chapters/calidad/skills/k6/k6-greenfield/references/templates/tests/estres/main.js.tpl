// {{project_name}} — tests/estres/main.js
// Ejecutable: k6 run tests/estres/main.js
//
// Orquesta scenario + workload + handleSummary. No contiene logica propia.
// Mismo scenario que linea-base / carga, cambia la curva (ramping-arrival-rate, 200-300% del peak).

export { options } from '../../workloads/estres.js';
export { default } from '../../scenarios/{{main_flow}}.js';
export { handleSummary } from '../../shared/handle-summary.js';
