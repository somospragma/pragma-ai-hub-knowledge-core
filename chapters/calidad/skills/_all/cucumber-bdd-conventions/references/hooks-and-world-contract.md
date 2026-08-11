# Hooks y contrato del World

En un arquetipo multi-plataforma, `hooks.ts` es el único punto donde se decide qué driver se crea, cuánto se espera y qué evidencia se captura. Es el archivo que más crece y el que peor envejece: la disciplina para mantenerlo pequeño es lo que permite agregar una plataforma sin reescribirlo.

## El contrato

**Un tag de plataforma, un hook, un driver.** El escenario declara su plataforma con un tag; el hook que matchea ese tag crea el driver y lo deja en el World; los steps consumen `this.driver` sin saber cómo se creó.

```typescript
for (const perfil of PERFILES) {
  Before({ tags: perfil.tagExpression, timeout: perfil.timeoutMs }, async function (this: HookWorld) {
    await new DriverStrategy(perfil).setup(this);
  });
}
```

El bucle es deliberado: con los perfiles definidos como datos (ver el skill del stack correspondiente), agregar una plataforma no agrega un hook. Seis `Before` casi idénticos es la señal de que falta esa abstracción — y el sitio donde una corrección se aplica en cinco de los seis.

## World tipado

El World es el único canal de estado entre steps de un mismo escenario. Debe estar declarado en un tipo, no crecer por asignación libre.

```typescript
export interface HookWorld extends World {
  driver?: WebdriverIO.Browser;      // driver activo (mobile)
  page?: Page;                        // página activa (web)
  pickle?: Pickle;                    // escenario en curso: tags, nombre
  testName: string;
  testLanguage?: string;              // dimensión de i18n, si aplica
  ltDevice?: DeviceInfo;              // dispositivo asignado en ejecución cloud
  recordingStarted?: boolean;
  attach: (data: string | Buffer, mime: string) => void;
}
```

Reglas:

- **Nada de estado global fuera del World.** Una variable de módulo compartida entre escenarios sobrevive al teardown y contamina la corrida siguiente; con ejecución en paralelo, produce fallos que no se reproducen.
- **El World se tipa una vez** y los steps lo consumen tipado (`this: HookWorld`). Un World con `any` convierte cada step en un punto de fallo en runtime.
- **Lo que un step necesita del escenario** (tags, nombre) sale de `pickle`, no de variables propias.

## Orden de hooks y qué va en cada uno

| Hook | Responsabilidad | Lo que NO va aquí |
|---|---|---|
| `BeforeAll` | Preparar el entorno de la corrida: carpetas de reportes, nombre de build, verificación de prerequisitos | Crear drivers |
| `Before` sin tags | Resolver el contexto del escenario: nombre, idioma, dimensiones desde tags | Lógica de plataforma |
| `Before` con tag de plataforma | Crear el driver de esa plataforma y dejarlo en el World | Navegación funcional, login |
| `BeforeStep` | Marcar tiempo, preparar captura | Aserciones |
| `AfterStep` | Capturar evidencia del paso (screenshot en fallo o siempre, según política) | Recuperación de errores |
| `After` con tag de plataforma | Cerrar video, adjuntar evidencia de fallo, marcar estado en el grid, cerrar sesión | Aserciones nuevas |
| `AfterAll` | Consolidar reporte, apagar servicios levantados por la corrida | Nada por escenario |

El error frecuente es meter precondiciones funcionales (login, navegación a una pantalla) en el `Before` de plataforma. Eso las hace invisibles en el `.feature`: el escenario dice que empieza en el dashboard sin ningún `Given` que lo explique, y nadie puede correr solo ese escenario desde otro estado. Las precondiciones funcionales son steps `Given`, siempre.

## Timeouts

Tres timeouts distintos que se confunden entre sí:

| Timeout | Qué cubre | Orden de magnitud |
|---|---|---|
| Timeout por defecto de step | Lo que tarda una interacción con la UI | decenas de segundos |
| Timeout del hook de creación de driver | Arranque de emulador, provisión de dispositivo en el grid, instalación de app | varios minutos |
| Timeout de espera de elemento | Lo que tarda una pantalla en pintar | segundos |

El de creación de driver es el que se olvida y produce fallos falsos en cloud: el dispositivo está en cola y el hook expira antes de que lo asignen. Se configura por perfil de plataforma, no globalmente.

## Evidencia por step

`AfterStep` es donde se captura la evidencia que hace diagnosticable un fallo sin reproducirlo. La política mínima:

- **Screenshot en cada fallo**, adjunto al reporte. Sin esto, un fallo en cloud es irreproducible.
- **Screenshot por step** en las suites críticas, comprimido antes de adjuntar. Sin compresión, un reporte de doscientos escenarios pesa cientos de megabytes y nadie lo abre.
- **Volcado del árbol de la pantalla** en el fallo, no solo la imagen: es lo que permite corregir un selector sin volver a correr.

Detalle de la instrumentación mobile en el skill del stack correspondiente.

## Teardown

El teardown se ejecuta **siempre**, incluso cuando el escenario falló en el primer step, y su fallo nunca debe enmascarar el del escenario: todo va envuelto en captura de errores que registra pero no relanza.

Orden: detener grabación → capturar evidencia de fallo → marcar estado en el grid remoto → cerrar sesión del driver. Cerrar la sesión primero deja sin evidencia justo el escenario que falló.

Una sesión que no se cierra deja el dispositivo ocupado y hace fallar la corrida siguiente por falta de dispositivos disponibles. En ejecución con sesiones múltiples simultáneas se cierran todas, en paralelo, sin que el fallo de una impida cerrar la otra.
