#!/usr/bin/env python3
"""Auditoria de la solicitud de datos: cada criterio tiene con que ejecutarse.

Cruza .evidence/ca-inventory.json contra .evidence/data-request.json y falla
listando lo que no cuadra. Es un join, no un razonamiento, y por eso no puede
depender de que alguien se acuerde de pedirlo: en campo se pidio dos veces, y la
segunda fue despues de que un caso base se quedara sin dato.

Comprueba siete cosas:
  1. Ningun criterio se queda sin dato ni sin justificacion de por que no lo lleva.
  2. Ningun dato pedido esta huerfano: si ningun criterio lo necesita, sobra.
  3. Ningun dato derivable de otro llega a la solicitud.
  4. Ningun dato de otro responsable se pide al cliente. Puede aparecer para trazabilidad
     marcado `documentar`, y entonces debe decir como se obtiene.
  5. Todo dato declara sujeto, condicion exigida y responsable.
  6. Toda historia citada por un dato existe en el inventario (caza erratas de id).
  7. Todo dato marcado `documentar` declara `como_se_obtiene`.

    python3 check-data-coverage.py [--evidence .evidence] [--json]

Salida: .evidence/data-coverage-audit.json  ·  exit 1 si la auditoria no pasa.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

RESPONSABLES = {"cliente-datos", "arquitecto", "po-negocio", "dev-pragma", "qa"}
# Solo uno de ellos viaja en el documento que recibe quien administra el ambiente.
DEL_CLIENTE = "cliente-datos"
OBLIGATORIOS = ("id", "familia", "sujeto", "condicion", "responsable")


def cargar(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"FALLA: no existe {p}")
        return None
    except json.JSONDecodeError as e:
        print(f"FALLA: {p} no es JSON valido ({e})")
        return None


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--evidence", default=".evidence")
    p.add_argument("--json", action="store_true", help="imprime el veredicto y nada mas")
    a = p.parse_args()

    ev = Path(a.evidence)
    inv = cargar(ev / "ca-inventory.json")
    req = cargar(ev / "data-request.json")
    if inv is None or req is None:
        return 1

    todos = req.get("items", [])
    # Un item `documentar` no se le pide a nadie del cliente: viaja en el documento para que
    # quien lo lea sepa que ese caso esta cubierto y por quien. Sigue contando para cobertura.
    items = [i for i in todos if not i.get("documentar")]
    documentados = [i for i in todos if i.get("documentar")]
    fuera = req.get("fuera_de_la_solicitud", [])
    justificados = {j.get("ca") for j in fuera if j.get("ca")}

    hus_inv = {c["hu"] for c in inv if c.get("hu")}
    claves_inv = {f"{c['hu']}:{c['ca']}" for c in inv if c.get("hu") and c.get("ca")}

    cubiertos = set()
    for it in todos:
        for k in it.get("ca", []):
            cubiertos.add(k)

    fallos = {
        "ca_sin_dato": sorted(k for k in claves_inv if k not in cubiertos and k not in justificados),
        "items_sin_ca": sorted(it.get("id", "?") for it in todos if not it.get("ca")),
        "derivables_en_la_solicitud": sorted(
            f"{it.get('id','?')} (derivado de {it['derivado_de']})"
            for it in todos if it.get("derivado_de")),
        "responsable_ajeno": sorted(
            f"{it.get('id','?')} -> {it.get('responsable')}"
            for it in items if it.get("responsable") != DEL_CLIENTE),
        "campos_faltantes": sorted(
            f"{it.get('id','?')}: {', '.join(c for c in OBLIGATORIOS if not it.get(c))}"
            for it in todos if any(not it.get(c) for c in OBLIGATORIOS)),
        "hu_desconocida": sorted(
            f"{it.get('id','?')} cita {h}"
            for it in todos for h in it.get("hu", []) if h not in hus_inv),
        "responsable_invalido": sorted(
            f"{it.get('id','?')} -> {it.get('responsable')}"
            for it in todos if it.get("responsable") not in RESPONSABLES),
        "documentado_sin_origen": sorted(
            it.get("id", "?") for it in documentados if not it.get("como_se_obtiene")),
    }

    veredicto = {
        "status": "fail" if any(fallos.values()) else "ok",
        "ca_total": len(claves_inv),
        "ca_con_dato": len(claves_inv & cubiertos),
        "ca_justificados_sin_dato": len(claves_inv & justificados),
        "items_pedidos_al_cliente": len(items),
        "items_documentados_sin_pedirse": len(documentados),
        "hallazgos": {k: v for k, v in fallos.items() if v},
    }
    ev.mkdir(parents=True, exist_ok=True)
    (ev / "data-coverage-audit.json").write_text(
        json.dumps(veredicto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if a.json:
        print(json.dumps(veredicto, ensure_ascii=False, indent=2))
        return 0 if veredicto["status"] == "ok" else 1

    print(f"Criterios inventariados : {veredicto['ca_total']}")
    print(f"  con dato que los habilita: {veredicto['ca_con_dato']}")
    print(f"  sin dato, justificado    : {veredicto['ca_justificados_sin_dato']}")
    print(f"Datos pedidos al cliente: {veredicto['items_pedidos_al_cliente']}")
    print(f"Datos documentados      : {veredicto['items_documentados_sin_pedirse']}")

    if veredicto["status"] == "ok":
        print("\nAUDITORIA VERDE — la solicitud se puede emitir.")
        return 0

    titulos = {
        "ca_sin_dato": "Criterios sin dato que los habilite y sin justificacion de por que",
        "items_sin_ca": "Datos que no sirven a ningun criterio: o sobran, o falta trazarlos",
        "derivables_en_la_solicitud": "Datos derivables de otro ya pedido: no se piden",
        "responsable_ajeno": "Datos de otro responsable pedidos al cliente: o los marca 'documentar', o salen",
        "campos_faltantes": "Datos sin sujeto, condicion exigida o responsable",
        "hu_desconocida": "Historias citadas que no estan en el inventario",
        "responsable_invalido": "Responsable fuera del catalogo " + str(sorted(RESPONSABLES)),
        "documentado_sin_origen": "Datos documentados que no dicen como se obtienen",
    }
    print("\nAUDITORIA ROJA — la solicitud NO se emite hasta cerrar esto:\n")
    for k, v in fallos.items():
        if not v:
            continue
        print(f"  {titulos[k]} ({len(v)}):")
        for x in v[:40]:
            print(f"    - {x}")
        if len(v) > 40:
            print(f"    ... y {len(v) - 40} mas")
        print()
    print("Un criterio sin dato es un caso que no se va a poder ejecutar, y se descubre")
    print("el dia de la ejecucion. Conseguir un dato en el ambiente de un cliente tarda dias.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
