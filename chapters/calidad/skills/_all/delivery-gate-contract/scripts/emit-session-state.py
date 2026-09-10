#!/usr/bin/env python3
"""Imprime el estado de apertura de sesion: fase, siguiente accion, bloqueos y pendientes.

Leer la traza y componer el reporte de apertura es determinista. Que lo haga un
comando en vez de prosa en el steering ahorra contexto en CADA peticion de TODAS
las sesiones, que es el unico coste verdaderamente fijo del sistema.

    python3 emit-session-state.py [--evidence .evidence]
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", default=".evidence")
    a = ap.parse_args()
    ev = Path(a.evidence)
    if not ev.is_dir():
        print("SESION NUEVA: no hay evidencia previa. Se crean traza y bitacora antes de tocar nada.")
        return 0

    st = ev / "pipeline-state.json"
    if not st.is_file():
        print("SESION NUEVA: no hay traza. Se crea antes de tocar nada.")
        return 0
    try:
        d = json.loads(st.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"TRAZA ILEGIBLE ({e.__class__.__name__}): no se continua a ciegas."); return 1

    fases = [f for f in d.get("phases", []) if isinstance(f, dict)]
    actual = next((f for f in fases if f.get("status") == "in_progress"), None) \
        or next((f for f in fases if f.get("status") not in ("done", "skipped")), None)
    bloq = [f for f in fases if f.get("status") == "blocked" or f.get("blocker")]
    corr = d.get("open_corrections") or []

    print(f"RUN: {d.get('run_id', '(sin id)')}")
    print(f"FASE ACTUAL: {actual.get('id') if actual else 'todas cerradas'}"
          + (f"  [{actual.get('status')}]" if actual else ""))
    print(f"SIGUIENTE ACCION: {d.get('next_action', '(no declarada — se declara antes de seguir)')}")

    if bloq:
        print(f"\nBLOQUEOS VIGENTES ({len(bloq)}):")
        for f in bloq:
            print(f"  - {f.get('id')}: {f.get('blocker') or f.get('reason') or 'sin razon declarada'}")
    else:
        print("\nBLOQUEOS VIGENTES: ninguno")

    if corr:
        print(f"\nCORRECCIONES VIGENTES ({len(corr)}) — se reafirman en voz alta antes de trabajar:")
        for c in corr:
            print(f"  - {c if isinstance(c, str) else c.get('text') or json.dumps(c, ensure_ascii=False)[:110]}")

    log = ev / "session-log.md"
    if log.is_file():
        txt = log.read_text(encoding="utf-8", errors="replace")
        m = list(re.finditer(r"^#{2,3}\s+(.+)$", txt, re.M))
        if m:
            print(f"\nULTIMA ENTRADA DE BITACORA: {m[-1].group(1).strip()}")
        ret = list(re.finditer(r"next_action[:\*\s]*(.+)", txt))
        if ret:
            print(f"PUNTO DE RETOME: {ret[-1].group(1).strip()[:200]}")

    idx = ev / "INDEX.md"
    print(f"\nINDICE DE EVIDENCIA: {'presente' if idx.is_file() else 'AUSENTE — regenerar con build-evidence-index.py'}")
    print("\nNo se toca nada hasta haber leido esto y continuado por la siguiente accion.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
