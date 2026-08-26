#!/usr/bin/env python3
"""
Genera bundles .kiro/ para cada stack del Chapter Calidad emulando lo que la CLI
pragma-ai produciria segun _config/ides.json. Se usa como workaround mientras
el Hub publica el bundle stale v1.0.0.

Mapeo de paths (Kiro workspace), verificado contra una instalacion real de la
CLI en un repositorio de cliente:
  steering  -> .kiro/steering/{id}.md
  workflow  -> .kiro/workflows/{id}.workflow.md
  prompt    -> .kiro/prompts/{id}.prompt.md
  hook      -> .kiro/hooks/{id}.kiro.hook
  skill     -> .kiro/skills/{id}/SKILL.md (+ references/ si es folder-style)

Frontmatter transformation:
  - skill    : name + description
  - steering : inclusion: always + name + description
  - workflow : inclusion: manual + name + description
  - prompt   : inclusion: manual + name + description
  - hook     : trigger + description

Sobre `inclusion`
-----------------
Kiro reconoce tres valores: `always`, `fileMatch` y `manual`. Un valor que no
sea uno de esos cae al default, que es cargar el archivo en cada turno. La
version anterior de este script emitia `inclusion: auto`, que no es valido: los
10 workflows del chapter entraban en cada peticion. Medido sobre la instalacion
real, la capa siempre-on pesaba 143 KB (~41.000 tokens POR TURNO).

Los workflows pasan a `manual` porque no son contexto: son procedimientos que
se invocan cuando toca. Lo que debe estar siempre presente es el steering, que
son las compuertas y las prohibiciones.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "chapters" / "calidad"
OUT = REPO / "salida"

STACKS = ["karate", "playwright", "k6", "appium-serenity", "appium-core", "appium-wdio"]

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    fm_block, body = m.group(1), m.group(2)
    fm: dict = {}
    for line in fm_block.splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm, body.lstrip("\n")


def kiro_frontmatter_for(asset_type: str, fm: dict) -> str:
    name = fm.get("id", "")
    desc = fm.get("description", "")
    if asset_type == "skill":
        return f"---\nname: {name}\ndescription: {desc}\n---\n\n"
    if asset_type == "steering":
        return f"---\ninclusion: always\nname: {name}\ndescription: {desc}\n---\n\n"
    if asset_type in ("workflow", "prompt"):
        return f"---\ninclusion: manual\nname: {name}\ndescription: {desc}\n---\n\n"
    if asset_type == "hook":
        trigger = fm.get("trigger", "agentStop")
        return f"---\ntrigger: {trigger}\ndescription: {desc}\n---\n\n"
    raise ValueError(f"unknown asset_type: {asset_type}")


def write_asset(src_path: Path, dst_path: Path, asset_type: str) -> None:
    raw = src_path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(raw)
    if not fm.get("id"):
        # references/ y archivos sin frontmatter se copian tal cual
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        dst_path.write_text(raw, encoding="utf-8")
        return
    new_fm = kiro_frontmatter_for(asset_type, fm)
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    dst_path.write_text(new_fm + body, encoding="utf-8")


def find_skill_files(folder: Path) -> list[tuple[Path, str]]:
    """Devuelve [(src_path, id)] para cada skill en folder.
    Maneja atom (.md) y folder-style (SKILL.md dentro de subfolder)."""
    out: list[tuple[Path, str]] = []
    for entry in sorted(folder.iterdir()):
        if entry.is_file() and entry.suffix == ".md":
            raw = entry.read_text(encoding="utf-8")
            fm, _ = parse_frontmatter(raw)
            if fm.get("type") == "skill":
                out.append((entry, fm["id"]))
        elif entry.is_dir():
            skill_md = entry / "SKILL.md"
            if skill_md.exists():
                raw = skill_md.read_text(encoding="utf-8")
                fm, _ = parse_frontmatter(raw)
                if fm.get("type") == "skill":
                    out.append((skill_md, fm["id"]))
    return out


def install_skill(src: Path, asset_id: str, kiro_root: Path) -> None:
    skill_dir = kiro_root / "skills" / asset_id
    write_asset(src, skill_dir / "SKILL.md", "skill")
    # Si es folder-style, copiar references/ tal cual (sin frontmatter transform)
    src_refs = src.parent / "references"
    if src_refs.exists():
        dst_refs = skill_dir / "references"
        if dst_refs.exists():
            shutil.rmtree(dst_refs)
        shutil.copytree(src_refs, dst_refs)


# Cada tipo tiene su carpeta y su sufijo en el workspace de Kiro.
FLAT_LAYOUT = {
    "steering": ("steering", ".md"),
    "workflow": ("workflows", ".workflow.md"),
    "prompt": ("prompts", ".prompt.md"),
}


def install_flat(src: Path, asset_type: str, kiro_root: Path) -> str | None:
    """Steering / workflow / prompt, cada uno en su carpeta."""
    raw = src.read_text(encoding="utf-8")
    fm, _ = parse_frontmatter(raw)
    if not fm.get("id"):
        return None
    folder, suffix = FLAT_LAYOUT[asset_type]
    dst = kiro_root / folder / f"{fm['id']}{suffix}"
    write_asset(src, dst, asset_type)
    return fm["id"]


def applies_to(src: Path, stack: str) -> bool:
    """Decide si un asset de `_all/` corresponde a este stack.

    `_all/` significaba «va a todos los bundles», y eso mete SEO, accesibilidad
    y contratos entre servicios en un bundle de Appium, donde no tienen nada que
    hacer. Un asset puede acotarse declarando `applies_to_stacks` en su
    frontmatter; sin el campo se sigue instalando en todos, que es el
    comportamiento anterior y el correcto para lo verdaderamente transversal.
    """
    fm, _ = parse_frontmatter(src.read_text(encoding="utf-8"))
    raw = fm.get("applies_to_stacks", "").strip()
    if not raw:
        return True
    allowed = {s.strip() for s in raw.strip("[]").split(",") if s.strip()}
    return stack in allowed


def install_hook(src: Path, kiro_root: Path) -> str | None:
    raw = src.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(raw)
    if not fm.get("id"):
        return None
    dst = kiro_root / "hooks" / f"{fm['id']}.kiro.hook"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(kiro_frontmatter_for("hook", fm) + body, encoding="utf-8")
    return fm["id"]


def build_for_stack(stack: str) -> dict:
    kiro = OUT / stack / ".kiro"
    if kiro.exists():
        shutil.rmtree(kiro)
    kiro.mkdir(parents=True, exist_ok=True)

    counts = {"steering": 0, "skill": 0, "workflow": 0, "prompt": 0, "hook": 0}
    installed_ids: list[str] = []
    skipped: list[str] = []

    # 1) Steering _all/
    steering_dir = SRC / "steering" / "_all"
    if steering_dir.exists():
        for f in sorted(steering_dir.glob("*.md")):
            sid = install_flat(f, "steering", kiro)
            if sid:
                counts["steering"] += 1
                installed_ids.append(f"steering: {sid}")

    # 2) Skills _all/
    all_skills_dir = SRC / "skills" / "_all"
    for src, sid in find_skill_files(all_skills_dir):
        if not applies_to(src, stack):
            skipped.append(f"skill (_all): {sid}")
            continue
        install_skill(src, sid, kiro)
        counts["skill"] += 1
        installed_ids.append(f"skill (_all): {sid}")

    # 3) Skills {stack}/
    stack_skills_dir = SRC / "skills" / stack
    if stack_skills_dir.exists():
        for src, sid in find_skill_files(stack_skills_dir):
            install_skill(src, sid, kiro)
            counts["skill"] += 1
            installed_ids.append(f"skill ({stack}): {sid}")

    # 4) Workflows _all/
    wf_all = SRC / "workflows" / "_all"
    if wf_all.exists():
        for f in sorted(wf_all.glob("*.md")):
            if not applies_to(f, stack):
                skipped.append(f"workflow (_all): {f.stem}")
                continue
            sid = install_flat(f, "workflow", kiro)
            if sid:
                counts["workflow"] += 1
                installed_ids.append(f"workflow (_all): {sid}")

    # 5) Workflows {stack}/
    wf_stack = SRC / "workflows" / stack
    if wf_stack.exists():
        for f in sorted(wf_stack.glob("*.md")):
            sid = install_flat(f, "workflow", kiro)
            if sid:
                counts["workflow"] += 1
                installed_ids.append(f"workflow ({stack}): {sid}")

    # 6) Prompts _all/
    pr_all = SRC / "prompts" / "_all"
    if pr_all.exists():
        for f in sorted(pr_all.glob("*.md")):
            if not applies_to(f, stack):
                skipped.append(f"prompt (_all): {f.stem}")
                continue
            sid = install_flat(f, "prompt", kiro)
            if sid:
                counts["prompt"] += 1
                installed_ids.append(f"prompt (_all): {sid}")

    # 7) Prompts {stack}/
    pr_stack = SRC / "prompts" / stack
    if pr_stack.exists():
        for f in sorted(pr_stack.glob("*.md")):
            sid = install_flat(f, "prompt", kiro)
            if sid:
                counts["prompt"] += 1
                installed_ids.append(f"prompt ({stack}): {sid}")

    # 8) Hooks _all/ del chapter
    hooks_all = SRC / "hooks" / "_all"
    if hooks_all.exists():
        for f in sorted(hooks_all.glob("*.md")):
            sid = install_hook(f, kiro)
            if sid:
                counts["hook"] += 1
                installed_ids.append(f"hook (_all): {sid}")

    # 8) Hooks de telemetria que la CLI pragma-ai inyecta (copiados de entrada/.kiro/hooks/)
    telemetry_src = REPO / "entrada" / ".kiro" / "hooks"
    if telemetry_src.exists():
        for f in sorted(telemetry_src.glob("*.md")):
            dst = kiro / "hooks" / f.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(f, dst)
            counts["hook"] += 1
            installed_ids.append(f"hook (telemetry): {f.stem}")

    # 9) Manifest reproducible
    manifest = kiro / "PRAGMA_BUNDLE.md"
    total = sum(counts.values())
    always_on = sorted((kiro / "steering").glob("*.md"))
    always_on_bytes = sum(f.stat().st_size for f in always_on)
    lines = [
        "# Bundle generado por scripts/build-kiro-bundles.py",
        "",
        f"Stack: {stack}",
        "Chapter: calidad",
        f"Total assets: {total}",
        "",
        "## Capa siempre-on",
        "",
        "Lo que Kiro carga en CADA turno sin que nadie lo pida. Es el "
        "multiplicador del costo de la sesion: se paga entero por peticion.",
        "",
        f"- archivos: {len(always_on)}",
        f"- bytes: {always_on_bytes:,}",
        f"- tokens estimados por turno: ~{int(always_on_bytes / 3.5):,}",
        "",
        "## Conteo por tipo",
        "",
    ]
    for k, v in counts.items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Inventario completo")
    lines.append("")
    for entry in installed_ids:
        lines.append(f"- {entry}")
    if skipped:
        lines.append("")
        lines.append("## Excluidos por `applies_to_stacks`")
        lines.append("")
        lines.append("Assets de `_all/` que declaran no aplicar a este stack.")
        lines.append("")
        for entry in skipped:
            lines.append(f"- {entry}")
    lines.append("")
    manifest.write_text("\n".join(lines), encoding="utf-8")
    return counts


def main() -> None:
    summary: dict[str, dict] = {}
    for stack in STACKS:
        summary[stack] = build_for_stack(stack)
    print(f"{'stack':<12} {'steering':>9} {'skill':>6} {'workflow':>9} {'prompt':>7} {'hook':>5} {'total':>6}")
    for stack, counts in summary.items():
        total = sum(counts.values())
        print(
            f"{stack:<12} {counts['steering']:>9} {counts['skill']:>6} "
            f"{counts['workflow']:>9} {counts['prompt']:>7} {counts['hook']:>5} {total:>6}"
        )


if __name__ == "__main__":
    main()
