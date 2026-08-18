# Test Data Management: serenity-wdio

Material de referencia específico del arquetipo TypeScript + WebdriverIO v9 + Serenity/JS v3.31 + Cucumber 11. Complementa el Skill_All `calidad-test-data-management` aportando los patrones, convenciones y ejemplos de código propios de este stack.

---

## Estructura de carpetas de datos

El arquetipo organiza los datos de prueba junto a cada módulo funcional, evitando carpetas de datos globales que generen acoplamiento:

```
features/
├── web/Data/
│   ├── Form/
│   │   └── datos_estudiante.json         # dataset nombrado por caso de uso
│   └── Images/
│       └── perfil.png
├── api/Data/                              # fixtures de request/response
└── shared/data/                           # datos verdaderamente transversales
```

Regla de colocación: cada módulo mantiene su propio directorio `Data/`. Solo los datos que se reutilizan entre dos o más módulos distintos viven en `shared/data/`.

---

## Carga de JSON tipado desde TypeScript

### Definición de tipos

```typescript
// features/web/Data/Form/types.ts
export interface DatosEstudiante {
  nombres: string;
  apellidos: string;
  email: string;
  genero: 'Male' | 'Female' | 'Other';
  movil: string;
  fechaNacimiento: { dia: string; mes: string; anio: string };
  materias: string[];
  hobbies: string[];
  imagenPerfil: string;
  direccion: string;
  estado: string;
  ciudad: string;
}
```

### Loader con validación de existencia

```typescript
// features/web/Data/Form/loader.ts
import * as fs from 'node:fs';
import * as path from 'node:path';
import { DatosEstudiante } from './types';

export const cargarDataset = (nombre: string): DatosEstudiante => {
  const filePath = path.resolve(
    process.cwd(),
    'features/web/Data/Form',
    `${ nombre }.json`,
  );

  if (!fs.existsSync(filePath)) {
    throw new Error(`Dataset no encontrado: ${ filePath }`);
  }

  const raw = fs.readFileSync(filePath, 'utf-8');
  return JSON.parse(raw) as DatosEstudiante;
};
```

Usar siempre `path.resolve(process.cwd(), ...)` en lugar de rutas relativas para garantizar portabilidad entre entornos.

### Import directo con `resolveJsonModule`

Si `tsconfig.json` tiene `"resolveJsonModule": true`, es posible importar JSON directamente con tipo inferido:

```typescript
import datosEstudiante from '../../web/Data/Form/datos_estudiante.json';
```

Preferir `cargarDataset(nombre)` cuando el dataset se selecciona dinámicamente desde el `.feature` (Scenario Outline). El import directo es adecuado cuando el dataset es único y conocido en tiempo de compilación.

---

## Parametrización con Scenario Outline

### Patrón del arquetipo

```gherkin
Feature: Gestión de formulario Practice Form

  @form
  Scenario Outline: Registro exitoso de estudiante
    Given que <actor> accede al formulario de registro
    When <actor> diligencia el formulario con "<dataset>"
    Then <actor> envía la información
    Then <actor> debería ver los datos registrados correctamente de acuerdo a "<dataset>"

    Examples:
      | actor   | dataset            |
      | Pepito  | datos_estudiante   |
      | Ana     | datos_estudiante_2 |
```

El nombre del dataset viaja como parámetro de texto desde el `.feature` hasta la Task, donde se resuelve en tiempo de ejecución.

### Step que delega la carga

```typescript
import { cargarDataset } from '../../web/Data/Form/loader';

When('{actor} diligencia el formulario con {string}',
  async (actor: Actor, dataset: string) => {
    await actor.attemptsTo(
      LlenarFormulario.conDataset(dataset),
    );
  },
);
```

### Task que carga y consume el JSON

```typescript
import { Task } from '@serenity-js/core';
import { cargarDataset } from '../../Data/Form/loader';

export class LlenarFormulario {
  static conDataset = (nombre: string) =>
    Task.where(`#actor diligencia el formulario con dataset "${ nombre }"`,
      Interaction.where('carga y diligencia', async actor => {
        const datos = cargarDataset(nombre);
        await actor.attemptsTo(
          Enter.theValue(datos.nombres).into(FormUI.firstName()),
          Enter.theValue(datos.email).into(FormUI.email()),
          // continuar con los demás campos del tipo DatosEstudiante
        );
      }),
    );
}
```

---

## DataTable de Cucumber

Cuando los datos vienen inline en el `.feature`, Cucumber provee un objeto `DataTable` con múltiples formas de lectura:

```gherkin
When Jorge crea un recurso en "/post" con:
  | name  | Julio |
  | role  | qa    |
```

```typescript
import { DataTable } from '@cucumber/cucumber';

When('{actor} crea un recurso en {string} con:',
  async (actor: Actor, endpoint: string, table: DataTable) => {
    const body = table.rowsHash();   // { name: 'Julio', role: 'qa' }
    await actor.attemptsTo(CrearRecurso.conBody(endpoint, body));
  },
);
```

### Variantes de DataTable

| Método | Estructura devuelta | Uso indicado |
|---|---|---|
| `table.raw()` | `string[][]` | Matriz cruda sin interpretación |
| `table.rows()` | `string[][]` sin la fila de cabecera | Cuando la primera fila es encabezado |
| `table.rowsHash()` | `Record<string, string>` | Tabla de dos columnas clave/valor |
| `table.hashes()` | `Record<string, string>[]` | Tabla con encabezado que genera lista de objetos |

Evitar DataTables con más de cinco columnas; para estructuras complejas, usar un dataset JSON externo referenciado por nombre.

---

## Generación dinámica de datos

### FakerAPI como servicio externo

El arquetipo ya consume `https://fakerapi.it/api/v2/` como endpoint de terceros para generar colecciones de entidades de prueba:

```typescript
GetRequest.to(`/api/v2/companies?_quantity=${ quantity }`);
GetRequest.to(`/api/v2/users?_quantity=10&_locale=es_CO`);
GetRequest.to(`/api/v2/addresses?_quantity=5`);
```

Adecuado para pruebas de API que requieren volumen. Requiere acceso a red; no usar en pruebas offline.

### `@faker-js/faker` local (sin red)

Si el proyecto incorpora `@faker-js/faker` como dependencia:

```typescript
import { faker } from '@faker-js/faker';
faker.locale = 'es';

const usuario = {
  nombres: faker.person.firstName(),
  apellidos: faker.person.lastName(),
  email: faker.internet.email(),
  movil: faker.phone.number('3#########'),
  direccion: faker.location.streetAddress(),
};
```

Regla de reproducibilidad: todo dato generado dinámicamente debe persistirse en disco para poder reproducir fallos:

```typescript
import * as fs from 'node:fs';
fs.writeFileSync(
  `features/web/Data/Form/_generated_${ Date.now() }.json`,
  JSON.stringify(usuario, null, 2),
);
```

Esta convención se alinea con `calidad-test-data-management` en la exigencia de seeds deterministas para reproducción de fallos.

---

## Persistencia de outputs durante la ejecución

Cuando un test extrae datos del DOM o del response y los guarda (patrón `CaptureOrderData` del arquetipo):

### Nombrado con timestamp para evitar colisiones

```typescript
const timestamp = new Date()
  .toISOString()
  .replace(/[:.]/g, '-')
  .slice(0, 19);                  // "2026-05-15T14-30-12"

const fileName = `pedido_${ timestamp }.json`;
```

### Escritura segura con creación de directorio

```typescript
import * as fs from 'node:fs';
import * as path from 'node:path';

const dir = path.resolve(process.cwd(), 'features/web/Data/orders');
if (!fs.existsSync(dir)) {
  fs.mkdirSync(dir, { recursive: true });
}

fs.writeFileSync(
  path.join(dir, fileName),
  JSON.stringify(data, null, 2),
  { encoding: 'utf-8' },
);
```

Reglas de escritura de outputs:

- Crear el directorio recursivamente si no existe.
- Usar indentación de dos espacios en JSON para legibilidad.
- Encoding UTF-8 para preservar tildes, eñes y caracteres especiales.
- Incluir timestamp en el nombre para no sobrescribir ejecuciones anteriores.
- Nunca usar `:` en nombres de archivo (incompatible con Windows).
- Agregar la ruta de outputs al `.gitignore` para no versionar artefactos de ejecución.

---

## Manejo de datos sensibles

### Reglas inviolables del arquetipo

1. No commitear credenciales reales, tokens, endpoints internos ni datos de clientes.
2. Usar valores mock en los archivos `.env.*` commiteados: `test_user`, `test_password`, `https://example.com`.
3. Los valores reales van en `.env.*.local` que no se versiona.
4. Enmascarar passwords y tokens en cualquier output de log: `password: "***"`.

### Patrón de separación mock/real

```typescript
// .env.web — commiteado, con valores mock
APP_USER=test_user
APP_PASSWORD=test_password
APP_URL=https://example.com
```

```typescript
// .env.web.local — NO commiteado, valores reales en local/CI
APP_USER=usuario_real
APP_PASSWORD=clave_real
APP_URL=https://app-real.empresa.com
```

```typescript
// step — consume variable de entorno con fallback
const user = process.env.APP_USER ?? 'test_user';
const pass = process.env.APP_PASSWORD ?? 'test_password';
```

### Enmascarado en reportes Serenity

En Tasks y Interactions, el password nunca debe aparecer en la descripción visible en el reporte:

```typescript
import { Task } from '@serenity-js/core';

export const Login = (user: string, pass: string) =>
  Task.where(
    `#actor inicia sesión con usuario ${ user }`,   // password ausente de la descripción
    Enter.theValue(user).into(LoginUI.user()),
    Enter.theValue(pass).into(LoginUI.password()),  // el valor no queda en el reporte
    Click.on(LoginUI.submit()),
  );
```

---

## Carga de datos por entorno

El arquetipo gestiona múltiples ambientes mediante archivos `.env.<modo>` cargados por `scripts/run.mjs`. Para datos que varían por ambiente, el patrón recomendado es:

```typescript
// features/web/Data/by-env.ts
const env = process.env.TEST_ENV ?? 'qa';   // qa | uat | prod-readonly

const datos = {
  qa:   { url: 'https://qa.app.com',   user: 'qa_user' },
  uat:  { url: 'https://uat.app.com',  user: 'uat_user' },
  prod: { url: 'https://app.com',      user: 'readonly_user' },
};

export const datosAmbiente = datos[env as keyof typeof datos];
```

La variable `TEST_ENV` se define en el `.env.<modo>` correspondiente. `prod-readonly` indica que solo se permiten operaciones de lectura en producción.

---

## Estructura recomendada de un dataset JSON

```json
{
  "_meta": {
    "descripcion": "Estudiante para flujo de registro feliz",
    "creadoPor": "QA Team",
    "version": 1
  },
  "datos": {
    "nombres": "Pepito",
    "apellidos": "Pérez",
    "email": "pepito@example.com",
    "genero": "Male",
    "movil": "3001234567"
  }
}
```

El campo `_meta` es opcional pero facilita entender el propósito de cada dataset sin necesidad de leer el código que lo consume.

---

## Anti-patrones

- Hardcodear datos directamente en Tasks (`Enter.theValue('Pepito').into(...)`).
- Repetir el mismo dataset en múltiples filas de `Examples` sin variación real.
- Importar JSON con rutas relativas frágiles; usar siempre `path.resolve(process.cwd(), ...)`.
- Reutilizar datasets entre escenarios que mutan estado del sistema; cada escenario debe tener su dataset independiente.
- Cargar el JSON en el nivel superior del módulo (se ejecuta en tiempo de importación, no de test).
- Commitear outputs de ejecución (`Data/orders/pedido_*.json`).
- Incluir datos sensibles reales en archivos `.env` commiteados.
- Usar DataTables con más de cinco columnas; para estructuras complejas, externalizar a JSON.

---

## Checklist de calidad por dataset

- El dataset reside en el directorio `Data/` del módulo que lo consume.
- Existe una interfaz TypeScript que describe la estructura del dataset.
- El loader usa `path.resolve(process.cwd(), ...)` y no rutas relativas frágiles.
- El `Scenario Outline` referencia el dataset por nombre, sin datos inline.
- Los datos sensibles están en `.env.*` y no en JSON commiteados.
- Los outputs de ejecución usan timestamp en el nombre y están en `.gitignore`.
- Si se usa un generador faker, los datos generados se persisten para reproducción de fallos.
- No hay credenciales reales hardcodeadas en ningún archivo del repositorio.
