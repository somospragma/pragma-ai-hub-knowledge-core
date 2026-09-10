#!/usr/bin/env python3
"""Renderiza la solicitud de datos al cliente desde .evidence/data-request.json.

La solicitud no se escribe como prosa: se declara como datos y se renderiza. Es la
decision que produce el ahorro. Medido en campo, cuatro de siete turnos de reproceso
de una sesion fueron reescrituras completas del mismo documento porque cambio una
regla de presentacion —anadir la columna de historia, renumerar, cambiar la leyenda
de roles—. Con la fuente en datos, cada uno de esos cambios es una linea.

El destino es un ticket del gestor de incidencias, no un archivo: el markdown que se
emite usa solo lo que ese renderizador soporta —tablas simples, citas con la barra
vertical en las lineas en blanco, enlaces completos en vez de identificadores sueltos—.

Y no emite si la auditoria de cobertura no pasa: la comprobacion deja de ser algo
que alguien tiene que exigir y pasa a ser una dependencia de la salida.

    python3 render-data-request.py [--evidence .evidence] [--out .evidence/SOLICITUD-DATOS.md]
                                   [--template ../references/template-solicitud.md]
                                   [--skip-audit]

exit 1 si la auditoria falla, si falta la fuente o si la plantilla no trae un slot.
"""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SLOTS = ("notas", "historias", "familias", "resumen", "confirmar", "fuera", "auditoria", "cierre")
COLUMNAS_POR_DEFECTO = [
    ["ID", "id"],
    ["Qué hay que habilitar", "sujeto"],
    ["Condición exacta que debe cumplir", "condicion"],
    ["HU", "hu"],
    ["Para qué lo usamos", "para_que"],
]
ROL = {
    "cliente-datos": "lo habilita el cliente",
    "arquitecto": "lo responde Arquitectura",
    "po-negocio": "lo responde PO / Negocio",
    "dev-pragma": "lo levanta Desarrollo / Pragma",
    "qa": "lo monta el propio equipo de QA",
}


def esc(s) -> str:
    if isinstance(s, list):
        s = ", ".join(str(x) for x in s)
    return str(s or "").replace("|", "\\|").replace("\n", " ").strip()


def tabla(cabeceras: list[str], filas: list[list]) -> str:
    out = ["| " + " | ".join(cabeceras) + " |",
           "| " + " | ".join("---" for _ in cabeceras) + " |"]
    out += ["| " + " | ".join(esc(c) for c in f) + " |" for f in filas]
    return "\n".join(out)


def cita(texto: str) -> str:
    """Cita de varios parrafos. La linea en blanco tambien lleva la barra vertical:
    sin eso el renderizador del gestor de incidencias parte la cita en dos."""
    parrafos = [p.strip() for p in str(texto).split("\n\n") if p.strip()]
    return "\n>\n".join("> " + p.replace("\n", "\n> ") for p in parrafos)


def enlace(hu: str, base: str) -> str:
    return f"{base}{hu}" if base else hu


def fila_de(it: dict, columnas: list) -> list:
    out = []
    for _, campo in columnas:
        v = it.get(campo, "")
        out.append(f"**{v}**" if campo == "id" else v)
    return out


def slot_notas(req: dict) -> str:
    notas = req.get("notas_generales", [])
    return "\n".join(f"* {n}" for n in notas) if notas else ""


def slot_historias(req: dict) -> str:
    hs = req.get("historias", [])
    if not hs:
        return ""
    base = req.get("meta", {}).get("alm_base_url", "")
    return tabla(["HU", "Descripción"],
                 [[enlace(h.get("id"), base), h.get("titulo", "")] for h in hs])


def bloque_familia(fam: dict, items: list, base: str) -> str:
    columnas = fam.get("columnas") or COLUMNAS_POR_DEFECTO
    cab = [c[0] for c in columnas]
    b = [f"## {fam.get('id')}. {fam.get('titulo', '')}".rstrip(". ")]
    if fam.get("objetivo"):
        b += ["", f"**Objetivo:** {fam['objetivo']}"]
    if fam.get("hu"):
        b += ["", f"**HU:** {esc(fam['hu'])}"]
    if fam.get("nota"):
        b += ["", cita(fam["nota"])]
    pedidos = [i for i in items if not i.get("documentar")]
    if pedidos:
        b += ["", tabla(cab, [fila_de(i, columnas) for i in pedidos])]
    if fam.get("nota_cierre"):
        b += ["", cita(fam["nota_cierre"])]
    documentados = [i for i in items if i.get("documentar")]
    if documentados:
        sub = fam.get("sub_bloque", {})
        b += ["", f"### {sub.get('titulo', 'Lo que montamos nosotros')}"]
        if sub.get("nota"):
            b += ["", f"*{sub['nota']}*"]
        cols = sub.get("columnas") or [
            ["ID", "id"], ["Cómo se obtiene", "como_se_obtiene"],
            ["Condición", "condicion"], ["HU", "hu"]]
        b += ["", tabla([c[0] for c in cols], [fila_de(i, cols) for i in documentados])]
    return "\n".join(b)


def slot_familias(req: dict) -> str:
    base = req.get("meta", {}).get("alm_base_url", "")
    items = req.get("items", [])
    bloques = []
    for fam in req.get("familias", []):
        propios = [i for i in items if i.get("familia") == fam.get("id")]
        if propios:
            bloques.append(bloque_familia(fam, propios, base))
    return "\n\n---\n\n".join(bloques)


def slot_resumen(req: dict) -> str:
    if req.get("resumen"):
        return "\n".join(f"* {l}" for l in req["resumen"])
    por_fam, items = {}, [i for i in req.get("items", []) if not i.get("documentar")]
    for i in items:
        por_fam.setdefault(i.get("familia"), []).append(i.get("id"))
    lineas = []
    for fam in req.get("familias", []):
        ids = por_fam.get(fam.get("id"))
        if ids:
            lineas.append(f"**{fam.get('titulo')}**: {', '.join(ids)} ({len(ids)})")
    lineas.append(f"Todo en **{req.get('meta', {}).get('ambiente', 'el ambiente de pruebas')}**, "
                  f"nunca producción.")
    return "\n".join(f"* {l}" for l in lineas)


def slot_confirmar(req: dict) -> str:
    pts = req.get("puntos_a_confirmar", [])
    return "\n".join(f"* {p}" for p in pts) if pts else "_Sin puntos abiertos._"


def slot_fuera(req: dict) -> str:
    fuera = req.get("fuera_de_la_solicitud", [])
    if not fuera:
        return "_No se identificaron datos excluidos._"
    lineas = []
    for f in fuera:
        if f.get("derivado_de"):
            motivo = f"se obtiene a partir de {f['derivado_de']}"
        elif f.get("responsable"):
            motivo = ROL.get(f["responsable"], f["responsable"])
        else:
            motivo = f.get("por_que", "")
        lineas.append(f"* **{f.get('que')}**: {motivo}.")
    return "\n".join(lineas)


def slot_auditoria(req: dict, inv: list, audit: dict) -> str:
    base = req.get("meta", {}).get("alm_base_url", "")
    por_hu, datos_por_hu = {}, {}
    for c in inv:
        por_hu.setdefault(c.get("hu"), []).append(c.get("ca"))
    for i in req.get("items", []):
        for h in i.get("hu", []):
            datos_por_hu.setdefault(h, []).append(i.get("id"))
    resumenes = {h.get("id"): h for h in req.get("historias", [])}
    filas = []
    for hu in sorted(set(por_hu) | set(datos_por_hu)):
        h = resumenes.get(hu, {})
        casos = h.get("casos_resumen") or f"{len(por_hu.get(hu, []))} criterios"
        datos = ", ".join(sorted(set(datos_por_hu.get(hu, [])))) or "—"
        if h.get("datos_extra"):
            datos += ". " + h["datos_extra"]
        filas.append([f"**{enlace(hu, base)}**", casos, datos])
    enc = (f"Criterios inventariados: **{audit.get('ca_total', 0)}** · con dato que los habilita: "
           f"**{audit.get('ca_con_dato', 0)}** · sin dato con justificación declarada: "
           f"**{audit.get('ca_justificados_sin_dato', 0)}**.")
    return enc + "\n\n" + tabla(["HU", "Casos que validan", "Datos que los habilitan"], filas)


def slot_cierre(req: dict) -> str:
    obj = req.get("meta", {}).get("objetivo")
    return f"**Objetivo:** {obj}" if obj else ""


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--evidence", default=".evidence")
    p.add_argument("--out", default=None)
    p.add_argument("--template", default=None)
    p.add_argument("--skip-audit", action="store_true",
                   help="solo para probar la plantilla; jamas para emitir")
    a = p.parse_args()

    ev = Path(a.evidence)
    fuente = ev / "data-request.json"
    if not fuente.is_file():
        print(f"FALLA: no existe {fuente} — la solicitud se declara como datos, no se escribe a mano.")
        return 1

    if not a.skip_audit:
        r = subprocess.run([sys.executable, str(AQUI / "check-data-coverage.py"),
                            "--evidence", str(ev)], capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout or r.stderr)
            print("\nNO SE EMITE la solicitud: la auditoria de cobertura no paso.")
            return 1

    req = json.loads(fuente.read_text(encoding="utf-8"))
    inv = json.loads((ev / "ca-inventory.json").read_text(encoding="utf-8")) \
        if (ev / "ca-inventory.json").is_file() else []
    audit = json.loads((ev / "data-coverage-audit.json").read_text(encoding="utf-8")) \
        if (ev / "data-coverage-audit.json").is_file() else {}

    tpl = Path(a.template) if a.template else AQUI.parent / "references" / "template-solicitud.md"
    if not tpl.is_file():
        print(f"FALLA: no existe la plantilla {tpl}")
        return 1
    texto = tpl.read_text(encoding="utf-8")

    for k, v in req.get("meta", {}).items():
        texto = texto.replace("{{meta." + k + "}}", str(v))

    generados = {
        "notas": slot_notas(req),
        "historias": slot_historias(req),
        "familias": slot_familias(req),
        "resumen": slot_resumen(req),
        "confirmar": slot_confirmar(req),
        "fuera": slot_fuera(req),
        "auditoria": slot_auditoria(req, inv, audit),
        "cierre": slot_cierre(req),
    }
    faltan = [s for s in SLOTS if f"<!-- slot:{s} -->" not in texto]
    if faltan:
        print("FALLA: la plantilla no declara los slots: " + ", ".join(faltan))
        return 1
    for s in SLOTS:
        texto = texto.replace(f"<!-- slot:{s} -->", generados[s])

    quedan = [l for l in texto.splitlines() if "{{meta." in l]
    if quedan:
        print("FALLA: la plantilla pide metadatos que la fuente no trae:")
        for l in quedan:
            print("  " + l.strip())
        return 1

    salida = Path(a.out) if a.out else ev / "SOLICITUD-DATOS.md"
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(texto, encoding="utf-8")
    pedidos = [i for i in req.get("items", []) if not i.get("documentar")]
    print(f"Solicitud emitida: {salida}")
    print(f"  datos pedidos al cliente : {len(pedidos)}")
    print(f"  documentados sin pedirse : {len(req.get('items', [])) - len(pedidos)}")
    print(f"  datos excluidos          : {len(req.get('fuera_de_la_solicitud', []))}")
    print(f"  criterios cubiertos      : {audit.get('ca_con_dato', 0)} de {audit.get('ca_total', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
