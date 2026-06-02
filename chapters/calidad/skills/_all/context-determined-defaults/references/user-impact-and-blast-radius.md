# User Impact y Blast Radius

Define cuántas personas y de qué tipo se ven afectadas si el sistema falla. Es uno de los inputs que **eleva o reduce** el `risk_factor` de Karate y la prioridad de Playwright.

## Categorías

### B2C masivo (>1M usuarios potenciales)

- **Definición**: aplicaciones de cara al consumidor con base de usuarios grande o pública.
- **Ejemplos cross-sector**: app de un banco retail, marketplace de e-commerce, app de un operador de telco, portal de identidad ciudadana, app de un sistema de salud público, plataforma de streaming.
- **Implicación**: blast radius alto; falla → millones de usuarios afectados, riesgo reputacional inmediato (RRSS, prensa), riesgo de multa regulatoria si hay datos personales.
- **risk_factor sugerido**: 0.7-1.0 según las otras variables.

### B2B contractual

- **Definición**: clientes son empresas con SLA escrito y penalización por incumplimiento. Volumen de usuarios típicamente menor (cientos o miles), pero cada cliente es revenue significativo.
- **Ejemplos cross-sector**: API de pagos para merchants, plataforma SaaS multi-tenant, integración EDI con cadena de suministro, gateway de identidad para partners federados, plataforma de prescripción electrónica para farmacias, sistema de liquidación interbancaria.
- **Implicación**: blast radius medio en número, alto en revenue y reputación. Cláusulas contractuales obligan a SLA, audit logs, evidencia de testing.
- **risk_factor sugerido**: 0.5-1.0 según SLA y penalizaciones.

### Interno (<1k usuarios)

- **Definición**: aplicaciones para empleados del cliente o de su ecosistema cerrado.
- **Ejemplos cross-sector**: ERP interno, dashboard de operaciones, herramienta de back-office, sistema de RRHH, CRM interno, monitor de planta industrial para operadores en sitio.
- **Implicación**: blast radius bajo en usuarios pero puede ser alto en operación (si el back-office para, no se vende). El "interno" no es excusa para baja calidad, pero el tier puede relajarse.
- **risk_factor sugerido**: 0.2-0.5 salvo que el sistema interno sea mission-critical (entonces sube).

## Mapeo con SLAs típicos

| User impact | SLA típico | Tiempo medio respuesta a incidente | Penalización |
|---|---|---|---|
| B2C masivo | 99.9%+ | < 15 min | reputacional + posible multa |
| B2B contractual | 99.95%+ con SLA escrito | < 15 min (P1) | crédito de servicio + revenue lost |
| Interno | 99.5% suficiente | horario laboral | productividad interna |

## Cómo el impacto cambia el risk_factor

- **B2C masivo + datos CONFIDENTIAL+** → risk_factor ≥ 0.7. La cobertura negativa debe ser robusta porque cada bug se ve en millones de sesiones.
- **B2B contractual con SLA** → risk_factor según penalización contractual; un SLA con créditos de 25% de la factura mensual por incumplimiento eleva a 0.8-1.0.
- **Interno mission-critical** (p. ej. ERP que detiene producción si cae) → risk_factor 0.7+; "interno" no significa bajo riesgo.
- **Interno con downtime tolerable** → 0.2-0.4.

## Blast radius — cómo cuantificarlo

- **Usuarios afectados**: estimación de MAU/DAU expuestos al endpoint.
- **Revenue afectado**: $/hora si el sistema cae (gross transaction value × % afectado).
- **Tiempo de recuperación percibido**: ¿el usuario reintenta y funciona, o pierde la sesión / dato?
- **Recuperabilidad**: ¿la falla es transitoria (retry funciona) o requiere intervención humana / data fix?
- **Reputación**: ¿la falla aparecería en prensa o redes? Si sí, blast radius mayor al numérico.

## Antipatrones

- Asumir que "interno" = bajo riesgo. Un ERP roto detiene operación entera de la planta.
- Asumir que B2C "bajo tráfico" hoy se mantendrá — los lanzamientos producen 100x en una semana.
- Tratar todos los endpoints de un sistema B2C con el mismo risk_factor — `/health` no tiene el mismo impacto que `/checkout`.
- No considerar SLA contractual cuando existe — el contrato es la regla, no la opinión del equipo de testing.
