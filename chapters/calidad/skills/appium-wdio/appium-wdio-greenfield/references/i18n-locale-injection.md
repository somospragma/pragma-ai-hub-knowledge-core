# Idioma y región como dimensión de prueba

En una aplicación multi-idioma, el idioma no es una preferencia del dispositivo: es una dimensión de la matriz de pruebas. El mismo escenario debe poder correr en cada idioma soportado sin duplicar escenarios ni ramificar los steps.

## Dónde se declara

En el escenario, con un tag o un ejemplo de la tabla; nunca dentro de un step.

```gherkin
@login @android @smoke @idioma-es
Scenario: Validación del saludo de bienvenida en español en Android
```

El hook lo lee del escenario y lo deja en el World antes de crear el driver, porque el idioma es una capability y no se puede cambiar con la sesión ya abierta:

```typescript
Before(function (this: HookWorld, { pickle }) {
  const tag = pickle.tags.find(t => t.name.startsWith('@idioma-'));
  this.testLanguage = tag?.name.replace('@idioma-', '') ?? env('DEFAULT_LANGUAGE', 'es');
  this.testLocale = mapearLocale(this.testLanguage);
});
```

## Inyección por plataforma

Android acepta idioma y región como capabilities directas:

```typescript
caps['appium:language'] = world.testLanguage;    // 'es'
caps['appium:locale']   = world.testLocale;      // 'ES'
```

iOS necesita además que el idioma llegue como argumento de lanzamiento de la app, porque las capabilities solas no siempre bastan cuando la app ya está instalada con otra preferencia:

```typescript
caps['appium:language'] = world.testLanguage;              // 'es'
caps['appium:locale']   = world.testLocale;                // 'es_ES'
caps['appium:processArguments'] = {
  args: ['-AppleLanguages', `(${world.testLanguage})`, '-AppleLocale', world.testLocale]
};
```

**Consecuencia que hay que asumir**: los argumentos de lanzamiento solo se aplican si la app se lanza en esa sesión. Eso obliga a `autoLaunch: true`, y en muchos casos a `noReset: false` para que la preferencia previa no sobreviva. El resultado es que los escenarios con idioma forzado en iOS arrancan más lento que los demás: es un costo consciente, y el timeout del perfil debe contemplarlo.

```typescript
caps['appium:autoLaunch'] = true;
caps['appium:noReset'] = false;
```

Los formatos difieren entre plataformas y es un error frecuente: Android espera la región suelta (`ES`), iOS espera la combinación completa (`es_ES`). Un mapa centralizado evita repetir la conversión:

```typescript
const LOCALES = {
  es: { android: 'ES', ios: 'es_ES', web: 'es-ES' },
  en: { android: 'US', ios: 'en_US', web: 'en-US' }
} as const;
```

## Web y navegador móvil

En web el idioma se fija en el contexto del navegador, y conviene fijar también la zona horaria: un formato de fecha o un saludo que dependa de la hora produce fallos intermitentes según dónde corra el pipeline.

```typescript
const contexto = await browser.newContext({
  locale: 'es-ES',
  timezoneId: 'Europe/Madrid'
});
```

## Los selectores no llevan lógica de idioma

Es la regla que hace viable todo lo anterior. El selector cubre las variantes de idioma en su propia expresión, o se apoya en un identificador de accesibilidad estable:

```json
{ "botonIngresar": "//android.widget.Button[@content-desc=\"Ingresar\" or @content-desc=\"Sign in\"]" }
```

```typescript
// Incorrecto: la ramificación se multiplica por elemento y por plataforma
const boton = idioma === 'en' ? s.botonIngresarEn : s.botonIngresarEs;

// Correcto: el selector no depende del idioma
await this.click(s.botonIngresar);
```

Detalle completo en `selectors-in-testdata-json.md`.

## Los textos esperados sí dependen del idioma

Lo que sí cambia por idioma son las aserciones sobre texto visible. Van a `test-data/shared/`, indexadas por idioma, nunca literales en el step:

```json
{
  "mensajes": {
    "es": { "credencialesInvalidas": "Los datos ingresados son incorrectos" },
    "en": { "credencialesInvalidas": "The information entered is incorrect" }
  }
}
```

```typescript
const esperado = mensajes[this.testLanguage].credencialesInvalidas;
expect(await pantalla.obtenerMensajeError()).toContain(esperado);
```

## Qué probar en cada idioma

Correr la suite completa en todos los idiomas multiplica el tiempo sin multiplicar la información. Una selección que rinde:

| Alcance | Idiomas |
|---|---|
| Suite de regresión completa | Idioma principal |
| Camino crítico (autenticación, transacción principal) | Todos los soportados |
| Pantallas con textos largos o formato de números, fechas y moneda | Todos los soportados |
| Escenarios de solo navegación | Idioma principal |

Los defectos de internacionalización se concentran en dos sitios: textos que desbordan el contenedor y formatos de número, fecha y moneda. La selección apunta ahí.
