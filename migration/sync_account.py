#!/usr/bin/env python3
"""Sincroniza conocimiento de CUENTA a Mimir.

Fuente:  accounts/{cliente}/{chapter}/*.md  (fuera del control de versiones del core)
Destino: /api/v1/accounts/{acc}/frentes/{frente}/projects/{proj}/documents

Separado de migrate_to_mimir.py a proposito: ese sincroniza el chapter y su
baseline no debe mezclarse con el de cuenta. Cada uno lleva su propio estado.

Modos:
  --dry-run  (default) no toca la red, imprime el plan
  --sync     crea los nuevos y actualiza los que cambiaron

NO implementa borrado. El conocimiento de cuenta se retira a mano y con
confirmacion; ver la regla de alcance de super admin.

Uso:
  export MIMIR_BASE_URL=https://api-mimir.pragma.com.co
  export MIMIR_TOKEN=...
  python3 migration/sync_account.py --client mercantil --chapter calidad \
      --account 608 --frente default --project SM0055 --audit
  python3 migration/sync_account.py --client mercantil --chapter calidad \
      --account 608 --frente default --project SM0055 --sync

Estructura de origen
--------------------
  accounts/<cliente>/<chapter>/_cuenta/    aplica a TODOS los proyectos de negocio
  accounts/<cliente>/<chapter>/<proyecto>/ aplica solo a ese proyecto de negocio

Un solo destino en Mimir
------------------------
La cuenta tiene UNA ruta de documentos —la de proyecto— y Mimir no ofrece un eje
que separe los proyectos de negocio entre si (Persona Natural y Persona Juridica
son el mismo proyecto de Mimir). Por eso todo sube junto y **la separacion vive
en el texto**: cada documento declara su alcance en la PRIMERA linea de su
cuerpo (`**Applies to: ...**`), no en el frontmatter, porque varios IDEs
concatenan todo el steering en un unico archivo y el frontmatter no sobrevive.
El script lo verifica y falla si falta.
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
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FM_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)

# Tipos que acepta el endpoint de cuenta (verificados contra la API real,
# el OpenAPI de entrada/ esta desactualizado y no los lista).
VALID_TYPES = {"decisions", "references", "limits", "skill", "steering", "workflow", "prompt"}


def parse_frontmatter(text: str) -> tuple[dict, str]:
    m = FM_RE.match(text)
    if not m:
        return {}, text
    fm: dict = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        val = v.strip().strip('"').strip("'")
        if val in ("true", "false"):
            fm[k.strip()] = val == "true"
        else:
            fm[k.strip()] = val
    return fm, m.group(2).lstrip("\n")


# Carpeta de cuenta -> a que proyectos aplica su contenido.
#   _cuenta/  vale para TODOS los proyectos de la cuenta y se sube a cada uno.
#   <proyecto>/  vale solo para ese proyecto.
ACCOUNT_WIDE_DIR = "_cuenta"


def discover(client: str, chapter: str) -> list[tuple[str, dict, str]]:
    """Devuelve [(localId, frontmatter, body)] de TODO el conocimiento de la cuenta.

    Mimir tiene un solo destino para esta cuenta —la ruta de proyecto— y no un eje
    que separe los proyectos de negocio entre si. Por eso todo sube junto y **la
    separacion vive en el texto**: cada documento declara su alcance en la primera
    linea de su cuerpo. Esa linea es lo unico que sobrevive a los IDEs que
    concatenan todo el steering en un archivo, donde el frontmatter se pierde.
    """
    base = REPO_ROOT / "accounts" / client / chapter
    if not base.is_dir():
        sys.exit(f"ERROR: no existe la carpeta fuente {base}")

    sueltos = sorted(base.glob("*.md"))
    if sueltos:
        sys.exit("ERROR: hay assets sueltos en la raiz de la cuenta. Cada uno debe "
                 f"declarar su alcance moviendolo a '{ACCOUNT_WIDE_DIR}/' o a la "
                 "carpeta de su proyecto:\n  "
                 + "\n  ".join(f.name for f in sueltos))

    folders = [base / ACCOUNT_WIDE_DIR] + sorted(
        d for d in base.iterdir() if d.is_dir() and d.name != ACCOUNT_WIDE_DIR)
    if not (base / ACCOUNT_WIDE_DIR).is_dir():
        sys.exit(f"ERROR: falta {base / ACCOUNT_WIDE_DIR}")

    out = []
    problemas = []
    for folder in folders:
        alcance = "account" if folder.name == ACCOUNT_WIDE_DIR else "project"
        for f in sorted(folder.glob("*.md")):
            fm, body = parse_frontmatter(f.read_text(encoding="utf-8"))
            # El id es la clave del estado y el destino de toda referencia cruzada.
            # Derivarlo en silencio deja pasar un frontmatter que dice otra cosa.
            local_id = f"{client}-{chapter}-{f.stem}"
            declarado = fm.get("id")
            if declarado and declarado != local_id:
                problemas.append(f"{folder.name}/{f.name}: id '{declarado}' no sigue "
                                 f"la convencion '<cliente>-<chapter>-<archivo>' "
                                 f"('{local_id}')")
            if not fm.get("title"):
                problemas.append(f"{folder.name}/{f.name}: falta title")
            if fm.get("type") not in VALID_TYPES:
                problemas.append(f"{folder.name}/{f.name}: type invalido ({fm.get('type')!r})")
            if fm.get("chapter") != chapter:
                problemas.append(f"{folder.name}/{f.name}: chapter debe ser {chapter}")
            if not fm.get("stack"):
                problemas.append(f"{folder.name}/{f.name}: falta stack "
                                 "(el endpoint de cuenta lo exige)")
            if fm.get("scope") != alcance:
                problemas.append(f"{folder.name}/{f.name}: scope debe ser "
                                 f"'{alcance}' por la carpeta en que vive")
            if alcance == "project" and fm.get("project") != folder.name:
                problemas.append(f"{folder.name}/{f.name}: project debe ser "
                                 f"'{folder.name}'")
            # Sin esta linea, y con todo en un mismo destino, nada le dice al agente
            # de que proyecto esta leyendo.
            if "**Applies to:" not in body[:1200]:
                problemas.append(f"{folder.name}/{f.name}: falta la linea de alcance "
                                 "'**Applies to: ...**' en el cuerpo, bajo el titulo")
            out.append((local_id, fm, body))
    if problemas:
        sys.exit("ERROR de validacion:\n  " + "\n  ".join(problemas))
    return out


def audit(assets, docs_path: str) -> int:
    """Radiografia de lo que se subiria, antes de subirlo.

    El dry-run dice QUE documentos van. Esto dice cuanto pesan, cuales entran en
    cada turno del agente, si alguno referencia algo que no viaja con ellos, y si
    algo se repite entre proyectos.
    """
    import re as _re

    on = [a for a in assets if a[1].get("type") == "steering"]
    off = [a for a in assets if a[1].get("type") != "steering"]
    bytes_on = sum(len(b.encode()) for _, _, b in on)
    bytes_off = sum(len(b.encode()) for _, _, b in off)

    print(f"  documentos            : {len(assets)}  "
          f"({len(on)} steering, {len(off)} bajo demanda)")
    print(f"  SIEMPRE-ON (steering) : {bytes_on:>8,} bytes  "
          f"~{bytes_on / 3.5:>6,.0f} tokens EN CADA TURNO")
    for lid, fm, b in sorted(on, key=lambda a: -len(a[2].encode())):
        print(f"       {len(b.encode()):>7,}  {fm['title']}")
    print(f"  bajo demanda          : {bytes_off:>8,} bytes  "
          f"(~{bytes_off / 3.5:,.0f} tokens si se abriera todo)")

    hallazgos = 0
    ids = {lid for lid, _, _ in assets}

    # Referencias a documentos que no viajan en este destino.
    # Ids de TODA la cuenta, para distinguir "no existe" de "existe pero es del
    # otro proyecto". Lo segundo es correcto y deliberado: un documento de PN
    # nombra los de PJ para decir que su regla no se generaliza.
    base = REPO_ROOT / "accounts"
    todos = set()
    for f in base.rglob("*.md"):
        rel = f.relative_to(base).parts
        if len(rel) >= 3:
            todos.add(f"{rel[0]}-{rel[1]}-{f.stem}")

    fuera = {}
    for lid, fm, b in assets:
        for ref in _re.findall(r"\[\[([a-z0-9][a-z0-9-]*)\]\]", b):
            if ref.startswith(("calidad-", "backend-", "mobile-", "frontend-",
                               "arquitectura-")):
                continue          # conocimiento de chapter: lo instala la CLI aparte
            if ref in ids:
                continue
            fuera.setdefault(ref, []).append(fm["title"])


    if fuera:
        hallazgos += 1
        print(f"\n  ! {len(fuera)} referencia(s) a un id que NO EXISTE en la cuenta:")
        for ref, quien in sorted(fuera.items()):
            print(f"      [[{ref}]]  citado por: {', '.join(sorted(set(quien))[:2])}")

    # El discriminador de alcance, que es lo unico que separa PN de PJ tras el
    # flattening, tiene que estar en el cuerpo y decir el proyecto correcto.
    malos = []
    for lid, fm, b in assets:
        cab = b[:1200]
        if "**Applies to:" not in cab:
            malos.append((fm["title"], "sin linea de alcance"))
        elif fm.get("scope") == "project" and (fm.get("project") or "").upper() not in cab.upper():
            malos.append((fm["title"], "la linea de alcance no nombra a "
                          f"{(fm.get('project') or '?').upper()}"))
    if malos:
        hallazgos += 1
        print(f"\n  ! {len(malos)} documento(s) con el alcance mal declarado:")
        for titulo, why in malos:
            print(f"      {titulo}: {why}")

    # Un documento de `_cuenta/` viaja a los DOS proyectos, asi que no puede
    # depender por nombre de uno que solo existe en uno: el puntero se rompe en
    # el otro destino. Los indices se eximen: su trabajo es nombrarlo todo.
    INDICES = {"identify-project", "asset-resolver"}
    solo_de_un_proyecto = {}
    for d in sorted(base.glob("*/*/*")):
        if d.is_dir() and d.name not in (ACCOUNT_WIDE_DIR,):
            for f in d.glob("*.md"):
                solo_de_un_proyecto[f"{d.parent.parent.name}-{d.parent.name}-{f.stem}"] = d.name
    cruzados = []
    for f in (base / "mercantil").glob(f"*/{ACCOUNT_WIDE_DIR}/*.md"):
        if f.stem in INDICES:
            continue
        cuerpo = f.read_text(encoding="utf-8")
        for ref in sorted(set(_re.findall(r"\[\[(mercantil-[a-z0-9-]+)\]\]", cuerpo))):
            if ref in solo_de_un_proyecto:
                cruzados.append((f.name, ref, solo_de_un_proyecto[ref]))
    if cruzados:
        hallazgos += 1
        print(f"\n  ! {len(cruzados)} documento(s) de alcance de cuenta apuntan a uno "
              f"de un solo proyecto (resuelve, pero manda al agente del otro "
              f"proyecto a la regla equivocada):")
        for quien, ref, proy in cruzados:
            print(f"      {quien} -> [[{ref}]] (solo {proy.upper()})")

    # Un titulo repetido produce dos carpetas con el mismo nombre al instalar.
    from collections import Counter
    dup = [t for t, n in Counter(fm["title"] for _, fm, _ in assets).items() if n > 1]
    if dup:
        hallazgos += 1
        print(f"\n  ! titulos duplicados (colisionan al instalar): {', '.join(dup)}")

    print(f"\n  Destino: {docs_path}")
    print(f"  Hallazgos: {hallazgos}")
    return 1 if hallazgos else 0


def build_request(fm: dict, body: str) -> dict:
    front = {
        "title": fm["title"],
        "type": fm["type"],
        "chapter": fm["chapter"],
        "stack": fm.get("stack", "default"),
        "tags": fm.get("tags") or [],
        "description": fm.get("description") or "ND",
    }
    if "required" in fm:
        front["required"] = fm["required"]
    for k in ("extensible", "overridable", "pragma_extends", "pragma_override"):
        if k in fm:
            front[k] = fm[k]
    return {"frontmatter": front, "body": body}


def source_hash(req: dict) -> str:
    return hashlib.sha256(
        json.dumps(req, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def bump_patch(v: str) -> str:
    try:
        a, b, c = (v or "1.0.0").split(".")
        return f"{a}.{b}.{int(c) + 1}"
    except Exception:
        return "1.0.1"


class Client:
    def __init__(self, base: str, token: str, docs_path: str):
        self.base = base.rstrip("/")
        self.token = token
        self.docs = docs_path

    def _req(self, method: str, path: str, payload: dict | None = None) -> dict:
        url = f"{self.base}{path}"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {self.token}")
        if data:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req) as r:
                raw = r.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"{method} {path} -> {e.code}: {e.read().decode('utf-8')[:300]}") from None

    def create(self, req: dict) -> str:
        resp = self._req("POST", self.docs, req)
        doc = resp.get("document") or resp
        return (doc.get("frontmatter") or doc).get("id") or doc.get("id")

    def get(self, doc_id: str) -> dict:
        return self._req("GET", f"{self.docs}/{doc_id}")

    def update(self, doc_id: str, req: dict, reason: str) -> str:
        cur = self.get(doc_id)
        curfm = (cur.get("document") or cur).get("frontmatter") or {}
        payload = dict(req)
        payload["frontmatter"] = dict(req["frontmatter"])
        payload["frontmatter"]["id"] = curfm.get("id", doc_id)
        payload["frontmatter"]["version"] = bump_patch(curfm.get("version", "1.0.0"))
        payload["changeType"] = "patch"
        payload["reason"] = reason
        self._req("PUT", f"{self.docs}/{doc_id}", payload)
        return payload["frontmatter"]["version"]


def main() -> int:
    ap = argparse.ArgumentParser(description="Sincroniza conocimiento de cuenta a Mimir")
    ap.add_argument("--client", required=True)
    ap.add_argument("--chapter", default="calidad")
    ap.add_argument("--account", required=True)
    ap.add_argument("--frente", default="default",
                    help="Frente de Mimir. Hoy la cuenta solo tiene 'default'.")
    ap.add_argument("--project", required=True,
                    help="Codigo del proyecto en Mimir (no cambia entre PN y PJ)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--audit", action="store_true",
                   help="Radiografia del payload: peso, capa siempre-on, "
                        "referencias que no viajan, alcance mal declarado.")
    g.add_argument("--sync", action="store_true")
    ap.add_argument("--only", default=None, help="filtra por texto contenido en el localId (CSV)")
    args = ap.parse_args()

    docs_path = (f"/api/v1/accounts/{args.account}/frentes/{args.frente}"
                 f"/projects/{args.project}/documents")
    # Un documento de `_cuenta/` se sube a CADA destino y recibe un id remoto
    # distinto en cada uno. Un unico archivo de estado por cuenta los pisaria
    # entre si, asi que el estado se lleva por destino.
    # Un solo destino para toda la cuenta, asi que un solo archivo de estado.
    state_path = (REPO_ROOT / "migration" /
                  f"sync-state-account-{args.client}-{args.chapter}.json")
    state = json.loads(state_path.read_text()) if state_path.exists() else {}

    assets = discover(args.client, args.chapter)
    if args.only:
        wanted = [s.strip() for s in args.only.split(",") if s.strip()]
        assets = [a for a in assets if any(w in a[0] for w in wanted)]

    print(f"=== cuenta {args.account} / frente {args.frente} / proyecto {args.project} ===")
    print(f"fuente: accounts/{args.client}/{args.chapter}/  "
          f"({len(assets)} documentos, todas las carpetas)")
    print(f"estado: {state_path.name}  ({len(state)} conocidos)\n")

    if args.audit:
        return audit(assets, docs_path)

    if not args.sync:
        for local_id, fm, body in assets:
            req = build_request(fm, body)
            accion = "NEW" if local_id not in state else (
                "SKIP" if state[local_id]["hash"] == source_hash(req) else "UPD")
            print(f"  {accion:5} {fm['type']:11} {fm['title']}")
        print(f"\nDRY-RUN. Destino: {docs_path}")
        return 0

    token = os.environ.get("MIMIR_TOKEN")
    base = os.environ.get("MIMIR_BASE_URL")
    if not token or not base:
        print("ERROR: define MIMIR_BASE_URL y MIMIR_TOKEN", file=sys.stderr)
        return 2

    client = Client(base, token, docs_path)
    nuevos = actualizados = sin_cambios = errores = 0
    for local_id, fm, body in assets:
        req = build_request(fm, body)
        h = source_hash(req)
        try:
            if local_id not in state:
                doc_id = client.create(req)
                state[local_id] = {"uuid": doc_id, "hash": h}
                print(f"  NEW  {fm['title']} -> {doc_id}")
                nuevos += 1
            elif state[local_id]["hash"] != h:
                v = client.update(state[local_id]["uuid"], req, "account knowledge sync")
                state[local_id]["hash"] = h
                print(f"  UPD  {fm['title']} -> {state[local_id]['uuid']} (v{v})")
                actualizados += 1
            else:
                sin_cambios += 1
        except RuntimeError as e:
            print(f"  ERR  {local_id}: {e}")
            errores += 1
        state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n")

    print(f"\nSYNC: nuevos {nuevos} | actualizados {actualizados} | "
          f"sin cambios {sin_cambios} | errores {errores}")
    print(f"Estado: {state_path}")
    if errores:
        print("Si un NEW fallo, verifica con un GET si el documento quedo creado "
              "antes de reintentar: podria duplicarse.")
    return 1 if errores else 0


if __name__ == "__main__":
    raise SystemExit(main())
