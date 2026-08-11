
# Calidad de criterios de aceptación

Los criterios de aceptación (CA) son el contrato de la HU con las pruebas: cada caso de prueba de alto nivel traza a un CA, y cada CA debe generar al menos un caso. CA débiles producen suites débiles — por eso se auditan antes de diseñar.

## Formatos aceptados

| Formato | Cuándo es adecuado | Riesgo típico |
|---|---|---|
| **Gherkin** (Dado/Cuando/Entonces) | Comportamientos con precondición-acción-resultado; insumo directo para BDD y automatización | Gherkin "decorativo": pasos que no son comportamiento sino instrucciones de UI paso a paso |
| **Checklist** (lista de verificaciones) | Reglas de validación enumerables (campos, formatos, permisos) | Items no atómicos ("el formulario valida todo correctamente") |
| **Prosa estructurada** | Contexto y reglas de negocio complejas | La menos testable; exigir reescritura a Gherkin/checklist en refinamiento |

## Checklist de auditoría por CA

1. **Atómico** — un solo comportamiento por criterio. "Valida el email y muestra el error y bloquea el botón" son tres.
2. **Decidible** — un tester tercero decide pass/fail sin preguntar. Palabras que lo rompen: "correctamente", "adecuado", "rápido", "amigable", "según diseño" (sin link al diseño).
3. **Con datos concretos** — límites, formatos y valores explícitos ("máximo 50 caracteres", "monto entre 1 y 20.000.000 COP"), no "un valor válido". Sin datos concretos no hay BVA posible (ver [[calidad-funcional-test-design]], `references/equivalence-partitioning-bva.md`).
4. **Cubre el no-happy** — ¿qué pasa cuando falla? Un set de CA 100% happy path es hallazgo automático: los caminos negativos (error, rechazo, timeout, permiso denegado) o existen como CA o se registran como vacío.
5. **Observable en una interfaz definida** — el resultado se ve en UI, response, evento o estado persistido nombrado. "El sistema lo procesa internamente" no es observable.
6. **Consistente con la narrativa** — cada CA aporta al Quiero/Para; CA huérfanos (que no sirven a la narrativa) sugieren HU mal partida.
7. **Sin solución técnica encubierta** — "se guarda en la tabla X con flag Y" es diseño, no aceptación; se marca como warn de negociabilidad.

## Señales de completitud (vacíos frecuentes)

Revisar si los CA responden estas familias; cada ausencia relevante es una pregunta al PO:

- **Autorización**: ¿quién puede y quién no? ¿qué ve el que no puede?
- **Validación de entrada**: ¿límites de cada campo? ¿caracteres especiales, vacíos, nulos?
- **Estados**: ¿qué pasa si la entidad ya está en el estado destino? ¿reintentos, duplicados, idempotencia?
- **Errores de dependencias**: ¿servicio caído, timeout, respuesta parcial?
- **Concurrencia/volumen** cuando la narrativa lo implique.
- **Internacionalización/formato regional** si el producto es multi-país (fechas, montos, decimales).

## Salida del análisis

Por cada CA: `CA-n: pass | warn | fail` + hallazgos numerados con cita textual. Más el veredicto de conjunto: cobertura de familias (tabla de arriba) y proporción happy/negativo.
