
# Estructura del plan de pruebas (ISO/IEC/IEEE 29119-3)

Esqueleto canónico del chapter, basado en la plantilla de Test Plan de ISO/IEC/IEEE 29119-3. La columna 829 mapea al legacy IEEE 829 para clientes que exigen esa nomenclatura. Plan ligero = mismas secciones, profundidad mínima (media página por sección); plan formal = completo.

| # | Sección | Contenido | IEEE 829 equiv. |
|---|---|---|---|
| 1 | **Contexto e identificación** | Proyecto/release, versión del plan, autor, aprobadores, referencias (estrategia, HUs, specs) | Test plan identifier / References |
| 2 | **Objetivos de las pruebas** | Qué se busca demostrar/descubrir, en términos verificables ("verificar que los flujos CRITICAL del release 2.3 cumplen sus CA y SLAs") | — |
| 3 | **Alcance** | Ítems y features EN alcance (lista enumerada, con IDs de HU/épica) y explícitamente FUERA (con motivo) | Test items / Features to be / not to be tested |
| 4 | **Estrategia / enfoque** | Embebida ([[calidad-funcional-test-strategy]]) o referenciada; niveles, tipos, técnicas, capas transversales, criterio de automatización | Approach |
| 5 | **Riesgos y análisis** | Matriz producto + proyecto con prob × impacto, mitigación, contingencia, dueño (`risk-analysis-matrix.md`) | Risks and contingencies |
| 6 | **Tipos de prueba y cobertura objetivo** | Por tipo: alcance, herramienta/stack, cobertura comprometida | — |
| 7 | **Premisas y consideraciones** | Supuestos (ambiente disponible desde X, datos entregados por Y), restricciones (ventanas, accesos), dependencias de terceros | Assumptions |
| 8 | **Criterios de entrada / salida / suspensión** | Medibles (`entry-exit-criteria.md`) | Item pass/fail criteria / Suspension criteria |
| 9 | **Ambientes y datos de prueba** | Ambientes por nivel, estado (real vs mock con plan de switchover — [[calidad-sut-readiness-gate]]), estrategia de datos ([[calidad-test-data-management]]) | Environmental needs |
| 10 | **Entregables de prueba** | Lo que se entrega: casos, RTM, informes de avance, reporte de cierre, evidencia, executive reports | Test deliverables |
| 11 | **Roles y responsabilidades** | RACI mínimo: quién diseña, ejecuta, aprueba, decide sobre riesgos; puntos de contacto dev/PO/infra | Responsibilities / Staffing |
| 12 | **Cronograma e hitos** | Hitos verificables atados a los criterios (inicio, fin de diseño, ciclos de ejecución, regresión, cierre) | Schedule |
| 13 | **Métricas y seguimiento** | Qué se mide (avance de ejecución, densidad de defectos, cobertura CA) y dónde se ve (dashboard ALM / informes) | — |
| 14 | **Aprobaciones y versionado** | Quién aprobó, cuándo; historial de cambios | Approvals |

## Reglas de elaboración

1. **Nada de secciones decorativas**: sección que no aplica se elimina con nota ("sin dependencias de terceros en este release"), no se rellena con generalidades.
2. Todo dato no confirmado queda `[A DETERMINAR — dueño, fecha]` visible. Un plan con TBDs honestos es mejor que uno completo e inventado.
3. Los IDs son reales (HUs del ALM, specs versionados) — el plan enlaza, no parafrasea.
4. Persistencia: `test-plan/{proyecto}-test-plan-v{X.Y}.md` en el `output_path`; si hay Confluence/wiki del cliente, se publica ahí vía el MCP correspondiente y el archivo local queda como fuente.
