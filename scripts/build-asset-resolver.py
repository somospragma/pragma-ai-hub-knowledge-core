#!/usr/bin/env python3
"""Genera el skill `calidad-asset-resolver` a partir de la fuente del chapter.

Por que existe
--------------
El chapter usa `[[asset-id]]` para las referencias cruzadas, y esa convencion
es correcta EN LA FUENTE: audit-chapter.py verifica que todo `[[id]]` apunte a
un asset que existe. El problema aparece al instalar: la CLI renombra cada
asset usando el titulo H1, no el `id`. Asi, `[[calidad-failure-triage-and-
classification]]` termina viviendo en una carpeta llamada
`failure-triage-and-classification-clasificacion-de-fallos-y-analisis-de-causa-ra`.

El agente lee la referencia, no encuentra nada con ese nombre, y sigue sin
abrir el documento. Medido sobre una instalacion real: 63 de 110 referencias
distintas no resuelven, y entre ellas estan los skills marcados
`enforcement: mandatory`.

Este script emite la tabla de traduccion `id -> titulo -> carpeta esperada`,
que es lo unico que cierra el hueco sin depender de un cambio en la CLI.

Se regenera y se compara en CI: un resolvedor obsoleto es peor que no tenerlo,
porque manda al agente a una carpeta que no existe.

Uso:
    python3 scripts/build-asset-resolver.py            # escribe el asset
    python3 scripts/build-asset-resolver.py --check    # exit 1 si esta obsoleto
"""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CHAPTER = REPO / "chapters" / "calidad"
ACCOUNTS = REPO / "accounts"
OUT = CHAPTER / "skills" / "_all" / "asset-resolver.md"
# El resolvedor del chapter viaja a TODOS los clientes, asi que no puede nombrar
# a ninguno. Las filas de cuenta salen en un resolvedor propio que se sincroniza
# con esa cuenta y solo con ella.
ACCOUNT_OUT_NAME = "asset-resolver.md"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
H1_RE = re.compile(r"^#\s+(.+)$", re.M)

# La CLI descarta estos prefijos editoriales antes de derivar el nombre.
TITLE_PREFIX_RE = re.compile(
    r"^(Reference|Decision|Limit|Skill|Workflow|Prompt|Steering)\s*:\s*", re.I
)
SLUG_CAP = 80


def installed_name(title: str) -> str:
    """Reproduce el nombre de carpeta que la CLI deriva del titulo H1.

    Verificado contra una instalacion real: reproduce 60 de las 72 carpetas
    del chapter Calidad. Las que no reproduce son de otros chapters o tienen
    puntuacion en un borde; por eso el resolvedor publica TAMBIEN el titulo,
    que es lo que el agente puede casar a ojo cuando el slug no cuadra.
    """
    t = TITLE_PREFIX_RE.sub("", title.strip())
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    # `.` y `/` se borran sin dejar separador: `.evidence/execution-status.json`
    # queda como `evidenceexecution-statusjson`, y `Frontend/Backend` como
    # `frontendbackend`. Verificado contra la instalacion real.
    t = re.sub(r"[./{}]", "", t)
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return t[:SLUG_CAP].rstrip("-")


def parse(p: Path) -> tuple[dict, str]:
    text = p.read_text(encoding="utf-8", errors="replace")
    fm: dict = {}
    m = FRONTMATTER_RE.match(text)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                fm[k.strip()] = v.strip().strip('"').strip("'")
    # La CLI prefiere el campo `title` del frontmatter y solo cae al H1 cuando
    # no existe. Los assets de cuenta lo llevan y su H1 difiere del titulo.
    h1 = H1_RE.search(text)
    title = fm.get("title") or (h1.group(1).strip() if h1 else "")
    return fm, title


def collect_chapter() -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()

    for p in sorted(CHAPTER.rglob("*.md")):
        if "/references/" in p.as_posix():
            continue
        fm, h1 = parse(p)
        aid, atype = fm.get("id"), fm.get("type")
        if not aid or not atype or aid in seen:
            continue
        seen.add(aid)
        rows.append({
            "id": aid,
            "type": atype,
            "stack": fm.get("stack", "").strip("[] ") or "_all",
            "title": h1 or aid,
            "folder": installed_name(h1 or aid),
        })

    return sorted(rows, key=lambda r: (r["type"], r["id"]))


def collect_accounts() -> dict[tuple[str, str], list[dict]]:
    """{(cliente, chapter): filas} — un resolvedor por cuenta, no uno global."""
    out: dict[tuple[str, str], list[dict]] = {}
    if not ACCOUNTS.is_dir():
        return out
    for p in sorted(ACCOUNTS.rglob("*.md")):
        rel = p.relative_to(ACCOUNTS).parts
        if len(rel) < 3 or p.name == ACCOUNT_OUT_NAME:
            continue
        client, chapter = rel[0], rel[1]
        fm, title = parse(p)
        if not title:
            continue
        aid = fm.get("id") or f"{client}-{chapter}-{p.stem}"
        out.setdefault((client, chapter), []).append({
            "id": aid,
            "type": fm.get("type", "steering"),
            "stack": f"cuenta:{client}",
            "title": title,
            "folder": installed_name(title),
        })
    return {k: sorted(v, key=lambda r: (r["type"], r["id"])) for k, v in out.items()}


HEADER = """---
id: calidad-asset-resolver
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "OBLIGATORIO al encontrar una referencia entre dobles corchetes que no exista con ese nombre. Traduce cada id del chapter al titulo y a la carpeta con que la CLI lo instala en el IDE. Sin esta tabla las referencias cruzadas del chapter no resuelven y el conocimiento obligatorio no se abre."
tags: [resolver, referencias, navegacion, enforcement, mandatory, generado]
enforcement: mandatory
generated_by: scripts/build-asset-resolver.py
---

# Asset Resolver — Traducir una Referencia al Nombre Instalado

## Cuándo aplicar

En cuanto encuentres una referencia entre dobles corchetes y no exista ningún
archivo ni carpeta con ese nombre. No es un enlace roto del documento: es que la
referencia es el **identificador en la fuente del chapter**, y la CLI instala
cada asset con un nombre derivado de su título, no de su id.

Ejemplo real: `[[calidad-failure-triage-and-classification]]` vive instalado en
`failure-triage-and-classification-clasificacion-de-fallos-y-analisis-de-causa-ra`.

## Instrucción

1. **Nunca des por inexistente un asset porque su identificador no aparezca.** Búscalo
   en la tabla de abajo y abre la carpeta de la columna *Instalado como*.
2. Si la carpeta no existe con ese nombre exacto, **busca por título**: el nombre
   instalado siempre empieza por las primeras palabras del título, en minúsculas
   y con guiones.
3. Si aun así no aparece, el asset no se instaló en este workspace. Dilo
   explícitamente: *"`X` está referenciado pero no instalado aquí"*. No lo
   sustituyas por tu criterio ni sigas adelante en silencio, sobre todo si el
   asset es una compuerta obligatoria.

### Dónde buscar según el IDE

| IDE | Skills | Steering / instrucciones | Workflows |
|---|---|---|---|
| Kiro | `.kiro/skills/<carpeta>/SKILL.md` | `.kiro/steering/<carpeta>.md` | `.kiro/workflows/<carpeta>.workflow.md` |
| GitHub Copilot | `.github/skills/<carpeta>/SKILL.md` | `.github/instructions/<carpeta>-instruction.md` | `.github/workflows/<carpeta>.workflow.md` |
| Claude Code | `.claude/skills/<carpeta>/SKILL.md` | `.claude/rules/<carpeta>.md` | `.claude/workflows/<carpeta>.workflow.md` |
| Amazon Q | `.amazonq/rules/<carpeta>.md` | `.amazonq/rules/<carpeta>.md` | `.amazonq/rules/<carpeta>.md` |

Un asset con `references/` cuelga de su propia carpeta:
`<ruta-del-skill>/references/<archivo>.md`.

## Lo que nunca debes hacer

- **Nunca concluyas que un recurso no existe a partir de una búsqueda que no
  comprobaste que corrió.** Una salida vacía puede ser "no hay resultados" o
  puede ser "el comando falló". Comprueba el código de salida antes de afirmar
  ausencia, y busca por dos caminos distintos antes de declarar que falta algo
  que un documento afirma que existe.
- **Nunca reemplaces un skill obligatorio que no encontraste por tu propio
  criterio.** Que no lo halles no reduce lo que exige.

## Tabla de traducción

"""

FOOTER = """
---

*Tabla generada por `scripts/build-asset-resolver.py` desde la fuente del
chapter. Si una fila no coincide con lo instalado, la fuente cambió y hay que
regenerarla: no la edites a mano.*
"""


def render(rows: list[dict]) -> str:
    out = [HEADER]
    by_type: dict[str, list[dict]] = {}
    for r in rows:
        by_type.setdefault(r["type"], []).append(r)

    label = {
        "skill": "Skills",
        "workflow": "Workflows",
        "prompt": "Prompts",
        "steering": "Steering / instrucciones",
        "agent": "Agentes",
        "hook": "Hooks",
    }
    for t in ("steering", "workflow", "skill", "prompt", "agent", "hook"):
        group = by_type.get(t)
        if not group:
            continue
        out.append(f"### {label.get(t, t)}\n")
        out.append("| Referencia | Instalado como |")
        out.append("|---|---|")
        for r in group:
            # El nombre instalado es el titulo en minusculas y con guiones, asi
            # que publicarlo aparte seria repetir la misma cadena dos veces.
            out.append(f"| `[[{r['id']}]]` | `{r['folder']}` |")
        out.append("")
    out.append(FOOTER)
    return "\n".join(out)


ACCOUNT_HEADER = """---
id: {client}-{chapter}-asset-resolver
title: Asset Resolver for the {client_title} Account
type: skill
chapter: {chapter}
stack: default
scope: account
account: {client}
description: "Traduce cada identificador del conocimiento de esta cuenta al nombre con que la CLI lo instala en el IDE. Consultar al encontrar una referencia cruzada que no exista con ese nombre."
required: true
---

# Asset Resolver for the {client_title} Account

> **Applies to: the whole {client_title} account** — todos sus proyectos.

## Instrucción

Una referencia entre dobles corchetes es el identificador del asset **en la
fuente**, y la CLI instala cada uno con un nombre derivado de su título. Cuando
una referencia a conocimiento de esta cuenta no exista con ese nombre, búscala
en la tabla y abre la carpeta de la columna *Instalado como*.

Para las referencias al conocimiento **del chapter** —las que empiezan por
`{chapter}-`— usa `[[{chapter}-asset-resolver]]`, que es otro documento: el del
chapter viaja a todos los clientes y por eso no lleva estas filas.

Si tampoco aparece por título, el asset no se instaló en este workspace. Dilo con
esas palabras y detente; no lo sustituyas por tu criterio.

## Lo que nunca debes hacer

- **Nunca des por inexistente un asset de esta cuenta porque su identificador no
  aparezca como carpeta.**
- **Nunca reemplaces por tu criterio una compuerta obligatoria que no encontraste.**

## Tabla de traducción

"""


def render_account(client: str, chapter: str, rows: list[dict]) -> str:
    out = [ACCOUNT_HEADER.format(client=client, chapter=chapter,
                                 client_title=client.capitalize())]
    out.append("| Referencia | Instalado como |")
    out.append("|---|---|")
    for r in rows:
        out.append(f"| `[[{r['id']}]]` | `{r['folder']}` |")
    out.append("")
    out.append("*Generada por `scripts/build-asset-resolver.py`. No editar a mano.*")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="No escribe; sale 1 si el asset generado esta obsoleto.")
    args = ap.parse_args()

    rows = collect_chapter()
    content = render(rows)
    account_files = {
        ACCOUNTS / client / chapter / "_cuenta" / ACCOUNT_OUT_NAME:
            render_account(client, chapter, arows)
        for (client, chapter), arows in collect_accounts().items()
    }

    if args.check:
        stale = [f for f, c in account_files.items()
                 if not f.is_file() or f.read_text(encoding="utf-8") != c]
        if stale:
            for f in stale:
                print(f"OBSOLETO {f.relative_to(REPO)} — regenera con "
                      f"build-asset-resolver.py", file=sys.stderr)
            return 1
        if not OUT.is_file():
            print(f"FALTA {OUT.relative_to(REPO)} — corre build-asset-resolver.py",
                  file=sys.stderr)
            return 1
        if OUT.read_text(encoding="utf-8") != content:
            print(f"OBSOLETO {OUT.relative_to(REPO)} — regenera con "
                  f"build-asset-resolver.py", file=sys.stderr)
            return 1
        print(f"OK {OUT.relative_to(REPO)} ({len(rows)} assets)")
        return 0

    OUT.write_text(content, encoding="utf-8")
    print(f"Escrito {OUT.relative_to(REPO)} — {len(rows)} assets del chapter, "
          f"{len(content):,} bytes")
    for f, c in account_files.items():
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(c, encoding="utf-8")
        n = c.count("| `[[")
        print(f"Escrito {f.relative_to(REPO)} — {n} assets de cuenta, "
              f"{len(c):,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
