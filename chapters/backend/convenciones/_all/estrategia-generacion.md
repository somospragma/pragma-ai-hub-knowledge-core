---
id: backend-convencion-estrategia-generacion
version: "1.0"
scope: chapter
type: convencion
chapter: backend
---

# Convención: Estrategia de Generación de Código

## Objetivo

Definir CÓMO se genera código: el orden de generación (inside-out), la definición del scaffold antes de escribir código, la verificación post-generación, y el registro automático de UseCases.

---

## Protocolo Paso a Paso

### Paso 1: Definir el Scaffold del Proyecto

ANTES de generar una sola línea de código, se DEBE definir la estructura completa del proyecto.

1. **Seleccionar la arquitectura:**
   - Si la especificación indica arquitectura → usarla.
   - Si NO indica arquitectura → preguntar al pragmatic presentando las opciones disponibles en la KB:
     1. Hexagonal multi-módulo (default recomendado)
     2. Onion architecture
     3. Simple pattern (para CRUD/MVP)
   - Si el pragmatic dice "cualquiera" o "el default" → usar **hexagonal multi-módulo**.

2. **Generar la estructura de carpetas y archivos de build:**
   - Estructura de módulos según la arquitectura seleccionada.
   - Archivos de configuración del build tool (Gradle).
   - Dependencias inter-módulo configuradas respetando la regla de dependencia.

3. **Verificar que el proyecto vacío compila** antes de agregar código.

---

### Paso 2: Generar Inside-Out (Dominio hacia Afuera)

El código se genera SIEMPRE desde el centro (dominio) hacia la periferia (infraestructura). Este orden garantiza que la regla de dependencia se cumple por construcción.

#### Orden obligatorio de generación:

```
1. domain/model        → Entidades, Value Objects, Excepciones de dominio, Interfaces de puertos (Gateways)
       │
       ▼
2. domain/usecases     → Casos de uso que orquestan la lógica usando el modelo y los puertos
       │
       ▼
3. driven-adapters     → Implementaciones concretas de los puertos (HTTP clients, repos, colas, cloud)
       │
       ▼
4. entry-points        → Controllers/Handlers, DTOs request/response, Mappers DTO↔Domain
       │
       ▼
5. application         → Registro de UseCases, bootstrap, configuración (beans, properties)
       │
       ▼
6. tests               → Unit tests (usecases, adapters), Integration tests (controllers)
       │
       ▼
7. archivos soporte    → application.yml, README, pipeline, configmap
```

#### Reglas por capa:

| Capa | Regla principal |
|------|----------------|
| `domain/model` | CERO anotaciones de framework. CERO dependencias de framework. Puro Java. |
| `domain/usecases` | Sin anotaciones de framework. Dependencias inyectadas por constructor (puertos). |
| `driven-adapters` | Implementan puertos del dominio. Tienen sus propios modelos internos (entidades de persistencia, DTOs externos). NUNCA exponen modelos internos al dominio. |
| `entry-points` | NUNCA exponen entidades de dominio. Siempre DTOs. DTOs inmutables. Anotaciones OpenAPI obligatorias. GlobalExceptionHandler obligatorio. |
| `application` | Solo wiring. CERO lógica de negocio. |

---

### Paso 3: Registrar UseCases Automáticamente

Cada UseCase se registra en el contenedor de inyección de dependencias de forma AUTOMÁTICA. No se usan métodos `@Bean` manuales.

#### Estrategia estándar Pragma: `UseCasesConfig` con Regex Scan

```java
@Configuration
@ComponentScan(
    basePackages = "{base.package}.usecases",
    includeFilters = {
        @ComponentScan.Filter(type = FilterType.REGEX, pattern = "^.+UseCase$")
    },
    useDefaultFilters = false
)
public class UseCasesConfig {
    // Body SIEMPRE vacío. Sin métodos @Bean.
}
```

**Reglas:**
- El body es SIEMPRE vacío. Sin métodos `@Bean`.
- El regex auto-registra cualquier clase cuyo nombre termine en `UseCase`.
- Los UseCases NO necesitan `@Component`, `@Service`, ni ninguna anotación Spring.
- Spring auto-inyecta las implementaciones de `I*Gateway` (adapters) vía constructor.

#### Excepción por cliente:

| Contexto | Mecanismo | ¿Se necesita UseCasesConfig? |
|----------|-----------|------------------------------|
| Pragma estándar | `UseCasesConfig` con regex scan | Sí (body vacío) |
| Ficohsa (`@FicohsaMainApplication`) | La anotación del cliente ya escanea | No |
| Mercantil (`@SpringBootApplication` estándar) | `UseCasesConfig` con regex scan | Sí (body vacío) |

#### Anti-patrón (SIEMPRE incorrecto):

```java
// ❌ INCORRECTO — registro manual derrota el auto-registro
@Configuration
public class UseCaseConfig {
    @Bean
    public IMyUseCase myUseCase(ISomeGateway gateway) {
        return new MyUseCase(gateway);
    }
}
```

---

### Paso 4: Verificación Post-Generación

Después de completar TODOS los pasos de generación, se DEBE ejecutar la secuencia de verificación en este orden exacto:

#### 4.1 Compilación
```bash
./gradlew compileJava
```
- Verifica que todos los módulos compilan sin errores.
- Si falla → diagnosticar y corregir ANTES de continuar.

#### 4.2 Ejecución de Tests
```bash
./gradlew test
```
- Verifica que todos los tests unitarios e integración pasan.
- Si falla → diagnosticar y corregir ANTES de continuar.

#### 4.3 Reporte de Cobertura
```bash
./gradlew jacocoTestReport
```
- La cobertura DEBE cumplir el umbral mínimo del proyecto (default: 85%).
- Si está por debajo → agregar tests adicionales.

#### 4.4 Escaneo de Vulnerabilidades
```bash
./gradlew dependencyCheckAnalyze
```
- Escanea dependencias por CVEs conocidos.
- Si hay CVEs con fix disponible → resolver.
- Si hay CVEs sin fix → documentar en `VULNERABILITY-REPORT.md`.

#### Regla: Si cualquier paso falla, se corrige y se reinicia desde el paso que falló. El output NO está listo hasta que los 4 pasos pasen.

#### Resumen de verificación (incluir en README o log):
```
- Compilación: PASS/FAIL
- Tests: X passed, Y failed
- Cobertura: X% (umbral: 85%)
- Vulnerabilidades: X CVEs encontrados (Y corregidos, Z documentados)
```

---

## Reglas Inquebrantables

1. **NUNCA generar código sin definir el scaffold primero.**
2. **SIEMPRE generar inside-out:** model → usecases → adapters → entry-points → assembly.
3. **NUNCA poner lógica de negocio en controllers o adapters.**
4. **NUNCA registrar UseCases con métodos `@Bean` manuales.**
5. **SIEMPRE verificar compilación y tests después de generar.**
6. **Si la verificación falla, corregir ANTES de entregar.**

---

## Fuentes

- ADR 008: Inside-Out Code Generation Strategy
- ADR 011: Architecture Scaffold Definition
- ADR 024: Post-Generation Verification Sequence
- ADR 028: Use Case Registration Strategy
