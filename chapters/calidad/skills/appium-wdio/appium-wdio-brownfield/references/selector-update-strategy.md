# Actualización de selectores

Un cambio de interfaz en una app multi-plataforma rompe el mismo elemento en varias sintaxis a la vez. Es el mantenimiento más frecuente de una suite mobile y el que más daño hace cuando se ejecuta mal: un "arreglo" que toca lógica introduce regresiones en escenarios que nadie estaba revisando.

## La regla

**Cambian valores en los archivos de test-data. El código no se toca.**

Si actualizar un selector exige modificar un objeto de pantalla o una definición de step, el selector estaba hardcodeado: eso es una migración (ver el workflow de migración de selectores), no una actualización.

## Procedimiento

### 1. Identificar el alcance real

Un elemento renombrado afecta a todas las plataformas base que lo declaran:

```bash
grep -rn "botonIngresar" test-data/
```

Actualizar solo la plataforma donde se detectó el fallo deja las demás rotas hasta que alguien corra ese perfil, que puede ser semanas después.

### 2. Obtener el selector nuevo de la evidencia, no por deducción

El árbol de la pantalla capturado en el fallo trae los atributos reales. Si no está, se captura:

```typescript
console.log(await driver.getPageSource());
```

O con las herramientas del ecosistema:

```bash
adb shell uiautomator dump && adb pull /sdcard/window_dump.xml   # Android
# Appium Inspector, conectando a la sesión activa, para ambas plataformas
```

**Un selector deducido del nombre de la clase o del texto visible es una apuesta.** Si acierta, acierta hasta el próximo cambio; si falla, el diagnóstico se atribuye a la app.

### 3. Verificar que el selector identifica exactamente un nodo

```typescript
const nodos = await driver.$$(selectorNuevo);
console.log(`Coincidencias: ${nodos.length}`);   // debe ser 1
```

Dos causas habituales de conteo mayor que uno:

- **Coincidencia parcial**: un `contains` sobre el identificador matchea también el nodo de la etiqueta asociada. El selector debe anclarse al valor completo.
- **Identidad contra capacidad**: el nodo que lleva el identificador no siempre es el que recibe el toque. En árboles con contenedores semánticos, el nodo capaz suele ser un descendiente. Un clic sobre el nodo identificador no hace nada y el escenario falla sin error.

### 4. Preferir el selector más estable disponible

| Prioridad | Estrategia | Por qué |
|---|---|---|
| 1 | Identificador de accesibilidad | No depende del idioma, del layout ni de la jerarquía |
| 2 | Identificador de recurso anclado (Android) | Estable salvo refactor del componente |
| 3 | Class chain o predicate (iOS) | Rápido y razonablemente estable |
| 4 | XPath por atributo | Sobrevive a cambios de posición pero no de texto |
| 5 | XPath por posición | Se rompe con cualquier cambio de layout. Último recurso, documentado |

Si el elemento no tiene identificador estable, **la solución de fondo es pedirlo al equipo de desarrollo**. Un selector frágil aceptado hoy es un fallo intermitente cada dos sprints. Se registra como recomendación en el reporte.

### 5. Preservar las variantes de idioma

```json
// Antes
{ "botonIngresar": "//android.widget.Button[@content-desc=\"Ingresar\" or @content-desc=\"Sign in\"]" }

// Después: cambia el texto, se mantienen las dos variantes
{ "botonIngresar": "//android.widget.Button[@content-desc=\"Entrar\" or @content-desc=\"Sign in\"]" }
```

Perder una variante al actualizar rompe la suite en el idioma que no se estaba probando. Es un fallo que aparece días después y cuesta relacionar con el cambio.

### 6. Preservar la forma del archivo

Solo cambia el valor. Se mantienen el nombre de la clave, el orden, el grupo, el formato y los comentarios si el formato los admite. Un JSON reordenado produce un diff ilegible en el que el revisor no puede ver qué cambió de verdad.

```diff
   "selectors": {
     "campoUsuario": "//android.widget.EditText[@hint=\"Usuario\"]",
-    "botonIngresar": "//android.widget.Button[@content-desc=\"Ingresar\"]",
+    "botonIngresar": "//android.widget.Button[@content-desc=\"Entrar\"]",
     "saludoBienvenida": "//*[contains(@content-desc,\"Hola,\")]"
   }
```

Ese es el aspecto que debe tener el diff de una actualización de selectores: una línea por elemento cambiado, cero archivos de código tocados.

### 7. Verificar

```bash
python3 -c "import json;json.load(open('test-data/android/login.json'))"   # JSON válido
npx cucumber-js --profile android --tags '@smoke'                          # los escenarios afectados
```

Y el conteo de nodos del paso 3 sobre el dispositivo, si el cambio fue mecánico y no se verificó en su momento.

## Cuando la actualización sí exige tocar código

Tres casos legítimos, y en los tres se avisa antes:

1. **El elemento cambió de naturaleza**: un campo de texto pasó a ser un selector desplegable. El selector nuevo no basta; el método del objeto de pantalla debe cambiar de interacción.
2. **El flujo cambió**: un paso nuevo entre dos pantallas. Es un cambio de escenario, no de selector.
3. **El elemento ya no existe**: el escenario debe replantearse con el equipo funcional, no repararse.

En los tres, el cambio se explica y se acuerda antes de aplicarlo. Reparar un selector para que un escenario pase cuando el flujo cambió es exactamente el falso verde que los guardrails anti-cheating del chapter prohíben.

## Lo que nunca se hace

| Acción | Por qué |
|---|---|
| Relajar el selector hasta que encuentre algo | Encuentra otro elemento y el escenario pasa sin probar lo que dice |
| Agregar una espera fija para que "funcione" | Oculta el problema real y hace la suite más lenta |
| Cambiar la aserción para que coincida con lo que devuelve la app | Es falsear el resultado, no corregir el selector |
| Comentar el escenario que falla | Deja cobertura reportada que no existe. Si hay que deshabilitarlo, va con el tag de exclusión y su motivo |
| Actualizar una sola plataforma | Las demás quedan rotas hasta que alguien las corra |
