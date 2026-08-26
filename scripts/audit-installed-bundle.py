#!/usr/bin/env python3
"""Audita un workspace donde la CLI pragma-ai YA instalo el conocimiento.

audit-chapter.py valida la FUENTE y audit-kiro-bundles.py valida lo que
construye scripts/build-kiro-bundles.py. Ninguno de los dos ve lo que el
agente ve realmente: los dos primeros trabajan sobre ids, y la CLI renombra
los assets al instalarlos. Este script corre sobre el repositorio del cliente
y mide lo que el agente encuentra al abrir el workspace.

Lo que responde, por IDE:

  1. Capa siempre-on   - cuantos bytes entran en CADA turno sin que nadie los
                         pida, y cuales. Es el multiplicador del costo.
  2. Links [[id]]      - cuantas referencias cruzadas resuelven contra los
                         nombres realmente instalados. Un link roto es
                         conocimiento obligatorio que nadie abre.
  3. Descubribilidad   - skills sin frontmatter name/description no entran en
                         el indice del IDE: solo se encuentran por listado de
                         directorio, es decir por casualidad.
  4. Relevancia        - assets instalados que no aplican a los stacks que ESE
                         IDE instalo. Cada IDE se instala por separado y pueden
                         diverger: en campo se encontro Kiro con un stack y
                         Copilot y Claude con tres, en el mismo repositorio.

Uso:
    python3 scripts/audit-installed-bundle.py <ruta-al-workspace>
    python3 scripts/audit-installed-bundle.py <ruta> --verbose
    python3 scripts/audit-installed-bundle.py <ruta> --json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

# Bytes por token, estimacion conservadora para markdown en espanol.
BYTES_PER_TOKEN = 3.5

WIKILINK_RE = re.compile(r"\[\[([^\]|#\n]+?)\]\]")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
H1_RE = re.compile(r"^#\s+(.+)$", re.M)

# Un [[...]] con estas pintas no es una referencia a un asset: son fragmentos
# de shell o de config que quedaron dentro de bloques de codigo.
def is_asset_ref(token: str) -> bool:
    if len(token) > 90 or "\n" in token:
        return False
    return re.fullmatch(r"[a-z0-9][a-z0-9._/-]*", token) is not None


# ---------------------------------------------------------------------------
# Layout de cada IDE: donde vive cada capa y cual de ellas es siempre-on.
#
# "siempre-on" = el IDE la carga en cada turno sin que el agente la pida.
# Cuando la deteccion depende de una condicion (frontmatter, nombre de
# archivo), se declara en `always_on_if` y se evalua por archivo.
# ---------------------------------------------------------------------------
IDE_LAYOUT = {
    "kiro": {
        "root": ".kiro",
        "layers": {
            "steering": "steering/*.md",
            "workflow": "workflows/*.md",
            "prompt": "prompts/*.md",
            "skill": "skills/*/SKILL.md",
            "reference": "skills/*/references/*.md",
            "hook": "hooks/*.json",
        },
        # Kiro decide por el campo `inclusion` del frontmatter.
        # Valores que documenta Kiro: always | fileMatch | manual.
        # Cualquier otro valor cae al default, que es cargar siempre.
        "always_on_if": "kiro_inclusion",
    },
    "copilot": {
        "root": ".github",
        "layers": {
            "steering": "instructions/*.md",
            "workflow": "workflows/*.md",
            "prompt": "prompts/*.md",
            "skill": "skills/*/SKILL.md",
            "reference": "skills/*/references/*.md",
        },
        # Copilot solo aplica solo: copilot-instructions.md (siempre) y
        # instructions/*.instructions.md con `applyTo` que case.
        "always_on_if": "copilot_applies",
    },
    "claude-code": {
        "root": ".claude",
        "layers": {
            "steering": "rules/*.md",
            "workflow": "workflows/*.md",
            "prompt": "prompt/*.md",
            "skill": "skills/*/SKILL.md",
            "reference": "skills/*/references/*.md",
        },
        # Claude Code solo carga CLAUDE.md por si mismo. `.claude/rules/` no
        # es una ruta que lea sola.
        "always_on_if": "claude_md_only",
    },
}

KIRO_VALID_INCLUSION = {"always", "fileMatch", "manual"}


def parse_frontmatter(text: str) -> dict:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm


def h1_of(text: str) -> str:
    m = H1_RE.search(text)
    return m.group(1).strip() if m else ""


class Asset:
    __slots__ = ("path", "rel", "layer", "text", "fm", "h1", "size")

    def __init__(self, path: Path, root: Path, layer: str):
        self.path = path
        self.rel = str(path.relative_to(root))
        self.layer = layer
        self.text = path.read_text(encoding="utf-8", errors="replace")
        self.fm = parse_frontmatter(self.text) if path.suffix == ".md" else {}
        self.h1 = h1_of(self.text) if path.suffix == ".md" else ""
        self.size = path.stat().st_size

    @property
    def handle(self) -> str:
        """El nombre por el que el agente puede referirse a este asset."""
        if self.layer in ("skill", "reference"):
            return self.path.parent.name if self.layer == "skill" else self.path.stem
        return self.path.name


def collect(workspace: Path, ide: str) -> list[Asset]:
    spec = IDE_LAYOUT[ide]
    root = workspace / spec["root"]
    if not root.is_dir():
        return []
    assets: list[Asset] = []
    for layer, glob in spec["layers"].items():
        for p in sorted(root.glob(glob)):
            if p.is_file():
                assets.append(Asset(p, workspace, layer))
    return assets


def always_on(assets: list[Asset], ide: str, workspace: Path) -> tuple[list[Asset], list[str]]:
    """Devuelve (assets cargados en cada turno, notas sobre por que)."""
    rule = IDE_LAYOUT[ide]["always_on_if"]
    notes: list[str] = []
    out: list[Asset] = []

    if rule == "kiro_inclusion":
        for a in assets:
            if a.layer not in ("steering", "workflow", "prompt"):
                continue
            inc = a.fm.get("inclusion", "")
            if inc == "always":
                out.append(a)
            elif inc in ("fileMatch", "manual"):
                continue
            else:
                out.append(a)
                notes.append(
                    f"inclusion: '{inc or '(ausente)'}' no es un valor que Kiro "
                    f"reconozca ({'|'.join(sorted(KIRO_VALID_INCLUSION))}); "
                    f"cae al default y se carga siempre -> {a.rel}"
                )
        return out, notes

    if rule == "copilot_applies":
        ci = workspace / ".github" / "copilot-instructions.md"
        if ci.is_file():
            out.append(Asset(ci, workspace, "steering"))
        else:
            notes.append(
                ".github/copilot-instructions.md NO existe: Copilot no tiene "
                "ninguna capa siempre-on en este workspace."
            )
        for a in assets:
            if a.layer != "steering":
                continue
            if not a.path.name.endswith(".instructions.md"):
                notes.append(
                    f"sufijo '{a.path.name[-20:]}' != '.instructions.md': Copilot "
                    f"no reconoce el archivo como instruccion -> {a.rel}"
                )
                continue
            if "applyTo" not in a.fm:
                notes.append(f"sin 'applyTo' en frontmatter: no se aplica solo -> {a.rel}")
                continue
            out.append(a)
        return out, notes

    # claude_md_only
    for name in ("CLAUDE.md", "AGENTS.md"):
        p = workspace / name
        if p.is_file():
            out.append(Asset(p, workspace, "steering"))
    if not out:
        notes.append(
            "No hay CLAUDE.md ni AGENTS.md en la raiz: Claude Code no tiene "
            "ninguna capa siempre-on. `.claude/rules/` no se lee solo."
        )
    return out, notes


def audit_links(assets: list[Asset], ide: str) -> dict:
    handles = {a.handle for a in assets}
    # Kiro y Copilot conservan frontmatter `name`; sirve como handle alterno.
    handles |= {a.fm["name"] for a in assets if a.fm.get("name")}
    stems = {a.path.stem for a in assets}

    counts: Counter[str] = Counter()
    for a in assets:
        for tok in WIKILINK_RE.findall(a.text):
            tok = tok.strip()
            if is_asset_ref(tok):
                counts[tok] += 1

    resolved, broken = {}, {}
    for tok, n in counts.items():
        stem = tok[len("calidad-"):] if tok.startswith("calidad-") else tok
        hit = (
            tok in handles
            or tok in stems
            or any(h == stem or h.startswith(stem + "-") for h in handles)
        )
        (resolved if hit else broken)[tok] = n

    return {
        "distinct": len(counts),
        "occurrences": sum(counts.values()),
        "resolved_distinct": len(resolved),
        "broken_distinct": len(broken),
        "broken_occurrences": sum(broken.values()),
        "broken": dict(sorted(broken.items(), key=lambda kv: -kv[1])),
    }


def audit_discoverability(assets: list[Asset]) -> dict:
    skills = [a for a in assets if a.layer == "skill"]
    no_fm = [a for a in skills if not a.fm]
    no_desc = [a for a in skills if a.fm and not a.fm.get("description")]
    return {
        "skills": len(skills),
        "sin_frontmatter": [a.rel for a in no_fm],
        "sin_description": [a.rel for a in no_desc],
    }


# Marcas por las que se reconoce un stack en el NOMBRE de un asset instalado.
# La CLI renombra los assets por su titulo, asi que el nombre es la unica pista
# de a que stack pertenece cada uno una vez instalado.
STACK_MARKERS = {
    "playwright": ("playwright",),
    "appium-wdio": ("appium-webdriverio", "appium-wdio"),
    "appium-serenity": ("appium-screenplay", "serenity"),
    "appium-core": ("appium",),          # generico: solo cuenta si no casa otro
    "karate": ("karate",),
    "k6": ("k6",),
}


def installed_stacks(assets: list[Asset]) -> set[str]:
    """Que stacks tiene instalados ESTE IDE, segun los assets que hay en disco.

    No se deduce del repositorio: el repositorio dice que stacks podria usar, no
    cual instalo cada IDE. En campo se encontro el mismo repositorio con Kiro
    trayendo solo un stack y Copilot y Claude trayendo tres.
    """
    found = set()
    names = [a.handle.lower() for a in assets if a.layer in ("skill", "workflow", "prompt")]
    for stack, marks in STACK_MARKERS.items():
        if stack == "appium-core":
            continue
        if any(any(m in n for m in marks) for n in names):
            found.add(stack)
    # appium-core viaja de acompanante: se instala junto a otro stack de Appium
    if any(s.startswith("appium-") for s in found):
        found.add("appium-core")
    return found


def detect_stack(workspace: Path) -> set[str]:
    """Que stacks PODRIA usar el repositorio, segun sus archivos de proyecto."""
    stacks = set()
    pkg = workspace / "package.json"
    if pkg.is_file():
        raw = pkg.read_text(encoding="utf-8", errors="replace")
        if "webdriverio" in raw:
            stacks |= {"appium-wdio", "appium-core"}
        if "playwright" in raw:
            stacks.add("playwright")
        if "k6 run" in raw:
            stacks.add("k6")
    if (workspace / "karate-config.js").is_file():
        stacks.add("karate")
    if (workspace / "build.gradle").is_file():
        raw = (workspace / "build.gradle").read_text(encoding="utf-8", errors="replace")
        if "appium-java-client" in raw:
            stacks |= {"appium-serenity", "appium-core"}
    return stacks


# Assets que la fuente marca `_all` pero que no aplican a cualquier stack.
# Cada entrada es (fragmento del handle, para que stacks tiene sentido).
NOT_UNIVERSAL = {
    "seo": {"playwright"},
    "accesibilidad": {"playwright"},
    "accessibility": {"playwright"},
    "a11y": {"playwright"},
    "visual-regression": {"playwright", "appium-wdio", "appium-serenity"},
    "comparacion-visual": {"playwright", "appium-wdio", "appium-serenity"},
    "contract-testing": {"karate"},
    "contratos-entre-servicios": {"karate"},
    "security-testing": {"karate", "playwright"},
    "mockoon": {"karate", "playwright"},
    "service-virtualization": {"karate", "playwright"},
}


def audit_relevance(assets: list[Asset], stacks: set[str]) -> list[dict]:
    out = []
    for a in assets:
        if a.layer not in ("skill", "steering", "workflow"):
            continue
        h = a.handle.lower()
        for frag, ok_for in NOT_UNIVERSAL.items():
            if frag in h and stacks and not (stacks & ok_for):
                size = a.size
                if a.layer == "skill":
                    refs = a.path.parent / "references"
                    if refs.is_dir():
                        size += sum(p.stat().st_size for p in refs.rglob("*") if p.is_file())
                out.append({"asset": a.rel, "layer": a.layer, "bytes": size,
                            "aplica_a": sorted(ok_for)})
                break
    return sorted(out, key=lambda d: -d["bytes"])


def tok(nbytes: int) -> int:
    return int(nbytes / BYTES_PER_TOKEN)


def run(workspace: Path, verbose: bool) -> dict:
    repo_stacks = detect_stack(workspace)
    report = {
        "workspace": str(workspace),
        "stacks_del_repositorio": sorted(repo_stacks),
        "ides": {},
    }

    for ide in IDE_LAYOUT:
        assets = collect(workspace, ide)
        if not assets:
            continue
        stacks = installed_stacks(assets)
        on, notes = always_on(assets, ide, workspace)
        on_bytes = sum(a.size for a in on)
        total_bytes = sum(a.size for a in assets)
        report["ides"][ide] = {
            "stacks_instalados": sorted(stacks),
            "stacks_del_repo_sin_instalar": sorted(repo_stacks - stacks),
            "assets_instalados": len(assets),
            "bytes_instalados": total_bytes,
            "siempre_on": {
                "archivos": len(on),
                "bytes": on_bytes,
                "tokens_por_turno": tok(on_bytes),
                "detalle": sorted(
                    ({"asset": a.rel, "bytes": a.size} for a in on),
                    key=lambda d: -d["bytes"],
                )[:15],
                "notas": notes,
            },
            "links": audit_links(assets, ide),
            "descubribilidad": audit_discoverability(assets),
            "irrelevante_para_el_stack": audit_relevance(assets, stacks),
        }
    return report


def emit(report: dict, verbose: bool) -> int:
    print(f"Workspace : {report['workspace']}")
    print(f"Repo usa  : {', '.join(report['stacks_del_repositorio']) or '(no detectado)'}")
    hallazgos = 0

    # Cada IDE se instala por separado y pueden acabar con stacks distintos. Eso
    # hace que el mismo repositorio se comporte distinto segun con que lo abras,
    # y no hay nada en el workspace que lo advierta.
    por_ide = {i: set(r["stacks_instalados"]) for i, r in report["ides"].items()}
    if len({frozenset(v) for v in por_ide.values()}) > 1:
        print("\n  ! Los IDEs no tienen los mismos stacks instalados:")
        for i, s in por_ide.items():
            print(f"      {i:12} {', '.join(sorted(s)) or '(ninguno)'}")
        print("    El mismo repositorio se comporta distinto segun con que IDE se abra.")
        hallazgos += 1

    for ide, r in report["ides"].items():
        print(f"\n{'=' * 72}\n{ide.upper()}\n{'=' * 72}")
        print(f"  stacks instalados : {', '.join(r['stacks_instalados']) or '(ninguno)'}")
        if r["stacks_del_repo_sin_instalar"]:
            print(f"  del repo, ausentes: {', '.join(r['stacks_del_repo_sin_instalar'])}")
        print(f"  instalado         : {r['assets_instalados']} assets, "
              f"{r['bytes_instalados']:,} bytes (~{tok(r['bytes_instalados']):,} tokens)")

        so = r["siempre_on"]
        print(f"  siempre-on        : {so['archivos']} archivos, {so['bytes']:,} bytes "
              f"-> ~{so['tokens_por_turno']:,} tokens EN CADA TURNO")
        if verbose and so["detalle"]:
            for d in so["detalle"]:
                print(f"       {d['bytes']:>8,}  {d['asset']}")
        for n in so["notas"][:6 if not verbose else 999]:
            print(f"     ! {n}")
            hallazgos += 1
        if not verbose and len(so["notas"]) > 6:
            print(f"     ! ... y {len(so['notas']) - 6} notas mas (--verbose)")

        li = r["links"]
        print(f"  links [[id]]      : {li['occurrences']:,} ocurrencias, "
              f"{li['distinct']} distintos")
        print(f"                      resuelven {li['resolved_distinct']}, "
              f"ROTOS {li['broken_distinct']} "
              f"({li['broken_occurrences']:,} ocurrencias)")
        if li["broken_distinct"]:
            hallazgos += 1
            for tokname, n in list(li["broken"].items())[:10 if not verbose else 999]:
                print(f"       {n:>5}x  [[{tokname}]]")

        dc = r["descubribilidad"]
        print(f"  skills            : {dc['skills']}")
        if dc["sin_frontmatter"]:
            hallazgos += 1
            print(f"     ! {len(dc['sin_frontmatter'])} SKILL.md sin frontmatter: "
                  f"no entran en el indice del IDE")
        if dc["sin_description"]:
            hallazgos += 1
            print(f"     ! {len(dc['sin_description'])} SKILL.md sin description")

        irr = r["irrelevante_para_el_stack"]
        if irr:
            hallazgos += 1
            tot = sum(d["bytes"] for d in irr)
            print(f"  fuera de stack    : {len(irr)} assets, {tot:,} bytes "
                  f"(~{tok(tot):,} tokens) que no aplican aqui")
            for d in irr[:8 if not verbose else 999]:
                print(f"       {d['bytes']:>8,}  {d['asset']}  (aplica a: {','.join(d['aplica_a'])})")

    print(f"\n{'=' * 72}")
    print(f"Hallazgos: {hallazgos}")
    return 1 if hallazgos else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workspace", type=Path)
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    ws = args.workspace.expanduser().resolve()
    if not ws.is_dir():
        print(f"No existe: {ws}", file=sys.stderr)
        return 2

    report = run(ws, args.verbose)
    if not report["ides"]:
        print(f"No se encontro conocimiento instalado en {ws}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    return emit(report, args.verbose)


if __name__ == "__main__":
    raise SystemExit(main())
