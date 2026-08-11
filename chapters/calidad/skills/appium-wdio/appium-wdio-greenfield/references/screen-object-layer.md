# Capa de objetos de pantalla

## Responsabilidades

| Capa | Sabe | No sabe |
|---|---|---|
| Definición de step | Qué acción de negocio ocurre | Cómo se hace clic, qué selector se usa |
| Objeto de pantalla | Qué elementos tiene la pantalla y qué se puede hacer en ella | Qué escenario lo invoca |
| `BaseScreen` | Cómo se interactúa con un elemento en Appium | Qué pantalla es |
| Test-data | Los selectores | Todo lo demás |

Un step que llama a `driver.$()` se saltó dos capas. La consecuencia es que ese selector queda fuera del test-data y el flujo no se puede reutilizar.

## `BaseScreen`

```typescript
export abstract class BaseScreen {
  constructor(protected readonly driver: WebdriverIO.Browser) {}

  async click(selector: string): Promise<void> {
    const el = await this.driver.$(selector);
    await el.waitForDisplayed({ timeout: 10_000 });
    await el.click();
  }

  async setValue(selector: string, texto: string): Promise<void> {
    const el = await this.driver.$(selector);
    await el.waitForDisplayed({ timeout: 10_000 });
    await el.setValue(texto);
  }

  async getText(selector: string): Promise<string> {
    return (await this.driver.$(selector)).getText();
  }

  async isDisplayed(selector: string): Promise<boolean> {
    const el = await this.driver.$(selector);
    return (await el.isExisting()) && (await el.isDisplayed());
  }

  async waitForDisplayed(selector: string, timeout = 10_000): Promise<void> {
    await (await this.driver.$(selector)).waitForDisplayed({ timeout });
  }
}
```

Todo método envuelve el error con contexto —selector, acción, pantalla— antes de relanzarlo. Un `element not found` sin decir cuál obliga a reproducir el fallo para diagnosticarlo; con el selector en el mensaje, muchas veces basta el reporte.

## Repertorio que no es obvio

### Esperar cualquiera de varios elementos

Una pantalla puede resolver de varias formas legítimas: el dashboard, o el diálogo de cambio de contraseña obligatorio, o el aviso de sesión en otro dispositivo. Esperar solo el camino feliz produce un timeout que se reporta como fallo de la app.

```typescript
async waitForAnyDisplayed(selectores: string[], timeout = 10_000): Promise<void> {
  await this.driver.waitUntil(
    async () => {
      for (const s of selectores) {
        if (await (await this.driver.$(s)).isExisting()) return true;
      }
      return false;
    },
    { timeout, timeoutMsg: `Ninguno visible tras ${timeout}ms: ${selectores.join(', ')}` }
  );
}
```

El mensaje de timeout enumera los selectores esperados: es la diferencia entre un fallo diagnosticable y uno que hay que reproducir.

### Tap por coordenadas, con el gesto de cada plataforma

Hay elementos sobre los que `click()` no funciona: envueltos en contenedores que interceptan el evento, parcialmente cubiertos, o renderizados por motores que no exponen el nodo capaz. El tap por coordenadas del centro del elemento los resuelve, y el comando difiere por plataforma:

```typescript
async tapElement(selector: string): Promise<void> {
  const el = await this.driver.$(selector);
  await el.waitForExist({ timeout: 10_000 });
  const { x, y } = await el.getLocation();
  const { width, height } = await el.getSize();
  const cx = Math.round(x + width / 2);
  const cy = Math.round(y + height / 2);

  const plataforma = String((this.driver.capabilities as Record<string, unknown>)?.platformName ?? '').toLowerCase();
  if (plataforma === 'ios') {
    await this.driver.execute('mobile: tap', { x: cx, y: cy });
  } else {
    await this.driver.execute('mobile: clickGesture', { x: cx, y: cy });
  }
}
```

Es un recurso de recuperación, no el método por defecto: un tap por coordenadas pasa aunque el elemento esté deshabilitado, con lo que puede ocultar un defecto real. Se usa cuando `click()` falla de forma reproducible y se documenta por qué en el objeto de pantalla.

### Scroll hasta un elemento

```typescript
// Android: el motor de UiAutomator scrollea hasta encontrar el descriptor
await this.driver.$(
  'android=new UiScrollable(new UiSelector().scrollable(true))' +
  '.scrollIntoView(new UiSelector().descriptionContains("Cerrar sesión"))'
);

// iOS: gesto de scroll sobre el contenedor
await this.driver.execute('mobile: scroll', { direction: 'down', predicateString: 'label == "Cerrar sesión"' });
```

### Ocultar el teclado

En Android el teclado tapa el botón que sigue al último campo, y el clic golpea la tecla en vez del botón. El canon de escritura es: tocar el campo, escribir, ocultar el teclado, continuar.

```typescript
async escribirYCerrarTeclado(selector: string, texto: string): Promise<void> {
  await this.click(selector);
  await this.setValue(selector, texto);
  if (await this.driver.isKeyboardShown()) {
    await this.driver.hideKeyboard();
  }
}
```

## Un objeto de pantalla concreto

```typescript
export class LoginScreen extends BaseScreen {
  private readonly s: LoginSelectors;

  constructor(driver: WebdriverIO.Browser, plataforma: Plataforma) {
    super(driver);
    this.s = TestDataLoader.load<LoginData>(PLATFORM_MAP[plataforma], 'login.json').selectors;
  }

  async esperarPantalla(): Promise<void> {
    await this.waitForAnyDisplayed([this.s.campoUsuario, this.s.saludoBienvenida], 30_000);
  }

  async ingresarCredenciales(usuario: string, contrasena: string): Promise<void> {
    await this.escribirYCerrarTeclado(this.s.campoUsuario, usuario);
    await this.escribirYCerrarTeclado(this.s.campoContrasena, contrasena);
    await this.click(this.s.botonIngresar);
  }

  async obtenerMensajeError(): Promise<string> {
    return this.getText(this.s.mensajeError);
  }
}
```

Los métodos son acciones de negocio, no operaciones de UI. `ingresarCredenciales` en vez de tres llamadas sueltas desde el step: si mañana el flujo agrega un paso, cambia un método y no diez escenarios.

## Anti-patrones

| Anti-patrón | Por qué |
|---|---|
| Aserciones dentro del objeto de pantalla | La pantalla expone estado; quien decide si está bien es el step. Con la aserción adentro, el mismo método no sirve para el caso negativo. |
| Llamadas HTTP a servicios de terceros en `BaseScreen` | Consultar correo, analítica o una API de datos no es interactuar con una pantalla. Va a un servicio aparte, inyectado. Es el error de diseño más común en esta capa y convierte la clase base en un objeto que todo lo hace. |
| Selectores literales en el objeto de pantalla | Rompe la propiedad 3. Los selectores vienen del test-data. |
| Un objeto de pantalla por plataforma con el mismo nombre | Duplica la lógica de negocio. Un objeto por pantalla, parametrizado por plataforma, resolviendo selectores por el mapa. |
| `driver.pause()` como espera | Espera fija: lenta cuando sobra, insuficiente cuando falta. Se usa espera por condición. Se acepta `pause` solo para animaciones de duración conocida, con un comentario que lo justifique. |
