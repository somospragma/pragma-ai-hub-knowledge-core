# Estructura del proyecto (Serenity WDIO Greenfield)

## Arbol

```
{project_name}/
├── package.json                    # scripts test:<modo>, dependencias v9/v3/v11 (ver package-dependencies.md)
├── tsconfig.json                   # target es2022, strict true
├── wdio.shared.conf.ts             # base compartida + workaround window handles NATIVE_APP
├── configs/
│   ├── wdio.web.conf.ts            # web desktop (enforceWebDriverClassic true)
│   ├── wdio.web_mobile.conf.ts     # WebView (enforceWebDriverClassic true)
│   ├── wdio.android.conf.ts        # movil nativo Android (UiAutomator2)
│   ├── wdio.ios.conf.ts            # movil nativo iOS (XCUITest)
│   ├── wdio.desktop.conf.ts        # Appium Windows
│   └── wdio.api.conf.ts            # pruebas REST
├── scripts/
│   └── run.mjs                     # orquestador --mode / --platform / --tags
├── .env.web
├── .env.web_movil
├── .env.movil.android
├── .env.movil.ios
├── .env.api
├── README.md                       # comandos, tabla modo -> config -> env
└── features/
    ├── web/                        # automatizacion web desktop
    │   ├── Features/               # archivos .feature
    │   ├── Tasks/                  # Tasks web
    │   ├── UI/                     # PageElement + By
    │   ├── Questions/              # Questions web
    │   ├── Data/                   # datos de prueba
    │   └── shared/                 # Interactions, Questions, Tasks, Utils reutilizables
    ├── mobile/                     # automatizacion movil nativo
    │   ├── android/                # Features, Tasks, UI (selectores como string)
    │   ├── ios/                    # Features, Tasks, UI (selectores como string)
    │   └── shared/                 # Interactions, Questions, Tasks reutilizables
    ├── api/                        # pruebas REST
    │   ├── Features/
    │   ├── Tasks/
    │   ├── Interactions/
    │   ├── Questions/
    │   └── Data/
    ├── step-definitions/           # steps de Cucumber por canal
    │   ├── web/
    │   ├── mobile/
    │   └── api/
    └── support/
        └── parameter.config.ts     # parameter types {actor} y {pronoun}
```

## Artefactos obligatorios del arquetipo

- **`features/web`**: capa web desktop completa. UI con `PageElement` localizado por `By.xpath()` o `By.css()`. Tasks componen Interactions con `Task.where`. Questions sin efectos secundarios.
- **`features/mobile`**: capa movil nativo por plataforma (`android`, `ios`) mas `shared`. UI expone selectores como `string` (Accessibility ID prioritario), nunca `PageElement`.
- **`step-definitions`**: glue de Cucumber separado por canal (`web`, `mobile`, `api`). Cada archivo de steps declara `setDefaultTimeout` explicito.
- **`support/parameter.config.ts`**: define los parameter types `{actor}` y `{pronoun}` usados en los steps.
- **`configs/wdio.*.conf.ts`**: un config por modo, todos heredan de `wdio.shared.conf.ts` mediante merge.
- **`scripts/run.mjs`**: orquestador que resuelve `--mode`, `--platform` y `--tags`, carga el `.env.<modo>` correcto y lanza WebdriverIO seguido del reporte serenity-bdd.

## Regla de directorios versionados

Usar `.gitkeep` en directorios vacios para conservarlos en git. Ver el detalle de cada modo y su env asociado en `run-and-modes.md`.

## Dependencias de `package.json`

La lista completa y verificada de `devDependencies` (incluidos paquetes periféricos como `@wdio/spec-reporter`, `@wdio/cucumber-framework` y `@serenity-js/webdriverio`, que otros generadores omiten por asumirlos transitivos) está en `references/package-dependencies.md`, junto con el fix de deduplicación de `@cucumber/cucumber` necesario para que los step-definitions se registren correctamente.
