
# Guía de selección de técnica de diseño

Ninguna técnica cubre todo. La selección se hace por el TIPO de comportamiento que la HU describe, se declara antes de diseñar y suele combinar 2-3 técnicas por HU.

## Tabla de decisión de técnicas

| Señal en la HU / CA | Técnica principal | Complementarias |
|---|---|---|
| Campos con rango, longitud, formato, monto, fecha | Particiones de equivalencia + **BVA** (obligatoria) | Error guessing sobre formatos rotos |
| Reglas de negocio combinadas ("si A y B pero no C...") | **Tabla de decisión** | BVA sobre los umbrales de cada condición |
| Entidad con ciclo de vida (estados: creado→aprobado→...) | **Transición de estados** | Tabla de decisión para los guards de cada transición |
| Matriz de configuración (plataforma × país × rol × idioma) | **Pairwise** | Priorización risk-based de combinaciones críticas que deben ir completas |
| Flujo de usuario multi-paso (wizard, onboarding, checkout) | **Casos de uso / escenarios** (principal + alternativos + excepción) | Transición de estados si hay volver-atrás |
| Reglas descubiertas en example map | Ejemplos verdes → casos directos | La técnica formal que corresponda para completar lo que la sesión no vio |
| Zona históricamente defectuosa, integración frágil | **Error guessing** con catálogo | Charter exploratorio time-boxed |
| Requisito difuso que no se pudo refinar aún | **Charter exploratorio** (mientras tanto) | Escalar a análisis/refinamiento — el charter no reemplaza el CA |

## Reglas de aplicación

1. **Declarar la selección**: el entregable de diseño abre con "Técnicas aplicadas: X (por qué), Y (por qué)". Un diseño sin técnicas declaradas es intuición con formato.
2. **BVA es innegociable** cuando hay límites numéricos o de longitud en los CA (regla heredada de la práctica de campo: límite exacto, límite+1, límite-1).
3. **Cobertura mínima por técnica**:
   - Particiones: 1 caso por partición válida e inválida.
   - Tabla de decisión: 1 caso por columna (regla) de la tabla simplificada.
   - Estados: cobertura de todas las transiciones válidas (0-switch) + los intentos de transición inválida relevantes.
   - Pairwise: todas las parejas cubiertas; las combinaciones CRITICAL además completas.
4. **El nivel se decide con la estrategia**: qué se prueba en API vs UI vs unitario lo gobierna `[[calidad-funcional-test-strategy]]` — el diseño marca el nivel sugerido por caso, la estrategia lo confirma.
5. Las técnicas basadas en experiencia (error guessing, exploratorio) **suman sobre** las formales; si el tiempo alcanza para una sola cosa, primero lo formal que cubre los CA.
