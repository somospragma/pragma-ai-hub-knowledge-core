#!/usr/bin/env python3
"""Compara la cobertura declarada contra la entregada y emite el resultado.

Contar escenarios y cruzarlos contra la matriz congelada es determinista. Confiarlo
al recuerdo del agente es lo que produjo, en campo, cerrar una historia creyendo
haber terminado con criterios sin escenario.

    python3 check-coverage-delivered.py --tests <dir> [--evidence .evidence]

Lee  .evidence/coverage-declared.json  (lista de {criterio, plataformas, escenario})
Emite .evidence/coverage-declared-vs-delivered.json y devuelve 1 si hay diferencia.
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

ESC = re.compile(r"^\s*(?:Scenario Outline|Scenario|Esquema del escenario|Escenario):\s*(.+?)\s*$", re.M)


def normaliza(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tests", required=True, help="raiz donde viven los archivos de escenarios")
    ap.add_argument("--evidence", default=".evidence")
    ap.add_argument("--ext", default=".feature", help="extension de los archivos de escenarios")
    a = ap.parse_args()

    ev = Path(a.evidence)
    decl_p = ev / "coverage-declared.json"
    if not decl_p.is_file():
        print("FALLA: no existe coverage-declared.json — la cobertura no se congelo antes de generar.")
        return 1
    declarados = json.loads(decl_p.read_text(encoding="utf-8"))
    if isinstance(declarados, dict):
        declarados = declarados.get("items") or declarados.get("entries") or []

    raiz = Path(a.tests)
    if not raiz.is_dir():
        print(f"FALLA: no existe {raiz}/"); return 1
    entregados = []
    for f in raiz.rglob(f"*{a.ext}"):
        entregados += [(m, str(f)) for m in ESC.findall(f.read_text(encoding="utf-8", errors="replace"))]

    idx = {normaliza(n): ruta for n, ruta in entregados}
    faltan, sobran = [], list(idx)
    for d in declarados:
        nombre = d.get("escenario") or d.get("scenario") or ""
        k = normaliza(nombre)
        hit = k if k in idx else next((x for x in idx if k and (k in x or x in k)), None)
        if hit:
            if hit in sobran: sobran.remove(hit)
        else:
            faltan.append({"criterio": d.get("criterio") or d.get("id"), "escenario": nombre,
                           "plataformas": d.get("plataformas") or d.get("platforms")})

    res = {"declared": len(declarados), "delivered": len(entregados),
           "difference": {"declarados_sin_escenario": faltan,
                          "escenarios_no_declarados": sorted(sobran)}}
    (ev / "coverage-declared-vs-delivered.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Declarados: {len(declarados)}  ·  Entregados: {len(entregados)}")
    if not faltan and not sobran:
        print("\nSIN DIFERENCIA: lo prometido es lo entregado.")
        return 0
    if faltan:
        print(f"\nDECLARADOS SIN ESCENARIO ({len(faltan)}) — la historia no esta terminada:")
        for x in faltan:
            print(f"  criterio {x['criterio']}  ·  {x['escenario']}  ·  {x['plataformas']}")
    if sobran:
        print(f"\nESCENARIOS NO DECLARADOS ({len(sobran)}) — o se amplio el alcance sin registrarlo, o sobran:")
        for x in sobran[:15]:
            print(f"  {x}")
    print("\nCerrar una historia sin este cruce ya dejo criterios sin cubrir.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
