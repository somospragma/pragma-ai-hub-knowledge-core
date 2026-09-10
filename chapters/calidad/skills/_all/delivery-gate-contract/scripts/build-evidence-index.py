#!/usr/bin/env python3
"""Genera .evidence/INDEX.md — el mapa de lectura de la evidencia.

Listar archivos y describirlos por convencion de nombre es determinista: no debe
gastarse en razonamiento del agente, y un indice mantenido a mano se desactualiza
en la segunda sesion. Se regenera; no se edita.

    python3 build-evidence-index.py [--evidence .evidence]
"""
from __future__ import annotations
import argparse, datetime, re, sys
from pathlib import Path

# Que es cada artefacto conocido. Lo desconocido se lista igual, sin descripcion:
# un archivo sin explicar es preferible a un archivo invisible.
CONOCIDOS = [
    ("pipeline-state.json",        "Traza del pipeline: fase actual, siguiente accion, correcciones vigentes"),
    ("session-log.md",             "Bitacora append-only de la entrega"),
    ("session-config.json",        "Modo de operacion y presupuesto de sesion"),
    ("input-sufficiency.json",     "Dictamen de preparacion del sistema, entrada por entrada"),
    ("coverage-declared.json",     "Matriz de cobertura congelada antes de generar"),
    ("coverage-declared-vs-delivered.json", "Lo prometido contra lo entregado"),
    ("functional-flow.md",         "Recorrido funcional: pantallas, bifurcaciones, intermitentes, desenlaces"),
    ("ui-sources.md",              "Que fuente cubre el flujo y cual la estructura, con procedencia"),
    ("tooling-gaps.md",            "Que resuelve el proyecto y que hueco queda"),
    ("platform-learnings.md",      "Libro de aprendizajes: correcciones compartidas y especificas"),
    ("repo-capability-map.md",     "Que resuelve ya el repositorio"),
    ("archetype-inventory.md",     "De que se hereda: patron, capas, convenciones"),
    ("mock-manifest.json",         "Estado de prototipos y mock: procedencia, confianza, historia"),
    ("preflight.json",             "Sondas del preflight con su salida"),
    ("execution-status.json",      "Bloqueo de ambiente con su evidencia"),
    ("metadata.json",              "Metadatos de la corrida"),
    ("healing-log.jsonl",          "Rastro de cada fallback de localizador"),
    ("alm-authorizations.md",      "Fichas de autorizacion de escritura, con conteo"),
    ("alm-publication.json",       "Que se publico y a que ciclo"),
    ("executive-report.md",        "Reporte ejecutivo de la corrida"),
    ("generation-manifest.json",   "Que se genero contra que criterio"),
    ("strategy-approval.md",       "Aprobacion de la estrategia"),
]
DIRS = {
    "cold-audit":    "Auditoria en frio por escenario: secuencia de interacciones y paso mas fragil",
    "fix-requests":  "Fichas de correccion de la persona",
    "verification":  "Veredictos del verificador con contexto limpio",
    "triage":        "Clasificacion por fallo",
    "audit-log":     "Diff y guardrail por iteracion de auto-correccion",
    "defects":       "Defectos documentados con su cadena de evidencia",
    "hierarchy":     "Volcados del arbol de interfaz",
    "runs":          "Evidencia preservada de corridas concretas",
    "figma-baselines": "Goldens de diseno con su nodo de origen",
}


def humano(n: int) -> str:
    return f"{n/1024:.0f} KB" if n >= 1024 else f"{n} B"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", default=".evidence")
    a = ap.parse_args()
    ev = Path(a.evidence)
    if not ev.is_dir():
        print(f"FALLA: no existe {ev}/"); return 1

    desc = dict(CONOCIDOS)
    orden = {n: i for i, (n, _) in enumerate(CONOCIDOS)}
    files = sorted([p for p in ev.iterdir() if p.is_file() and p.name != "INDEX.md"],
                   key=lambda p: (orden.get(p.name, 999), p.name))
    dirs = sorted([p for p in ev.iterdir() if p.is_dir()])

    out = ["# Indice de evidencia",
           "",
           "> Generado por `build-evidence-index.py`. **No se edita a mano**: se regenera.",
           f"> Ultima generacion: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
           "",
           "## Que leer para retomar",
           "",
           "1. `pipeline-state.json` — fase actual y siguiente accion",
           "2. La ultima entrada de `session-log.md` — el punto exacto de retome",
           "3. `input-sufficiency.json` — que insumo falta y que cuesta seguir sin el",
           "",
           "Con esos tres se retoma. El resto se abre solo si la siguiente accion lo pide.",
           "", "## Archivos", "",
           "| Artefacto | Que es | Tamano |", "|---|---|---|"]
    for p in files:
        out.append(f"| `{p.name}` | {desc.get(p.name, '—')} | {humano(p.stat().st_size)} |")
    if dirs:
        out += ["", "## Carpetas", "", "| Carpeta | Que contiene | Elementos |", "|---|---|---|"]
        for p in dirs:
            n = sum(1 for _ in p.rglob('*') if _.is_file())
            out.append(f"| `{p.name}/` | {DIRS.get(p.name, '—')} | {n} |")
    sin = [p.name for p in files if p.name not in desc]
    if sin:
        out += ["", "## Sin describir", "",
                "Artefactos que este indice no reconoce. Si alguno es estable, se agrega al generador:", ""]
        out += [f"- `{x}`" for x in sin]

    (ev / "INDEX.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"INDEX.md generado: {len(files)} archivos, {len(dirs)} carpetas, {len(sin)} sin describir")
    return 0


if __name__ == "__main__":
    sys.exit(main())
