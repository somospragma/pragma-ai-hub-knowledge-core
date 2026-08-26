#!/usr/bin/env python3
"""Reescribe refs [[id]] rotas del chapter Calidad a la convencion correcta.

Patrones que detecta y arregla:

A) `[[<stack>-<ref-stem>]]` que en realidad apunta a un archivo dentro de
   `references/` de algun SKILL del stack -> reescribe a:
   - Si la cita vive dentro del MISMO skill folder: usar la ruta relativa
     a `references/X.md`.
   - Si la cita vive en otro skill: `[[<owning-skill-id>]] (consultar
     references/X.md en su subfolder)`.

B) Typos conocidos (`karate-negative-coverage` -> `karate-negative-coverage-formula`).

C) Ids que no existen en ningun lado y tampoco como reference: log y skip.

Corre sobre `chapters/calidad/` y produce un report dry-run o aplica cambios.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "chapters" / "calidad"
APPLY = "--apply" in sys.argv

FM_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)
WIKI_REF_RE = re.compile(r"\[\[([a-z][a-z0-9-]+)\]\]")
PATH_REF_RE = re.compile(
    r"\[\[([a-z][a-z0-9-]+)/references/([a-z0-9][a-z0-9./-]*\.md)\]\]"
)


def parse_fm(text: str) -> tuple[dict, str]:
    m = FM_RE.match(text)
    if not m:
        return {}, text
    fm: dict = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm, m.group(2)


def build_indexes() -> tuple[set[str], dict[str, list[tuple[str, str]]]]:
    """Devuelve:
      - valid_ids: todos los ids reales del chapter (con frontmatter)
      - ref_index: { reference_stem: [(owning_skill_id, reference_filename), ...] }
        Multiples entradas porque el mismo stem (project-structure, convention-detection)
        puede existir en varios skills cross-stack. La desambiguacion se hace por
        prefijo de stack en el nombre del ref.
    """
    valid_ids: set[str] = set()
    ref_index: dict[str, list[tuple[str, str]]] = defaultdict(list)

    for pattern in [
        "steering/_all/*.md",
        "hooks/_all/*.md",
        "skills/_all/*.md",
        "skills/_all/*/SKILL.md",
        "skills/karate/*.md",
        "skills/karate/*/SKILL.md",
        "skills/playwright/*.md",
        "skills/playwright/*/SKILL.md",
        "skills/k6/*.md",
        "skills/k6/*/SKILL.md",
        "skills/appium/*.md",
        "skills/appium/*/SKILL.md",
        "workflows/_all/*.md",
        "workflows/karate/*.md",
        "workflows/playwright/*.md",
        "workflows/k6/*.md",
        "workflows/appium/*.md",
        "prompts/karate/*.md",
        "prompts/playwright/*.md",
        "prompts/k6/*.md",
        "prompts/appium/*.md",
    ]:
        for f in SRC.glob(pattern):
            fm, _ = parse_fm(f.read_text(encoding="utf-8"))
            if fm.get("id"):
                valid_ids.add(fm["id"])

    # Build ref_index: mapa stem -> [(skill_id, filename_inside_references), ...]
    for skill_md in SRC.glob("skills/**/SKILL.md"):
        skill_fm, _ = parse_fm(skill_md.read_text(encoding="utf-8"))
        skill_id = skill_fm.get("id")
        if not skill_id:
            continue
        refs_dir = skill_md.parent / "references"
        if refs_dir.exists():
            for ref in refs_dir.rglob("*.md"):
                stem = ref.stem
                # filename inside references/ (sin prefijo "references/")
                rel_to_refs = str(ref.relative_to(refs_dir))
                ref_index[stem].append((skill_id, rel_to_refs))
    return valid_ids, dict(ref_index)


# Typos conocidos: bad -> good (sintaxis [[id]] valida en ambos lados)
KNOWN_TYPOS = {
    "karate-negative-coverage": "karate-negative-coverage-formula",
    "karate-feature-file-location-constraint": "karate-file-location-constraint",
}


def find_owning_skill_dir(file_path: Path) -> Path | None:
    """Si file_path vive dentro de un skill folder, retorna el dir del skill."""
    for parent in file_path.parents:
        if (parent / "SKILL.md").exists():
            return parent
    return None


def resolve_ref(
    ref: str,
    valid_ids: set[str],
    ref_index: dict[str, list[tuple[str, str]]],
) -> tuple[str, str, str] | None:
    """Resuelve un ref rota. Devuelve (owning_skill_id, ref_filename, kind) o None.
    kind in {'reference', 'typo_id'}.
    Cuando el stem aparece en multiples skills, desambigua por prefijo de stack.
    """
    if ref in valid_ids:
        return None  # ya resuelve, no hace falta tocar
    # Typos primero
    fixed = KNOWN_TYPOS.get(ref)
    if fixed and fixed in valid_ids:
        return ("__id__", fixed, "typo_id")
    if fixed:
        ref = fixed
    # Strategy: si tiene prefijo de stack, prioriza skills cuyo id arranca con ese stack
    for stack in ("karate", "playwright", "k6", "appium"):
        if ref.startswith(f"{stack}-"):
            stem = ref[len(stack) + 1 :]
            if stem in ref_index:
                matches = ref_index[stem]
                # Filtra por stack
                stack_matches = [
                    (sid, fn) for sid, fn in matches if sid.startswith(f"{stack}-")
                ]
                if stack_matches:
                    return (*stack_matches[0], "reference")
                # Si no hay match exacto de stack pero hay otros, descarta:
                # eso significa que la ref es ambigua. Reportar como no resuelta.
                return None
    # Sin prefijo de stack: solo resuelve si el stem es unico
    if ref in ref_index and len(ref_index[ref]) == 1:
        sid, fn = ref_index[ref][0]
        return (sid, fn, "reference")
    return None


def build_replacement(
    file_path: Path,
    original_ref: str,
    resolved: tuple[str, str, str],
) -> str:
    """Construye el reemplazo en formato apropiado."""
    skill_id, ref_filename, kind = resolved
    if kind == "typo_id":
        # ref_filename aca es el id correcto
        return f"[[{ref_filename}]]"
    # kind == 'reference': la ref apunta a references/<ref_filename> del skill <skill_id>
    owning_dir = find_owning_skill_dir(file_path)
    if owning_dir:
        skill_md = owning_dir / "SKILL.md"
        if skill_md.exists():
            fm, _ = parse_fm(skill_md.read_text(encoding="utf-8"))
            if fm.get("id") == skill_id:
                # Misma carpeta de skill -> ruta intra-skill
                # Si el archivo que cita YA vive dentro de references/, es sibling
                try:
                    file_path.relative_to(owning_dir / "references")
                    return f"`{ref_filename}`"
                except ValueError:
                    return f"`references/{ref_filename}`"
    # Cross-skill
    return f"[[{skill_id}]] (consultar `references/{ref_filename}` en su subfolder)"


def scan_and_fix() -> tuple[dict[str, int], list[str]]:
    valid_ids, ref_index = build_indexes()
    stats = {"files_scanned": 0, "files_modified": 0, "refs_fixed": 0, "refs_unresolved": 0}
    unresolved: list[str] = []
    modifications: list[str] = []

    # Scan all md files in chapters/calidad/
    for f in SRC.rglob("*.md"):
        stats["files_scanned"] += 1
        text = f.read_text(encoding="utf-8")
        new_text = text
        changed = False

        # Pass 1: refs en formato [[id]]
        refs = set(WIKI_REF_RE.findall(text))
        broken = [r for r in refs if r not in valid_ids]
        for ref in broken:
            resolved = resolve_ref(ref, valid_ids, ref_index)
            if not resolved:
                unresolved.append(f"{f.relative_to(SRC)}: [[{ref}]]")
                stats["refs_unresolved"] += 1
                continue
            replacement = build_replacement(f, ref, resolved)
            pattern = f"[[{ref}]]"
            if pattern in new_text:
                count_before = new_text.count(pattern)
                new_text = new_text.replace(pattern, replacement)
                stats["refs_fixed"] += count_before
                changed = True
                modifications.append(
                    f"{f.relative_to(SRC)}: [[{ref}]] -> {replacement}"
                )

        # Pass 2: refs en formato [[skill-id/references/file.md]]
        path_refs = set(PATH_REF_RE.findall(new_text))
        for skill_id, ref_filename in path_refs:
            if skill_id not in valid_ids:
                unresolved.append(
                    f"{f.relative_to(SRC)}: [[{skill_id}/references/{ref_filename}]]"
                )
                stats["refs_unresolved"] += 1
                continue
            replacement = build_replacement(
                f, f"{skill_id}/references/{ref_filename}",
                (skill_id, ref_filename, "reference"),
            )
            pattern = f"[[{skill_id}/references/{ref_filename}]]"
            if pattern in new_text:
                count_before = new_text.count(pattern)
                new_text = new_text.replace(pattern, replacement)
                stats["refs_fixed"] += count_before
                changed = True
                modifications.append(
                    f"{f.relative_to(SRC)}: [[{skill_id}/references/{ref_filename}]] -> {replacement}"
                )

        if changed:
            stats["files_modified"] += 1
            if APPLY:
                f.write_text(new_text, encoding="utf-8")

    return stats, unresolved, modifications


def main() -> int:
    stats, unresolved, modifications = scan_and_fix()
    print(f"Modo: {'APPLY' if APPLY else 'DRY-RUN (usa --apply para aplicar)'}")
    print(f"")
    print(f"Archivos escaneados: {stats['files_scanned']}")
    print(f"Archivos {'modificados' if APPLY else 'a modificar'}: {stats['files_modified']}")
    print(f"Refs {'reescritas' if APPLY else 'a reescribir'}: {stats['refs_fixed']}")
    print(f"Refs sin resolver: {stats['refs_unresolved']}")
    print(f"")
    if unresolved:
        print("=== SIN RESOLVER ===")
        for u in unresolved[:20]:
            print(f"  {u}")
        if len(unresolved) > 20:
            print(f"  ... +{len(unresolved) - 20} mas")
    print(f"")
    print(f"=== MUESTRA DE REWRITES (primeros 30) ===")
    for m in modifications[:30]:
        print(f"  {m}")
    if len(modifications) > 30:
        print(f"  ... +{len(modifications) - 30} mas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
