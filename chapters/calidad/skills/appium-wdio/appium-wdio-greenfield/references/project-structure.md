# Estructura del arquetipo y configuración base

## Árbol

```
{project}/
├── package.json
├── tsconfig.json
├── cucumber.config.js                # un perfil por plataforma
├── .env.example                      # nombres de variables, nunca valores
├── src/
│   ├── main/
│   │   ├── config/
│   │   │   ├── mobile.config.ts      # constructores de capabilities locales
│   │   │   ├── cloud.config.ts       # capabilities del device farm
│   │   │   └── config.manager.ts     # entorno activo, base URLs
│   │   ├── e2e-runtime/
│   │   │   ├── appium/appium-server-manager.ts
│   │   │   ├── drivers/
│   │   │   │   ├── mobile-platform-profile.ts   # el tipo
│   │   │   │   ├── profiles.ts                  # los perfiles como datos
│   │   │   │   └── generic-mobile-driver.ts     # el motor único
│   │   │   ├── devices/device-catalog.ts
│   │   │   ├── evidence/               # video, screenshots
│   │   │   ├── teardown/
│   │   │   └── types/hook-world.ts
│   │   ├── screens/
│   │   │   ├── base/BaseScreen.ts
│   │   │   └── {epica}/{Nombre}Screen.ts
│   │   └── utils/
│   │       ├── logger.ts
│   │       └── loaders/test-data-loader.ts
│   └── test/e2e/
│       ├── features/{epica}/*.feature
│       ├── steps/{epica}/{plataforma}/*.steps.ts
│       ├── steps/{auth,common}/**       # compartidos
│       ├── hooks/hooks.ts
│       └── types/cucumber.d.ts
├── test-data/{web,android,ios,shared}/*.json
└── reports/                          # ignorado por git
```

La separación `main` / `test` es deliberada: `main` es el framework —reutilizable, con pruebas unitarias propias—, `test` es la suite. Mezclarlos hace imposible testear el framework y difícil saber qué se puede cambiar sin romper escenarios.

## `cucumber.config.js`

Un perfil por plataforma. Cada uno declara qué definiciones carga y qué tags filtra. Es el archivo que decide si un escenario corre o no.

```javascript
const BASE = 'src/test/e2e';

const COMMON = {
  requireModule: ['ts-node/register'],
  paths: [`${BASE}/features/**/*.feature`],
  formatOptions: { snippetInterface: 'async-await' },
  parallel: 1
};

const perfil = (nombre, carpetas, tags) => ({
  ...COMMON,
  require: [
    `${BASE}/hooks/**/*.ts`,
    `${BASE}/steps/{auth,common}/**/*.ts`,      // compartidos: siempre
    ...carpetas.map(c => `${BASE}/steps/**/${c}/**/*.ts`)
  ],
  format: [
    `html:reports/${nombre}/index.html`,
    `json:reports/${nombre}/report.json`
  ],
  tags
});

module.exports = {
  default:  perfil('default', [], 'not @ignore'),
  android:  perfil('android', ['android'], '@android and not @ignore'),
  ios:      perfil('ios',     ['ios'],     '@ios and not @ignore'),
  ipad:     perfil('ipad',    ['ipad'],    '@ipad and not @ignore'),
  tablet:   perfil('tablet',  ['tablet'],  '@tablet and not @ignore'),
  'android-web': perfil('android-web', ['android'], '@android-web and not @ignore'),
  'ios-web':     perfil('ios-web',     ['ios'],     '@ios-web and not @ignore')
};
```

Cuatro cosas que se rompen si se hacen a mano y por eso van en la función:

- **Olvidar los compartidos** en un perfil deja sus steps de login `undefined`.
- **Olvidar `not @ignore`** hace que los escenarios deshabilitados corran igual.
- **Reportes al mismo directorio** hace que la última plataforma pise el reporte de la anterior.
- **Perfiles que cargan más plataformas de las necesarias** multiplican la superficie de ambigüedad sin ganar nada.

Los perfiles derivados (`ipad`, `tablet`) cargan la carpeta de definiciones de su plataforma base cuando comparten implementación; si tienen definiciones propias, cargan las suyas. La decisión se toma una vez y se documenta en el README.

## Scripts de `package.json`

Un script por perfil, más las variantes de modo de ejecución y dispositivo. La forma compuesta evita duplicar la cadena del runner:

```json
{
  "scripts": {
    "test:android": "cucumber-js --config cucumber.config.js --profile android",
    "test:ios": "cucumber-js --config cucumber.config.js --profile ios",
    "test:android:emulator": "ANDROID_DEVICE_TYPE=emulator npm run test:android",
    "test:android:device": "ANDROID_DEVICE_TYPE=physical npm run test:android",
    "test:ios:simulator": "IOS_DEVICE_TYPE=simulator npm run test:ios",
    "test:ios:device": "IOS_DEVICE_TYPE=physical npm run test:ios",
    "test:cloud:android": "EXECUTION_MODE=cloud npm run test:android",
    "test:smoke": "cucumber-js --tags '@smoke and not @ignore'",
    "typecheck": "tsc --noEmit",
    "lint": "eslint 'src/**/*.ts' --max-warnings 0"
  }
}
```

El mismo perfil corre en emulador, dispositivo físico y device farm cambiando variables de entorno, nunca el código ni el config. Ver `local-vs-cloud-execution.md`.

## `tsconfig.json`

Estricto desde el primer día. Un arquetipo que empieza laxo no se endurece nunca, y el World sin tipar es donde aparecen los fallos en runtime.

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "types": ["node", "@wdio/globals/types"]
  },
  "include": ["src/**/*.ts"]
}
```

`npx tsc --noEmit` es parte del health-check: los tipos de WebdriverIO detectan en compilación la mitad de los errores de uso del driver.

## `.env.example`

Lleva **todas** las variables con descripción y ningún valor real. Es el contrato de configuración del arquetipo y lo primero que lee quien lo recibe.

```bash
# Servidor Appium
APPIUM_HOST=127.0.0.1
APPIUM_PORT=4723

# Android — dejar vacío para autodetectar el dispositivo conectado
ANDROID_DEVICE_TYPE=physical        # physical | emulator
ANDROID_UDID=
ANDROID_APP_PACKAGE=
ANDROID_APP_ACTIVITY=
ANDROID_EMULATOR_NAME=

# iOS — obtener el UDID con: xcrun xctrace list devices
IOS_DEVICE_TYPE=simulator           # simulator | physical
IOS_UDID=
IOS_BUNDLE_ID=
IOS_XCODE_ORG_ID=                   # solo dispositivo físico
IOS_XCODE_SIGNING_ID=

# Ejecución
EXECUTION_MODE=local                # local | cloud
RECORD_VIDEO=false
```

Cada variable que el README marca como pendiente lleva el comando exacto para obtener su valor. Un `.env.example` con valores reales de otro proyecto es una fuga de datos y una fuente de fallos silenciosos.
