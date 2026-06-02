# Executor as Skill vs as Pipeline

Decisión arquitectónica clave: ¿cuándo el AI ejecuta los tests directamente (este skill) y cuándo los ejecuta la CI (`[[calidad-cicd-integration]]`)? Ambos coexisten, pero cubren momentos distintos del ciclo de vida.

## AI ejecuta (modo `full` o `dry-run`)

Aplica durante:

- **Construcción inicial de la suite** — validación inmediata de que lo recién generado corre.
- **Validación rápida** — smoke run después de cambios puntuales en un test o en config.
- **Iteración con auto-corrección** — loop corto con `[[calidad-test-self-correction-loop]]` para resolver fallos triviales (selector cambiado, timeout corto, fixture desactualizado) sin esperar al pipeline.
- **Demo / handover** — demostrar al cliente que la suite produce resultados antes del cutover a CI.

Características:

- Ejecuta **1 smoke run + 1-2 iteraciones** de auto-corrección como máximo.
- **No paraleliza** más allá de lo que el runner local soporte.
- **No usa device cloud** (BrowserStack, SauceLabs, AWS Device Farm) — coste prohibitivo en iteración rápida.
- **No corre regresión completa** — solo un subset (típicamente `@smoke`).

## CI ejecuta (después de entrega)

Aplica para:

- **Regresión completa** post-merge a `develop`/`main`.
- **Nightly builds** con la suite full + suites de carga (K6).
- **Release gates** que bloquean despliegue a producción si los gates de calidad fallan.
- **Mobile cloud devices** con matriz de devices reales (Appium en BrowserStack/SauceLabs).
- **Cross-browser matrix** (Playwright en Chromium + Firefox + WebKit + Edge).
- **Sharding paralelizado** a gran escala (4-16 shards típicamente).

Características:

- Acceso a runners dedicados / pools self-hosted.
- Integración con secret stores corporativos.
- Publicación de resultados como artifacts y dashboards (Allure / ReportPortal).
- Política de retención larga (90 días → 7 años según cliente).

## Boundary recomendado

El AI **ejecuta una smoke run + 1-2 iteraciones de auto-corrección máximo** durante la fase de construcción. Una vez que la suite está estable y el AI puede demostrar `status: passed` en la smoke run, **la suite completa se entrega a CI** para ejecución regular.

Si el AI necesitara más de 3 iteraciones para hacer pasar la smoke run, el problema **no es del test** — es de spec, de entorno o del SUT. Escalar a humano vía `[[calidad-failure-triage-and-classification]]`.

## Tabla de decisión por contexto

| Contexto | Ejecuta AI | Ejecuta CI | Notas |
|---|---|---|---|
| Generación inicial de suite Karate | Sí (smoke) | Sí (regression) | AI corre `@smoke` para validar; CI corre tags completos en nightly. |
| Generación inicial de suite Playwright | Sí (smoke, chromium) | Sí (matriz de browsers) | AI no corre Firefox/WebKit/Edge salvo solicitud explícita. |
| Generación inicial de suite K6 (carga) | No (solo smoke functional) | Sí (full load) | Pruebas de carga consumen recursos shared — siempre coordinadas vía CI. |
| Generación inicial de suite Appium | Sí (1 emulador local) | Sí (cloud device farm) | AI no toca BrowserStack/SauceLabs durante iteración. |
| Fix puntual en test ya productivo | Sí (test específico) | Sí (re-run del shard afectado) | AI valida el fix; CI valida no-regresión. |
| Validación pre-deploy (modo `execute-only`) | Sí | No | AI ejecuta y reporta, no modifica nada. |
| Cliente regulado en `dry-run` | Sí (con diff sugerido) | Sí (ejecución oficial) | Cualquier cambio requiere aprobación humana entre AI y CI. |
| Sin shell / sin env (modo `scaffold-only`) | No | Sí | AI entrega comandos; ejecución completa en CI. |
| Cliente con SUT on-prem sin acceso desde el agente | No | Sí (runner self-hosted) | Coordinar runner con red privada. |
| Smoke check post-deploy | Sí (si tiene acceso) | Sí (como gate de release) | Ambos válidos según urgencia. |
| Carga performance contra producción | No | Sí (con ventana coordinada) | Nunca el AI dispara carga a producción. |

## Anti-patrones

- **AI ejecutando la regresión completa cada vez que genera un test** — desperdicio de tiempo, no escala.
- **CI ejecutando smoke runs en cada cambio del AI** — latencia que hace inviable la iteración rápida.
- **AI corriendo suites de carga (K6)** — riesgo de afectar el SUT del cliente sin coordinación.
- **AI tocando device cloud (BrowserStack/SauceLabs)** durante construcción — quema presupuesto del cliente.
- **CI sin gates de calidad** — el pipeline pasa pero no garantiza nada.
- **AI en modo `full` contra producción** — siempre `dry-run` o `execute-only` con ventana coordinada.

## Handover AI → CI

Una vez que el AI valida la suite en smoke run:

1. Commit de los tests + config + dependencies.
2. Generar pipeline con `[[calidad-cicd-integration]]`.
3. Trigger inicial manual del pipeline para confirmar que corre en CI.
4. Cierre del engagement con dashboard (Allure/ReportPortal) accesible al cliente.
5. Documentar el modo de operación recomendado para el equipo del cliente (cuándo correr smoke, cuándo nightly, cómo interpretar gates).
