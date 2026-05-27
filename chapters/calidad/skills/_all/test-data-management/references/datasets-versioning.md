# Versionado de Datasets

Los datasets sintéticos y anonimizados se versionan como cualquier otro artefacto. Tres dimensiones: almacenamiento, naming y regeneración.

## Cuándo versionar un dataset

- El dataset tiene tamaño no trivial (>1MB) y se reutiliza en múltiples corridas.
- La reproducibilidad de los tests depende de tener el mismo dataset exacto.
- El dataset cambia con cierta frecuencia (cada release o cada cambio de esquema).
- Hay valor en poder volver a una versión previa para reproducir bugs históricos.

Datasets triviales (<10 registros, helper inline) no requieren versionado.

## Almacenamiento por tamaño

| Tamaño del dataset | Almacenamiento recomendado          | Notas                                       |
|--------------------|-------------------------------------|---------------------------------------------|
| <100 KB            | Repositorio directo (`fixtures/`)   | Texto puro, JSON pequeño                    |
| 100 KB - 50 MB     | Git LFS                             | Binarios, datasets medianos                 |
| 50 MB - 5 GB       | DVC + remote (S3/GCS)               | DVC versiona pointers en git                |
| >5 GB              | S3/GCS con tags de versión          | Acceso directo, `s3://bucket/datasets/...`  |

### Git LFS

```bash
git lfs install
git lfs track "fixtures/*.json.gz"
git add .gitattributes fixtures/users-10k.json.gz
git commit -m "test: add users 10k fixture"
```

Pros: integrado con git, pull automático.
Cons: cuotas en GitHub (1GB free), tracking byte-exacto.

### DVC

```bash
dvc init
dvc remote add -d s3remote s3://my-bucket/dvc
dvc add fixtures/users-1m.json
git add fixtures/users-1m.json.dvc fixtures/.gitignore
git commit -m "test: add users 1m fixture via DVC"
dvc push
```

Pros: datasets grandes, soporte para múltiples remotes, integra con pipelines ML/data.
Cons: requiere DVC instalado en CI, curva de aprendizaje.

### S3 con tags

```bash
aws s3 cp users-10m.json s3://qa-datasets/v1.2.0/users-10m.json \
  --tagging "purpose=perf&schema=v2&hash=abc123"
```

En CI, descarga por versión:

```bash
aws s3 cp s3://qa-datasets/v1.2.0/users-10m.json ./fixtures/
```

## Naming

Convención del chapter: `dataset-v{major.minor.patch}-{purpose}-{schemaHash}.{ext}`.

Ejemplos:

- `dataset-v1.0.0-perf-users-a3f1.json` — performance, 10K usuarios, esquema hash `a3f1`.
- `dataset-v2.1.0-security-payloads-b9c2.json` — payloads adversariales para suite security.
- `dataset-v1.3.0-e2e-fixtures-c4d8.tar.gz` — fixtures e2e bundle.

Reglas:

- `major` cambia cuando cambia el **esquema** (campos añadidos/removidos/renombrados).
- `minor` cambia cuando cambian las reglas de generación (mismo esquema, distintos datos).
- `patch` para fix puntual (corregir error en un campo, regenerar con seed correcto).
- `schemaHash` (primeros 4 chars de hash SHA-256 del schema JSON) ayuda a detectar drift.

## Regeneración cuando cambia el esquema

Cuando el esquema del dominio cambia (nueva columna, columna renombrada, tipo distinto), los datasets quedan obsoletos. Política:

1. **Script de regeneración versionado** — cada dataset tiene un script `scripts/generate-{dataset}.{js|py|java}` en el repo. Reproduce el dataset desde cero con `FAKER_SEED` fijo.
2. **CI valida frescura** — un job nightly compara `hash(schema actual)` vs `schemaHash en filename`. Si difiere, alerta.
3. **Pull-request de regeneración** — el dev abre PR con: script actualizado, nuevo dataset, bump de versión, changelog.
4. **Datasets obsoletos** — se mantienen 2 versiones (current + previous) para permitir bisect de bugs. Versiones más viejas se archivan a `archive/` o se eliminan.

Snippet de script (`scripts/generate-users-perf.ts`):

```typescript
import { faker } from '@faker-js/faker/locale/es_CO';
import * as fs from 'fs';

const SEED = Number(process.env.FAKER_SEED || 12345);
const COUNT = Number(process.env.COUNT || 10000);
const OUT = process.argv[2] || './fixtures/users-perf.json';

faker.seed(SEED);

const users = Array.from({ length: COUNT }, () => ({
  id: faker.string.uuid(),
  email: faker.internet.email({ provider: 'example.com' }),
  phone: faker.phone.number('+57 3## ### ####'),
  createdAt: faker.date.recent({ days: 365 }).toISOString(),
}));

fs.writeFileSync(OUT, JSON.stringify(users));
console.log(`Generated ${COUNT} users to ${OUT} (seed=${SEED})`);
```

Invocación:

```bash
FAKER_SEED=12345 COUNT=10000 npx ts-node scripts/generate-users-perf.ts \
  fixtures/dataset-v1.0.0-perf-users-a3f1.json
```

## Manifest por dataset

Cada dataset versionado tiene un `manifest.json` adyacente:

```json
{
  "name": "users-perf",
  "version": "1.0.0",
  "purpose": "performance",
  "schemaHash": "a3f1",
  "recordCount": 10000,
  "generator": "scripts/generate-users-perf.ts",
  "seed": 12345,
  "generatedAt": "2026-05-27T00:00:00Z",
  "locale": "es_CO",
  "piiPolicy": "synthetic-only"
}
```

Esto permite auditoría: cualquiera puede saber cómo se generó y reproducirlo.

## Cleanup de versiones viejas

Política por defecto:

- Mantener `current` y `previous` (2 últimas versiones) en hot storage.
- Versiones anteriores: archivar a cold storage (S3 Glacier) por 1 año.
- Después de 1 año: eliminar salvo retención regulatoria.

## Restricciones

- No commitees datasets sin manifest.
- No regeneres un dataset sin bumpear versión: rompe reproducibilidad.
- No uses datasets `latest` sin pin de versión en CI: te muerde en regresiones.
- Para datasets que cubren múltiples ambientes (dev/staging), versiona uno por ambiente.
- Encadena con `[[calidad-test-evidence-and-traceability]]` para que el reporte indique versión exacta usada.
