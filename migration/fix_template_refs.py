#!/usr/bin/env python3
"""
b3.1 — Reapunta referencias a las plantillas viejas (templates/*.tpl|.sh)
hacia el consolidado `references/templates.md` (indicando la seccion destino).

Solo actua dentro de bundles que tengan references/templates.md, y solo sobre
rutas que terminan en .tpl o .sh (evita falsos positivos como templates/*.yml).

Uso: --dry-run | --apply
"""
from __future__ import annotations
import argparse
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CHAPTER_DIR = REPO_ROOT / "chapters" / "calidad"

# 1) ref con ruta: [[bundle/]references/]templates/<path>.tpl|.sh
PAT_PATH = re.compile(
    r"(?:\[\[)?"
    r"(?:[a-z0-9-]+/)?"
    r"(?:references/)?"
    r"templates/([A-Za-z0-9._/-]+?\.(?:tpl|sh))"
    r"(?:\]\])?"
)
# 2) mencion bare entre backticks: `<name>.tpl`
PAT_BARE = re.compile(r"`([A-Za-z0-9._/-]+?\.tpl)`")


def dest_name(orig_sub: str) -> str:
    return orig_sub[:-4] if orig_sub.endswith(".tpl") else orig_sub


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    apply = args.apply

    files_changed = 0
    repl_total = 0
    for md in sorted(CHAPTER_DIR.rglob("*.md")):
        if md.name == "templates.md":
            continue
        txt = md.read_text(encoding="utf-8")
        count = [0]

        def repl_path(m):
            count[0] += 1
            return f"`references/templates.md` (sección `{dest_name(m.group(1))}`)"

        def repl_bare(m):
            count[0] += 1
            return f"`{dest_name(m.group(1))}`"

        new = PAT_PATH.sub(repl_path, txt)
        new = PAT_BARE.sub(repl_bare, new)
        if count[0]:
            files_changed += 1
            repl_total += count[0]
            rel = md.relative_to(REPO_ROOT)
            print(f"  {rel}: {count[0]} refs")
            if apply:
                md.write_text(new, encoding="utf-8")

    mode = "APLICADO" if apply else "DRY-RUN"
    print(f"\n[{mode}] archivos: {files_changed} | refs reapuntadas: {repl_total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
