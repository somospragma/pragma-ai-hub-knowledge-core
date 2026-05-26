---
id: frontend-skill-solid-clean
version: "1.0"
scope: chapter
type: skill
chapter: frontend
name: solid-clean
description: Reglas SOLID y Clean Code para generación de código. Activar siempre que se genere o modifique código.
trigger: always_on
type: rule
---

Cuando te pida generar código debes seguir estas reglas:

# Reglas de desarrollo: SOLID + Clean Code

## Principios generales

- Escribir código para humanos, no solo para máquinas.
- Priorizar claridad sobre complejidad.
- Cada pieza de código debe tener una intención clara.

## Principios SOLID

- SRP: Cada clase/función tiene una única responsabilidad.
- OCP: Abierto a extensión, cerrado a modificación. Usar interfaces y composición.
- LSP: Implementaciones sustituyen abstracciones sin romper comportamiento.
- ISP: Interfaces pequeñas y específicas. No forzar métodos innecesarios.
- DIP: Depender de abstracciones, no implementaciones. Inyectar dependencias.

## Clean Code

- Nombres descriptivos y explícitos. getUserById, no getUsr.
- Funciones pequeñas (< 20 líneas), una sola cosa.
- Clases cohesivas, no "Dios" con muchas responsabilidades.
- Evitar comentarios innecesarios — código autoexplicativo.
- Manejar errores de forma explícita, no ignorarlos.
- Bajo acoplamiento, alta cohesión.
- Composición sobre herencia.

## Reglas para IA

- NO generar código si no se entiende el requerimiento.
- SIEMPRE priorizar claridad sobre optimización prematura.
- SI rompe SOLID, proponer alternativa mejor.
- SI el código existente no cumple, sugerir mejoras.
