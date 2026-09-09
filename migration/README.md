# Herramientas de migración del Chapter Calidad → Mimir

Tooling para publicar y mantener los assets de `chapters/calidad/` en la plataforma
**Mimir** (Knowledge Registry, API REST).

> ⚠️ **Qué se versiona de esta carpeta y qué no.**
> **Sí:** los scripts y este README. Son código con historia, y perderlos obligaba a
> reescribirlos de memoria.
> **No:** el estado operativo y los reportes — `sync-state*.json`, `id-map.json` y
> `report*.json` están en el `.gitignore`. Cambian en cada corrida, son regenerables y
> versionarlos llenaría cada diff de ruido.
>
> Conserva los archivos de estado entre corridas aunque no estén en git: **son la
> memoria de qué está publicado en Mimir**. Sin ellos, `--sync` no sabe qué existe y
> hay que rehacer el baseline.

---

## 1. Requisitos

- **Python 3.9+** (sin dependencias externas; solo stdlib: `urllib`, `json`, `hashlib`).
- La carpeta `migration/` ubicada en la **raíz del repo**:
  ```
  pragma-ai-hub-knowledge-core/
  ├── chapters/calidad/        <- tu dominio (esto sí se commitea)
  └── migration/               <- esta carpeta (NO se commitea; pégala aquí)
      ├── migrate_to_mimir.py
      └── ...
  ```
  Los scripts calculan `REPO_ROOT` como el directorio padre de `migration/`. Si la
  pones en otro lugar, no encontrará `chapters/calidad/`.

## 2. Autenticación (variables de entorno)

```bash
export MIMIR_BASE_URL="https://api-mimir-dev.pragma.com.co"   # DEV (cambia para PROD)
export MIMIR_TOKEN="<JWT sin la palabra 'Bearer'>"            # token Cognito
# alternativa para consumidores externos:
# export MIMIR_API_KEY="mk_xxxxxxxx"
```

- El **token expira (~1 h)**. Si ves `401 Invalid or expired token`, pide uno nuevo y
  re-exporta `MIMIR_TOKEN`.
- Cómo obtener el token: desde el front de Mimir (DevTools → Network → cualquier
  request → header `authorization: Bearer <token>`), copia solo el JWT (sin `Bearer `).

---

## 3. Scripts y para qué sirve cada uno

| Script | Propósito | ¿Cuándo se corre? |
|--------|-----------|-------------------|
| `migrate_to_mimir.py` | Publica/actualiza assets en Mimir (dry-run, probe, apply, sync) | Cada vez que migras o sincronizas |
| `normalize_source_ids.py` | (b1) Normaliza `id:` a `calidad-*` y reescribe `[[links]]` en la fuente | Una sola vez (ya aplicado). Reusar si entran assets sin prefijo |
| `consolidate_templates.py` | (b3) Convierte `.tpl/.sh` de bundles en un `references/templates.md` | Una sola vez (ya aplicado). Reusar si reaparecen no-`.md` |
| `fix_template_refs.py` | (b3.1) Reapunta referencias `templates/*.tpl` al `templates.md` | Junto con `consolidate_templates.py` |
| `seo_integrate.py` | (b5) Integró los assets SEO de `entrada/` (estructura inicial) | Histórico (ya aplicado; el SEO final es un bundle `calidad-seo`) |

Los scripts `normalize_source_ids`, `consolidate_templates`, `fix_template_refs` y
`seo_integrate` son **transformaciones de contenido** que ya se aplicaron a
`chapters/calidad/`. Se conservan para reproducibilidad y por si entran assets nuevos
que necesiten el mismo tratamiento. El día a día es `migrate_to_mimir.py`.

---

## 4. `migrate_to_mimir.py` — uso

Todos los modos son mutuamente excluyentes; sin modo = `--dry-run`.

```bash
# (a) PLAN sin tocar la red: clasifica assets y escribe migration/report.json
python3 migration/migrate_to_mimir.py --dry-run

# (b) PROBE: crea 1 doc de prueba y reporta el id que asigna Mimir (diagnóstico)
python3 migration/migrate_to_mimir.py --probe

# (c) APPLY: crea TODOS los assets desde cero (baseline). Escribe id-map.json y sync-state.json
python3 migration/migrate_to_mimir.py --apply

# (d) SYNC: incremental. Crea nuevos, actualiza cambiados, omite iguales
python3 migration/migrate_to_mimir.py --sync

# (e) SYNC + PRUNE: además borra en Mimir lo que ya no está en la fuente
python3 migration/migrate_to_mimir.py --sync --prune

# (f) REINDEX: fuerza reindexación tocando todos los documentos (ver sección 8)
python3 migration/migrate_to_mimir.py --reindex

# Filtrar a un subconjunto (substring del localId), útil para pruebas:
python3 migration/migrate_to_mimir.py --apply --only k6-brownfield
python3 migration/migrate_to_mimir.py --sync --only seo
```

Flags:

| Flag | Default | Descripción |
|------|---------|-------------|
| `--dry-run` | (default) | No toca la red; escribe `report.json` |
| `--apply` | — | Migración completa desde cero (baseline) |
| `--sync` | — | Sincronización incremental por hash |
| `--reindex` | — | Fuerza reindexación tocando todos los documentos (version bump, sin cambio de contenido) |
| `--probe` | — | Diagnóstico de estrategia de id |
| `--prune` | off | Con `--sync`: borra huérfanos en Mimir |
| `--only <csv>` | — | Solo assets cuyo `localId` contenga alguno de los textos |
| `--state <ruta>` | `migration/sync-state.json` | Estado para `--sync` y `--reindex` |
| `--report <ruta>` | `migration/report.json` | Reporte de salida |

### Archivos de estado que genera

- **`id-map.json`** — `{ "calidad-<id>": "<uuid-mimir>" }`. Útil para la CLI (mapear
  `[[calidad-id]]` ↔ UUID) y para limpiar (borrar por UUID).
- **`sync-state.json`** — `{ "calidad-<id>": { "uuid", "hash" } }`. Baseline del
  `--sync`: el `hash` es de la fuente; si cambia, el asset se actualiza. **Consérvalo
  junto con `migration/`** entre corridas (es la memoria de qué ya está publicado).

---

## 5. Flujos típicos

### 5.1 Primera migración a un entorno nuevo (DEV o PROD)

```bash
export MIMIR_BASE_URL="https://api-mimir-<env>.pragma.com.co"
export MIMIR_TOKEN="<token fresco>"

python3 migration/migrate_to_mimir.py --dry-run     # revisa el plan
python3 migration/migrate_to_mimir.py --apply       # crea todo + escribe id-map/sync-state
```

El `--apply`:
1. Crea los **stacks** que falten en el chapter (karate, k6, appium, playwright).
2. Crea cada asset (single y bundle), sube los archivos de los bundles.
3. Escribe `id-map.json` y `sync-state.json`.

> Pre-requisito en el entorno: que exista el **chapter `calidad`**. Si no existe, créalo
> (SUPER_ADMIN) o pídelo al equipo Mimir. Los stacks sí los crea el script.

### 5.2 Actualización incremental (lo que pediste)

Cuando creas una rama que **agrega** o **cambia** assets en `chapters/calidad/`:

```bash
export MIMIR_TOKEN="<token fresco>"
python3 migration/migrate_to_mimir.py --sync
```

El `--sync` compara el hash de cada asset contra `sync-state.json` y:
- **localId nuevo** → lo **crea**.
- **hash cambiado** → lo **actualiza** (PUT con version bump automático + `changeType=patch`).
- **igual** → lo **omite**.
- **en estado pero ya no en la fuente** → lo **reporta** (y lo borra si pasas `--prune`).

Es decir: toca **exactamente** lo que agregaste/cambiaste. Al terminar, `sync-state.json`
queda actualizado para la siguiente vez.

### 5.3 Re-migrar limpio (si el entorno quedó inconsistente)

El migrador **no es idempotente en `--apply`**: re-correr `--apply` crea duplicados
(Mimir asigna un UUID nuevo en cada create). Para empezar de cero:

```bash
# borrar lo migrado usando id-map.json
python3 - <<'PY'
import os, json, urllib.request
base=os.environ["MIMIR_BASE_URL"].rstrip("/"); tok=os.environ["MIMIR_TOKEN"]
idmap=json.load(open("migration/id-map.json"))
for lid,uuid in idmap.items():
    req=urllib.request.Request(f"{base}/api/v1/chapters/calidad/documents/{uuid}",
        data=json.dumps({"reason":"reset"}).encode(), method="DELETE",
        headers={"Authorization":f"Bearer {tok}","Content-Type":"application/json"})
    try: urllib.request.urlopen(req); print("del",lid)
    except Exception as e: print("err",lid,e)
PY
# luego volver a aplicar
python3 migration/migrate_to_mimir.py --apply
```

---

## 6. Contrato real de Mimir (aprendido en campo)

- **id = UUID** asignado por Mimir; ignora cualquier `id` de la fuente. Por eso el
  `localId` (id `calidad-*`) se manda como **campo de frontmatter** (Mimir preserva
  campos extra) y queda en `id-map.json` para mapear.
- **`name` y `description` son obligatorios** en el entry file de un bundle (estándar
  Agent Skills). El script envía `name = calidad-<id>` para skills.
- **Los stacks deben existir** antes de crear docs con ese stack (el script los crea con
  `{stackId, stackName}` — ojo: el OpenAPI dice `{id, name}`, está desactualizado).
- **Schema de bundle (`skill`)**: solo `references/*.md|.mmd`, `scripts/*.py|.sh|.js|.ts`,
  `assets/*.yaml|.dart|.md`, sin subdirectorios, `allowExtraFiles:false`. Tras la
  consolidación b3 (todo `.md`), los bundles encajan nativo y no requieren reestructura.
- **Campos extra preservados** (`localId`, `sourcePath`, `bundleManifest`): la CLI puede
  usarlos para resolver `[[calidad-id]]` ↔ UUID al instalar en los IDEs.
- Docs chapter y stack-scoped van al **mismo endpoint**
  `POST /api/v1/chapters/calidad/documents` (el `stack` es metadata).
- **Hooks** (`type: hook`) NO se migran: Mimir no tiene ese tipo (son de Kiro).
- **Staging de archivos de bundle** (detectado 2026-07-23): `PUT /api/v1/documents/{id}/files/{path}`
  responde `"File ... staged"` — el archivo queda en staging y solo se **materializa
  con el siguiente update del documento** (PUT del doc). Archivos nuevos (p.ej. las
  `references/` de un bundle recién creado) no aparecen hasta ese commit. El script ya
  lo maneja: tras subir archivos hace un `update_document(reason="commit bundle files")`;
  por eso los bundles nuevos nacen en v1.0.1. Síntoma si regresa: `bundleFileCount`
  bajo y `GET .../files` solo lista `SKILL.md`.
- **El listado va rezagado** (detectado 2026-08-11): `GET /chapters/{id}/documents` puede
  reportar menos documentos de los que existen — se vio 100 con 102 reales, verificados
  uno a uno por `GET .../documents/{uuid}`. **Nunca usar el listado como prueba de que
  algo falta**; confirmar por uuid antes de concluir.
- **El PUT reemplaza el frontmatter, no lo mezcla** (verificado 2026-08-11 moviendo 11
  docs de `stack: funcional` a chapter-scoped): si el payload no lleva `stack`, Mimir lo
  deja en `default`. Es lo que permite reclasificar assets sin borrarlos.
- **El migrador nunca borra archivos de un bundle.** Si una `reference` se mueve a otro
  bundle, la copia vieja **permanece** en el documento anterior y el bundle queda con más
  archivos que la fuente. Es divergencia silenciosa: la copia congelada sigue siendo
  legible para el agente. Verificar con el byte-check de la sección 9 tras cualquier
  movimiento, y eliminar a mano lo que sobre.
- **Un ERR en un NEW no siempre deja documento.** El uuid que aparece en el mensaje de
  error puede no existir: comprobar con `GET` antes de reintentar. Si existe, el reintento
  duplica; si no existe (404), el reintento es seguro. Ambos casos se han dado.
- **El token vive ~1 hora.** Una ola grande puede cortarse a mitad con 401. No es grave:
  el estado se escribe asset por asset, así que lo que falló conserva su hash anterior y
  la corrida siguiente lo reintenta sola. Sí exige byte-check del documento que estaba en
  curso, que pudo quedar con archivos en staging sin commitear.


---

## 7. Convenciones de contenido aplicadas a `chapters/calidad/`

- Todo asset tiene `id: calidad-*` (prefijo de chapter).
- Cross-asset → `[[calidad-id]]`; intra-skill (a un reference hermano) → link relativo
  `[nombre](nombre.md)`.
- Sin archivos de contenido en extensiones distintas a `.md`: las plantillas viven en
  `references/templates.md` (una sección por archivo destino, con su ruta lógica).
- Conceptos transversales en `skills/_all/` (p.ej. `calidad-accessibility-testing`,
  `calidad-visual-regression`, y el bundle `calidad-seo` con sus 8 dimensiones como
  references); los stacks enlazan a la política.

## 8. Reindexación

Cuando Mimir necesita **reconstruir su índice** (búsqueda / discovery) sin que haya
cambiado el contenido, hay que "tocar" cada documento para disparar el evento de
actualización. El modo `--reindex` lo hace por ti:

```bash
export MIMIR_BASE_URL="https://api-mimir.pragma.com.co"
export MIMIR_TOKEN="<token fresco>"
python3 migration/migrate_to_mimir.py --reindex
```

### Cómo funciona

- Recorre todos los documentos del baseline (`sync-state.json`) y, por cada uno, hace un
  **update** (`PUT`) re-enviando su **contenido actual** con `reason: "reindex"`.
- Mimir **acepta el update aunque el contenido no cambie**: no se agregan espacios, puntos
  ni caracteres. El cuerpo queda **idéntico** al del repo — no hay divergencia repo ↔ Mimir.
- Requiere `sync-state.json` (el baseline con los `uuid`). Si no existe, corre `--apply` antes.

### Efecto colateral: version bump

Cada documento **sube su versión de patch** (p.ej. `1.0.0 → 1.0.1`). Es inevitable: la
única forma de "editar para reindexar" es generar una nueva versión. El contenido no
cambia, solo el número de versión y el historial (queda una entrada `reason: "reindex"`).

### Notas

- Es **idempotente en contenido** pero no en versión: correrlo N veces sube la versión N
  veces. Úsalo solo cuando de verdad necesites reindexar.
- No modifica `id-map.json` ni `sync-state.json` (los `uuid` y los hashes de fuente no
  cambian), así que un `--sync` posterior sigue siendo consistente (verá los hashes
  iguales y omitirá todo; la versión bumpeada no le afecta).
- Admite `--only` para reindexar solo un subconjunto:
  `python3 migration/migrate_to_mimir.py --reindex --only seo,accessibility`.

---

## 9. Byte-check tras sincronizar (obligatorio si se movieron archivos)

El sync reporta éxito aunque el bundle remoto haya quedado distinto de la fuente. Comparar
explícitamente:

```python
# por cada bundle: GET /api/v1/documents/{uuid}/files
# remotos = {f["relativePath"] for f in files if not f["isDirectory"]}
# locales = {"SKILL.md"} | {f"references/{p.name}" for p in (base/"references").glob("*.md")}
# diff    = locales ^ remotos      -> debe ser vacio
```

Cuidado con dos detalles: el listado incluye una entrada de **directorio** (`references/`
con `isDirectory: true`) que no cuenta como archivo, y lo que sobra en remoto casi siempre
es una `reference` movida a otro bundle que nadie borró.

## 10. Conocimiento de cuenta

Mimir tiene **cuatro niveles**, no dos. Hoy el chapter usa uno.

| Nivel | Endpoint |
|---|---|
| global | `/api/v1/global/documents` |
| chapter | `/api/v1/chapters/{chapterId}/documents` |
| cuenta | `/api/v1/accounts/{accountId}/documents` |
| proyecto | `/api/v1/accounts/{accountId}/frentes/{frenteId}/projects/{projectId}/documents` |

**La jerarquía real incluye un nivel `frentes` que el OpenAPI de `entrada/` no documenta.**
Como con `stackId`/`stackName`, la fuente de verdad es la API, no el contrato publicado.

Puntos que cambian cómo se modela:

- **Un documento de cuenta sigue exigiendo `chapter` y `stack`** (responde 422 sin ellos).
  El conocimiento de cuenta no reemplaza al del chapter: lo **especializa**.
- **Los tipos son otros**: además de los del chapter, el nivel de cuenta acepta
  `decisions`, `references` y `limits`. El enum del OpenAPI está incompleto.
- **En la práctica el conocimiento vive en el proyecto**, no en la cuenta: la cuenta 608
  tiene 0 documentos y el proyecto SM0055 los tiene todos.
- **Herencia explícita**: `extensible`, `overridable`, `pragma_extends` (id del padre) y
  `pragma_override: full | merge`, más `GET /documents/inheritable` y
  `GET /documents/{id}/derivatives` para navegarla.

### Qué va a cuenta y qué no

Va a cuenta lo que el cliente **impone** y el chapter no debe adoptar: nomenclatura de
tags, prefijos de trazabilidad del ALM, idioma de los steps, versiones fijadas,
restricciones de su pipeline, decisiones de arquitectura de su suite. Se modela como
documento que declara en su `Purpose` qué asset del chapter especializa.

**Nunca va a cuenta** el conocimiento generalizable: si sirve a más de un cliente, es del
chapter, escrito en genérico. Y **nunca, en ningún nivel**, credenciales, identificadores
de dispositivo, equipos de firma ni hostnames internos: eso vive en el `.env` del proyecto.

### Fuente y herramienta

La fuente vive en `accounts/{cliente}/{chapter}/*.md` en la raíz del repo, **excluida de
git** (`.git/info/exclude`): el core no lleva nombres de cliente. Se sincroniza con
`sync_account.py`, separado del migrador del chapter para que los baselines no se mezclen:

```bash
python3 migration/sync_account.py --client mercantil --chapter calidad \
    --account 608 --frente default --project SM0055 --dry-run
```

Estado propio en `sync-state-account-{cliente}-{chapter}.json`. **No implementa borrado**
a propósito: retirar conocimiento de cuenta se hace a mano y con confirmación.

### Plantilla (seguir la que ya existe en el proyecto)

En inglés, con `stack: default`, `required: true` y `description: "ND"`.

- `limits` → Identification Context (con `**Client:**`) · The Restriction, con tabla
  *Global status* contra *estado en el cliente* y la razón del cambio · Evidence and
  Impact · Warning Signs · Workarounds and Mitigations · Maintainers.
- `references` → Purpose, declarando qué documento del chapter extiende ·
  `**Specialization reason:**` · Scope of Application · Step by Step / Guidelines.
- `decisions` → Context · Decision · Rationale · Consequences · Warning Signs.

**Enlaces**: usar `[[calidad-*]]`, que resuelve porque nuestros documentos conservan
`localId` en el frontmatter. Los documentos preexistentes de la cuenta usan un esquema de
paths (`[[references/backend/karate/v1/...]]`) que **no resuelve contra nada**: son
enlaces muertos heredados de la migración que los creó.

## 11. Alcance de permisos

El token de Mauro es **SUPER_ADMIN**. El alcance permitido es el de quien crea
conocimiento del chapter Calidad, ni un endpoint más. Prohibido, aunque el token lo
permita: crear, archivar o borrar cuentas, chapters, frentes y proyectos; tocar otros
chapters o el nivel global; gestionar usuarios, roles o curadores; cualquier DELETE o
`--prune`. Ante la duda, preguntar antes de ejecutar.

**Nunca combinar `--only` con `--prune`**: `--only` filtra la fuente, así que todo lo demás
aparece como huérfano y `--prune` borraría el chapter entero.
