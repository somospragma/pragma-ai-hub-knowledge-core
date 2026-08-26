#!/usr/bin/env python3
"""Regresion del chapter Calidad sobre la FUENTE (no sobre los bundles).

Complementa a audit-kiro-bundles.py, que audita lo ya construido en salida/.
Este corre antes: valida que la fuente este sana para que el build tenga sentido.

Checks:
  1. Frontmatter      - campos requeridos por tipo, semver, coherencia scope/stack
  2. Coherencia       - la carpeta del asset coincide con su campo stack
  3. Links [[id]]     - todas las referencias resuelven a un id existente
  4. Portabilidad     - cero paths relativos que salgan del bundle propio
  5. References       - un bundle no cita references propias inexistentes
  6. Cadena del router- los eslabones de la certificacion de una historia existen
  7. Huerfanos        - todo workflow es invocado por algun asset

Uso:
    python3 scripts/audit-chapter.py            # exit 1 si hay hallazgos
    python3 scripts/audit-chapter.py --verbose  # detalle por hallazgo
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "chapters" / "calidad"
ACCOUNTS = REPO / "accounts"   # el chapter referencia assets de cuenta por id

FM = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
WIKI = re.compile(r"\[\[([a-z][a-z0-9-]+)\]\]")
REL_OUT = re.compile(r"\]\((\.\./[^)]+\.md)\)")          # sale del bundle -> se rompe al sync
REF_LOCAL = re.compile(r"`references/([a-z0-9\-]+\.md)`")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")

REQUERIDOS = {
    "skill":     ["id", "version", "scope", "type", "chapter"],
    "workflow":  ["id", "version", "scope", "type", "chapter"],
    "prompt":    ["id", "version", "scope", "type", "chapter"],
    "steering":  ["id", "version", "scope", "type"],
}

# Cadena que recorre un QA para certificar una historia de principio a fin.
# Si un eslabon desaparece, el recorrido se corta en silencio.
CADENA = [
    ("traza del pipeline",        "calidad-pipeline-state-tracking"),
    ("inputs obligatorios",       "calidad-mandatory-inputs-protocol"),
    ("SUT readiness gate",        "calidad-sut-readiness-gate"),
    ("mapa de locators",          "calidad-ui-locator-map-contract"),
    ("deteccion de intent",       "calidad-intent-detection"),
    ("router",                    "calidad-route-test-generation"),
    ("analisis de HU",            "calidad-analyze-and-refine-stories"),
    ("diseno de casos",           "calidad-design-test-cases"),
    ("estrategia y plan",         "calidad-build-test-strategy-and-plan"),
    ("capacidades transversales", "calidad-transversal-capabilities"),
    ("validacion de spec",        "calidad-spec-validation"),
    ("brownfield vs greenfield",  "calidad-brownfield-vs-greenfield"),
    ("pre-diseno STRATEGY",       "calidad-pre-design-strategy-document"),
    ("emision de archivos",       "calidad-streaming-files-protocol"),
    ("evidencia y trazabilidad",  "calidad-test-evidence-and-traceability"),
    ("gate de smoke",             "calidad-smoke-gate-policy"),
    ("ejecucion",                 "calidad-test-execution-orchestration"),
    ("triage de fallos",          "calidad-failure-triage-and-classification"),
    ("auto-correccion",           "calidad-test-self-correction-loop-workflow"),
    ("reporte ejecutivo",         "calidad-generate-executive-report"),
    ("delivery gate",             "calidad-delivery-gate-contract"),
]


def parse_fm(texto: str) -> dict:
    m = FM.match(texto)
    if not m:
        return {}
    fm = {}
    for linea in m.group(1).splitlines():
        if ":" in linea:
            k, _, v = linea.partition(":")
            fm[k.strip()] = v.strip()
    return fm


def es_asset(f: Path) -> bool:
    return "/references/" not in str(f) and f.name != "README.md"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    archivos = sorted(SRC.rglob("*.md"))
    ids: dict[str, Path] = {}
    hallazgos: dict[str, list[str]] = {k: [] for k in
        ["frontmatter", "coherencia", "links", "portabilidad", "references", "cadena", "huerfanos"]}

    # --- inventario de ids ---
    # Los assets de cuenta viven fuera de chapters/ pero se referencian con la
    # misma sintaxis. Sin indexarlos, toda referencia a la cuenta sale rota.
    for f in sorted(ACCOUNTS.rglob("*.md")):
        fm = parse_fm(f.read_text(encoding="utf-8"))
        aid = fm.get("id") or f"{f.parent.parent.name}-{f.parent.name}-{f.stem}"
        ids.setdefault(aid, f)

    for f in archivos:
        if not es_asset(f):
            continue
        fm = parse_fm(f.read_text(encoding="utf-8"))
        if fm.get("id"):
            if fm["id"] in ids:
                hallazgos["frontmatter"].append(f"id duplicado '{fm['id']}': {f} y {ids[fm['id']]}")
            ids[fm["id"]] = f

    # --- 1 y 2: frontmatter y coherencia carpeta/stack ---
    for f in archivos:
        if not es_asset(f):
            continue
        fm = parse_fm(f.read_text(encoding="utf-8"))
        if not fm:
            hallazgos["frontmatter"].append(f"{f}: sin frontmatter")
            continue
        for campo in REQUERIDOS.get(fm.get("type", ""), []):
            if not fm.get(campo):
                hallazgos["frontmatter"].append(f"{f}: falta '{campo}'")
        if fm.get("version") and not SEMVER.match(fm["version"]):
            hallazgos["frontmatter"].append(f"{f}: version '{fm['version']}' no es semver")
        if fm.get("scope") == "stack" and not fm.get("stack"):
            hallazgos["frontmatter"].append(f"{f}: scope=stack sin campo stack")
        if fm.get("scope") != "stack" and fm.get("stack"):
            hallazgos["frontmatter"].append(f"{f}: declara stack con scope={fm.get('scope')}")
        # la carpeta manda: skills/<stack>/... debe declarar ese stack
        partes = f.relative_to(SRC).parts
        if len(partes) > 1 and partes[1] not in ("_all",):
            carpeta = partes[1]
            declarado = (fm.get("stack") or "").strip("[]")
            if fm.get("scope") == "stack" and declarado != carpeta:
                hallazgos["coherencia"].append(
                    f"{f}: carpeta '{carpeta}' pero stack '{declarado}'")

    # --- 3, 4 y 5: links, portabilidad, references locales ---
    for f in archivos:
        texto = f.read_text(encoding="utf-8")
        propio = parse_fm(texto).get("id")
        for ref in set(WIKI.findall(texto)):
            # placeholders de sintaxis usados en la documentacion, no son punteros reales
            if ref not in ids and ref not in ("asset-id", "skill-id", "id"):
                hallazgos["links"].append(f"{f}: [[{ref}]] no resuelve")
        for destino in set(REL_OUT.findall(texto)):
            hallazgos["portabilidad"].append(f"{f}: path relativo sale del bundle -> {destino}")
        # references propias
        if f.name == "SKILL.md":
            base = f.parent
        elif "/references/" in str(f):
            base = f.parent.parent
        else:
            base = None
        if base:
            for m in set(REF_LOCAL.findall(texto)):
                lineas = [l for l in texto.splitlines() if f"references/{m}" in l]
                if all("[[" in l for l in lineas):
                    continue  # cita cualificada a otro bundle
                if not (base / "references" / m).exists():
                    hallazgos["references"].append(
                        f"{f}: cita references/{m} que no existe en su bundle")

    # --- 6: cadena de certificacion ---
    for etapa, aid in CADENA:
        if aid not in ids:
            hallazgos["cadena"].append(f"eslabon roto '{etapa}': falta {aid}")

    # --- 7: workflows huerfanos ---
    workflows = {i for i, f in ids.items() if "/workflows/" in str(f)}
    referenciados = set()
    for f in archivos:
        texto = f.read_text(encoding="utf-8")
        propio = parse_fm(texto).get("id")
        referenciados |= {r for r in WIKI.findall(texto) if r != propio}
    for w in sorted(workflows - referenciados):
        hallazgos["huerfanos"].append(f"workflow '{w}' no lo invoca ningun asset")

    # --- reporte ---
    total = sum(len(v) for v in hallazgos.values())
    print(f"=== Regresion del chapter Calidad — {len(ids)} assets ===\n")
    ETIQUETAS = {
        "frontmatter":  "Frontmatter y ids unicos",
        "coherencia":   "Carpeta coincide con stack declarado",
        "links":        "Referencias [[id]] resuelven",
        "portabilidad": "Sin paths relativos fuera del bundle",
        "references":   "References propias existen",
        "cadena":       "Cadena de certificacion completa",
        "huerfanos":    "Sin workflows huerfanos",
    }
    for clave, etiqueta in ETIQUETAS.items():
        items = hallazgos[clave]
        print(f"  {'OK   ' if not items else 'FALLA'}  {etiqueta:42} {len(items) or ''}")
        if items and args.verbose:
            for i in items:
                print(f"           {i}")
    if total and not args.verbose:
        print("\n  (correr con --verbose para el detalle)")
    print(f"\nHallazgos: {total}")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
