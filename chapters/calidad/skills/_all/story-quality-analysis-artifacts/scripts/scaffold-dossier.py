#!/usr/bin/env python3
"""Crea el dossier de analisis por historia desde las plantillas del skill.

Una carpeta por historia con sus tres archivos, con cabecera, epica, fecha y leyenda de
roles ya puestas. Lo unico que queda por escribir es lo que exige criterio.

Por que existe: en una sesion de trece historias, la cabecera y la leyenda de responsables
eran identicas en treinta y nueve archivos y se escribieron a mano una por una. Cuando la
leyenda cambio —de dos roles a cuatro—, cambiarla costo un turno entero de busqueda y
reemplazo, y quedaron archivos sin actualizar.

Es ADITIVO: nunca sobrescribe un archivo que ya existe. El analisis escrito no se pierde
al volver a correrlo cuando entra una historia nueva al lote.

    python3 scaffold-dossier.py [--evidence .evidence] [--templates ../references]

Salida: .evidence/analisis/<HU>-<slug>/{01-dudas,02-estrategia-de-pruebas,03-datos-y-accesos}.md
        .evidence/analisis/README.md   (indice del lote, se regenera siempre)
exit 1 si no hay dictamen de fuentes o si alguna historia venia incompleta.
"""
from __future__ import annotations
import argparse, json, re, unicodedata
from datetime import date
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ARCHIVOS = [
    ("01-dudas.md", "template-01-dudas.md"),
    ("02-estrategia-de-pruebas.md", "template-02-estrategia-de-pruebas.md"),
    ("03-datos-y-accesos.md", "template-03-datos-y-accesos.md"),
]


def slug(texto: str, largo: int = 48) -> str:
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()[:largo].rstrip("-")


def rellena(texto: str, f: dict) -> str:
    vals = {
        "hu": f.get("hu", ""),
        "titulo": f.get("titulo", "") or "",
        "epica": f.get("epica", "") or "(sin épica declarada)",
        "estado": f.get("estado", "") or "(sin estado)",
        "fecha": date.today().isoformat(),
        "fuente": f.get("archivo", ""),
        "criterios": str(f.get("criterios", 0)),
        "arquitectura": ", ".join(a.get("archivo", "") for a in f.get("arquitectura", []))
                        or (f.get("arquitectura_ausente") or "(sin fuente de arquitectura)"),
    }
    for k, v in vals.items():
        texto = texto.replace("{{" + k + "}}", str(v))
    return texto


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--evidence", default=".evidence")
    p.add_argument("--templates", default=None)
    a = p.parse_args()

    ev = Path(a.evidence)
    src = ev / "story-sources.json"
    if not src.is_file():
        print(f"FALLA: no existe {src} — las historias se normalizan antes de armar el dossier.")
        return 1
    fuentes = json.loads(src.read_text(encoding="utf-8"))

    tpl_dir = Path(a.templates) if a.templates else AQUI.parent / "references"
    faltan_tpl = [t for _, t in ARCHIVOS if not (tpl_dir / t).is_file()]
    if faltan_tpl:
        print("FALLA: faltan plantillas en " + str(tpl_dir) + ": " + ", ".join(faltan_tpl))
        return 1

    base = ev / "analisis"
    base.mkdir(parents=True, exist_ok=True)
    creados, existian, incompletas = [], [], []
    for f in fuentes:
        if not f.get("completo"):
            incompletas.append(f.get("hu"))
        carpeta = base / f"{f.get('hu')}-{slug(f.get('titulo', ''))}"
        carpeta.mkdir(parents=True, exist_ok=True)
        for nombre, tpl in ARCHIVOS:
            destino = carpeta / nombre
            if destino.exists():
                existian.append(str(destino))
                continue
            destino.write_text(
                rellena((tpl_dir / tpl).read_text(encoding="utf-8"), f), encoding="utf-8")
            creados.append(str(destino))

    filas = ["| HU | Título | Épica | Criterios | Dossier |", "| --- | --- | --- | --- | --- |"]
    for f in sorted(fuentes, key=lambda x: str(x.get("hu"))):
        carpeta = f"analisis/{f.get('hu')}-{slug(f.get('titulo', ''))}/"
        filas.append(f"| {f.get('hu')} | {f.get('titulo','')} | {f.get('epica','') or '—'} "
                     f"| {f.get('criterios',0)} | `{carpeta}` |")
    (base / "README.md").write_text(
        "# Análisis de calidad por historia\n\n"
        f"Lote de {len(fuentes)} historias · índice generado el {date.today().isoformat()}.\n\n"
        "Cada historia es autocontenida: dudas, estrategia de pruebas y datos y accesos.\n"
        "Este índice lo regenera `scaffold-dossier.py`; no se edita a mano.\n\n"
        + "\n".join(filas) + "\n", encoding="utf-8")

    print(f"Historias en el lote : {len(fuentes)}")
    print(f"Archivos creados     : {len(creados)}")
    print(f"Ya existían (intactos): {len(existian)}")
    print(f"Índice               : {base / 'README.md'}")
    if incompletas:
        print("\nAVISO — dossier creado sobre base de evidencia incompleta: "
              + ", ".join(str(x) for x in incompletas))
        print("Se analiza sobre lo que hay y el hueco queda declarado, pero no se cierra "
              "el analisis\nde esas historias hasta completarlas.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
