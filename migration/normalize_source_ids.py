#!/usr/bin/env python3
"""
b1 — Normaliza los ids de los assets de calidad al prefijo 'calidad-' EN LA FUENTE.

- Cambia el campo `id:` del frontmatter de cada asset (entry files y single docs)
  a 'calidad-<id>' cuando no lo tenga.
- Reescribe TODOS los enlaces [[old-id]] -> [[calidad-old-id]] en todos los .md
  del chapter (incluye references), solo para ids que sean assets reales.

Uso:
  python3 migration/normalize_source_ids.py --dry-run
  python3 migration/normalize_source_ids.py --apply
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CHAPTER_DIR = REPO_ROOT / "chapters" / "calidad"
PREFIX = "calidad-"


def read_id(text: str) -> str | None:
    if not text.startswith("---"):
        return None
    lines = text.splitlines()
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            break
        m = re.match(r"^id:\s*(.+?)\s*$", lines[i])
        if m:
            return m.group(1).strip().strip("'\"")
    return None


def asset_entry_files() -> list[Path]:
    """Entry files de bundle (SKILL.md) + single docs con frontmatter `type:`."""
    files = []
    bundle_roots = {p.parent for p in CHAPTER_DIR.rglob("SKILL.md")}

    def under_bundle(p: Path) -> bool:
        return any(r in p.parents for r in bundle_roots)

    files.extend(CHAPTER_DIR.rglob("SKILL.md"))
    for md in CHAPTER_DIR.rglob("*.md"):
        if md.name == "SKILL.md" or under_bundle(md):
            continue
        if read_id(md.read_text(encoding="utf-8")):
            files.append(md)
    # hooks (.kiro.hook.md) tambien son assets con id
    for hk in CHAPTER_DIR.rglob("*.hook.md"):
        if hk not in files:
            files.append(hk)
    return sorted(set(files))


def build_rename_map(entry_files: list[Path]) -> dict[str, str]:
    rename = {}
    for f in entry_files:
        cur = read_id(f.read_text(encoding="utf-8"))
        if not cur:
            continue
        new = cur if cur.startswith(PREFIX) else PREFIX + cur
        rename[cur] = new
    return rename


def rewrite_id_field(text: str, rename: dict[str, str]) -> tuple[str, bool]:
    lines = text.splitlines(keepends=True)
    changed = False
    in_fm = False
    for i, line in enumerate(lines):
        s = line.rstrip("\n")
        if i == 0 and s.strip() == "---":
            in_fm = True
            continue
        if in_fm and s.strip() == "---":
            break
        if in_fm:
            m = re.match(r"^(id:\s*)(.+?)(\s*)$", s)
            if m:
                cur = m.group(2).strip().strip("'\"")
                new = rename.get(cur, cur if cur.startswith(PREFIX) else PREFIX + cur)
                if new != cur:
                    lines[i] = f"{m.group(1)}{new}\n"
                    changed = True
                break
    return "".join(lines), changed


def rewrite_links(text: str, rename: dict[str, str]) -> tuple[str, int]:
    n = 0
    def repl(m):
        nonlocal n
        target = m.group(1)
        if target in rename and rename[target] != target:
            n += 1
            return f"[[{rename[target]}]]"
        return m.group(0)
    out = re.sub(r"\[\[([a-z0-9][a-z0-9-]*)\]\]", repl, text)
    return out, n


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    apply = args.apply

    entry_files = asset_entry_files()
    rename = build_rename_map(entry_files)
    to_change = {k: v for k, v in rename.items() if k != v}
    print(f"Assets detectados: {len(rename)} | ids a renombrar: {len(to_change)}")
    for k, v in sorted(to_change.items()):
        print(f"  {k}  ->  {v}")

    # 1) cambiar campo id en entry/single files
    id_changes = 0
    for f in entry_files:
        txt = f.read_text(encoding="utf-8")
        new, ch = rewrite_id_field(txt, rename)
        if ch:
            id_changes += 1
            if apply:
                f.write_text(new, encoding="utf-8")

    # 2) reescribir [[links]] en TODOS los .md del chapter
    link_files = 0
    link_total = 0
    for md in CHAPTER_DIR.rglob("*.md"):
        txt = md.read_text(encoding="utf-8")
        new, n = rewrite_links(txt, rename)
        if n:
            link_files += 1
            link_total += n
            if apply:
                md.write_text(new, encoding="utf-8")

    mode = "APLICADO" if apply else "DRY-RUN (sin escribir)"
    print(f"\n[{mode}] campos id cambiados: {id_changes} | "
          f"archivos con links reescritos: {link_files} | links: {link_total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
