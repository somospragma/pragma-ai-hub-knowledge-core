---
id: calidad-business-driven-prioritization
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: Asignación de prioridad de pruebas (CRITICAL/HIGH/MEDIUM/LOW) basada en valor de negocio y riesgo, no en heurísticas de nombre.
tags: [prioritization, risk, business-value, governance]
---

# Business-Driven Prioritization — Prioridad por valor de negocio

## Cuándo aplicar

Aplica este skill **cada vez** que sea necesario asignar una prioridad a:

- Páginas web (Playwright) o pantallas móviles (Appium).
- Escenarios o features (Karate, Cucumber).
- Endpoints o métodos del contrato (Karate, K6).
- Flujos end-to-end o user journeys completos.
- Casos de uso dentro de una user story.

Es transversal a los cuatro frameworks del Chapter Calidad y a cualquier workflow que necesite ordenar por importancia.

## Principio

**La prioridad la fija el negocio, no el nombre del recurso.**

- La asigna el **Product Owner**, el **QA Lead** o un **risk assessment formal** hecho con stakeholders del negocio.
- **NUNCA** se infiere por keywords del path, URL o nombre de archivo. `/login` no es CRITICAL por defecto: en una app interna de catálogo puede ser MEDIUM; en un portal de telemedicina, banca digital, identidad ciudadana o gaming en vivo puede ser CRITICAL.
- **NUNCA** se inventa: si nadie asignó la prioridad y no hay señal en la documentación, se pregunta.

## Cómo obtener prioridades

Orden recomendado de fuentes, de más confiable a menos:

1. **Risk assessment explícito** del PO/QA Lead, idealmente entregado como input del workflow.
2. **`user_story`**: los criterios de aceptación suelen indicar criticidad ("Como cliente Pyme, debo poder transferir... — bloqueante para release"). Buscar señales de regulatorio, financiero, SLA, compliance.
3. **`firma` del servicio**: los SLAs declarados son señal directa. SLA p95 < 200ms y disponibilidad 99.99% → típicamente CRITICAL. SLA p95 < 2s y disponibilidad 99% → típicamente MEDIUM.
4. **Documentación de dominio** (steering del cliente, glosario, política de riesgo): si menciona "flujo crítico" o "operación regulada", es señal explícita.
5. **Preguntar al usuario** con la siguiente tabla a llenar:

   ```
   Por favor asigna riesgo (CRITICAL/HIGH/MEDIUM/LOW) a cada item:
   - <item 1>: ___
   - <item 2>: ___
   ...
   ```

6. **Default**: si **nada** de lo anterior aplica, defaultear a `HIGH` y **solicitar revisión explícita** al usuario antes de proceder. Nunca defaultear silenciosamente.

## Tabla de niveles

| Nivel      | Impacto financiero          | Impacto regulatorio                   | Alcance de usuarios     | Frecuencia de uso        | Ejemplos típicos                                        |
|------------|-----------------------------|---------------------------------------|-------------------------|--------------------------|---------------------------------------------------------|
| `CRITICAL` | Pérdida directa de dinero o reputación de marca | Falla causa incumplimiento (SOX, PCI, HIPAA, GDPR, SFC) | Todos los usuarios externos | Diaria, en hora pico    | Transacciones financieras, autenticación de identidad, prescripción médica, expediente clínico, voto electrónico, matchmaking en gaming live, checkout e-commerce en peak, sensores life-safety en IoT industrial |
| `HIGH`     | Pérdida indirecta (costo operacional, retrabajo) | Falla auditable pero no sancionable inmediato            | Mayoría de usuarios       | Diaria fuera de pico     | Consulta de saldo, alta de productos, integraciones B2B |
| `MEDIUM`   | Sin pérdida monetaria directa  | Sin impacto regulatorio                | Subset de usuarios       | Semanal / bajo demanda   | Configuración de preferencias, búsquedas filtradas       |
| `LOW`      | Costo nulo / cosmético         | Ninguno                                | Internos o automatizados | Esporádica               | Health checks, metadata, catálogos estáticos, admin tooling |

Criterio de tie-break: si un item cumple criterios de dos niveles, se asigna el **mayor**.

## Anti-patrones

- **Inferir por keywords**: "el path contiene `/login` → CRITICAL", "el path contiene `/profile` → MEDIUM", "el path contiene `/checkout` → CRITICAL". Falso en general: depende del dominio.
- **Asumir que un recurso existe** porque "todas las apps tienen checkout": no todas las apps lo tienen, y asignar prioridad a algo que no existe genera ruido.
- **Usar el nombre del recurso como única señal**: `POST /pago` puede ser un mock, un endpoint de staging o un side-effect; sin contexto del negocio no se sabe.
- **Defaultear silenciosamente a MEDIUM** para evitar la pregunta: oculta el problema, genera cobertura desbalanceada y diluye la trazabilidad.
- **Mezclar prioridad técnica con prioridad de negocio**: la complejidad técnica de testing NO es señal de criticidad de negocio. Un endpoint trivial puede ser CRITICAL si maneja dinero.

## Encadenamiento

- En Karate, el `risk_factor` definido en `chapters/calidad/skills/automation/karate/karate-greenfield/references/negative-coverage-formula.md` consume directamente esta clasificación para modular la cantidad de escenarios negativos por endpoint.
- En Playwright y Appium, el orden de scaffold (`[[calidad-streaming-files-protocol]]`) prioriza páginas/pantallas CRITICAL primero.
- En K6, los thresholds más estrictos se aplican a endpoints CRITICAL/HIGH.

## Restricciones

- **NUNCA** generar pruebas con prioridades inventadas: documentar siempre la fuente de la asignación (PO, user_story, firma, default-pendiente-revisión).
- **NUNCA** ocultar el default `HIGH` cuando se usó: hay que reportarlo explícitamente para que el usuario lo confirme o corrija.
