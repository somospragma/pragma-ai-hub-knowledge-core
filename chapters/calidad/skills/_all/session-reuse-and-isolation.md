---
id: calidad-session-reuse-and-isolation
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Cuándo compartir sesión entre escenarios y cuándo empezar de cero, en suites con login costoso: pool por clave de usuario, reset verificado con autorreparación, contrato de tags y orden de preferencia para las precondiciones de datos. Consultar al diseñar el arranque de escenarios."
tags: [sesion, aislamiento, login, precondiciones, paralelismo, rendimiento]
---

# Session Reuse and Isolation — Compartir sin Arrastrar Estado

## Cuándo aplicar

Al diseñar el arranque de los escenarios de cualquier suite donde el login sea
caro —decenas de segundos—, y cuando una suite existente dedique más tiempo a
autenticarse que a verificar.

Señal de que hace falta: medir un escenario y encontrar que la precondición
cuesta varias veces más que lo que certifica. Un caso medido: 33,9 s de login en
un escenario de 52,2 s, el 65 %, y casi todo latencia de backend.

## Instrucción

Pagar el login por escenario domina el tiempo de la suite. Pero compartir **una
sola** sesión introduce fallos dependientes del orden, que son los más caros de
diagnosticar porque **el escenario que falla no es el que causó el problema**.

La respuesta no es elegir entre los dos extremos: es **reutilizar por clave**.

### 1. Pool por clave, no sesión única

La clave natural es el usuario. Los escenarios que piden lo mismo comparten
sesión; los que piden otro usuario abren la suya. Las sesiones se abren **bajo
demanda**: un worker que solo corra escenarios de un usuario nunca paga el login
de los demás.

### 2. Contrato de tags

| Tag | Qué recibe | Para qué |
|---|---|---|
| *(sin tag)* | Sesión compartida del usuario por defecto | El caso normal |
| `@usuario:<ALIAS>` | Sesión compartida **de ese usuario** | Otro perfil de datos |
| `@fresh-login` | Sesión propia, autenticada, **desechable** | El escenario ensucia estado global |
| `@fresh-session` | Contexto nuevo **sin autenticar** | Escenarios que prueban el propio login |

El alias se declara en datos de prueba versionados que dicen **de qué variables
de entorno** salen las credenciales, nunca los valores
(`[[calidad-test-data-management]]`).

### 3. El reset se verifica, no se supone

Compartir sesión exige devolver la aplicación a un punto de partida conocido.
**Verificarlo y, si no se consigue, descartar la sesión y abrir otra:**

```
adquirir(clave) → reset()
      ├─ lo consiguió    → el escenario reutiliza
      └─ no lo consiguió → invalidar(clave) → adquirir(clave) → login nuevo
```

El escenario no tiene que saber cuál de las dos ocurrió. Y el criterio es
explícito: **pagar un login cuesta segundos; arrastrar estado sucio cuesta una
investigación.**

Esta autorreparación es lo que hace que el reuso sea seguro por defecto, y lo que
permite reservar la sesión desechable a lo que el reset no puede deshacer.

### 4. Volver al inicio resuelve la navegación, no el estado

Si el escenario dejó algo cambiado **en el sistema** y no en la pantalla, el
siguiente lo encontrará así — y **ni siquiera una sesión nueva lo deshace**. Para
eso hace falta un usuario dedicado o preparación explícita del dato.

Antes de asumir que una recarga resetea: **comprueba que la aplicación restaura
la sesión al recargar.** Hay aplicaciones que no lo hacen, y entonces la corrida
entera cae al login.

### 5. Precondiciones de datos, en orden de preferencia

1. **Usuario de prueba dedicado** con los datos ya montados. Lo más estable y lo
   más rápido: no hay preparación que pueda fallar.
2. **Preparar por API o base de datos** dentro del escenario, con sesión
   desechable.
3. **Preparar por la interfaz.** Último recurso: lento, frágil, y convierte un
   fallo de preparación en un fallo del caso que se quería probar.

## Restricciones

- **NUNCA hagas que un escenario dependa de que otro haya dejado el dato listo.**
  Es un orden implícito que nadie declara y que se rompe en cuanto cambie el
  paralelismo.
- **NUNCA marques sesión sin autenticar junto a un alias de usuario**: el primero
  entrega un contexto sin autenticar, así que el usuario no se usa. Es un error
  que debe cazar el gate de CI, no una corrida.
- **NUNCA recargues para resetear** sin haber comprobado que la aplicación
  restaura la sesión.
- **NUNCA compartas sesión entre escenarios que corren en paralelo sobre el mismo
  usuario.** El pool comparte dentro de un worker; entre workers, la cuenta sigue
  siendo un recurso con estado — ver `[[calidad-test-data-management]]`.
- **NUNCA introduzcas una limpieza como step de Gherkin**: un step de limpieza
  solo corre si el escenario llegó hasta él, es decir, **solo cuando no hacía
  falta**. La limpieza va en un hook que corre pase lo que pase.

## Cross-links

- `[[calidad-test-data-management]]` — la cuenta de pruebas como recurso con estado.
- `[[calidad-automation-feasibility-assessment]]` — cuándo una precondición cara
  deja de justificarse.
- `[[calidad-test-execution-orchestration]]` — paralelismo y perfiles.
