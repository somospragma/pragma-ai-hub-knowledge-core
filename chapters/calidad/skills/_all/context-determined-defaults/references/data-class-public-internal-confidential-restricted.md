# Data Class — PUBLIC / INTERNAL / CONFIDENTIAL / RESTRICTED

Clasificación universal de datos. Aplica cross-sector. Define cuán fuerte debe ser la protección, qué tier de testing aplica, qué controles regulatorios disparar.

## PUBLIC

- **Definición**: información que puede ser publicada en internet sin riesgo. Su divulgación no causa daño.
- **Ejemplos cross-sector**:
  - Catálogo de productos en e-commerce.
  - Página corporativa "Acerca de" de cualquier sector.
  - Documentación pública de una API open-source.
  - Horarios de atención de una clínica, oficina de gobierno, banco, escuela.
  - Tarifario público de un servicio.
- **Cómo identificar**: el dato ya es público (sitio corporativo, redes sociales) o está diseñado para serlo.

## INTERNAL

- **Definición**: información para uso interno del cliente o de su ecosistema (empleados, partners autorizados). Su divulgación causa daño bajo o moderado a la operación pero no a personas.
- **Ejemplos cross-sector**:
  - Tickets de soporte interno (sin PII de cliente).
  - Procesos operativos documentados.
  - Métricas de uso agregadas.
  - Telemetría no-sensible de dispositivos IoT (uptime, versión de firmware).
  - Backlog de un equipo de producto.
- **Cómo identificar**: requiere autenticación para acceder, pero su pérdida no implica notificación regulatoria ni daño a individuos.

## CONFIDENTIAL

- **Definición**: información cuya divulgación causa daño significativo: PII identificable, propiedad intelectual del cliente, datos financieros operativos, secretos comerciales.
- **Ejemplos cross-sector**:
  - Datos personales del usuario (nombre + email + teléfono + dirección).
  - Historial de compras y preferencias.
  - Datos financieros operativos (facturación, contratos B2B).
  - PHI mínimo (agendamiento de citas sin diagnóstico).
  - Logs de auditoría con identificadores de usuario.
  - Código fuente propietario y secretos comerciales.
- **Cómo identificar**: presencia de campos que identifican a una persona o entidad, o que tienen valor económico/competitivo. En OpenAPI: campos como `email`, `phone`, `dni`, `taxId`, `address`, `birthDate`, `accountNumber`.

## RESTRICTED

- **Definición**: información cuya divulgación causa daño grave a personas, a la operación crítica o a la seguridad. Sujeta a marcos regulatorios estrictos o a impactos life-safety.
- **Ejemplos cross-sector**:
  - PHI completo (diagnósticos, prescripciones, imágenes médicas).
  - Datos PCI completos (PAN, CVV, datos de tarjeta no tokenizados).
  - Datos biométricos (huellas, iris, facial).
  - Credenciales (passwords, tokens privados, llaves criptográficas, certificados).
  - Datos de menores de edad bajo cualquier contexto.
  - Telemetría de seguridad (sensores life-safety industrial, dispositivos médicos clase II/III).
  - Datos de inteligencia o defensa.
  - Identidad ciudadana en sistemas nacionales.
- **Cómo identificar**: aplica regulación específica (HIPAA, PCI-DSS, GDPR especial-categoría, biométricos, menores) o la divulgación causa daño físico/legal/reputacional grave e irreversible. En OpenAPI: campos como `pan`, `cvv`, `diagnosis`, `prescription`, `biometric`, `nationalId` en sistemas oficiales, `password`, `privateKey`.

## Identificación a partir de la firma del SUT

- **OpenAPI / proto / AsyncAPI / schema SQL**: revisar nombres de campos y `description` para detectar PII/PHI/PCI.
- **Modelo de datos**: tablas con `users`, `patients`, `accounts`, `payments`, `audit_log`, `auth_*` típicamente contienen al menos CONFIDENTIAL.
- **Firma del dominio**: un servicio que se llama `payment-gateway`, `clinical-records`, `identity-provider`, `fraud-detection`, `kyc` ya implica RESTRICTED por defecto.
- **Pregunta al PO**: cuando hay ambigüedad, preguntar — `mandatory-inputs-protocol` lo respalda.

## Heurística rápida

- ¿Puedo publicarlo en X/Twitter sin permiso? → PUBLIC.
- ¿Requiere login interno pero no notifico al regulador si se filtra? → INTERNAL.
- ¿Identifica a una persona o tiene valor competitivo? → CONFIDENTIAL.
- ¿Aplica regulación estricta o el daño es grave/irreversible? → RESTRICTED.
