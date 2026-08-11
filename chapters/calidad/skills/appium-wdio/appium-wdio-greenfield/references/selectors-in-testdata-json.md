# Selectores en archivos de test-data

## La regla

Ningún selector de UI se escribe en TypeScript. Todos viven en `test-data/{plataforma-base}/{epica}.json` y se cargan por un loader tipado.

La razón es operativa, no estética: en una suite multi-plataforma, un cambio de UI toca el mismo elemento en tres o cuatro sintaxis distintas. Con los selectores en código, ese cambio es una edición de lógica en varios archivos con riesgo de regresión y revisión completa. Con los selectores en datos, es una edición de un JSON, verificable de un vistazo, que un agente puede hacer con seguridad.

## Estructura del archivo

```json
{
  "selectors": {
    "campoUsuario": "//android.widget.EditText[@hint=\"Usuario\" or @hint=\"User\"]",
    "campoContrasena": "//android.widget.EditText[@password=\"true\"]",
    "botonIngresar": "//android.widget.Button[@content-desc=\"Ingresar\" or @content-desc=\"Sign in\"]",
    "saludoBienvenida": "//*[contains(@content-desc,\"Hola,\")]"
  },
  "loginErrorSelectors": {
    "mensajeError": "//android.view.View[@content-desc=\"{mensaje}\"]",
    "botonCerrar": "//android.widget.Button[@content-desc=\"Cerrar\"]"
  },
  "app": {
    "appPackage": "com.ejemplo.app",
    "esperaArranqueMs": 4000
  }
}
```

Convenciones:

- **Un archivo por épica y plataforma base**, no por historia. Doce historias de login comparten `login.json` con varios grupos.
- **Grupos de primer nivel en camelCase**, nombrados por pantalla o flujo. La propiedad 10 de `[[calidad-cucumber-bdd-conventions]]` lo verifica.
- **`shared/` no contiene selectores**: solo datos de configuración, usuarios de prueba y tiempos.
- **Nunca credenciales reales.** Los usuarios de prueba van con identificador y sus secretos por variable de entorno.

## Sintaxis por plataforma

| Plataforma base | Sintaxis | Ejemplo |
|---|---|---|
| `android` | XPath sobre atributos de UiAutomator | `//android.widget.Button[@content-desc="Ingresar"]` |
| `ios` | XPath sobre tipos XCUITest, o class chain | `//XCUIElementTypeButton[@name="Ingresar"]` |
| `web` | CSS o selectores del framework web | `button:has-text("Ingresar")` |

Cuando el identificador de accesibilidad existe, gana sobre todo lo demás: es más rápido y sobrevive a cambios de layout y de texto.

```json
{ "botonIngresar": "~botonIngresar" }
```

## El mapa de plataformas derivadas

Un iPad ejecuta la misma app que un iPhone; una tablet Android, la misma que un teléfono Android. Duplicar el archivo garantiza que las copias diverjan en el primer cambio.

```typescript
const PLATFORM_MAP = {
  web: 'web',
  android: 'android',
  tablet: 'android',
  ios: 'ios',
  ipad: 'ios'
} as const;

export class LoginScreen extends BaseScreen {
  private readonly s: LoginSelectors;

  constructor(driver: WebdriverIO.Browser, plataforma: keyof typeof PLATFORM_MAP) {
    super(driver);
    this.s = TestDataLoader.load<LoginData>(PLATFORM_MAP[plataforma], 'login.json').selectors;
  }
}
```

Si una plataforma derivada necesita un selector propio —una tablet con navegación lateral que el teléfono no tiene— se agrega **un grupo específico** en el archivo de la plataforma base (`tabletSelectors`), no un archivo nuevo.

## Selectores multi-idioma

Cuando la suite corre en más de un idioma, la variante va **dentro del selector**, no en una condicional del step:

```json
{ "botonIngresar": "//android.widget.Button[@content-desc=\"Ingresar\" or @content-desc=\"Sign in\"]" }
```

```typescript
// Incorrecto: lógica de idioma en el step
const boton = idioma === 'en' ? selectors.botonIngresarEn : selectors.botonIngresarEs;

// Correcto: el selector cubre ambos idiomas
await this.click(this.s.botonIngresar);
```

La condicional en el step se multiplica por cada elemento y cada plataforma, y se olvida en uno de los casos. El `or` en el XPath se escribe una vez y no tiene ramas que olvidar. Cuando los idiomas son muchos, la alternativa es un identificador de accesibilidad estable, que no depende del idioma: es la solución de fondo y vale pedirla al equipo de desarrollo.

## Selectores con valores de runtime

Para un mensaje cuyo texto solo se conoce en el escenario, el JSON define una plantilla con marcador:

```json
{ "mensajeError": "//android.view.View[@content-desc=\"{mensaje}\"]" }
```

```typescript
const selector = this.s.mensajeError.replace('{mensaje}', textoEsperado);
await this.waitForDisplayed(selector);
```

El marcador se sustituye en el objeto de pantalla, nunca en el step. Concatenar el selector en el step es hardcodearlo con pasos extra.

## El loader

```typescript
export class TestDataLoader {
  private static cache = new Map<string, unknown>();

  static load<T>(plataformaBase: string, archivo: string): T {
    const clave = `${plataformaBase}/${archivo}`;
    if (!this.cache.has(clave)) {
      const ruta = path.resolve(process.cwd(), 'test-data', plataformaBase, archivo);
      if (!fs.existsSync(ruta)) {
        throw new Error(`Archivo de test-data no encontrado: ${ruta}`);
      }
      this.cache.set(clave, JSON.parse(fs.readFileSync(ruta, 'utf-8')));
    }
    return this.cache.get(clave) as T;
  }
}
```

- **Cache por clave**: el archivo se lee una vez por corrida, no una vez por escenario.
- **Error explícito con la ruta absoluta**: un archivo faltante debe decir exactamente qué falta y dónde se buscó.
- **Tipo genérico**: la interfaz se declara junto al objeto de pantalla que la consume, de modo que un grupo renombrado en el JSON rompa la compilación en vez de fallar en runtime.

## Verificación

```bash
# Propiedad 3: ningún selector fuera del test-data
grep -rnE "//android\.|//XCUIElement|\[@content-desc|:has-text\(" src --include='*.ts'
```

Salida esperada: vacía. Cualquier hallazgo es un selector que sobrevivirá al próximo cambio de UI sin que nadie lo actualice.
