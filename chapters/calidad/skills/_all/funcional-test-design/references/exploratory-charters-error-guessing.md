
# Error guessing y testing exploratorio (técnicas basadas en experiencia)

Complementan a las técnicas formales: atacan lo que las particiones y tablas no ven porque no está escrito en ningún CA. **Nunca las sustituyen** — si solo hay tiempo para una cosa, primero lo formal que cubre los CA.

## Error guessing con catálogo

No es "ocurrencias": es aplicar un catálogo de fallas históricas al contexto de la HU. Catálogo base del chapter (extender con la memoria de defectos del proyecto):

| Familia | Ataques típicos |
|---|---|
| Entrada de texto | Vacío, solo espacios, emojis, caracteres de control, HTML/script (`<script>`), SQL (`'; --`), longitud extrema, RTL, acentos y ñ en campos "ASCII" |
| Números y montos | 0, negativos, decimales de más, notación científica, separador de miles/decimal regional (1.000,50 vs 1,000.50), overflow |
| Fechas | 29/feb, fin de mes, zona horaria (UTC vs local, medianoche), fechas futuras/pasadas prohibidas, formato regional |
| Duplicación e idempotencia | Doble click en enviar, reintento tras timeout, misma petición dos veces (¿dos cobros?) |
| Sesión y permisos | Sesión expirada a mitad de flujo, mismo usuario en dos pestañas/dispositivos, rol degradado con página abierta |
| Interrupciones | Red caída a mitad de transacción, cierre de app en paso 3 de 4, volver-atrás del navegador en flujos de pago |
| Dependencias | Servicio downstream caído/lento/respuesta parcial, catálogo desactualizado |

Cada "adivinanza" que se convierte en caso se documenta con su familia — así el catálogo del proyecto crece y es auditable.

## Charters exploratorios (session-based)

Para zonas de riesgo sin CA suficiente o de comportamiento emergente. Formato del charter:

```markdown
## Charter EX-{n}
**Explorar** el flujo de recuperación de contraseña
**Con** múltiples dispositivos y sesiones simultáneas del mismo usuario
**Para descubrir** condiciones de carrera, tokens reutilizables y estados inconsistentes
**Time-box**: 60 min | **Prioridad**: HIGH (heredada del risk map)
**Notas de sesión**: hallazgos, defectos, preguntas nuevas (se registran DURANTE la sesión)
```

Reglas:

1. Charter time-boxed con objetivo falsable ("descubrir X"), no "probar un rato".
2. La salida de la sesión alimenta el ciclo: defectos → ALM (`[[calidad-alm-mcp-integration]]`); comportamientos descubiertos sin CA → hallazgos para `[[calidad-funcional-story-analysis]]`; casos repetibles valiosos → formalizar en el set diseñado.
3. Los charters se planifican en el plan de pruebas (`[[calidad-funcional-test-plan]]`) como actividad con esfuerzo propio, no como relleno.
4. Un charter NO es la excusa para saltarse el refinamiento: si toda la HU necesita exploración, la HU no estaba `ready`.
