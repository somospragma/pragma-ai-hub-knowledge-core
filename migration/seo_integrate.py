#!/usr/bin/env python3
"""
b5 — Integra los assets SEO (entrada/ChapterSEO-Pragma-main) al chapter calidad
como assets chapter-scoped transversales en skills/_all y workflows/_all.

- 8 skills -> chapters/calidad/skills/_all/seo-<x>.md (single-file, scope chapter)
- 1 workflow -> chapters/calidad/workflows/_all/seo-audit.workflow.md
Convierte el frontmatter Agent Skills (name/description) al frontmatter calidad
(id calidad-seo-*, version, scope, type, chapter, description, tags).

Uso: --dry-run | --apply
"""
from __future__ import annotations
import argparse
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "entrada" / "ChapterSEO-Pragma-main"
SKILLS_OUT = REPO_ROOT / "chapters" / "calidad" / "skills" / "_all"
WF_OUT = REPO_ROOT / "chapters" / "calidad" / "workflows" / "_all"

TAGS = {
    "seo-technical": ["seo", "web", "tecnico", "indexacion", "crawl"],
    "seo-on-page": ["seo", "web", "on-page", "metadata", "headings"],
    "seo-performance": ["seo", "web", "performance", "core-web-vitals"],
    "seo-schema": ["seo", "web", "schema", "json-ld", "datos-estructurados"],
    "seo-images": ["seo", "web", "imagenes", "alt", "cls"],
    "seo-sitemap": ["seo", "web", "sitemap", "indexnow"],
    "seo-hreflang": ["seo", "web", "hreflang", "i18n"],
    "seo-accessibility": ["seo", "web", "accesibilidad", "wcag", "aria"],
}


def split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines()
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return {}, text
    fm_lines = lines[1:end]
    body = "\n".join(lines[end + 1:]).lstrip("\n")
    # parse description folded (>) y name
    fm = {}
    i = 0
    while i < len(fm_lines):
        line = fm_lines[i]
        m = re.match(r"^(\w[\w-]*):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val in (">", "|", ">-", "|-"):
                buf = []
                i += 1
                while i < len(fm_lines) and (fm_lines[i].startswith("  ") or not fm_lines[i].strip()):
                    buf.append(fm_lines[i].strip())
                    i += 1
                fm[key] = " ".join(x for x in buf if x).strip()
                continue
            fm[key] = val.strip("'\"")
        i += 1
    return fm, body


def calidad_frontmatter(asset_id: str, description: str, tags: list[str],
                        atype: str) -> str:
    tag_str = ", ".join(tags)
    desc = description.replace('"', "'")
    return (
        "---\n"
        f"id: {asset_id}\n"
        "version: 1.0.0\n"
        "scope: chapter\n"
        f"type: {atype}\n"
        "chapter: calidad\n"
        f"description: \"{desc}\"\n"
        f"tags: [{tag_str}]\n"
        "---\n\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    apply = args.apply

    created = []
    # skills
    for d in sorted((SRC / "skills").iterdir()):
        if not d.is_dir():
            continue
        name = d.name  # seo-on-page
        fm, body = split_frontmatter((d / "SKILL.md").read_text(encoding="utf-8"))
        asset_id = f"calidad-{name}"
        desc = fm.get("description", "")
        tags = TAGS.get(name, ["seo", "web"])
        out = SKILLS_OUT / f"{name}.md"
        content = calidad_frontmatter(asset_id, desc, tags, "skill") + body
        created.append((out, content, asset_id))

    # workflow
    wf_src = SRC / "workflow" / "SEO" / "workflow.md"
    fm, body = split_frontmatter(wf_src.read_text(encoding="utf-8"))
    if not body:
        body = wf_src.read_text(encoding="utf-8")  # sin frontmatter: todo es body
    wf_id = "calidad-seo-audit-workflow"
    wf_desc = ("Workflow de auditoria SEO tecnica agnostica de stack para pruebas web "
               "(aplica a Playwright y futuros stacks web del chapter calidad).")
    wf_content = calidad_frontmatter(wf_id, wf_desc,
                                     ["seo", "web", "workflow", "auditoria"],
                                     "workflow") + body
    created.append((WF_OUT / "seo-audit.workflow.md", wf_content, wf_id))

    print(f"Assets SEO a crear: {len(created)}")
    for out, content, aid in created:
        rel = out.relative_to(REPO_ROOT)
        print(f"  {aid}  ->  {rel}")
        if apply:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(content, encoding="utf-8")

    print(f"\n[{'APLICADO' if apply else 'DRY-RUN'}] {len(created)} assets SEO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
