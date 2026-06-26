# Severidad, clasificación de hallazgos y flujos críticos

## Clasificación de resultados

Todo criterio evaluado se clasifica obligatoriamente en una categoría:

- **Hallazgo comprobado** — incumplimiento con evidencia suficiente.
- **Criterio parcialmente verificable** — solo se valida en parte desde la evidencia disponible.
- **Riesgo potencial** — posible barrera sin evidencia concluyente.
- **Criterio no verificable por falta de evidencia**.

Regla de evidencia: ningún criterio se marca como cumplido sin evidencia suficiente. Los
criterios parcialmente verificables generan un **requerimiento de implementación accesible**.

## Severidad

- **Crítica** — impide por completo el uso o una operación a usuarios con discapacidad.
- **Alta** — impide el uso de una funcionalidad clave (ej. botón sin etiqueta, navegación rota).
- **Media** — afecta parcialmente la experiencia, con alternativas (ej. contraste bajo, mal
  orden de lectura).
- **Baja** — detalle menor que no impide el acceso (ej. foco poco visible, ARIA innecesario).

## Flujos bancarios críticos

Priorizar el riesgo en: login, registro, onboarding, MFA/OTP, recuperación de contraseña,
pagos, transferencias, créditos, extractos, PQRS, consentimientos, firma digital,
confirmaciones transaccionales, alertas antifraude, soporte y ayuda.

**Regla de escalamiento de severidad**: en un flujo bancario crítico, la severidad de un
hallazgo se incrementa si la barrera puede impedir, bloquear o comprometer el acceso, la
autenticación, la comprensión, la autorización o la ejecución segura de una operación
financiera.

## Riesgo de exclusión financiera

Además de la severidad, clasificar el **riesgo de exclusión financiera** (Alto / Medio / Bajo):
mide si la barrera puede dejar a una persona fuera del acceso o uso de un producto/servicio
financiero. Es la dimensión que diferencia un hallazgo de accesibilidad genérico de uno con
impacto regulatorio y de negocio en banca.

## Issues comunes a detectar

- Falta de texto alternativo en imágenes.
- Contrastes insuficientes entre texto y fondo.
- Formularios sin etiquetas o instrucciones claras.
- Botones e íconos sin nombre accesible.
- Orden incorrecto de foco y navegación con teclado.
- Uso excesivo o incorrecto de roles/atributos ARIA.
- Errores en estructuras semánticas (encabezados, listas, tablas).
- Contenido dinámico sin avisos a tecnologías de asistencia.

## Tags y ejecución (pruebas automatizadas)

- Etiquetar escenarios con `@accessibility @a11y` (más `@mobile` en suites móviles) además
  de los tags del chapter.
- Recomendado: ejecutar por PR sobre pantallas priorizadas, no en cada test.
