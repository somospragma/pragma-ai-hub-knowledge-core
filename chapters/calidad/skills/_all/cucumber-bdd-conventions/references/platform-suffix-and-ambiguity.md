# Sufijo de plataforma y resolución de ambigüedades

## El problema

Cucumber resuelve cada línea Gherkin contra un **registro global de definiciones**: todas las que el perfil activo carga, sin importar de qué carpeta o épica vengan. Dos definiciones cuyo patrón matchea el mismo texto producen:

```
Multiple step definitions match:
  el usuario inicia sesión - steps/nt-100_login/android/login.steps.ts:12
  el usuario inicia sesión - steps/nt-240_transfers/android/transfers.steps.ts:8
```

El escenario falla como `ambiguous`, no como `failed`, y el error no apunta al archivo que se acaba de tocar sino a los dos que colisionan. En una suite de varios cientos de escenarios, diagnosticar esto cuesta más que escribirlo bien.

En un arquetipo multi-plataforma la superficie de colisión se multiplica: la misma acción de negocio ("el usuario inicia sesión") necesita una implementación por plataforma, y todas se cargan juntas en los perfiles que combinan plataformas.

## La regla

**Todo step termina con un sufijo que identifica la plataforma destino.** El sufijo es parte del texto del step, no un tag ni un comentario.

Un juego de sufijos coherente para un arquetipo de cinco plataformas:

```
en Web
en Android
en iOS
en iPad
en Tablet Android
```

Con el sufijo, cada definición es única por texto completo y el registro global las distingue sin ambigüedad, aunque el perfil cargue las cinco a la vez.

```gherkin
Given el usuario desea ingresar a la banca digital en Android
When accede a la plataforma Mobile en Android
Then el sistema debe mostrar la pantalla de inicio de sesión en Android
```

El sufijo también hace legible el `.feature`: al leer el escenario se sabe contra qué plataforma corre sin buscar el tag.

## Steps parametrizados por plataforma

Cuando varias plataformas comparten **exactamente** el mismo comportamiento, no se escriben N definiciones: se parametriza el sufijo.

```typescript
Then(
  'el sistema debe mostrar el mensaje {string} en {plataforma}',
  async function (mensaje: string, plataforma: string) { /* ... */ }
);
```

El parámetro `{plataforma}` se registra como parameter type con el juego cerrado de valores válidos, de modo que un sufijo mal escrito quede `undefined` en vez de matchear por accidente:

```typescript
defineParameterType({
  name: 'plataforma',
  regexp: /Web|Android|iOS|iPad|Tablet Android/,
  transformer: (s: string) => s
});
```

Regla de decisión: se parametriza cuando la implementación es idéntica salvo por el selector, que ya viene del test-data de la plataforma. Se separa cuando la implementación difiere (gestos distintos, cambio de contexto, esperas propias del driver).

## Cómo se resuelve una ambigüedad ya presente

1. **Identificar las dos definiciones** con el mensaje de error de Cucumber, que trae archivo y línea de ambas.
2. **Decidir cuál sobrevive**: la que esté en la carpeta compartida, o —si ambas son locales— la de la épica que la creó primero.
3. **Eliminar la duplicada** y referenciar la que sobrevive desde el `.feature`. Nunca se resuelve renombrando la nueva con un sinónimo: eso deja dos steps que hacen lo mismo con textos distintos, que es el problema de fondo un paso más adelante.
4. Si la que sobrevive queda usada por más de una épica, **moverla a la carpeta compartida** y registrarla en el catálogo.
5. Si las dos implementaciones difieren de verdad en comportamiento, entonces no era un duplicado sino dos steps con el mismo nombre: **el texto de uno estaba mal redactado**. Se corrige el texto para que describa lo que realmente hace.

## Anti-patrones

| Anti-patrón | Por qué falla |
|---|---|
| Confiar en el tag `@android` para desambiguar | Los tags filtran escenarios, no resuelven definiciones. El registro se arma antes de aplicar el filtro. |
| Confiar en la carpeta (`steps/android/...`) para desambiguar | La ruta no participa del matching. Dos archivos en carpetas distintas colisionan igual. |
| Regex laxa (`/^el usuario inicia sesión/`) | Matchea cualquier step que empiece igual, incluidos los de otras plataformas. Usar Cucumber Expressions con texto completo. |
| Sufijo en el `.feature` pero no en la definición | El step queda `undefined`. El texto debe coincidir en ambos lados. |
| Un perfil que carga todos los steps de todas las plataformas | Multiplica las colisiones sin necesidad. Cada perfil carga solo lo suyo y lo compartido. |
