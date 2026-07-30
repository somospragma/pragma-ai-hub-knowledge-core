
# Combinatoria pairwise (matrices de configuración)

## Cuándo

Cuando el comportamiento debe verificarse sobre una matriz de variantes: plataforma (Android/iOS/Web) × país (CO/MX/AR) × rol (cliente/comercio) × idioma... El producto cartesiano explota (3×3×2×2 = 36 combinaciones); probarlo completo no escala y probarlo "algunas al azar" no cubre.

## La técnica

Pairwise garantiza que **cada PAR de valores** de cualquier par de parámetros aparezca en al menos una combinación. La evidencia empírica: la gran mayoría de defectos de configuración los dispara la interacción de 1 o 2 parámetros, no de 4.

Procedimiento:

1. Listar parámetros y sus valores reales (los que el producto soporta, no los teóricos — verificar contra la HU/firma).
2. Generar el set pairwise (el agente puede construirlo a mano para matrices chicas; para grandes, ortogonal arrays o herramienta tipo PICT — documentar cuál se usó).
3. **Excepciones por riesgo**: las combinaciones que el negocio marca CRITICAL (vía `[[calidad-business-driven-prioritization]]` — ej. Android+Colombia si es el 70% del tráfico) se prueban COMPLETAS contra todos los casos, por fuera de la reducción pairwise. La reducción aplica al resto.
4. Excluir combinaciones imposibles declarándolas (iOS + feature Android-only), no silenciosamente.

Ejemplo (3 plataformas × 3 países × 2 roles = 18 → 9 combinaciones pairwise):

| # | Plataforma | País | Rol |
|---|---|---|---|
| 1 | Android | CO | cliente |
| 2 | Android | MX | comercio |
| 3 | Android | AR | cliente |
| 4 | iOS | CO | comercio |
| 5 | iOS | MX | cliente |
| 6 | iOS | AR | comercio |
| 7 | Web | CO | cliente |
| 8 | Web | MX | comercio |
| 9 | Web | AR | cliente |

(Verificación: cada par plataforma-país, plataforma-rol y país-rol aparece al menos una vez.)

## Empaquetado

La matriz pairwise se monta como **tabla de parámetros del caso data-driven** (`@plataforma`, `@pais`, `@rol` — formato en `test-case-format.md`): un caso lógico, N filas. En Azure Test Plans esto mapea nativo a Parameter Values; en la automatización, a Examples de Gherkin o proyectos de Playwright.

En el entregable declarar: parámetros, valores, tamaño del cartesiano completo, tamaño del set generado, combinaciones CRITICAL completas y combinaciones excluidas con motivo. Esa declaración es lo que diferencia cobertura diseñada de muestreo casual.
