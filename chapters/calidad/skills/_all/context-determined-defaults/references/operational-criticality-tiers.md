# Operational Criticality Tiers

Cuatro niveles de criticidad operacional. Universal cross-sector. Es el input que, junto con la clase de datos, **más eleva el tier de testing** cuando es alto.

## life-safety

- **Definición**: la falla del sistema puede causar **daño físico** a personas (lesión, enfermedad agravada, muerte) o **daño ambiental** grave.
- **Ejemplos cross-sector**:
  - Dispositivos médicos clase II/III (monitor cardíaco, bomba de insulina, ventilador).
  - Sistema de control industrial (SCADA) en planta química, eléctrica, nuclear.
  - Sensores de paro de emergencia en línea de producción.
  - Sistemas de control automotriz (ABS, airbags, ADAS).
  - Aviónica.
  - Telemetría de salud crítica en wearables certificados (FDA / CE-MDR).
  - Sistemas de emergencia (911, alertas sísmicas, alertas tsunami).
  - Robótica colaborativa con humanos en el loop.
- **Implicación testing**: Conservative SIEMPRE. risk_factor 1.0. Cobertura negativa exhaustiva. HIL obligatorio si hay hardware. Evidencia compatible con FDA / ISO 26262 / IEC 62304 según aplique.

## mission

- **Definición**: la falla **detiene un proceso central** del negocio o de la operación del cliente. No causa daño físico, pero detiene revenue, atención al ciudadano, o servicio crítico.
- **Ejemplos cross-sector**:
  - Checkout en peak de un e-commerce grande.
  - Sistema de matchmaking de un juego durante un evento global.
  - API de autenticación de un sistema de identidad nacional.
  - Sistema de liquidación interbancaria intradía.
  - Sistema de prescripción en una farmacia durante horario de atención.
  - Streaming de un evento en vivo con derechos exclusivos.
  - Plataforma de educación durante exámenes en vivo.
  - Sistema de booking durante temporada alta.
  - LMS durante semana de admisión.
- **Implicación testing**: Conservative o Moderate alto (risk_factor 0.7-1.0). Page priority CRITICAL/HIGH. Stress y resilience tests obligatorios.

## business

- **Definición**: la falla **degrada el negocio** pero no lo detiene. Hay workaround manual, tolerancia de horas, alternativa parcial.
- **Ejemplos cross-sector**:
  - Sistema de notificaciones (email, push) — la transacción ocurre, la notificación llega tarde.
  - Recomendaciones de producto — el e-commerce sigue vendiendo sin recomendaciones.
  - Dashboard de reportes ejecutivos — se puede reconstruir manualmente.
  - Sistema de gestión de tickets de soporte — el soporte puede usar teléfono temporalmente.
  - CRM para fuerza de ventas — se sigue vendiendo con planilla.
- **Implicación testing**: Moderate. risk_factor 0.4-0.7. Page priority MEDIUM/HIGH.

## internal

- **Definición**: la falla **afecta solo operaciones internas** no críticas. Productividad de un equipo se reduce pero no hay impacto a usuario final ni revenue.
- **Ejemplos cross-sector**:
  - Herramienta interna de QA o devops.
  - Wiki interna de documentación.
  - Sistema de feedback interno de empleados.
  - Dashboards de métricas no-criticas.
- **Implicación testing**: Relaxed permitido. risk_factor 0.2-0.4. Page priority LOW/MEDIUM.

## Reglas de elevación / no-elevación

- Una variable life-safety **siempre eleva** el tier a Conservative + risk_factor 1.0, sin importar las demás.
- Datos RESTRICTED **siempre elevan** al menos a Moderate, aunque la criticidad operacional sea internal (un dataset de empleados con números de tarjeta no se relaja por ser interno).
- Downtime tolerable alto **no compensa** life-safety ni RESTRICTED — siempre se mantiene el tier alto.
- Cuando hay conflicto entre variables, **gana la más estricta** (la que sube el tier).

## Antipatrones

- Clasificar como "business" cuando hay impacto a vida humana — el costo de equivocarse es enorme.
- Asumir que algo "interno" siempre es internal — un ERP que detiene producción es mission-critical aunque sea de empleados.
- No reclasificar cuando el sistema crece — un MVP internal puede convertirse en mission en un trimestre.
- Tratar todo el sistema con un tier único — un solo sistema puede tener endpoints mission y endpoints internal.
