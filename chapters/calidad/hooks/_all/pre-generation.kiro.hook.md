---
id: calidad-pre-generation-hook
version: 1.0.0
scope: chapter
type: hook
chapter: calidad
description: "Kiro hook que bloquea la generación si el agente no completó los pasos del calidad-pre-generation-protocol. Capa bonus para usuarios Kiro."
tags: [kiro, hook, pre-generation, bonus]
trigger: promptSubmit
---

# Hook — Pre-generation enforcement (Kiro)

Trigger: promptSubmit cuando intent matchea generación de tests del chapter Calidad.

Acciones:
1. Verificar que el agente declaró: project_name, output_path, ui_source/spec/apk, modo, risk_map.
2. Si falta cualquiera → bloquear con mensaje: "Falta inputs: {lista}. Aplicar [[calidad-pre-generation-protocol]]."
3. Verificar que el agente declaró effective_minimum.
4. Verificar que el usuario respondió "procede" explícitamente.

Si bloquea: emit prompt al agente con la lista de faltantes.

Mirror de la Capa 1 (steering pre-generation-protocol) para usuarios Kiro como segunda capa de defensa.
