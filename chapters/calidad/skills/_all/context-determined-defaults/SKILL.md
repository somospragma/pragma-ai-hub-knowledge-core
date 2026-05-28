---
id: calidad-context-determined-defaults
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Los defaults técnicos (tiers de performance, niveles de cobertura, prioridad de páginas, severidad de findings) derivan del CONTEXTO del sistema (criticidad, datos, exposición, tráfico) y NO del sector del cliente."
tags: [defaults, context, tiers, priority, neutral, governance]
---

# Context-Determined Defaults — Defaults Derivados del Contexto, No del Sector

## Principio

La criticidad de un sistema **no la determina el sector del cliente** (banca, salud, gobierno, retail, gaming, telco, edu, manufactura, etc.). Razonamientos del tipo "este cliente es un banco → tier Conservative", "este es de gaming → tier Relaxed", "es gobierno → todo CRITICAL", son **antipatrones**. Sectores enteros tienen sistemas de baja criticidad (un blog de marketing de un banco), y sectores históricamente "ligeros" tienen sistemas de altísima criticidad (matchmaking en gaming con SLA contractual a partners, telemetría de wearable médico FDA-cleared).

La criticidad real se determina por una combinación de **variables objetivas**: clase de datos, clase de tráfico, impacto al usuario, exposición regulatoria, criticidad operacional y ventana de tolerancia a downtime. Estas variables son universales y aplican igual cross-sector.

Este skill define cómo derivar los defaults técnicos (tier de k6, `risk_factor` de Karate, prioridad de páginas de Playwright, severidad de hallazgos) desde esos inputs, **independiente del sector**.

## Inputs para determinar contexto

- **Clase de datos (data class)**: `PUBLIC` | `INTERNAL` | `CONFIDENTIAL` | `RESTRICTED`. Mapea con tipos como PII, PHI, PCI, IP corporativa, datos públicos. Detalle en `references/data-class-public-internal-confidential-restricted.md`.
- **Clase de tráfico (traffic class)**: peak QPS observado, distribución diaria/semanal/mensual, picos estacionales (Black Friday, fin de mes, días de pago, inicio de período escolar, eventos en vivo). Método de cálculo en `references/traffic-class-and-peak-analysis.md`.
- **Impacto al usuario (user impact)**: B2C masivo (>1M usuarios), B2B contractual (SLA escrito), interno (<1k usuarios). Detalle en `references/user-impact-and-blast-radius.md`.
- **Exposición regulatoria (regulatory exposure)**: explícita (texto del marco regulatorio aplica directamente — PCI-DSS, HIPAA, GDPR art. 32, etc.), implícita (contrato B2B referencia compliance en cláusula), ninguna. Detalle en `references/regulatory-exposure-mapping.md`.
- **Criticidad operacional (operational criticality)**: `life-safety` (la falla puede causar daño físico), `mission` (la falla detiene el negocio o un proceso central), `business` (la falla degrada el negocio sin detenerlo), `internal` (la falla afecta solo operaciones internas). Detalle en `references/operational-criticality-tiers.md`.
- **Ventana de downtime tolerable**: `zero` (24/7, sin ventana), `bajo` (minutos/mes), `medio` (horas/semana), `alto` (horas/día).

## Tabla de derivación: contexto → tier k6 / cobertura Karate / prioridad Playwright

| Contexto | k6 tier | Karate `risk_factor` | Page priority |
|---|---|---|---|
| RESTRICTED + life-safety + zero downtime | Conservative | 1.0 | CRITICAL |
| CONFIDENTIAL + mission + bajo downtime | Conservative | 1.0 | CRITICAL |
| CONFIDENTIAL + business + medio downtime | Moderate | 0.7 | HIGH |
| INTERNAL + business + medio downtime | Moderate | 0.4-0.7 | MEDIUM-HIGH |
| INTERNAL + internal + alto downtime | Relaxed | 0.2-0.4 | LOW-MEDIUM |
| PUBLIC + internal + alto downtime | Relaxed | 0.2 | LOW |

**Notar**: ninguna fila menciona sector. Solo variables objetivas. Dos sistemas del mismo cliente (mismo sector) pueden caer en filas diferentes, y eso es correcto.

## Ejemplos cross-sector

Se rotan los sectores deliberadamente para mostrar que el mismo contexto produce el mismo tier sin importar quién es el cliente.

- **Salud — telemedicina sincrónica con dispositivos**: RESTRICTED (PHI + video) + life-safety + zero downtime → Conservative + CRITICAL.
- **Salud — portal de agendamiento de citas**: CONFIDENTIAL (PHI mínimo) + business + medio downtime → Moderate + HIGH.
- **Gobierno — identidad ciudadana / sistema de autenticación nacional**: RESTRICTED + mission + bajo downtime → Conservative + CRITICAL.
- **Gobierno — portal de trámites no críticos (renovación de carnet de biblioteca)**: CONFIDENTIAL + business + medio downtime → Moderate + HIGH.
- **Gaming — matchmaking en partida live con apuestas o ranking**: INTERNAL (PII mínimo) + mission (UX colapsa sin él) + bajo downtime → Moderate + HIGH (puede ser Conservative si hay SLA contractual con partners y revenue significativo durante el evento).
- **E-commerce — checkout durante peak (Black Friday, Cyber Monday)**: CONFIDENTIAL (PCI) + mission + bajo downtime → Conservative + CRITICAL durante la ventana.
- **SaaS B2B multi-tenant — API core de la plataforma**: CONFIDENTIAL (datos del cliente) + business + medio downtime → Moderate + HIGH.
- **IoT industrial — sensor de seguridad en planta (presión, gas, paro de emergencia)**: RESTRICTED (telemetría crítica de seguridad) + life-safety + zero downtime → Conservative + CRITICAL.
- **Educación — LMS durante exámenes en vivo**: INTERNAL + mission durante la ventana de examen + alto downtime fuera de ella → variable por ventana: Conservative durante examen, Relaxed fuera.
- **Media streaming — live event (final deportiva, concierto)**: INTERNAL + mission durante el evento + alto downtime fuera → Moderate con auto-scaling validado por tests; Conservative si hay contrato exclusivo con partners.

Los mismos criterios se aplican a clientes de **fintech, telco, manufactura, agro, retail físico, logística, energy & utilities, real estate, hospitality, transporte, defensa, biotech, edtech, govtech, legaltech** y cualquier otro sector. La pregunta nunca es "qué sector es el cliente"; siempre es "qué contexto tiene este sistema".

## Restricciones

- **NUNCA** elegir tier por sector. "Este cliente es banco → Conservative" es razonamiento incorrecto. La justificación debe citar las variables objetivas (datos, tráfico, impacto, regulación, criticidad, downtime).
- **SIEMPRE** pedir los inputs de contexto al usuario / PO / arquitecto del cliente antes de fijar tier. Defaultear es válido solo cuando se marca explícitamente "default, revisar" en el entregable y se incluye en los `mandatory-inputs` pendientes (`[[calidad-mandatory-inputs-protocol]]`).
- **Cambio de tier requiere registro escrito** de la razón (parte de la evidencia auditable, ver `[[calidad-test-evidence-and-traceability]]`). No se ajusta el tier "porque el cliente pidió que pasara el build".
- Distintos sistemas del mismo cliente pueden caer en tiers distintos — eso es esperado y deseable. Forzar un solo tier por cliente es antipatrón.
- Una variable extrema (p. ej. life-safety, o RESTRICTED) **eleva** el tier aunque otras variables estén bajas. Nunca lo baja.

## Cross-links

- `references/data-class-public-internal-confidential-restricted.md`
- `references/traffic-class-and-peak-analysis.md`
- `references/user-impact-and-blast-radius.md`
- `references/regulatory-exposure-mapping.md`
- `references/operational-criticality-tiers.md`
- `[[calidad-chapter-perspective]]`
- `[[calidad-business-driven-prioritization]]`
- `[[calidad-mandatory-inputs-protocol]]`
- `[[calidad-test-evidence-and-traceability]]`
- `[[calidad-security-testing]]`
- `[[calidad-sut-types-and-adaptations]]`
- `[[k6-thresholds-three-tiers]]`
- `[[karate-negative-coverage-formula]]`
