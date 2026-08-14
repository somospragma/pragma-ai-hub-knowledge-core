---
id: calidad-execution-discipline-protocol
version: 1.0.0
scope: chapter
type: steering
chapter: calidad
description: "Compuerta obligatoria antes de CUALQUIER ejecución de pruebas, incluso cuando la sesión abre pidiendo ejecutar y no hay nada que generar: comando salido del repositorio y preflight verde con salida de comando."
tags: [protocol, mandatory, ejecucion, preflight, runbook, enforcement]
---

# Execution Discipline Protocol — No se Ejecuta a Ciegas

## Rol

Este protocolo cubre el hueco de las sesiones que **abren pidiendo ejecutar**, donde no hay nada que generar y por tanto el protocolo pre-generación no aplica. Antes de lanzar cualquier ejecución —gate de humo, suite, re-corrida de un test, exploración— se cumplen dos condiciones, en este orden:

1. **El comando sale del repositorio, no de tu cabeza.** En brownfield, del mapa de recursos de `[[calidad-repo-capability-discovery]]` (scripts declarados, texto de ayuda de los ejecutores, definición de CI). Si el mapa no existe, se construye antes de ejecutar. La taxonomía de etiquetas del proyecto manda sobre cualquier default del chapter.
2. **Preflight verde, con salida de comando registrada** (`[[calidad-execution-preflight]]`): SUT alcanzable, la sesión apunta al destino que se levantó, y en móvil o front la aplicación está instalada, abierta y con captura inicial que lo demuestra.

Si la entrega cubre varias plataformas, usar el ejecutor multiplataforma del repositorio cuando exista, y aplicar los aprendizajes compartidos antes de arrancar la siguiente (`[[calidad-cross-platform-learning-propagation]]`).

## Lo que nunca debes hacer

- **NUNCA** inventar un comando de ejecución. Si no sale del repositorio ni lo confirmó el usuario, no se ejecuta.
- **NUNCA** construir a mano lo que el repositorio ya resuelve con un script propio.
- **NUNCA** dar por pasada una sonda del preflight sin su salida: "el dispositivo está conectado" sin el listado es una suposición.
- **NUNCA** interpretar resultados de una corrida con el preflight en rojo, y **NUNCA** clasificar un fallo como defecto del SUT sin preflight verde en esa misma corrida: si no está demostrado que la corrida tocó la aplicación, no hay nada que afirmar sobre ella.
- **NUNCA** lanzar la suite completa para "ver qué más falla" mientras el gate de un escenario siga rojo.
