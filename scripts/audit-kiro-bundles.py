#!/usr/bin/env python3
"""Auditoria de los bundles generados en salida/{stack}/.kiro/.

Valida:
  1. Coherencia      - IDs unicos por bundle, frontmatter completo, no duplicados.
  2. Cohesion        - tipo de asset coincide con su path destino.
  3. Portabilidad IDE - [[id]] refs resuelven dentro del bundle, paths relativos
                        intra-skill validos, no contiene rutas rotas tipo
                        ../../skills o ../../workflows.
  4. Cobertura       - cuenta esperada vs cuenta real por tipo de asset.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "chapters" / "calidad"
OUT = REPO / "salida"
STACKS = ["karate", "playwright", "k6", "appium-serenity", "appium-core", "appium-wdio"]

FM_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)
WIKI_REF_RE = re.compile(r"\[\[([a-z][a-z0-9-]+)\]\]")
# cualquier link relativo que SALGA del bundle propio se rompe al aplanar en el IDE:
# no solo ../../skills/... sino tambien ../otro-skill/references/X.md
REL_BROKEN_RE = re.compile(r"\]\(\.\./[^)]+\.md\)")


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


def collect_source_ids() -> tuple[dict[str, set[str]], set[str], set[str], set[str]]:
    """Devuelve:
      - expected[stack]: ids esperados en el bundle de cada stack (excluye hooks)
      - all_ids: TODOS los ids con frontmatter en el chapter (cross-stack y stack)
      - hook_ids: ids de hooks (van en hooks/, no en skills/steering)
      - reference_paths: nombres de archivos en references/ subfolders (no son IDs validos)
    """
    by_stack: dict[str, set[str]] = {s: set() for s in STACKS}
    cross_cutting: set[str] = set()
    hook_ids: set[str] = set()
    # Un asset de `_all/` puede acotarse con `applies_to_stacks`. Ahi no falta del
    # bundle: esta excluido a proposito, y contarlo como faltante enmascara los
    # que si faltan.
    scoped: dict[str, set[str]] = {}

    for pattern in [
        "steering/_all/*.md",
        "skills/_all/*.md",
        "skills/_all/*/SKILL.md",
        "workflows/_all/*.md",
        "prompts/_all/*.md",
    ]:
        for f in SRC.glob(pattern):
            fm, _ = parse_fm(f.read_text(encoding="utf-8"))
            if not fm.get("id"):
                continue
            raw = fm.get("applies_to_stacks", "").strip()
            if raw:
                scoped[fm["id"]] = {s.strip() for s in raw.strip("[]").split(",") if s.strip()}
            cross_cutting.add(fm["id"])

    for f in SRC.glob("hooks/_all/*.md"):
        fm, _ = parse_fm(f.read_text(encoding="utf-8"))
        if fm.get("id"):
            hook_ids.add(fm["id"])

    for s in STACKS:
        for pattern in [
            f"skills/{s}/*.md",
            f"skills/{s}/*/SKILL.md",
            f"workflows/{s}/*.md",
            f"prompts/{s}/*.md",
        ]:
            for f in SRC.glob(pattern):
                fm, _ = parse_fm(f.read_text(encoding="utf-8"))
                if fm.get("id"):
                    by_stack[s].add(fm["id"])

    # El conocimiento de cuenta vive en accounts/ y lo sincroniza sync_account.py,
    # no viaja en el bundle del chapter. Sus ids se referencian legitimamente desde
    # el chapter, asi que se indexan para no reportarlos como referencias rotas.
    account_ids: set[str] = set()
    for f in (REPO / "accounts").rglob("*.md"):
        fm, _ = parse_fm(f.read_text(encoding="utf-8"))
        if fm.get("id"):
            account_ids.add(fm["id"])

    all_ids = cross_cutting | hook_ids | account_ids
    for s in STACKS:
        all_ids |= by_stack[s]

    # reference filenames (sin extension) -> indica candidatos a "ID-like" que en realidad
    # son archivos dentro de references/ y no SKILLs reales
    ref_files: set[str] = set()
    for ref in SRC.glob("skills/**/references/*.md"):
        ref_files.add(ref.stem)
    for ref in SRC.glob("skills/**/references/**/*.md"):
        ref_files.add(ref.stem)

    expected = {}
    for s in STACKS:
        universal = {i for i in cross_cutting if s in scoped.get(i, {s})}
        expected[s] = universal | by_stack[s]
    return (expected, all_ids, hook_ids, ref_files)


def audit_stack(
    stack: str,
    expected_ids: set[str],
    all_chapter_ids: set[str],
    hook_ids: set[str],
    reference_files: set[str],
) -> dict:
    kiro = OUT / stack / ".kiro"
    findings = {
        "missing_assets": [],
        "extra_assets": [],
        "duplicate_ids": [],
        "missing_frontmatter": [],
        "refs_cross_stack_ok": defaultdict(list),    # ref existe en chapter pero en otro stack -> esperado
        "refs_to_reference_file": defaultdict(list),  # ref apunta a archivo dentro de references/ -> bug del chapter
        "refs_unknown": defaultdict(list),            # ref no existe en ningun lado -> bug del chapter
        "broken_relative_paths": [],
        "counts": defaultdict(int),
    }

    # 1. Inventario instalado
    installed_ids: set[str] = set()
    id_to_paths: dict[str, list[Path]] = defaultdict(list)

    # skills: .kiro/skills/{id}/SKILL.md
    for skill_md in (kiro / "skills").glob("*/SKILL.md"):
        sid = skill_md.parent.name
        installed_ids.add(sid)
        id_to_paths[sid].append(skill_md)
        findings["counts"]["skill"] += 1
        fm, _ = parse_fm(skill_md.read_text(encoding="utf-8"))
        if not fm.get("name"):
            findings["missing_frontmatter"].append(str(skill_md.relative_to(kiro)))

    # steering -> steering/{id}.md ; workflow -> workflows/{id}.workflow.md ;
    # prompt -> prompts/{id}.prompt.md  (el builder dejo de aplanarlos a steering)
    flat = []
    for sub, suffix in (("steering", ".md"), ("workflows", ".workflow.md"),
                        ("prompts", ".prompt.md")):
        for f in (kiro / sub).glob("*" + suffix):
            flat.append((f, f.name[: -len(suffix)]))
    for st, sid in flat:
        installed_ids.add(sid)
        id_to_paths[sid].append(st)
        findings["counts"]["steering_or_flat"] += 1
        fm, _ = parse_fm(st.read_text(encoding="utf-8"))
        if not fm.get("name"):
            findings["missing_frontmatter"].append(str(st.relative_to(kiro)))

    # hooks: .kiro/hooks/*.kiro.hook + telemetry .md
    hooks_dir = kiro / "hooks"
    if hooks_dir.exists():
        for f in hooks_dir.iterdir():
            if f.is_file():
                findings["counts"]["hook"] += 1

    # hooks instalados (lookup por filename stem) - no son IDs validos
    installed_hook_ids: set[str] = set()
    if hooks_dir.exists():
        for f in hooks_dir.iterdir():
            if f.is_file():
                name = f.name
                for ext in (".kiro.hook", ".md"):
                    if name.endswith(ext):
                        installed_hook_ids.add(name[: -len(ext)])
                        break

    # 2. Cobertura
    findings["missing_assets"] = sorted(expected_ids - installed_ids - installed_hook_ids)
    # extras: instalado que no esta en expected ni es hook
    findings["extra_assets"] = sorted(
        installed_ids - expected_ids - installed_hook_ids
    )

    # 3. IDs duplicados
    for sid, paths in id_to_paths.items():
        if len(paths) > 1:
            findings["duplicate_ids"].append(
                {sid: [str(p.relative_to(kiro)) for p in paths]}
            )

    # 4. Wiki refs [[id]] - clasificar en tres categorias
    all_md_files = []
    for sub in ["skills", "steering", "workflows", "prompts"]:
        d = kiro / sub
        if d.is_dir():
            all_md_files.extend(d.rglob("*.md"))
    for f in all_md_files:
        text = f.read_text(encoding="utf-8")
        for ref in set(WIKI_REF_RE.findall(text)):
            if ref in installed_ids:
                continue  # resuelve dentro del bundle
            rel = str(f.relative_to(kiro))
            if ref in all_chapter_ids:
                # existe en el chapter pero no en este stack (cross-stack legitimo)
                findings["refs_cross_stack_ok"][ref].append(rel)
            elif ref in reference_files:
                # es un archivo dentro de references/, no un SKILL ID -> bug del chapter
                findings["refs_to_reference_file"][ref].append(rel)
            else:
                # no existe en ningun lado -> bug del chapter
                findings["refs_unknown"][ref].append(rel)

    # 5. Paths relativos rotos (que apuntan a folders aplanados)
    for f in all_md_files:
        text = f.read_text(encoding="utf-8")
        for line_num, line in enumerate(text.splitlines(), 1):
            if REL_BROKEN_RE.search(line):
                findings["broken_relative_paths"].append(
                    f"{f.relative_to(kiro)}:{line_num}: {line.strip()[:120]}"
                )

    return findings


def report(stack: str, findings: dict) -> int:
    """Imprime hallazgos. Retorna numero de issues criticos."""
    critical = 0
    print(f"\n=== {stack.upper()} ===")
    c = findings["counts"]
    print(
        f"Conteo instalado: skills={c['skill']} "
        f"steering+workflows+prompts={c['steering_or_flat']} hooks={c['hook']}"
    )

    if findings["missing_assets"]:
        critical += len(findings["missing_assets"])
        print(f"\n  FALTAN {len(findings['missing_assets'])} asset(s):")
        for sid in findings["missing_assets"]:
            print(f"    - {sid}")

    if findings["extra_assets"]:
        print(f"\n  EXTRAS {len(findings['extra_assets'])} asset(s) no en chapter:")
        for sid in findings["extra_assets"]:
            print(f"    - {sid}")

    if findings["duplicate_ids"]:
        critical += len(findings["duplicate_ids"])
        print(f"\n  IDs DUPLICADOS:")
        for d in findings["duplicate_ids"]:
            for sid, paths in d.items():
                print(f"    - {sid}: {paths}")

    if findings["missing_frontmatter"]:
        critical += len(findings["missing_frontmatter"])
        print(f"\n  FRONTMATTER INCOMPLETO ({len(findings['missing_frontmatter'])}):")
        for p in findings["missing_frontmatter"]:
            print(f"    - {p}")

    cross_ok = findings["refs_cross_stack_ok"]
    if cross_ok:
        print(
            f"\n  REFS CROSS-STACK (esperadas para single-stack install, "
            f"{len(cross_ok)} ids):"
        )
        for ref in sorted(cross_ok)[:5]:
            print(f"    - [[{ref}]]")
        if len(cross_ok) > 5:
            print(f"    ... +{len(cross_ok) - 5} mas (cross-stack)")

    ref_to_refs = findings["refs_to_reference_file"]
    if ref_to_refs:
        critical += len(ref_to_refs)
        print(
            f"\n  REFS A ARCHIVOS references/ EN VEZ DE SKILL IDs "
            f"(BUG DEL CHAPTER, {len(ref_to_refs)}):"
        )
        for ref, callers in sorted(ref_to_refs.items()):
            print(f"    - [[{ref}]] -> en {len(callers)} archivo(s)")
            for c in callers[:2]:
                print(f"        {c}")
            if len(callers) > 2:
                print(f"        ... +{len(callers) - 2} mas")

    unknown = findings["refs_unknown"]
    if unknown:
        critical += len(unknown)
        print(
            f"\n  REFS A IDs INEXISTENTES (BUG DEL CHAPTER, {len(unknown)}):"
        )
        for ref, callers in sorted(unknown.items()):
            print(f"    - [[{ref}]] -> en {len(callers)} archivo(s)")
            for c in callers[:2]:
                print(f"        {c}")
            if len(callers) > 2:
                print(f"        ... +{len(callers) - 2} mas")

    if findings["broken_relative_paths"]:
        critical += len(findings["broken_relative_paths"])
        print(
            f"\n  PATHS RELATIVOS QUE ROMPEN POST-FLATTEN "
            f"({len(findings['broken_relative_paths'])}):"
        )
        for p in findings["broken_relative_paths"][:10]:
            print(f"    - {p}")
        if len(findings["broken_relative_paths"]) > 10:
            print(f"    ... +{len(findings['broken_relative_paths']) - 10} mas")

    if critical == 0:
        print("  OK - sin hallazgos criticos")
    return critical


def main() -> int:
    expected, all_ids, hook_ids, ref_files = collect_source_ids()
    total_critical = 0
    summary: dict[str, dict] = {}
    for s in STACKS:
        f = audit_stack(s, expected[s], all_ids, hook_ids, ref_files)
        summary[s] = f
        total_critical += report(s, f)

    print("\n=== RESUMEN ===")
    print(
        f"{'stack':<12} {'inst':>5} {'falt':>5} {'extra':>5} "
        f"{'xstack':>7} {'ref->ref':>9} {'unknown':>8} {'paths':>6}"
    )
    for s in STACKS:
        f = summary[s]
        c = f["counts"]
        total_installed = c["skill"] + c["steering_or_flat"]
        print(
            f"{s:<12} {total_installed:>5} {len(f['missing_assets']):>5} "
            f"{len(f['extra_assets']):>5} {len(f['refs_cross_stack_ok']):>7} "
            f"{len(f['refs_to_reference_file']):>9} {len(f['refs_unknown']):>8} "
            f"{len(f['broken_relative_paths']):>6}"
        )

    print(f"\nIssues criticos totales (faltantes + bugs de chapter): {total_critical}")
    return 1 if total_critical > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
