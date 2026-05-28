# Desktop Applications — Patrones y Adaptación

## Patrones canónicos

- **Plataforma**: Windows (WPF, WinForms, UWP, Win32), macOS (Cocoa, SwiftUI, Catalyst), Linux (GTK, Qt), cross-platform (Electron, JavaFX, Flutter desktop, Qt, .NET MAUI).
- **Driver de automation**: cada plataforma tiene su accesibilidad tree (UI Automation en Windows, AX en macOS, AT-SPI en Linux). El framework de testing lo consume.
- **Distribución**: instaladores (MSI, MSIX, pkg, dmg, AppImage, snap, flatpak, deb, rpm). Test de instalación + uninstall + upgrade es parte de la suite, no opcional.
- **Auto-update**: Squirrel, Sparkle, MAU — testear el flujo de update y rollback.
- **Permisos OS**: filesystem, cámara, micrófono, notificaciones. Validar comportamiento sin permisos y request flow.

## Framework primario por plataforma

- **Electron** → **Playwright** (`_electron` API): launch del binario, acceso a `BrowserWindow`, mismo DSL que web.
- **Windows nativo** (WPF, WinForms, UWP) → **WinAppDriver** (Microsoft, basado en WebDriver protocol) o **FlaUI** (.NET nativo).
- **macOS nativo** → **XCUITest** (proyecto Xcode UI tests) o **AppleScript** para flujos simples.
- **Cross-platform comercial** → **TestComplete** (SmartBear) cuando el cliente paga la licencia y necesita object recognition robusto.
- **Linux GTK/Qt** → **dogtail** (AT-SPI), **squish** (comercial), o tests funcionales por CLI cuando aplica.

## Complementarios

- **Sikuli / SikuliX** para visual fallback cuando el accessibility tree no expone un control (gráficos custom, canvas).
- **Applitools** para visual regression cross-platform.
- **Spectron** está deprecado para Electron — usar Playwright.

## Patrón canónico: testing Electron con Playwright

```javascript
const { _electron: electron } = require('playwright');

const app = await electron.launch({ args: ['.'] });
const window = await app.firstWindow();
await window.click('text=New Project');
await window.fill('input[name=projectName]', 'demo');
await app.close();
```

## Accesibilidad (a11y)

Desktop tiene a11y como requisito en muchos contratos B2B y gobierno (WCAG aplicable también en desktop vía equivalentes nativos).

- **macOS**: Accessibility Inspector (Xcode).
- **Windows**: Narrator, Accessibility Insights for Windows.
- **Linux**: Orca screen reader, Accerciser para explorar AT-SPI.
- Validar navegación por teclado (tab order), contraste, role/name/state de cada control.

## Antipatrones

- Probar solo el "binario corre" sin cubrir instalación/upgrade/uninstall.
- Asumir que Electron y Web tienen 100% paridad — APIs nativas de Electron (clipboard, shell, notificaciones) requieren tests propios.
- Skipear a11y porque "no se ve en la suite funcional" — los contratos B2B lo exigen.
- Visual regression sin tolerancia de pixel — falla por antialiasing del SO.
- Tests sin teardown: el proceso queda colgado y bloquea CI.
