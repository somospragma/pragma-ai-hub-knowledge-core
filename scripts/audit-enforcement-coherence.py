#!/usr/bin/env python3
"""Auditoria de coherencia del enforcement del chapter.

Contexto: el migrador a Mimir publica solo un subconjunto fijo del frontmatter
(title, type, chapter, tags, description, localId, sourcePath, name, stack,
category, bundleManifest y campos de herencia) mas el cuerpo. Los campos
`enforcement` y `verification` NO viajan: existen unicamente en este repositorio.

Por eso la obligatoriedad se transporta por tres canales que si llegan al
consumidor:

  1. `description` que declara la obligatoriedad (ademas decide si el skill se
     carga bajo demanda en los IDEs que lo hacen por descripcion).
  2. tag `mandatory` (queda filtrable en Mimir).
  3. seccion `## Verificacion` en el CUERPO, con los mismos checks y mensajes
     de bloqueo del frontmatter.

El cuerpo es la fuente canonica para el consumidor; el frontmatter queda como
metadato local para auditorias. Este script vigila que no se separen.

Uso:
  python3 scripts/audit-enforcement-coherence.py          # reporta
  python3 scripts/audit-enforcement-coherence.py --strict # exit 1 si hay fallos
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "chapters" / "calidad"
FM_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)
SECTION_RE = re.compile(r"^##+\s*Verificaci", re.M | re.I)


def parse_checks(fm: str) -> list[str]:
    m = re.search(r"^verification:\n(.*?)(?=^\w|\Z)", fm, re.M | re.S)
    if not m:
        return []
    out = []
    for part in re.split(r"^\s*-\s+check:\s*", m.group(1), flags=re.M)[1:]:
        c = re.match(r'"(.*?)"', part.strip(), re.S)
        if c:
            out.append(" ".join(c.group(1).split()))
    return out


def main() -> int:
    problemas: list[str] = []
    total = 0

    for f in sorted(ROOT.rglob("*.md")):
        if "references" in f.parts:
            continue
        m = FM_RE.match(f.read_text(encoding="utf-8"))
        if not m:
            continue
        fm, body = m.group(1), m.group(2)
        if "enforcement: mandatory" not in fm:
            continue
        total += 1
        rel = f.relative_to(ROOT.parent.parent)
        aid_m = re.search(r"^id:\s*(\S+)", fm, re.M)
        aid = aid_m.group(1) if aid_m else str(rel)

        desc = re.search(r"^description:\s*(.*)$", fm, re.M)
        if not desc or not re.search(r"obligatori|mandator", desc.group(1), re.I):
            problemas.append(f"{aid}: la description no declara obligatoriedad")

        tags = re.search(r"^tags:\s*\[(.*?)\]", fm, re.M | re.S)
        tl = [t.strip() for t in tags.group(1).split(",")] if tags else []
        if "mandatory" not in tl:
            problemas.append(f"{aid}: falta el tag 'mandatory'")

        checks = parse_checks(fm)
        if not checks:
            problemas.append(
                f"{aid}: marcado mandatory pero SIN bloque verification "
                f"(no hay criterio de comprobacion en ningun canal)"
            )
            continue

        if not SECTION_RE.search(body):
            problemas.append(
                f"{aid}: tiene {len(checks)} checks en el frontmatter pero no la "
                f"seccion '## Verificacion' en el cuerpo — no llegan al consumidor"
            )
            continue

        faltan = [c for c in checks if c[:60] not in body]
        if faltan:
            problemas.append(
                f"{aid}: {len(faltan)} de {len(checks)} checks del frontmatter no "
                f"aparecen en el cuerpo — las dos fuentes divergieron"
            )

    print(f"Assets mandatory revisados: {total}")
    if problemas:
        print(f"Problemas: {len(problemas)}\n")
        for p in problemas:
            print(f"  - {p}")
    else:
        print("Sin problemas: enforcement coherente entre frontmatter y cuerpo.")

    return 1 if (problemas and "--strict" in sys.argv) else 0


if __name__ == "__main__":
    raise SystemExit(main())
