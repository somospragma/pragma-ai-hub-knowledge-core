
# Patrones de splitting de historias

Se aplica cuando INVEST-Small dio `warn|fail`. El objetivo: historias hijas que entregan valor por sí mismas (verticales), no capas técnicas (horizontales). Partir por capas (una HU "backend" + una HU "frontend") es el anti-patrón número uno.

## SPIDR (marco principal)

| Letra | Patrón | Cuándo | Ejemplo de corte |
|---|---|---|---|
| **S** — Spike | Incógnita que impide estimar | INVEST-E falló por incógnita técnica | Spike time-boxed "investigar si el PSP soporta débitos parciales" separado de la HU funcional |
| **P** — Paths | Flujo con múltiples caminos | Flujos alternativos con valor propio | "Pagar con tarjeta" / "pagar con PSE" / "pagar con puntos" |
| **I** — Interfaces | Múltiples canales/plataformas | Web + móvil + API en la misma HU | "Consultar saldo en web" primero; móvil después |
| **D** — Data | Variantes por tipo de dato | Tipos de dato con reglas distintas | "Transferir a cuenta propia" / "a terceros" / "internacional" |
| **R** — Rules | Reglas de negocio apilables | Reglas que endurecen incrementalmente | v1 sin límite diario; v2 agrega límite y bloqueo |

## Patrones complementarios

- **Por pasos del workflow**: si el proceso tiene N pasos, la primera historia recorre el esqueleto end-to-end (walking skeleton) y las siguientes profundizan pasos.
- **Happy path primero**: la primera hija entrega el camino feliz completo; las siguientes agregan manejo de errores y bordes. OJO: la hija "manejo de errores" sigue siendo vertical (se demo-a provocando el error).
- **CRUD por operación**: crear/consultar suele ser la primera; actualizar/eliminar después, si cada una tiene valor demo-able.
- **Por criterio de aceptación**: cuando los CA son casi independientes entre sí, cada grupo cohesivo de CA es candidata a hija. Es el patrón más mecánico — validar que cada hija conserve narrativa con valor.
- **Extraer lo no funcional**: performance/hardening que infló la HU se separa como historia técnica explícita con su propio criterio medible (conecta con [[calidad-funcional-test-strategy]] para decidir cómo se prueba).

## Reglas de la propuesta de splitting

1. Cada hija propuesta lleva: narrativa completa, CA borrador (marcados `[PROPUESTO]`), y qué CA/hallazgos de la madre hereda.
2. Proponer el **orden de implementación por valor** (qué hija primero y por qué), no solo la lista.
3. La suma de las hijas debe cubrir el 100% del alcance de la madre; lo que se recorta a propósito se declara ("fuera de alcance de esta partición: X").
4. Verificar INVEST de cada hija antes de proponerla (una partición que produce hijas dependientes entre sí en el mismo sprint no resolvió nada).
5. La creación de work items hijos en Azure/Jira ocurre SOLO tras aprobación del PO, vía [[calidad-alm-mcp-integration]] (con links parent-child correctos).
