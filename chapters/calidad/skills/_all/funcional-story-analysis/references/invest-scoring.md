
# Rúbrica INVEST — scoring por criterio

Cada criterio se evalúa `pass | warn | fail` con evidencia textual. El score global es el peor de los seis (una HU no es "casi INVEST").

## I — Independent

| Veredicto | Señal |
|---|---|
| pass | La HU puede desarrollarse y probarse sin esperar otra HU del mismo sprint; las dependencias externas están declaradas y disponibles |
| warn | Depende de otra HU del sprint pero la dependencia está declarada y secuenciada |
| fail | Dependencias no declaradas descubiertas en el análisis (ej. menciona un servicio/pantalla que otra HU aún no construye), o dependencia circular |

Preguntas guía: ¿se puede demo-ar sola? ¿el orden de implementación está forzado y nadie lo dijo?

## N — Negotiable

| Veredicto | Señal |
|---|---|
| pass | Describe el QUÉ y el PARA QUÉ; deja el CÓMO al equipo |
| warn | Fija detalles de implementación (componentes, librerías, SQL) que restringen sin justificación |
| fail | Es una especificación técnica disfrazada de HU (sin narrativa de usuario ni valor) o un contrato cerrado sin espacio de conversación |

## V — Valuable

| Veredicto | Señal |
|---|---|
| pass | El "Para" expresa un beneficio verificable para un usuario/negocio identificable |
| warn | Valor genérico ("mejorar la experiencia") sin métrica ni comportamiento observable |
| fail | Sin "Para", o el beneficiario es el propio sistema ("para que el backend guarde X") sin traza al usuario |

## E — Estimable

| Veredicto | Señal |
|---|---|
| pass | El equipo puede dimensionarla con la información presente |
| warn | Estimable solo asumiendo respuestas a preguntas abiertas (listar cuáles) |
| fail | Incógnitas técnicas o funcionales que la vuelven un spike encubierto; corresponde separar el spike |

## S — Small

| Veredicto | Señal |
|---|---|
| pass | Cabe en un sprint con margen; un solo objetivo funcional |
| warn | Múltiples flujos o roles en una sola HU; splitting recomendable (patrones en [[calidad-funcional-story-refinement]], `references/story-splitting-patterns.md`) |
| fail | Es una épica: varios objetivos, varias pantallas/servicios, criterios de aceptación de dominios distintos |

Señal cuantitativa de warn: más de ~7 criterios de aceptación o criterios que mezclan dominios (UI + batch + reporting).

## T — Testable

| Veredicto | Señal |
|---|---|
| pass | Cada criterio de aceptación tiene un resultado observable y decidible (pass/fail sin juicio subjetivo) |
| warn | Criterios testables pero incompletos (solo happy path) o con datos vagos ("un monto grande") |
| fail | Criterios subjetivos ("rápido", "amigable", "correctamente") sin cuantificar, o HU sin criterios de aceptación |

Este criterio pesa doble para el chapter: una HU no testable bloquea el diseño de casos (`[[calidad-funcional-test-design]]`) y la automatización. `T: fail` implica veredicto DoR `not_ready` sin excepción.

## Formato de salida por criterio

```
I: warn — "depende del servicio de scoring (HU-231)" citado en la descripción; HU-231 está en el mismo sprint sin secuencia declarada.
```

Evidencia textual obligatoria: cita la frase de la HU (o su ausencia: "sin sección Para") que motiva el veredicto.
