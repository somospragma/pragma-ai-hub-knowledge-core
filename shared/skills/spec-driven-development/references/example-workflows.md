# Example Workflows

Complete end-to-end walkthroughs of the Spec-Driven Development skill in action.
Use these as reference for how each phase should look in conversation.

---

## EN — Notification System

**User**: "I need to build a notification system for the app"

**Phase 1 Response** (you):
> Great! Let's use spec-driven development to structure this properly.
>
> I've created `.specs/notification_system/requirements.md` with a template.
> Here are some initial functional requirements I'm proposing:
> - Users can opt-in/opt-out of notification types
> - Notifications are delivered via [email/push/in-app]
> - Real-time notifications work offline-first
>
> But let me ask: **What notification types matter most?** Email, push, in-app?  
> And **who can send notifications**—only admins, or any user?
>
> Once you clarify, I'll fill in the full requirements for your approval.

**User** (after discussion): "Looks good. Let's move to design."

**Phase 2 Response** (you):
> Perfect. I've created `.specs/notification_system/design.md`.
>
> Based on the requirements, here's my proposed architecture:
> - A queue system for handling async notifications
> - Database schema for notification preferences
> - A notification service that respects user opt-in/opt-out
>
> **Design decisions**:
> 1. Async delivery to prevent blocking user actions
> 2. User preferences stored in `user_notification_settings` table
> 3. Integration with existing scheduler for batching
>
> **Risks**: Potential race conditions if preferences change during delivery. We'll mitigate with locks and tests.
>
> Does this approach work? Any concerns or alternatives?

**User** (after discussion): "Looks good. Let's do tasks."

**Phase 3 Response** (you):
> Excellent. I've created `.specs/notification_system/tasks.md` with the execution plan:
>
> **Phase 1 - Foundation**:
> - Create database schema for notification settings
> - Create NotificationPreference entity
>
> **Phase 2 - Core**:
> - Implement NotificationService
> - Add opt-in/opt-out endpoints
>
> **Phase 3 - Integration**:
> - Hook notifications into existing queue system
> - Add integration tests
>
> **Phase 4 - Polish**:
> - Add monitoring/logging
> - User documentation
>
> Does this breakdown look right? Ready to start with Task 1.1?

---

## ES — Sistema de Referidos

**Input del usuario:** "Quiero preparar las especificaciones para un sistema de referidos en la app."

**Tu flujo de pensamiento:** El usuario quiere especificar una funcionalidad → aplico el flujo SDD. Empiezo únicamente con la Fase 1.

**Fase 1 — Requerimientos:**
> ¡Claro! Empecemos con la Fase 1 de Requerimientos. He creado el documento inicial en `.specs/sistema_referidos/requirements.md`.
>
> Antes de continuar, necesito entender mejor el contexto:
> 1. ¿Los usuarios ganan recompensas por referidos exitosos?
> 2. ¿Pueden ver y rastrear sus referidos en tiempo real?
> 3. ¿Hay límites? (máx. referidos por usuario, tope en recompensas)
> 4. ¿Cómo verificamos que alguien fue referido por un usuario específico?
>
> Por favor revisa el borrador, dime si falta alguna regla de negocio, y cuando lo apruebes, pasaré a redactar el diseño arquitectónico.

**Usuario aprueba → Fase 2 — Diseño:**
> He creado `.specs/sistema_referidos/design.md`.
>
> **Decisión de diseño**: Usaremos una tabla `referrals` con estado (pending/confirmed) en lugar de lógica en memoria — esto permite auditoría y evita fraudes.
>
> **Riesgo**: Auto-referidos. Mitigación: Validar que referrer_id ≠ referred_id + rate limiting.
>
> ¿Este enfoque se alinea con la visión? ¿Alguna preocupación sobre el diseño?

**Usuario aprueba → Fase 3 — Tareas:**
> He creado `.specs/sistema_referidos/tasks.md`:
>
> **Fase 1 - Fundación**: Crear tabla `referrals` y migración.
> **Fase 2 - Core**: Implementar ReferralService con validaciones.
> **Fase 3 - Integración**: Conectar con sistema de recompensas.
> **Fase 4 - Pulido**: Tests de integración + documentación.
>
> ¿Empezamos con la Tarea 1.1?

---

El éxito de este proceso radica en la colaboración paso a paso. Explica siempre qué fase completaste y espera la luz verde del usuario antes de continuar.
