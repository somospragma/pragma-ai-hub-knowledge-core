#!/usr/bin/env python3
"""Puerta de artefactos obligatorios del chapter Calidad.

Comprueba EXISTENCIA y FORMA. Validar que un campo esta es determinista y no debe
gastarse en razonamiento del agente; lo que exige juicio va al verificador con
contexto limpio, no aqui.

Comprueba que existan los artefactos que los assets OBLIGATORIOS exigen y devuelve 1
si falta alguno, para engancharse a un pre-commit o a la puerta de entrega sin depender
de que nadie se acuerde. Autocontenido a proposito: un solo archivo, sin dependencias.

    python3 check-required-artifacts.py [--evidence .evidence] [--when X] [--all]

Condiciones: always, analysis, front, brownfield, multiplatform, executed, mock, delivery.
Se deducen de .evidence/pipeline-state.json cuando es posible; se fuerzan con --when.

`analysis` es la excepcion: NO se deduce, se declara con `"route": "analisis-y-datos"`.
Es la ruta previa a que exista codigo —analizar historias y pedir datos al cliente— y sus
artefactos no tienen nada que ver con una generacion. Deducirla de un nombre de fase la
activaba en cualquier automatizacion cuya primera fase se llama "diseno".
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
    {"path": ".evidence/input-sufficiency.json", "when": "always",       "by": "calidad-sut-readiness-gate",                  "why": "dictamen de preparacion del sistema antes de gastar la primera corrida"},
    {"path": ".evidence/tooling-gaps.md",       "when": "always",       "by": "calidad-deterministic-work-to-tooling",       "why": "que resuelve ya el proyecto y que hueco queda: es lo que abarata la historia siguiente"},
    {"path": ".evidence/ui-sources.md",         "when": "front",        "by": "calidad-ui-source-contract",                  "why": "que fuente cubre el flujo y cual la estructura; una sola casi nunca cubre las dos"},
    {"path": ".evidence/functional-flow.md",    "when": "front",         "by": "calidad-functional-flow-input",               "why": "el recorrido es insumo; descubrirlo ejecutando es lo mas caro que hace un agente"},
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
    {"path": ".evidence/verification",          "when": "always",       "by": "calidad-fresh-context-verification",          "why": "lo que ninguna puerta puede comprobar lo revisa alguien sin el sesgo de quien lo hizo", "kind": "dir"},
    # --- fase de analisis: lo previo a que exista una linea de codigo ---
    {"path": ".evidence/historias",             "when": "analysis",      "by": "calidad-story-evidence-baseline",             "why": "la historia integra: analizar desde el resumen del ticket obliga a rehacer el analisis", "kind": "dir"},
    {"path": ".evidence/story-sources.json",    "when": "analysis",      "by": "calidad-story-evidence-baseline",             "why": "de que fuentes se alimenta cada historia, y cual falta con su razon"},
    {"path": ".evidence/analisis",              "when": "analysis",      "by": "calidad-story-quality-analysis-artifacts",    "why": "un dossier por historia: dudas, estrategia y datos, autocontenidos", "kind": "dir"},
    {"path": ".evidence/ca-inventory.json",     "when": "analysis",      "by": "calidad-client-test-data-request",            "why": "inventario de criterios: sin el, la cobertura de datos se audita de memoria"},
    {"path": ".evidence/data-request.json",     "when": "analysis",      "by": "calidad-client-test-data-request",            "why": "la solicitud como datos; el markdown es salida, no fuente"},
    {"path": ".evidence/data-coverage-audit.json","when": "analysis",    "by": "calidad-client-test-data-request",            "why": "el cruce criterio a dato que condiciona la emision de la solicitud"},
    {"path": ".evidence/SOLICITUD-DATOS.md",    "when": "analysis",      "by": "calidad-client-test-data-request",            "why": "la solicitud emitida: el ticket es el canal, el repositorio es el registro"},
    # --- cierre A: los obligatorios que si producen artefacto ---
    {"path": ".evidence/execution-status.json", "when": "executed",      "by": "calidad-environment-blocker-evidence",        "why": "un bloqueo de ambiente afirmado sin evidencia ya cerro una entrega en falso"},
    {"path": ".evidence/session-config.json",   "when": "always",        "by": "calidad-post-generation-execution-prompt",    "why": "modo de operacion y presupuesto de sesion declarados, no supuestos"},
    {"path": ".evidence/metadata.json",         "when": "executed",      "by": "calidad-execution-metadata-schema",           "why": "metadatos de la corrida: sin ellos un resultado no se puede atribuir"},
    {"path": ".evidence/healing-log.jsonl",     "when": "executed",      "by": "calidad-test-self-healing",                   "why": "todo fallback de localizador deja rastro; sin el, el healing esconde deuda"},
    {"path": ".evidence/triage",                "when": "executed",      "by": "calidad-failure-triage-and-classification",   "why": "clasificacion por fallo: sin ella la correccion arranca sin causa raiz", "kind": "dir"},
    {"path": ".evidence/audit-log",             "when": "executed",      "by": "calidad-test-self-correction-loop",           "why": "diff y guardrail por iteracion; sin trazabilidad la auto-correccion es invalida", "kind": "dir"},
    {"path": ".evidence/alm-authorizations.md", "when": "delivery",      "by": "calidad-alm-write-authorization-gate",        "why": "la ficha de autorizacion con conteo, antes de cada escritura en el ALM"},
    {"path": ".evidence/alm-publication.json",  "when": "delivery",      "by": "calidad-alm-test-publishing-cycle",           "why": "que se publico y a que ciclo: el publicador imprime exito aunque la auth falle"},
    {"path": ".evidence/executive-report.md",   "when": "delivery",      "by": "calidad-executive-report-generator",          "why": "el reporte ejecutivo de la corrida"},
    {"path": ".evidence/locators-discovered.json","when": "front",       "by": "calidad-appium-apk-auto-discovery",           "why": "localizadores descubiertos del binario, no inferidos"},
]

# Obligatorios que NO producen artefacto propio, con la razon y como se verifican.
# La regresion del chapter exige que todo obligatorio este arriba o aqui: asi
# ninguno se queda sin capa de exigibilidad por olvido.
NO_ARTIFACT = {
    "calidad-asset-resolver":                       "tabla de traduccion; se verifica con la resolucion de enlaces de la regresion",
    "calidad-results-structure-universal":           "convencion de rutas; se verifica en la estructura de results/, no en un archivo",
    "calidad-streaming-files-protocol":              "cubierto por generation-manifest.json",
    "calidad-test-execution-orchestration":          "cubierto por preflight.json y el veredicto de corrida",
    "calidad-smoke-gate-policy":                     "cubierto por la fase smoke_gate de pipeline-state.json",
    "calidad-automation-feasibility-assessment":     "cubierto por coverage-declared.json: que se automatiza y que no",
    "calidad-business-driven-prioritization":        "cubierto por coverage-declared.json: la prioridad por criterio",
    "calidad-flutter-locators-and-gestures":         "doctrina de localizacion; se verifica por la procedencia en ui-sources.md y por eval",
    "calidad-karate-runtime-traps":                  "doctrina de stack; se verifica por eval",
    "calidad-data-volatility-and-assertion-anchoring":"doctrina de diseno de asercion; se verifica por eval",
    "calidad-measure-before-proposing":              "doctrina de proceso: la medicion acompana la propuesta; se verifica por eval",
}


# Forma esperada de cada artefacto. La puerta valida ESTRUCTURA, no solo existencia:
# comprobar que un campo esta es determinista y no debe gastarse en razonamiento del
# agente. Lo que exige juicio —si un criterio es convertible en asercion— no esta aqui:
# eso es del verificador con contexto limpio.
#   json: claves requeridas en la raiz, o en cada elemento si es lista (usar "[]" al frente)
#   md:   marcadores que deben aparecer en el texto
SHAPE = {
    ".evidence/pipeline-state.json":        {"json": ["phases"]},
    ".evidence/input-sufficiency.json":     {"json": ["[]", "input", "expected", "got", "missing", "action"]},
    ".evidence/coverage-declared.json":     {"json": ["[]", "criterio", "plataformas", "escenario"]},
    ".evidence/mock-manifest.json":         {"json": ["units", "contract_version", "design_system_version", "front_revision"]},
    ".evidence/preflight.json":             {"json": ["probes"]},
    ".evidence/execution-status.json":      {"json": ["status"]},
    ".evidence/metadata.json":              {"json": ["run_id"]},
    ".evidence/alm-publication.json":       {"json": ["cycle", "published"]},
    ".evidence/coverage-declared-vs-delivered.json": {"json": ["declared", "delivered", "difference"]},
    ".evidence/functional-flow.md":         {"md": ["pantalla", "bifurcaci", "intermitente", "desenlace", "precondici"]},
    ".evidence/ui-sources.md":              {"md": ["flujo", "estructura", "procedencia"]},
    ".evidence/tooling-gaps.md":            {"md": ["existe", "falta"]},
    ".evidence/platform-learnings.md":      {"md": ["compartida", "espec"]},
    ".evidence/alm-authorizations.md":      {"md": ["conteo"]},
    ".evidence/story-sources.json":         {"json": ["[]", "hu", "archivo", "criterios", "completo"]},
    ".evidence/ca-inventory.json":          {"json": ["[]", "hu", "ca", "texto"]},
    ".evidence/data-request.json":          {"json": ["meta", "familias", "items", "fuera_de_la_solicitud"]},
    ".evidence/data-coverage-audit.json":   {"json": ["status", "ca_total", "ca_con_dato"]},
}


def valida_forma(art: dict) -> str | None:
    """Devuelve el motivo si la forma no cumple; None si esta bien."""
    reglas = SHAPE.get(art["path"])
    if not reglas:
        return None
    ruta = Path(art["path"])
    try:
        txt = ruta.read_text(encoding="utf-8")
    except Exception as e:
        return f"no se pudo leer ({e.__class__.__name__})"
    if "json" in reglas:
        try:
            d = json.loads(txt)
        except Exception:
            return "no es JSON valido"
        req = list(reglas["json"])
        if req and req[0] == "[]":
            req = req[1:]
            if not isinstance(d, list):
                d = d.get("items") or d.get("entries") or d
            if not isinstance(d, list) or not d:
                return "se esperaba una lista con al menos un elemento"
            faltan = sorted({k for k in req if any(k not in e for e in d if isinstance(e, dict))})
        else:
            faltan = sorted(k for k in req if k not in (d if isinstance(d, dict) else {}))
        if faltan:
            return "faltan campos: " + ", ".join(faltan)
    if "md" in reglas:
        low = txt.lower()
        faltan = [k for k in reglas["md"] if k not in low]
        if faltan:
            return "el documento no cubre: " + ", ".join(faltan)
    return None


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
        # La ruta de analisis se DECLARA, no se deduce. Deducirla del nombre de fase
        # activaba sus artefactos en cualquier generacion cuya primera fase se llama
        # "diseno", y la puerta acababa exigiendo una solicitud de datos al cliente en
        # medio de una automatizacion. Solo la escribe el workflow de analisis.
        ruta = str(d.get("route") or d.get("ruta") or "").lower()
        if ruta in ("analisis-y-datos", "analysis-and-data"):
            c.add("analysis")
        fases = {f.get("id"): f.get("status") for f in d.get("phases", []) if isinstance(f, dict)}
        if fases.get("smoke_gate") or fases.get("suite_executed"):
            c.add("executed")
        if fases.get("delivery_gate"):
            c.add("delivery")
        plats = d.get("platforms") or d.get("plataformas") or []
        if isinstance(plats, list) and len(plats) > 1:
            c.add("multiplatform")
        if any(k in blob for k in ("web", "android", "ios", "mobile", "playwright", "appium")):
            c.add("front")
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
        if not existe:
            faltan.append(dict(art, _motivo="no existe"))
            continue
        motivo = valida_forma(art)
        if motivo:
            faltan.append(dict(art, _motivo=motivo))
        else:
            ok += 1

    print(f"Condiciones activas: {', '.join(sorted(activas))}")
    print(f"Artefactos verificados: {ok + len(faltan)}  ·  presentes: {ok}  ·  faltan: {len(faltan)}")
    if not faltan:
        print("\nPUERTA VERDE.")
        return 0
    print("\nPUERTA ROJA — artefactos ausentes o con forma incompleta:\n")
    for art in faltan:
        print(f"  {art['path']}  [{art.get('_motivo','no existe')}]\n      lo exige : {art['by']}\n      para que : {art['why']}\n")
    print("Un artefacto obligatorio que nunca se crea es una regla que no existe.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
