#!/usr/bin/env python3
"""Inventario de criterios de aceptacion desde las historias ya descargadas.

Recorre los .md normalizados de las historias y emite una fila por criterio en
.evidence/ca-inventory.json. Enumerar criterios es determinista: no debe gastarse
en razonamiento del agente, y menos una vez por cada vez que alguien pregunta si
la cobertura esta completa.

Lo que NO hace, a proposito: decidir si un criterio es verificable. Eso exige
juicio y va al agente y al verificador con contexto limpio. El campo `verificable`
sale en null y alguien lo llena.

    python3 extract-ca.py [--evidence .evidence] [--stories .evidence/historias]

Salida: .evidence/ca-inventory.json  ·  exit 1 si alguna historia no expone criterios.
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

# Un criterio empieza por una de estas formas al principio de linea.
MARCA = re.compile(
    r"^\s*(?:[-*]\s*)?(?:"
    r"(?P<id1>CA[\s\-_]?\d+)"                      # CA-1, CA 1, CA_1
    r"|(?P<id2>(?:Criterio|Escenario)\s+\d+)"      # Criterio 3, Escenario 3
    r"|(?P<id3>\d{1,2})[.)]\s"                     # 1. / 1)
    r"|(?P<id4>Escenario|Scenario)\s*:"            # Escenario: ...
    r")\s*[:.\-]?\s*(?P<txt>.+)$",
    re.I,
)
# Encabezado de la seccion de criterios en el .md normalizado.
SECCION = re.compile(r"^#{1,4}\s*(criterios?\s+de\s+aceptaci|acceptance\s+criteri)", re.I)
OTRA_SECCION = re.compile(r"^#{1,4}\s+")


def bloque_criterios(texto: str) -> list[str]:
    """Devuelve las lineas de la seccion de criterios, o [] si no hay seccion."""
    lineas, dentro, out = texto.splitlines(), False, []
    for ln in lineas:
        if SECCION.match(ln):
            dentro = True
            continue
        if dentro and OTRA_SECCION.match(ln):
            break
        if dentro:
            out.append(ln)
    return out


def criterios_de(archivo: Path) -> tuple[str, list[dict]]:
    texto = archivo.read_text(encoding="utf-8")
    hu = ""
    m = re.search(r"^hu:\s*(\S+)", texto, re.M) or re.search(r"\b(NT-\d+|[A-Z]{2,}-\d+)\b", texto)
    if m:
        hu = m.group(1)
    filas, n = [], 0
    for ln in bloque_criterios(texto):
        m = MARCA.match(ln)
        if not m:
            continue
        n += 1
        cid = (m.group("id1") or m.group("id2") or m.group("id4") or "").strip()
        cid = re.sub(r"[\s_]+", "-", cid).upper() if cid else ""
        if not cid or cid in ("ESCENARIO", "SCENARIO"):
            cid = f"CA-{n}"
        txt = m.group("txt").strip().strip("*_` ")
        filas.append({
            "hu": hu,
            "ca": cid,
            "texto": txt[:400],
            "fuente": str(archivo),
            "verificable": None,   # lo decide una persona o el verificador, no este script
        })
    return hu, filas


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--evidence", default=".evidence")
    p.add_argument("--stories", default=None, help="carpeta de historias normalizadas")
    a = p.parse_args()

    ev = Path(a.evidence)
    src = Path(a.stories) if a.stories else ev / "historias"
    if not src.is_dir():
        print(f"FALLA: no existe {src}/ — las historias se normalizan antes de inventariar criterios.")
        return 1

    todo, sin_criterios = [], []
    for f in sorted(src.glob("*.md")):
        hu, filas = criterios_de(f)
        if not filas:
            sin_criterios.append(hu or f.name)
        todo.extend(filas)

    ev.mkdir(parents=True, exist_ok=True)
    (ev / "ca-inventory.json").write_text(
        json.dumps(todo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    hus = sorted({f["hu"] for f in todo if f["hu"]})
    print(f"Historias leidas: {len(list(src.glob('*.md')))}  ·  con criterios: {len(hus)}")
    print(f"Criterios inventariados: {len(todo)}  ->  {ev / 'ca-inventory.json'}")
    if sin_criterios:
        print("\nSIN CRITERIOS LEGIBLES — no se puede auditar cobertura de datos contra ellas:")
        for h in sin_criterios:
            print(f"  - {h}")
        print("\nO la historia no los tiene (hallazgo de analisis) o el .md no los expone "
              "en una seccion 'Criterios de aceptacion' (normalizar de nuevo).")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
