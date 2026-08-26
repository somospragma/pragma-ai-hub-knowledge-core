#!/usr/bin/env python3
"""
Migrador del chapter Calidad (knowledge-core) a la plataforma Mimir.

Lee chapters/calidad/, mapea cada asset al modelo de Mimir y lo publica vía la
API REST. Soporta documentos single-file y bundle (SKILL.md + references/).

Sin dependencias externas: solo stdlib (urllib + parser de frontmatter acotado
al subconjunto YAML que usamos en el repo).

Modos:
  --dry-run   (default) No toca la red. Imprime el plan y escribe un reporte JSON.
  --probe     Crea UN documento de prueba y reporta el id que asigna Mimir vs el
              slug del title (para confirmar la estrategia de ids / [[links]]).
  --apply     Ejecuta la migración real contra Mimir.

Auth (variables de entorno):
  MIMIR_BASE_URL   default http://localhost:3002
  MIMIR_TOKEN      Bearer JWT  -> Authorization: Bearer <token>
  MIMIR_API_KEY    API key     -> x-api-key: <key>   (alternativa a TOKEN)

Uso:
  python3 migration/migrate_to_mimir.py --dry-run
  MIMIR_TOKEN=... python3 migration/migrate_to_mimir.py --apply
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------- #
# Configuración fija del chapter a migrar
# --------------------------------------------------------------------------- #
REPO_ROOT = Path(__file__).resolve().parent.parent
CHAPTER_ID = "calidad"
CHAPTER_DIR = REPO_ROOT / "chapters" / CHAPTER_ID

# type local -> soportado por el enum DocumentType de Mimir
MIMIR_TYPES = {"steering", "skill", "workflow", "prompt", "agent", "convencion"}
# tipos que NO migramos (específicos de un IDE)
SKIP_TYPES = {"hook"}

# extensiones de texto que subimos como utf-8 dentro de un bundle
TEXT_EXTS = {".md", ".tpl", ".sh", ".properties", ".txt", ".json", ".yaml", ".yml", ".gitkeep"}

# schema bundle real del type def `skill` en Mimir (dir -> extensiones permitidas).
# Usado para detectar bundles incompatibles ANTES de subir (evita estados parciales).
BUNDLE_ALLOWED = {
    "references": {".md", ".mmd"},
    "scripts": {".py", ".sh", ".js", ".ts"},
    "assets": {".yaml", ".dart", ".md"},
}


# --------------------------------------------------------------------------- #
# Parser de frontmatter (subconjunto YAML usado en el repo)
# --------------------------------------------------------------------------- #
def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Devuelve (frontmatter_dict, body). Frontmatter delimitado por '---'."""
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines()
    if lines[0].strip() != "---":
        return {}, text
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, text
    fm: dict = {}
    for raw in lines[1:end]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", raw)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        fm[key] = _parse_scalar(val)
    body = "\n".join(lines[end + 1:]).lstrip("\n")
    return fm, body


def _parse_scalar(val: str):
    if val == "":
        return ""
    # array en línea: [a, b, c]
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1].strip()
        if not inner:
            return []
        return [_unquote(x.strip()) for x in inner.split(",")]
    if val in ("true", "false"):
        return val == "true"
    return _unquote(val)


def _unquote(s: str) -> str:
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    return s


# --------------------------------------------------------------------------- #
# Modelo de asset
# --------------------------------------------------------------------------- #
@dataclass
class Asset:
    local_id: str
    type: str
    scope: str            # chapter | stack (global/project no existen en calidad hoy)
    entry_path: Path      # SKILL.md para bundle, o el .md para single
    is_bundle: bool
    frontmatter: dict
    body: str
    bundle_files: list[Path] = field(default_factory=list)  # rutas absolutas (excluye entry)
    category: str | None = None
    # plan de subida: lista de (mimir_rel_path, source_path) tras reestructurar
    upload_plan: list[tuple[str, Path]] = field(default_factory=list)
    # manifiesto de paths reubicados (mimir_rel -> original_rel) para que la CLI restaure
    manifest: dict[str, str] = field(default_factory=dict)

    # asignado tras crear en Mimir
    mimir_uuid: str | None = None


def mimir_id(local_id: str) -> str:
    """Garantiza prefijo de chapter: todo id de calidad empieza con 'calidad-'."""
    if local_id.startswith(f"{CHAPTER_ID}-"):
        return local_id
    return f"{CHAPTER_ID}-{local_id}"


# mapa global id-local-original -> id-normalizado (calidad-*), para reescribir [[links]]
RENAME_MAP: dict[str, str] = {}


def rewrite_links(text: str) -> str:
    """Reescribe [[old-id]] -> [[calidad-...]] segun RENAME_MAP. Idempotente."""
    def repl(m):
        target = m.group(1)
        return f"[[{RENAME_MAP.get(target, mimir_id(target))}]]"
    return re.sub(r"\[\[([a-z0-9][a-z0-9-]*)\]\]", repl, text)


def humanize(local_id: str) -> str:
    """calidad-delivery-gate-contract -> 'Delivery Gate Contract' (sin prefijo chapter)."""
    s = local_id
    if s.startswith(f"{CHAPTER_ID}-"):
        s = s[len(CHAPTER_ID) + 1:]
    return " ".join(w.capitalize() for w in s.replace("_", "-").split("-") if w)


def first_h1(body: str) -> str | None:
    for line in body.splitlines():
        m = re.match(r"^#\s+(.+?)\s*$", line)
        if m:
            return m.group(1).strip()
    return None


def slugify(title: str) -> str:
    s = title.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


# --------------------------------------------------------------------------- #
# Descubrimiento de assets
# --------------------------------------------------------------------------- #
def discover_assets() -> tuple[list[Asset], list[str]]:
    assets: list[Asset] = []
    warnings: list[str] = []

    # 1) raíces de bundle = directorios con SKILL.md
    bundle_roots = {p.parent for p in CHAPTER_DIR.rglob("SKILL.md")}

    def under_bundle(path: Path) -> Path | None:
        for root in bundle_roots:
            if root in path.parents:
                return root
        return None

    # 2) bundles
    for root in sorted(bundle_roots):
        entry = root / "SKILL.md"
        fm, body = parse_frontmatter(entry.read_text(encoding="utf-8"))
        a = _build_asset(fm, body, entry, is_bundle=True, warnings=warnings)
        if a is None:
            continue
        a.bundle_files = sorted(
            p for p in root.rglob("*") if p.is_file() and p != entry
        )
        compute_upload_plan(a)
        a.category = _category_for(root)
        assets.append(a)

    # 3) documentos single-file (no SKILL.md, no dentro de un bundle)
    for md in sorted(CHAPTER_DIR.rglob("*.md")):
        if md.name == "SKILL.md":
            continue
        if under_bundle(md):
            continue
        fm, body = parse_frontmatter(md.read_text(encoding="utf-8"))
        if not fm.get("type"):
            continue  # no es un asset versionable (README, etc.)
        a = _build_asset(fm, body, md, is_bundle=False, warnings=warnings)
        if a is None:
            continue
        a.category = _category_for(md.parent)
        assets.append(a)

    # mapa global para reescribir [[links]] a ids normalizados (calidad-*)
    RENAME_MAP.clear()
    for a in assets:
        RENAME_MAP[a.local_id] = mimir_id(a.local_id)

    return assets, warnings


def _build_asset(fm: dict, body: str, entry: Path, is_bundle: bool,
                 warnings: list[str]) -> Asset | None:
    rel = entry.relative_to(REPO_ROOT)
    typ = fm.get("type")
    if typ in SKIP_TYPES:
        warnings.append(f"SKIP (tipo no soportado por Mimir: {typ}): {rel}")
        return None
    if typ not in MIMIR_TYPES:
        warnings.append(f"SKIP (tipo desconocido '{typ}'): {rel}")
        return None
    scope = fm.get("scope", "chapter")
    local_id = fm.get("id") or slugify(entry.stem)
    return Asset(
        local_id=local_id, type=typ, scope=scope, entry_path=entry,
        is_bundle=is_bundle, frontmatter=fm, body=body,
    )


def _category_for(directory: Path) -> str | None:
    """Plataforma/carpeta como categoría (p.ej. appium, k6). Ignora _all."""
    try:
        rel = directory.relative_to(CHAPTER_DIR)
    except ValueError:
        return None
    parts = [p for p in rel.parts if p not in ("references",)]
    # parts[0] = skills|prompts|workflows|steering ; parts[1] = plataforma/stack
    if len(parts) >= 2 and parts[1] != "_all":
        return parts[1]
    return None


# --------------------------------------------------------------------------- #
# Construcción del request para Mimir
# --------------------------------------------------------------------------- #
def _dir_for_ext(ext: str) -> str:
    if ext in BUNDLE_ALLOWED["scripts"]:
        return "scripts"
    if ext in (".yaml", ".dart"):
        return "assets"
    return "references"


def compute_upload_plan(a: Asset) -> None:
    """Reestructura los archivos del bundle para encajar en el schema de Mimir.

    Schema: solo dirs references/(.md,.mmd), scripts/(.py,.sh,.js,.ts),
    assets/(.yaml,.dart,.md), sin subdirectorios. Para lo que no encaja:
      - .sh/.py/.js/.ts -> scripts/<plano>  (extension nativa, sin perdida)
      - .yaml/.dart      -> assets/<plano>
      - resto (.tpl, .properties, .gitkeep, .md anidado) -> <dir>/<plano>.md
    Path original aplanado con '__'. Se guarda manifiesto mimir_rel -> original_rel
    para que la CLI restaure la estructura/nombres reales al instalar.
    """
    plan: list[tuple[str, Path]] = []
    manifest: dict[str, str] = {}
    for f in a.bundle_files:
        orig = bundle_rel(a, f)
        parts = orig.split("/")
        ext = f.suffix if f.suffix else f.name
        top = parts[0]
        # ya compatible: references|scripts|assets en primer nivel, ext valida, sin anidar
        if (top in BUNDLE_ALLOWED and ext in BUNDLE_ALLOWED[top] and len(parts) == 2):
            plan.append((orig, f))
            continue
        # reubicar: quita el dir de primer nivel redundante antes de aplanar
        target_dir = _dir_for_ext(ext)
        rest = orig[len(top) + 1:] if top in BUNDLE_ALLOWED else orig
        flat = rest.replace("/", "__")
        if ext not in BUNDLE_ALLOWED[target_dir]:
            flat = flat + ".md"  # ext no permitida -> envolver como .md (reversible)
        mimir_rel = f"{target_dir}/{flat}"
        plan.append((mimir_rel, f))
        manifest[mimir_rel] = orig
    a.upload_plan = plan
    a.manifest = manifest


def bundle_incompatibilities(a: Asset) -> list[str]:
    """Archivos del bundle que NO encajan en el schema bundle de Mimir."""
    bad = []
    for f in a.bundle_files:
        rel = bundle_rel(a, f)
        parts = rel.split("/")
        top = parts[0]
        ext = f.suffix if f.suffix else f.name
        allowed = BUNDLE_ALLOWED.get(top)
        if allowed is None or ext not in allowed or len(parts) > 2:
            bad.append(rel)
    return bad


def normalize_stack(fm: dict) -> str | None:
    stack = fm.get("stack")
    if stack is None or stack == "":
        return None
    if isinstance(stack, list):
        if len(stack) == 0:
            return None
        return str(stack[0])
    return str(stack)


def build_create_request(a: Asset) -> dict:
    fm = a.frontmatter
    norm_id = mimir_id(a.local_id)
    title = fm.get("title") or first_h1(a.body) or humanize(a.local_id)
    description = fm.get("description") or ""
    front = {
        "title": title,
        "type": a.type,
        "chapter": CHAPTER_ID,
        "tags": fm.get("tags") or [],
        "description": description,
        # id normalizado con prefijo de chapter (todo calidad empieza con 'calidad-')
        "localId": norm_id,
        # Mimir preserva campos extra; sourcePath permite a la CLI trazar el origen.
        "sourcePath": a.entry_path.relative_to(REPO_ROOT).as_posix(),
    }
    # 'name' es obligatorio en el entry file de bundle (estandar Agent Skills);
    # lo ponemos en todos los skills para identidad consistente.
    if a.type == "skill":
        front["name"] = norm_id
    stack = normalize_stack(fm)
    if stack:
        front["stack"] = stack
    if a.category:
        front["category"] = a.category
    if a.manifest:
        front["bundleManifest"] = a.manifest
    # campos de herencia opcionales
    for k in ("extensible", "overridable", "pragma_extends", "pragma_override"):
        if k in fm:
            front[k] = fm[k]
    # Acotado por stack de un asset de `_all`. Sin esto el campo se queda en la
    # fuente y nunca llega al cliente: el payload lleva lista blanca, y lo que no
    # esta en ella se descarta en silencio. `stack` no sirve para esto porque es
    # de un solo valor y estos assets aplican a varios, pero no a todos.
    if "applies_to_stacks" in fm:
        v = fm["applies_to_stacks"]
        front["appliesToStacks"] = (
            [s.strip() for s in v.strip("[] ").split(",") if s.strip()]
            if isinstance(v, str) else v
        )
    # reescribe [[links]] del cuerpo a los ids normalizados
    return {"frontmatter": front, "body": rewrite_links(a.body)}


def entry_file_content(a: Asset) -> str:
    """Contenido del SKILL.md de un bundle: frontmatter (name/description
    requeridos + metadata útil) + body con links reescritos."""
    fm = a.frontmatter
    norm_id = mimir_id(a.local_id)
    title = fm.get("title") or first_h1(a.body) or humanize(a.local_id)
    description = (fm.get("description") or "").replace('"', "'")
    tags = fm.get("tags") or []
    stack = normalize_stack(fm)
    lines = ["---", f"name: {norm_id}", f'description: "{description}"']
    if tags:
        lines.append("tags: [" + ", ".join(str(t) for t in tags) + "]")
    if stack:
        lines.append(f"stack: {stack}")
    lines += [f"title: {title}", "---", "", rewrite_links(a.body).rstrip("\n"), ""]
    return "\n".join(lines)


def compute_source_hash(a: Asset) -> str:
    """Hash estable del contenido que se publicaria (frontmatter+body+archivos)."""
    h = hashlib.sha256()
    req = build_create_request(a)
    h.update(json.dumps(req, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    for mimir_rel, src in sorted(a.upload_plan):
        content, enc = file_payload(src)
        h.update(mimir_rel.encode("utf-8"))
        h.update(content.encode("utf-8"))
    return h.hexdigest()


def bump_patch(version: str) -> str:
    parts = (version or "1.0.0").split(".")
    while len(parts) < 3:
        parts.append("0")
    try:
        parts[2] = str(int(parts[2]) + 1)
    except ValueError:
        parts[2] = "1"
    return ".".join(parts[:3])


def endpoint_for(a: Asset) -> str:
    # En calidad solo hay scope chapter/stack -> ambos van al endpoint de chapter.
    return f"/api/v1/chapters/{CHAPTER_ID}/documents"


# --------------------------------------------------------------------------- #
# Cliente HTTP Mimir
# --------------------------------------------------------------------------- #
class MimirClient:
    def __init__(self, base_url: str, token: str | None, api_key: str | None):
        self.base = base_url.rstrip("/")
        self.headers = {"Content-Type": "application/json"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
        if api_key:
            self.headers["x-api-key"] = api_key

    def _req(self, method: str, path: str, body: dict | None = None) -> dict:
        url = self.base + path
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")
            raise RuntimeError(f"{method} {path} -> {e.code}: {detail}") from None

    def list_stacks(self) -> set[str]:
        resp = self._req("GET", f"/api/v1/chapters/{CHAPTER_ID}/stacks")
        return {s.get("id") for s in (resp.get("stacks") or [])}

    def create_stack(self, stack_id: str) -> None:
        # la API real espera stackId/stackName (el OpenAPI dice id/name, desactualizado)
        self._req("POST", f"/api/v1/chapters/{CHAPTER_ID}/stacks",
                  {"stackId": stack_id, "stackName": stack_id})

    def ensure_stacks(self, needed: set[str]) -> None:
        existing = self.list_stacks()
        for s in sorted(needed - existing):
            self.create_stack(s)
            print(f"  + stack creado: {s}")

    def create_document(self, a: Asset) -> str:
        resp = self._req("POST", endpoint_for(a), build_create_request(a))
        doc = resp.get("document") or {}
        return (doc.get("frontmatter") or {}).get("id") or doc.get("id")

    def get_document(self, doc_id: str) -> dict:
        resp = self._req("GET", f"/api/v1/chapters/{CHAPTER_ID}/documents/{doc_id}")
        return resp.get("document") or {}

    def update_document(self, a: Asset, doc_id: str, reason: str) -> str:
        cur = self.get_document(doc_id)
        curfm = cur.get("frontmatter") or {}
        req = build_create_request(a)
        # el API exige que el frontmatter del update lleve el id (UUID) existente
        req["frontmatter"]["id"] = curfm.get("id", doc_id)
        req["frontmatter"]["version"] = bump_patch(curfm.get("version", "1.0.0"))
        req["changeType"] = "patch"
        req["reason"] = reason
        self._req("PUT", f"/api/v1/chapters/{CHAPTER_ID}/documents/{doc_id}", req)
        return req["frontmatter"]["version"]

    def upload_bundle_files(self, a: Asset, doc_id: str) -> int:
        try:
            self.migrate_to_bundle(doc_id)
        except RuntimeError:
            pass
        # El entry file SKILL.md que genera Mimir queda sin frontmatter (solo body);
        # lo reescribimos con su frontmatter (name/description requeridos por el
        # estándar Agent Skills) para que el bundle tenga los campos obligatorios.
        self.put_file(doc_id, a.entry_path.name, entry_file_content(a), "utf-8")
        n = 1
        for mimir_rel, src in a.upload_plan:
            content, enc = file_payload(src)
            self.put_file(doc_id, mimir_rel, content, enc)
            n += 1
        return n

    def migrate_to_bundle(self, doc_id: str) -> None:
        self._req("POST", f"/api/v1/documents/{doc_id}/migrate",
                  {"targetStructure": "bundle"})

    def put_file(self, doc_id: str, rel_path: str, content: str,
                 encoding: str = "utf-8") -> None:
        self._req("PUT", f"/api/v1/documents/{doc_id}/files/{rel_path}",
                  {"content": content, "encoding": encoding})

    def health(self) -> dict:
        return self._req("GET", "/health")


# --------------------------------------------------------------------------- #
# Ejecución
# --------------------------------------------------------------------------- #
def bundle_rel(a: Asset, f: Path) -> str:
    return f.relative_to(a.entry_path.parent).as_posix()


def file_payload(f: Path) -> tuple[str, str]:
    if f.suffix in TEXT_EXTS or f.name == ".gitkeep":
        # reescribe [[links]] tambien dentro de los archivos de referencia
        return rewrite_links(f.read_text(encoding="utf-8")), "utf-8"
    import base64
    return base64.b64encode(f.read_bytes()).decode("ascii"), "base64"


def run_dry(assets: list[Asset], warnings: list[str], report_path: Path) -> None:
    report = {"chapter": CHAPTER_ID, "totalAssets": len(assets),
              "warnings": warnings, "operations": []}
    by_type: dict = {}
    for a in assets:
        by_type[a.type] = by_type.get(a.type, 0) + 1
        op = {
            "localId": a.local_id, "type": a.type, "scope": a.scope,
            "isBundle": a.is_bundle, "endpoint": endpoint_for(a),
            "request": build_create_request(a),
        }
        if a.is_bundle:
            op["bundleFiles"] = [bundle_rel(a, f) for f in a.bundle_files]
        report["operations"].append(op)
    report["byType"] = by_type
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n=== DRY-RUN: chapter '{CHAPTER_ID}' ===")
    print(f"Assets a migrar: {len(assets)}")
    for t, n in sorted(by_type.items()):
        print(f"  {t:10s}: {n}")
    bundles = sum(1 for a in assets if a.is_bundle)
    files = sum(len(a.bundle_files) for a in assets)
    print(f"  bundles   : {bundles} (con {files} archivos internos a subir)")
    if warnings:
        print(f"\nAdvertencias ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")
    # muestra de títulos sintetizados (para validar estrategia de id/links)
    print("\nMuestra título sintetizado -> slug (compara con id local):")
    for a in assets[:8]:
        req = build_create_request(a)
        title = req["frontmatter"]["title"]
        print(f"  [{a.local_id}] title='{title}'  slug='{slugify(title)}'")
    print(f"\nReporte completo: {report_path}")


def run_probe(client: MimirClient) -> None:
    print("=== PROBE: estrategia de id ===")
    print("Health:", client.health())
    probe = Asset(
        local_id="calidad-probe-id-strategy", type="skill", scope="chapter",
        entry_path=CHAPTER_DIR, is_bundle=False,
        frontmatter={"tags": ["probe"], "description": "probe id strategy"},
        body="# Probe Id Strategy\n\n## Instrucción\nDocumento temporal de prueba.\n",
    )
    req = build_create_request(probe)
    title = req["frontmatter"]["title"]
    print(f"Enviando title='{title}' (slug='{slugify(title)}')")
    mimir_id = client.create_document(probe)
    print(f"Mimir asignó id = '{mimir_id}'")
    if mimir_id == slugify(title):
        print("=> Mimir slugifica el title. Estrategia: title=id-local para preservar [[links]].")
    else:
        print("=> Mimir NO deriva id del title. Hay que reescribir [[links]] con el mapa id-local->id-mimir.")
    print("NOTA: borra el documento de prueba manualmente si es necesario.")


def run_apply(assets: list[Asset], client: MimirClient,
              warnings: list[str], report_path: Path) -> None:
    print(f"=== APPLY: migrando {len(assets)} assets a Mimir ===")
    needed = {s for s in (normalize_stack(a.frontmatter) for a in assets) if s}
    if needed:
        print("Asegurando stacks:", sorted(needed))
        client.ensure_stacks(needed)
    id_map: dict[str, str] = {}
    results = []
    for a in assets:
        norm = mimir_id(a.local_id)
        try:
            doc_id = client.create_document(a)
            a.mimir_uuid = doc_id
            id_map[norm] = doc_id
            line = {"localId": norm, "mimirId": doc_id, "status": "created"}
            if a.is_bundle:
                if doc_id is None:
                    raise RuntimeError("create no devolvió id; no puedo subir archivos del bundle")
                try:
                    client.migrate_to_bundle(doc_id)
                except RuntimeError as e:
                    line["migrateNote"] = str(e)
                uploaded = 0
                for mimir_rel, src in a.upload_plan:
                    content, enc = file_payload(src)
                    client.put_file(doc_id, mimir_rel, content, enc)
                    uploaded += 1
                # Commit del staging: sin este update, los archivos PUTeados a un
                # documento recién creado quedan staged y no se materializan.
                client.update_document(a, doc_id, reason="commit bundle files")
                line["bundleFilesUploaded"] = uploaded
                if a.manifest:
                    line["restructured"] = len(a.manifest)
            print(f"  OK  {norm} -> {doc_id}")
            results.append(line)
        except RuntimeError as e:
            print(f"  ERR {norm}: {e}", file=sys.stderr)
            results.append({"localId": norm, "status": "error", "error": str(e)})

    report = {"chapter": CHAPTER_ID, "idMap": id_map,
              "warnings": warnings, "results": results}
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    # id-map.json independiente: lo consume la CLI para resolver [[local-id]] <-> UUID
    id_map_path = report_path.parent / "id-map.json"
    id_map_path.write_text(json.dumps(id_map, indent=2, ensure_ascii=False), encoding="utf-8")
    # sync-state.json: baseline para futuras corridas incrementales (--sync)
    state = {mimir_id(a_.local_id): {
        "uuid": id_map.get(mimir_id(a_.local_id)),
        "hash": compute_source_hash(a_),
    } for a_ in assets if id_map.get(mimir_id(a_.local_id))}
    (report_path.parent / "sync-state.json").write_text(
        json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    ok = sum(1 for r in results if r.get("status") == "created")
    errs = sum(1 for r in results if r.get("status") == "error")
    print(f"\nMigrados OK: {ok} | errores: {errs}")
    print(f"Reporte: {report_path}")
    print(f"Mapa id-local->UUID: {id_map_path}")


def run_sync(assets: list[Asset], client: MimirClient, state_path: Path,
             prune: bool = False) -> None:
    """Sincroniza incrementalmente: crea nuevos, actualiza cambiados, omite iguales."""
    state = {}
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
    print(f"=== SYNC: estado previo {len(state)} assets | fuente {len(assets)} ===")
    needed = {s for s in (normalize_stack(a.frontmatter) for a in assets) if s}
    if needed:
        client.ensure_stacks(needed)

    seen = set()
    created = updated = skipped = 0
    for a in assets:
        nid = mimir_id(a.local_id)
        seen.add(nid)
        cur_hash = compute_source_hash(a)
        prev = state.get(nid)
        try:
            if prev is None:
                doc_id = client.create_document(a)
                if a.is_bundle and doc_id:
                    client.upload_bundle_files(a, doc_id)
                    # Los PUT de archivos quedan en STAGING (el API responde
                    # '"File ... staged"'); sin un update posterior del documento,
                    # los archivos nuevos (p.ej. references/ de un bundle recién
                    # creado) NO se materializan. El update commitea el staging
                    # (costo: el bundle nuevo nace en v1.0.1).
                    client.update_document(a, doc_id, reason="commit bundle files")
                state[nid] = {"uuid": doc_id, "hash": cur_hash}
                created += 1
                print(f"  NEW  {nid} -> {doc_id}")
            elif prev.get("hash") != cur_hash:
                doc_id = prev["uuid"]
                # Orden: primero stage de archivos, después update del documento
                # — el update commitea cualquier archivo staged (incluidas
                # references NUEVAS en bundles existentes) con un solo version bump.
                if a.is_bundle:
                    client.upload_bundle_files(a, doc_id)
                ver = client.update_document(a, doc_id, reason="sync: actualización de contenido")
                state[nid] = {"uuid": doc_id, "hash": cur_hash}
                updated += 1
                print(f"  UPD  {nid} -> {doc_id} (v{ver})")
            else:
                skipped += 1
        except RuntimeError as e:
            print(f"  ERR  {nid}: {e}", file=sys.stderr)

    orphans = [k for k in state if k not in seen]
    if orphans:
        print(f"\nHuérfanos en estado pero no en fuente ({len(orphans)}): {orphans}")
        if prune:
            for k in orphans:
                try:
                    client._req("DELETE",
                                f"/api/v1/chapters/{CHAPTER_ID}/documents/{state[k]['uuid']}",
                                {"reason": "sync: eliminado de la fuente"})
                    del state[k]
                    print(f"  DEL  {k}")
                except RuntimeError as e:
                    print(f"  ERR borrando {k}: {e}", file=sys.stderr)

    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSYNC: nuevos {created} | actualizados {updated} | sin cambios {skipped} "
          f"| huérfanos {len(orphans)}")
    print(f"Estado: {state_path}")


def run_reindex(assets: list[Asset], client: MimirClient, state_path: Path) -> None:
    """Fuerza reindexación tocando cada documento (update = version bump + re-push
    del contenido actual). Mimir acepta el update sin cambio de contenido, así que
    NO se agregan espacios ni caracteres: el cuerpo queda idéntico, solo sube la
    versión y se dispara el reindex."""
    if not state_path.exists():
        print(f"ERROR: falta {state_path} (baseline con los uuid). Corre --apply primero.",
              file=sys.stderr)
        return
    state = json.loads(state_path.read_text(encoding="utf-8"))
    print(f"=== REINDEX: tocando {len(state)} documentos ===")
    ok = err = 0
    for a in sorted(assets, key=lambda x: x.local_id):
        nid = mimir_id(a.local_id)
        entry = state.get(nid)
        if not entry:
            print(f"  SKIP sin uuid: {nid}")
            continue
        try:
            v = client.update_document(a, entry["uuid"], reason="reindex")
            ok += 1
            print(f"  OK  {nid} v{v}")
        except RuntimeError as e:
            err += 1
            print(f"  ERR {nid}: {e}", file=sys.stderr)
    print(f"\nREINDEX: ok {ok} | err {err}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Migrador chapter Calidad -> Mimir")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", help="(default) plan sin tocar la red")
    g.add_argument("--apply", action="store_true", help="ejecuta la migración real")
    g.add_argument("--probe", action="store_true", help="prueba la estrategia de id")
    g.add_argument("--sync", action="store_true",
                   help="sincroniza incrementalmente (crea nuevos, actualiza cambiados)")
    g.add_argument("--reindex", action="store_true",
                   help="fuerza reindexación tocando cada documento (version bump, sin cambio de contenido)")
    ap.add_argument("--prune", action="store_true",
                    help="con --sync: borra en Mimir los assets que ya no estan en la fuente")
    ap.add_argument("--state", default=str(REPO_ROOT / "migration" / "sync-state.json"))
    ap.add_argument("--report", default=str(REPO_ROOT / "migration" / "report.json"))
    ap.add_argument("--only", default=None,
                    help="migra solo los assets cuyo local_id contenga este texto (CSV)")
    args = ap.parse_args()

    base = os.environ.get("MIMIR_BASE_URL", "http://localhost:3002")
    token = os.environ.get("MIMIR_TOKEN")
    api_key = os.environ.get("MIMIR_API_KEY")
    report_path = Path(args.report)

    assets, warnings = discover_assets()

    if args.only:
        wanted = [s.strip() for s in args.only.split(",") if s.strip()]
        assets = [a for a in assets if any(w in a.local_id for w in wanted)]
        print(f"Filtro --only={wanted}: {len(assets)} assets seleccionados")

    if args.probe or args.apply or args.sync or args.reindex:
        if not token and not api_key:
            print("ERROR: define MIMIR_TOKEN o MIMIR_API_KEY para --apply/--probe/--sync/--reindex",
                  file=sys.stderr)
            return 2
        client = MimirClient(base, token, api_key)
        if args.probe:
            run_probe(client)
        elif args.sync:
            run_sync(assets, client, Path(args.state), prune=args.prune)
        elif args.reindex:
            run_reindex(assets, client, Path(args.state))
        else:
            run_apply(assets, client, warnings, report_path)
    else:
        run_dry(assets, warnings, report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
