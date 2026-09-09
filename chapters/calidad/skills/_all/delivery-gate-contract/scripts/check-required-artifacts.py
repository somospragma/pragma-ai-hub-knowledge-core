#!/usr/bin/env python3
"""Puerta de artefactos obligatorios del chapter Calidad.

Comprueba que existan los artefactos que los assets OBLIGATORIOS exigen y devuelve 1
si falta alguno, para engancharse a un pre-commit o a la puerta de entrega sin depender
de que nadie se acuerde. Autocontenido a proposito: un solo archivo, sin dependencias.

    python3 check-required-artifacts.py [--evidence .evidence] [--when X] [--all]

Condiciones: always, brownfield, multiplatform, executed, mock, delivery.
Se deducen de .evidence/pipeline-state.json cuando es posible; se fuerzan con --when.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

# Lista canonica. La auditoria de la fuente del chapter falla si un asset obligatorio
# prescribe un artefacto que no este aqui: asi la lista no se puede quedar atras.
REQUIRED = [
    {"path": ".evidence/pipeline-state.json",   "when": "always",        "by": "calidad-pipeline-state-tracking",             "why": "sin traza, la sesion siguiente reconstruye a ciegas"},
    {"path": ".evidence/session-log.md",        "when": "always",        "by": "calidad-pipeline-state-tracking",             "why": "bitacora append-only de la entrega"},
    {"path": ".evidence/INDEX.md",              "when": "always",        "by": "calidad-pipeline-state-tracking",             "why": "mapa de lectura: sin el, retomar significa releerlo todo"},
    {"path": ".evidence/strategy-approval.md",  "when": "always",        "by": "calidad-pre-design-strategy-document",        "why": "la aprobacion de estrategia es previa a generar"},
    {"path": ".evidence/coverage-declared.json","when": "always",        "by": "calidad-mandatory-inputs-protocol",           "why": "cobertura congelada antes de generar; se mide contra ella al cierre"},
    {"path": ".evidence/repo-capability-map.md","when": "brownfield",    "by": "calidad-repo-capability-discovery",           "why": "sin mapa se reconstruye lo que el repositorio ya resuelve"},
    {"path": ".evidence/archetype-inventory.md","when": "brownfield",    "by": "calidad-chapter-entry-point",                 "why": "inventario del arquetipo del que se hereda"},
    {"path": ".evidence/platform-learnings.md", "when": "multiplatform", "by": "calidad-cross-platform-learning-propagation", "why": "sin el, el segundo canal repite el descubrimiento del primero"},
    {"path": ".evidence/preflight.json",        "when": "executed",      "by": "calidad-execution-preflight",                 "why": "demostrar que la corrida toca el sistema bajo prueba"},
    {"path": ".evidence/cold-audit",            "when": "executed",      "by": "calidad-cold-audit-before-execution",         "why": "lectura de la cadena antes de gastar la primera corrida", "kind": "dir"},
    {"path": ".evidence/fix-requests",          "when": "executed",      "by": "calidad-human-fix-request-protocol",          "why": "el diagnostico humano entra por ficha, no por conversacion", "kind": "dir"},
    {"path": ".evidence/mock-manifest.json",    "when": "mock",          "by": "calidad-pre-development-artifacts-continuity","why": "estado de prototipos y mock sin tener que analizarlos"},
    {"path": ".evidence/mock-verification.json","when": "mock",          "by": "calidad-pipeline-state-tracking",             "why": "evidencia de que el sistema consume el mock"},
    {"path": ".evidence/coverage-declared-vs-delivered.json", "when": "delivery", "by": "calidad-delivery-gate-contract",      "why": "lo prometido contra lo entregado"},
    {"path": ".evidence/generation-manifest.json","when": "delivery",    "by": "calidad-delivery-gate-contract",              "why": "que se genero contra que criterio"},
]


def condiciones(ev: Path, forzadas: set[str]) -> set[str]:
    c = {"always"} | forzadas
    st = ev / "pipeline-state.json"
    if st.is_file():
        try:
            d = json.loads(st.read_text(encoding="utf-8"))
        except Exception:
            return c
        blob = json.dumps(d).lower()
        if "brownfield" in blob:
            c.add("brownfield")
        if '"mock"' in blob or '"hybrid"' in blob:
            c.add("mock")
        fases = {f.get("id"): f.get("status") for f in d.get("phases", []) if isinstance(f, dict)}
        if fases.get("smoke_gate") or fases.get("suite_executed"):
            c.add("executed")
        if fases.get("delivery_gate"):
            c.add("delivery")
        plats = d.get("platforms") or d.get("plataformas") or []
        if isinstance(plats, list) and len(plats) > 1:
            c.add("multiplatform")
    return c


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--evidence", default=".evidence")
    p.add_argument("--when", action="append", default=[])
    p.add_argument("--all", action="store_true")
    a = p.parse_args()

    ev = Path(a.evidence)
    if not ev.is_dir():
        print(f"FALLA: no existe {ev}/ — la entrega no tiene evidencia.")
        return 1

    activas = condiciones(ev, set(a.when))
    faltan, ok = [], 0
    for art in REQUIRED:
        if not a.all and art["when"] not in activas:
            continue
        ruta = Path(art["path"])
        existe = ruta.is_dir() if art.get("kind") == "dir" else ruta.is_file()
        ok, faltan = (ok + 1, faltan) if existe else (ok, faltan + [art])

    print(f"Condiciones activas: {', '.join(sorted(activas))}")
    print(f"Artefactos verificados: {ok + len(faltan)}  ·  presentes: {ok}  ·  faltan: {len(faltan)}")
    if not faltan:
        print("\nPUERTA VERDE.")
        return 0
    print("\nPUERTA ROJA — faltan artefactos que un asset obligatorio exige:\n")
    for art in faltan:
        print(f"  {art['path']}\n      lo exige : {art['by']}\n      para que : {art['why']}\n")
    print("Un artefacto obligatorio que nunca se crea es una regla que no existe.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
