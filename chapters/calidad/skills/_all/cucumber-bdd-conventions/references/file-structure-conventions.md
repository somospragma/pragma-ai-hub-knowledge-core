# Estructura de archivos de un arquetipo Cucumber multi-plataforma

La estructura no es preferencia estética: los perfiles de Cucumber seleccionan qué definiciones cargar **por glob de ruta**. Un archivo fuera de la convención no lo carga ningún perfil, sus steps quedan `undefined` y el escenario nunca corre — sin error de compilación que lo delate.

## Árbol de referencia

```
src/
├── test/{base}/e2e/
│   ├── features/
│   │   └── {epica}/
│   │       └── {historia}.feature          # Gherkin, todas las plataformas juntas
│   ├── steps/
│   │   ├── auth/                           # Compartidos: autenticación
│   │   ├── common/                          # Compartidos: mensajes, utilidades
│   │   ├── navbar/                          # Compartidos: navegación
│   │   │   ├── android/
│   │   │   ├── ios/
│   │   │   ├── ipad/
│   │   │   └── tablet/
│   │   └── {epica}/                         # Específicos de la épica
│   │       ├── web/
│   │       ├── android/
│   │       ├── ios/
│   │       ├── ipad/
│   │       ├── tablet/
│   │       └── mobile-web/
│   ├── hooks/
│   │   └── hooks.ts                         # Un único punto de ciclo de vida
│   └── types/
│       └── cucumber.d.ts                    # Tipado del World
└── main/{base}/
    ├── pages/                               # Objetos de página (web)
    │   ├── base/BasePage.ts
    │   └── {epica}/{Nombre}Page.ts
    ├── screens/                             # Objetos de pantalla (mobile)
    │   ├── base/BaseScreen.ts
    │   └── {epica}/{Nombre}Screen.ts
    └── utils/loaders/test-data-loader.ts

test-data/
├── web/{epica}.json
├── android/{epica}.json                     # cubre android y tablet
├── ios/{epica}.json                         # cubre ios e ipad
└── shared/{datos-transversales}.json
```

## Las tres decisiones que sostienen la estructura

### 1. El feature agrupa por historia, los steps por plataforma

Un único `.feature` por historia contiene los escenarios de **todas** las plataformas, separados por sus tags. Es lo que permite leer la cobertura de la historia completa en un archivo y detectar de un vistazo que iOS quedó sin cubrir.

Las definiciones, en cambio, se separan por plataforma en subcarpetas, porque es el eje por el que los perfiles filtran.

### 2. Compartido contra específico: la carpeta decide, no el nombre

Un step que aplica a más de una épica va a una carpeta compartida (`auth/`, `common/`, `navbar/`, `home/`). Uno específico se queda en la carpeta de su épica.

La consecuencia práctica: **todo perfil debe cargar las carpetas compartidas además de las de su plataforma**. Un perfil que solo carga su épica deja los steps de login sin resolver.

```javascript
// Cada perfil: hooks + compartidos + los de su plataforma
require: [
  `${BASE}/hooks/**/*.ts`,
  `${BASE}/steps/{auth,common,navbar,home}/**/*.ts`,
  `${BASE}/steps/**/android/**/*.ts`
]
```

### 3. Los objetos de pantalla y de página no conocen selectores

Un objeto de pantalla expone acciones de negocio (`ingresarCredenciales`, `esperarPantalla`) y obtiene sus selectores del test-data de la plataforma. Un cambio de UI se resuelve editando un JSON, sin recompilar ni tocar lógica.

Esto es lo que hace que un agente pueda mantener la suite: reparar un selector roto es una edición de datos verificable, no una modificación de código con riesgo de regresión.

## Mapeo de plataformas a datos

Las plataformas derivadas comparten el test-data de su plataforma base — un iPad ejecuta la misma app que un iPhone, con los mismos identificadores:

```typescript
const PLATFORM_MAP = {
  web:     'web',
  android: 'android',
  tablet:  'android',
  ios:     'ios',
  ipad:    'ios'
} as const;
```

El objeto de pantalla resuelve su plataforma base con este mapa antes de cargar el JSON. Duplicar `test-data/ipad/` es el error que garantiza que los dos archivos diverjan en el primer cambio de UI.

## Nomenclatura

| Elemento | Convención | Ejemplo |
|---|---|---|
| Carpeta de épica | Identificador de la épica en el ALM + nombre kebab-case | `hu-26690_login/` |
| Archivo de feature | Identificador de la historia + nombre kebab-case | `hu-24688_login-con-contrasena.feature` |
| Archivo de definiciones | Igual que el feature, sufijo `.steps.ts` | `hu-24688_login-con-contrasena.steps.ts` |
| Objeto de página / pantalla | PascalCase con sufijo `Page` / `Screen` | `LoginPage.ts`, `LoginScreen.ts` |
| Archivo de test-data | Nombre de la épica en kebab-case | `login.json` |
| Grupo de selectores | camelCase describiendo pantalla o flujo | `otpSelectors` |

Si el arquetipo del cliente ya tiene otra convención, **manda la del cliente**. Lo que no es negociable es que exista una y que todos los archivos la cumplan: las propiedades 4, 5 y 11 de `static-correctness-properties.md` la verifican, cualquiera que sea el patrón declarado.

## Un archivo de test-data por épica y plataforma

No por historia. Una épica con doce historias tiene un `login.json` con doce grupos de selectores, no doce archivos. La regla evita el escenario en que dos historias definen el mismo selector con nombres distintos y solo una se actualiza cuando cambia la UI.
