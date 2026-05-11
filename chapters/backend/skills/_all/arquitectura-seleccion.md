---
id: backend-skill-arquitectura-seleccion
version: "1.0"
scope: chapter
type: skill
chapter: backend
---

# Selección de Arquitectura — Criterios de Decisión

## Objetivo

Este skill define los criterios para elegir la arquitectura correcta en cada proyecto. La decisión depende de la complejidad del dominio, las integraciones, el equipo y el cliente.

## Opciones Arquitectónicas

### 1. Hexagonal Multi-Módulo (Estándar Pragma)

**Descripción:** Separación estricta en 3 capas (dominio, aplicación, infraestructura) con puertos y adaptadores.

**Usar cuando:**
- El servicio tiene lógica de negocio significativa
- Hay múltiples integraciones externas (DB, APIs, colas)
- El dominio evoluciona frecuentemente
- Se necesita testear la lógica de negocio aislada
- No se especifica otra arquitectura explícitamente

**No usar cuando:**
- Es un CRUD puro sin reglas de negocio
- Es una lambda de transformación simple
- Es un proxy/passthrough sin lógica

### 2. Arquitectura Simple (Flat)

**Descripción:** Estructura plana controller → service → repository sin separación en módulos.

**Usar cuando:**
- CRUD puro sin lógica de negocio
- Lambdas de transformación de datos
- Proxies o gateways sin lógica
- Servicios de infraestructura (health checks, config servers)
- PoC o prototipos rápidos

**No usar cuando:**
- Hay reglas de negocio que validar
- Hay más de 2 integraciones externas
- El servicio va a crecer en complejidad

### 3. DDD (Domain-Driven Design)

**Descripción:** Patrones tácticos DDD (Aggregates, Entities, Value Objects, Domain Events) dentro de la capa de dominio hexagonal.

**Usar cuando:**
- Dominio con reglas de negocio complejas e invariantes
- Múltiples aggregates que interactúan
- Necesidad de consistencia transaccional dentro de boundaries
- Equipo con acceso a expertos de dominio
- Comunicación entre bounded contexts vía eventos

**No usar cuando:**
- El dominio es simple (pocas entidades, pocas reglas)
- No hay experto de dominio disponible
- El servicio es principalmente de integración
- Es un MVP donde la velocidad es prioridad

### 4. BIAN (Banking Industry Architecture Network)

**Descripción:** Framework de arquitectura bancaria que define Service Domains, Control Records y Functional Patterns estándar de la industria.

**Usar cuando:**
- Proyecto bancario con requisito explícito de alineación BIAN
- Cliente bancario (especialmente Ficohsa)
- El Service Domain está claramente identificado en el catálogo BIAN
- Integración con core bancario que usa nomenclatura BIAN

**No usar cuando:**
- Proyecto fintech sin requisito BIAN
- Servicio interno no bancario
- Microservicio de soporte (notificaciones, archivos, logs)
- El cliente no requiere alineación con estándares bancarios

## Tabla de Decisión

```
┌─────────────────────┬────────────┬──────────┬─────────┬──────────┐
│ Criterio            │ Hexagonal  │  Simple  │   DDD   │   BIAN   │
├─────────────────────┼────────────┼──────────┼─────────┼──────────┤
│ Lógica de negocio   │  Media+    │  Ninguna │  Alta   │  Media+  │
│ Integraciones       │  2+        │  0-1     │  2+     │  2+      │
│ Reglas de dominio   │  Algunas   │  Ninguna │  Muchas │  Algunas │
│ Aggregates          │  1-2       │  0       │  3+     │  1-2     │
│ Equipo (personas)   │  2+        │  1-2     │  3+     │  2+      │
│ Experto de dominio  │  Opcional  │  No req. │  Req.   │  Req.    │
│ Cliente bancario    │  No        │  No      │  No     │  Sí      │
│ Tiempo de setup     │  Medio     │  Bajo    │  Alto   │  Alto    │
│ Testabilidad        │  Alta      │  Baja    │  Muy alta│ Alta    │
│ Escalabilidad arq.  │  Alta      │  Baja    │  Muy alta│ Alta    │
└─────────────────────┴────────────┴──────────┴─────────┴──────────┘
```

## Árbol de Decisión

```
¿El proyecto es bancario con requisito BIAN?
├── SÍ → BIAN + Hexagonal
└── NO
    └── ¿Tiene lógica de negocio?
        ├── NO → Arquitectura Simple
        └── SÍ
            └── ¿El dominio es complejo (3+ aggregates, invariantes ricas)?
                ├── SÍ → DDD + Hexagonal
                └── NO → Hexagonal Multi-Módulo (estándar)
```

## Señales para Cambiar de Arquitectura

### De Simple → Hexagonal

- El service empieza a tener más de 3 métodos con lógica condicional
- Se agregan integraciones externas (más de 1)
- Los tests requieren mockear múltiples dependencias
- El código del controller mezcla lógica de negocio con transformación de datos

### De Hexagonal → DDD

- Aparecen múltiples entidades con relaciones de consistencia
- Las reglas de negocio cruzan entre entidades
- Se necesitan transacciones que abarcan múltiples objetos
- El lenguaje del dominio se vuelve rico y específico

### De Hexagonal → BIAN

- El cliente solicita alineación con estándares bancarios
- El servicio mapea directamente a un Service Domain BIAN
- Se integra con sistemas que usan nomenclatura BIAN/ISO 20022

## Combinaciones Válidas

| Combinación | Descripción |
|-------------|-------------|
| Hexagonal puro | Estándar para la mayoría de servicios |
| Hexagonal + DDD | Para dominios complejos |
| Hexagonal + BIAN | Para servicios bancarios |
| Hexagonal + DDD + BIAN | Para servicios bancarios con dominio complejo |
| Simple | Solo para CRUD/proxies/lambdas |

**Combinaciones INVÁLIDAS:**
- Simple + DDD (contradictorio)
- Simple + BIAN (BIAN requiere estructura)
- DDD sin Hexagonal (DDD necesita la separación de capas)

## Regla por Defecto

> Si NO se especifica una arquitectura explícitamente → DEBE usarse **Hexagonal Multi-Módulo**.
> Es el estándar de Pragma y cubre el 80% de los casos.

## Checklist de Decisión Rápida

Antes de iniciar un proyecto, responde estas preguntas:

1. **¿Es un proyecto bancario con requisito BIAN?** → Si sí: BIAN
2. **¿Tiene lógica de negocio?** → Si no: Simple
3. **¿El dominio tiene 3+ aggregates con invariantes complejas?** → Si sí: DDD
4. **¿Ninguna de las anteriores?** → Hexagonal estándar

## Impacto en el Proyecto

| Arquitectura | Archivos iniciales | Tiempo setup | Curva aprendizaje |
|-------------|-------------------|--------------|-------------------|
| Simple | ~5-10 | 30 min | Baja |
| Hexagonal | ~15-25 | 1-2 horas | Media |
| Hexagonal + DDD | ~25-40 | 2-4 horas | Alta |
| Hexagonal + BIAN | ~20-35 | 2-3 horas | Alta (requiere conocer BIAN) |
