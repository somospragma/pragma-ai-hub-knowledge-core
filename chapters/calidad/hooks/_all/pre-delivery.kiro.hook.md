---
id: calidad-pre-delivery-hook
version: 1.0.0
scope: chapter
type: hook
chapter: calidad
description: "Kiro hook que verifica que el agente emitió el delivery_gate yaml + .evidence/ poblado antes de permitir el mensaje final. Capa bonus para usuarios Kiro."
tags: [kiro, hook, pre-delivery, evidence, bonus]
trigger: agentStop
---

# Hook — Pre-delivery gate (Kiro)

Trigger: agentStop justo antes del mensaje final al usuario.

Acciones:
1. Verificar que el agente emitió el bloque ```yaml delivery_gate:``` completo según [[calidad-delivery-gate-contract]].
2. Verificar que .evidence/ tiene mínimo: session-config.json, generation-manifest.json.
3. Si modo=full: además debe tener execution-log-*.json.
4. Si hubo correcciones: además audit-log-*.md.
5. Verificar status declarado coherente con execution: si exit_code != 0 pero status: success → contradicción, rechazar.

Si bloquea: pedir al agente completar antes de cerrar.

Mirror del delivery-gate-contract para usuarios Kiro como segunda capa.
