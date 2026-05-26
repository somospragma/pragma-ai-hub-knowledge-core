---
id: frontend-skill-security
version: "1.0"
scope: chapter
type: skill
chapter: frontend
name: security
description: Reglas de seguridad frontend. XSS, tokens, headers, dependencias. Activar siempre que se genere código frontend.
trigger: always_on
type: rule
---

Cuando generes o modifiques código frontend, aplica estas reglas de seguridad:

# Reglas de Seguridad Frontend

## Prohibiciones absolutas

- NUNCA usar eval(), new Function(), document.write(), setTimeout con strings.
- NUNCA usar dangerouslySetInnerHTML (React) o bypassSecurityTrust* (Angular) sin DOMPurify.
- NUNCA usar innerHTML con contenido dinámico sin sanitizar.
- NUNCA almacenar tokens en localStorage o sessionStorage.
- NUNCA incluir API keys secretas en código frontend.
- NUNCA usar prefijos que exponen al browser (NEXT_PUBLIC_, VITE_, REACT_APP_) para secretos.

## Obligaciones

- SIEMPRE validar inputs con Zod o equivalente antes de enviar al servidor.
- SIEMPRE validar URLs antes de usarlas en href — bloquear javascript: protocol.
- SIEMPRE usar rel="noopener noreferrer" en links con target="_blank".
- SIEMPRE usar HTTPS para todas las comunicaciones.
- SIEMPRE sanitizar mensajes de error — nunca exponer detalles internos.

## Tokens y autenticación

- Preferir HttpOnly cookies para auth tokens.
- Logout: limpiar memoria + invalidar sesión + redirigir con navegación completa.

## Dependencias

- Versiones exactas o lock files.
- Scripts externos con Subresource Integrity (SRI).
- Eliminar console.log en producción.
