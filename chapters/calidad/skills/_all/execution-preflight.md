---
id: calidad-execution-preflight
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Sonda obligatoria de ejecución real antes del smoke gate: el SUT está alcanzable, la sesión apunta al destino que se levantó y la aplicación está efectivamente abierta, con salida de comando y captura que lo demuestren. Sin preflight verde no hay ejecución válida ni diagnóstico de fallos."
tags: [preflight, ejecucion, sonda, evidencia, mobile, web, api, mandatory, gate, universal]
enforcement: mandatory
verification:
  - check: "existe .evidence/preflight.json con todas las sondas del stack en estado pass y con la salida real de cada comando"
    failure_message: "Bloqueado: se ejecutó sin verificar que el SUT estuviera alcanzable y activo. Los resultados de una corrida sin preflight no son evidencia de nada."
  - check: "para móvil, el identificador del dispositivo de la sesión coincide con el del dispositivo verificado, y existe captura inicial que demuestra la aplicación en primer plano"
    failure_message: "Bloqueado: la sesión puede estar apuntando a un dispositivo distinto del que se levantó, o la aplicación no está abierta. Ya ocurrió en campo y produjo un falso defecto del SUT."
  - check: "ningún fallo se clasificó ni se reportó como defecto del SUT sin preflight verde en esa misma corrida"
    failure_message: "Bloqueado: no se puede afirmar nada sobre el SUT si no está demostrado que la corrida llegó a tocarlo."
---

# Execution Preflight — Demostrar que la Corrida Toca el SUT

## Principio

Antes de ejecutar, hay que **demostrar con salida de comando** que existe un SUT alcanzable y que la sesión de prueba apunta a él. No basta con que el ambiente "debería" estar listo: la sonda se ejecuta y su salida se guarda.

Verificado en campo, tres veces en una misma entrega: se reportaron resultados de ejecución sin que la aplicación estuviera instalada; la sesión apuntó a un destino distinto del emulador que se había levantado; y se declaró un defecto del SUT sin que la aplicación se hubiera abierto nunca. **Cualquier conclusión sobre el SUT en ese estado es ficción**, y una ficción que se reporta al cliente como hallazgo de calidad.

## Cuándo aplicar

**Inmediatamente antes del `[[calidad-smoke-gate-policy]]`**, y de nuevo tras cualquier cambio de ambiente, de dispositivo o de destino de ejecución dentro de la misma corrida. Es la fase `preflight` de `[[calidad-pipeline-state-tracking]]`.

El comando de cada sonda sale del mapa de `[[calidad-repo-capability-discovery]]` cuando el repositorio ya lo provee; no se inventa.

## Sondas por stack

Cada sonda se ejecuta y **se guarda su salida real**. Una sonda sin salida registrada no está pasada.

| Stack | Sondas obligatorias, en orden |
|---|---|
| **Móvil** | 1. Listar dispositivos conectados o emuladores activos. 2. El identificador objetivo de la sesión es **exactamente uno** de los listados. 3. La aplicación bajo prueba está instalada en **ese** dispositivo. 4. La aplicación arranca y queda en primer plano. 5. Captura de pantalla inicial que lo demuestra. |
| **Web** | 1. La URL objetivo responde. 2. El navegador levanta con el perfil declarado. 3. La primera pantalla carga (no una página en blanco ni un error del proxy). 4. Captura de pantalla inicial. |
| **API** | 1. El endpoint base o de salud responde con el código esperado. 2. La autenticación resuelve, si aplica. 3. Respuesta registrada. |
| **Carga** | Las de API, más: el objetivo es un ambiente autorizado para carga y no un mock (ver `[[calidad-sut-readiness-gate]]`). |

Cuando `execution_target` es `mock` o `hybrid`, las sondas apuntan al mock: debe estar levantado y responder antes de ejecutar. El blocker por mock caído es `mock_unavailable`, no `environment_blocked_*`.

**Instalada no es lo mismo que utilizable.** En móvil, "el dispositivo está
conectado y la app instalada" se lee a menudo como preflight suficiente, y no lo
es: la sonda 4 —abrir la aplicación y confirmar la primera pantalla esperada, con
su captura— es la que separa *saber que algo va mal* de *saber qué*. Cuarenta
segundos de sonda convierten cinco escenarios rojos con cinco mensajes distintos
en un solo mensaje al principio: *"la app no llega al login en este build"*.

## Cambiar el artefacto bajo prueba estrena un camino que la suite no recorre

Una suite que lleva meses ejecutándose contra una aplicación ya instalada **nunca
ha recorrido la primera instalación**. Al subir un build nuevo, ese camino se
estrena entero y con él tres cosas que ningún fallo nombra por su nombre:

| Qué aparece | Cómo se manifiesta | Qué lo arregla |
|---|---|---|
| **Diálogos que solo se piden la primera vez** — notificaciones, cámara, ubicación | El error habla del botón que no encontró, no del diálogo que lo tapaba | Neutralizarlo **por el permiso concreto** |
| **Arranque en frío mucho más lento** — el sistema optimiza la app al vuelo | El escenario se rinde *mientras la pantalla está llegando* | Margen, calibrado sobre el arranque en frío y no sobre la app ya instalada |
| **La app no llega a primer plano** | La orden de activar responde bien y el aparato se queda en el lanzador | Comprobar y **reactivar**; esperar más no lo arregla |

La distinción que un volcado de jerarquía resuelve de un vistazo: *¿la app
tardó?* se arregla con margen. *¿la app está siquiera delante?* solo se arregla
reintentando el arranque. Si lo que se ve es el lanzador, ningún timeout va a
salvarlo.

**Al neutralizar un diálogo de permisos, hacerlo por el permiso concreto.** Una
capability que los concede todos apaga en silencio los escenarios que existen
para verificar esos mismos diálogos, y el resultado es un verde que no prueba
nada.

## Salida obligatoria

`.evidence/preflight.json`:

```json
{
  "schema_version": "1.0",
  "run_id": "2026-08-13T09:12:00Z",
  "stack": "appium",
  "execution_target": "real",
  "target": { "device_id": "<id>", "app_package": "<paquete>", "platform": "android" },
  "probes": [
    { "id": "devices_listed",   "status": "pass", "command": "<comando>", "output": "<salida real>" },
    { "id": "target_matches",   "status": "pass", "detail": "el id de la sesión coincide con el dispositivo listado" },
    { "id": "app_installed",    "status": "pass", "command": "<comando>", "output": "<salida real>" },
    { "id": "app_foreground",   "status": "pass", "evidence": ".evidence/preflight/initial-screen.png" }
  ],
  "result": "green"
}
```

## Reglas

1. **Sin preflight verde no hay smoke gate.** Y sin smoke gate no hay suite, no hay triage y no hay contrato de cierre.
2. **Discrepancia de destino es blocker `device_target_mismatch`.** El caso real: emulador levantado y sesión apuntando a otro destino. Se corrige la configuración, no se ignora.
3. **La aplicación no instalada no es un supuesto: es un paso.** Instalar es una acción explícita, verificada con su propia sonda, no algo que "ya debería estar".
4. **La captura inicial es obligatoria en front y móvil.** Es la prueba de que la corrida vio la aplicación. Sin ella no se puede afirmar después qué mostraba la pantalla.
5. **Toda sonda fallida se reclasifica** según `[ver schema](./environment-blocker-evidence.md)`: el preflight distingue ambiente caído de aplicación ausente de configuración equivocada, y el blocker nombra la causa exacta.
6. **El preflight se repite** si cambia el dispositivo, el ambiente, el destino **o el artefacto bajo prueba** a mitad de corrida. No se arrastra. Un build nuevo invalida el preflight anterior tanto como un dispositivo nuevo.

## Restricciones

- **NUNCA** declarar una sonda pasada sin su salida: "el dispositivo está conectado" sin el listado es una suposición.
- **NUNCA** ejecutar la suite para "ver qué pasa" con el preflight en rojo: multiplica el ruido y produce fallos cuya causa ya se conocía.
- **NUNCA** clasificar un fallo como defecto del SUT sin preflight verde en esa misma corrida (`[[calidad-failure-triage-and-classification]]`, `references/sut-defect-evidence-chain.md`).
- **NUNCA** dar por bueno un preflight de una corrida anterior: el ambiente cambia entre corridas y esa es justamente la clase de fallo que la sonda detecta.

## Verificación

Asset de **cumplimiento obligatorio**. Antes de cerrar la fase que lo invoca, comprobar cada punto. Si alguno no se cumple, se detiene y se reporta con el mensaje indicado.

| # | Comprobación | Si no se cumple |
|---|---|---|
| 1 | existe .evidence/preflight.json con todas las sondas del stack en estado pass y con la salida real de cada comando | Bloqueado: se ejecutó sin verificar que el SUT estuviera alcanzable y activo. Los resultados de una corrida sin preflight no son evidencia de nada. |
| 2 | para móvil, el identificador del dispositivo de la sesión coincide con el del dispositivo verificado, y existe captura inicial que demuestra la aplicación en primer plano | Bloqueado: la sesión puede estar apuntando a un dispositivo distinto del que se levantó, o la aplicación no está abierta. Ya ocurrió en campo y produjo un falso defecto del SUT. |
| 3 | ningún fallo se clasificó ni se reportó como defecto del SUT sin preflight verde en esa misma corrida | Bloqueado: no se puede afirmar nada sobre el SUT si no está demostrado que la corrida llegó a tocarlo. |

## Cross-links

`[[calidad-smoke-gate-policy]]`, `[[calidad-failure-triage-and-classification]]`, `[[calidad-repo-capability-discovery]]`, `[[calidad-sut-readiness-gate]]`, `[[calidad-pipeline-state-tracking]]`, `[[calidad-test-execution-orchestration]]`, `[ver schema](./environment-blocker-evidence.md)`.
