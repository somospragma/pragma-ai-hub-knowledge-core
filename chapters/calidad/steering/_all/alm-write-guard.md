---
id: calidad-alm-write-guard
version: 1.0.0
scope: chapter
type: steering
chapter: calidad
description: "Prohibición permanente: leer del ALM del cliente es libre, escribir exige autorización humana explícita, previa y específica, con conteo. Aplica en cualquier momento de cualquier sesión, dentro o fuera de un flujo de generación."
tags: [alm, jira, xray, azure-devops, escritura, autorizacion, mandatory, seguridad, enforcement]
---

# ALM Write Guard — Nada se Escribe en el Sistema del Cliente sin Permiso

## Rol

**Leer del ALM del cliente es libre. Escribir exige autorización humana explícita, previa y específica.** Sin distinción entre crear y modificar: crear casos o defectos, editar campos, transicionar estados, comentar, vincular, mover carpetas del repositorio de pruebas, cambiar el tipo de un test, subir Gherkin, subir resultados y adjuntar evidencias son **todas** escritura.

Aplica en cualquier momento de cualquier sesión, también fuera de un flujo de generación: "súbelo a Jira" es una frase suelta que llega sin contexto previo.

La autorización se pide con la **ficha de operación** de `[[calidad-alm-write-authorization-gate]]`: operación exacta, sistema destino, proyecto o ambiente, **conteo de elementos**, muestra si es un lote, efectos colaterales y qué es reversible. Es por lote y por operación, no se hereda entre sesiones, y toda escritura ejecutada se registra en la bitácora con quién autorizó.

El daño de una escritura no autorizada ocurre **fuera de nuestro perímetro**: notifica a terceros, altera métricas de sprint y no se deshace con un deshacer.

## Lo que nunca debes hacer

- **NUNCA** escribir en el ALM para "probar si funciona" o "ver si tengo permisos". Verificar una capacidad **es** escribir: pasa por la ficha y se hace sobre un elemento desechable.
- **NUNCA** tomar una instrucción general ("automatiza el ciclo", "encárgate de la trazabilidad") como autorización de escritura.
- **NUNCA** pedir autorización sin conteo: "voy a crear varios casos" es un aviso, no una autorización pedida.
- **NUNCA** continuar un lote que falló a la mitad sin volver a pedir autorización, ni dejar sin reportar qué alcanzó a escribirse.
- **NUNCA** borrar elementos del ALM del cliente, ni editar un caso que ya tiene ejecuciones registradas.
- Si el usuario rechaza, el flujo **no se bloquea**: se entrega el artefacto equivalente y se registra la decisión.
