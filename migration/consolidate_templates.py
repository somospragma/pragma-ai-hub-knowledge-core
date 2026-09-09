#!/usr/bin/env python3
"""
b3 — Elimina archivos no-.md de los bundles consolidandolos en un unico
`references/templates.md` por bundle, con una seccion por archivo destino.

Cada plantilla/script queda como:
    ## `<ruta destino dentro del proyecto generado>`
    ```<lang>
    <contenido>
    ```
El agente lee templates.md y materializa cada archivo en su ruta. Los .gitkeep
se descartan (solo marcaban directorios vacios).

Uso:
  python3 migration/consolidate_templates.py --dry-run
  python3 migration/consolidate_templates.py --apply
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CHAPTER_DIR = REPO_ROOT / "chapters" / "calidad"

LANG = {
    ".sh": "bash", ".js": "javascript", ".ts": "typescript", ".java": "java",
    ".xml": "xml", ".json": "json", ".yaml": "yaml", ".yml": "yaml",
    ".properties": "properties", ".gradle": "groovy", ".py": "python",
    ".feature": "gherkin", ".md": "markdown", ".dart": "dart", ".sql": "sql",
}


def guess_lang(target_name: str) -> str:
    # target_name ya sin .tpl; usa su extension real
    suf = Path(target_name).suffix.lower()
    return LANG.get(suf, "text")


def target_name(rel: str) -> str:
    """Quita .tpl final si existe -> nombre del archivo a materializar."""
    return rel[:-4] if rel.endswith(".tpl") else rel


def collect_non_md(root: Path, entry: Path) -> list[Path]:
    return sorted(
        p for p in root.rglob("*")
        if p.is_file() and p != entry and p.suffix != ".md"
    )


def build_templates_md(root: Path, files: list[Path]) -> tuple[str, list[str]]:
    lines = ["# Plantillas del proyecto generado", "",
             ("Cada seccion corresponde a un archivo que el agente debe materializar "
              "en la ruta indicada (relativa a la raiz del proyecto generado). "
              "Respeta los placeholders `{{...}}`."), ""]
    handled = []
    for f in files:
        rel = f.relative_to(root).as_posix()
        if f.name == ".gitkeep":
            handled.append(rel)  # se descarta, sin seccion
            continue
        # ruta destino en el proyecto generado: quita prefijo donde vive la
        # plantilla dentro del asset (references/templates/ o references/) y .tpl.
        # Conserva subdirectorios significativos (scenarios/, shared/, tests/...).
        dest = rel
        for pre in ("references/templates/", "references/"):
            if dest.startswith(pre):
                dest = dest[len(pre):]
                break
        dest = target_name(dest)
        lang = guess_lang(dest)
        try:
            content = f.read_text(encoding="utf-8").rstrip("\n")
        except UnicodeDecodeError:
            handled.append(rel + "  (binario, omitido)")
            continue
        fence = "```"
        # evita colision si el contenido tiene ```
        while fence in content:
            fence += "`"
        lines.append(f"## `{dest}`")
        lines.append("")
        lines.append(f"{fence}{lang}")
        lines.append(content)
        lines.append(fence)
        lines.append("")
        handled.append(rel)
    return "\n".join(lines) + "\n", handled


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    apply = args.apply

    bundle_roots = sorted({p.parent for p in CHAPTER_DIR.rglob("SKILL.md")})
    total_bundles = 0
    total_files = 0
    for root in bundle_roots:
        entry = root / "SKILL.md"
        files = collect_non_md(root, entry)
        if not files:
            continue
        total_bundles += 1
        total_files += len(files)
        rel_root = root.relative_to(REPO_ROOT)
        real = [f for f in files if f.name != ".gitkeep"]
        out = root / "references" / "templates.md"
        if not real:
            # solo .gitkeep: no se crea templates.md, solo se borran los placeholders
            print(f"\n[{rel_root}] solo .gitkeep ({len(files)}) -> se eliminan, sin templates.md")
            if apply:
                for f in files:
                    f.unlink()
            continue
        md, handled = build_templates_md(root, files)
        print(f"\n[{rel_root}] {len(files)} archivos -> references/templates.md")
        for h in handled:
            print(f"    - {h}")
        if apply:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(md, encoding="utf-8")
            # borra originales no-md
            for f in files:
                f.unlink()
            # borra subdir templates/ si quedo vacio
            tdir = root / "references" / "templates"
            if tdir.exists():
                for d in sorted((p for p in tdir.rglob("*") if p.is_dir()),
                                reverse=True):
                    try:
                        d.rmdir()
                    except OSError:
                        pass
                try:
                    tdir.rmdir()
                except OSError:
                    pass

    mode = "APLICADO" if apply else "DRY-RUN"
    print(f"\n[{mode}] bundles afectados: {total_bundles} | archivos no-md: {total_files}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
