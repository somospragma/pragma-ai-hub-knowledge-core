# Embedded / IoT Systems — Patrones y Adaptación

## Patrones canónicos

- **Protocolos**: MQTT (v3.1.1, v5.0), CoAP, AMQP 1.0, OPC UA, Modbus TCP/RTU, BLE, Zigbee, LoRaWAN. Cada uno tiene su semántica (QoS, retained messages, will, observe).
- **MQTT QoS**: 0 (at-most-once, fire-and-forget), 1 (at-least-once, ack), 2 (exactly-once, 4-way handshake). Tests deben cubrir las tres si el broker/cliente las soportan.
- **Retained messages**: el broker guarda el último mensaje por topic con `retain=true`. Tests deben validar que un nuevo subscriber recibe el retained inmediatamente.
- **Last Will & Testament (LWT)**: mensaje publicado por el broker cuando el cliente se desconecta abruptamente. Validar con disconnect forzado.
- **Firmware OTA**: actualización remota. Validar checksum, signed firmware, rollback ante fallo, doble partición A/B.
- **Conectividad intermitente**: dispositivos pasan por túneles, sombras, bajada de batería. Tests de pérdida y reconexión son obligatorios.
- **Batería baja**: comportamiento degradado documentado (reducir frecuencia de telemetría, dormir sensores).
- **Hora del dispositivo**: muchos IoT no tienen RTC fiable; validar tolerancia a clock skew y dependencia de NTP.

## Framework primario

- **Cliente MQTT propio en lenguaje del equipo** (Eclipse Paho, MQTTnet, HiveMQ MQTT client) + **Pact Messaging** para contratos.
- **Mosquitto** o **HiveMQ** local para integration tests.
- **Hardware-in-the-loop (HIL)**: la suite corre contra hardware real (board, sensor, gateway).
- **Software-in-the-loop (SIL)**: simulador del firmware corre en host, la suite no toca hardware. Usar para CI; HIL para gates de release.

## Complementarios

- **k6 con xk6-mqtt** para perf de broker y throughput sostenido.
- **OASIS MQTT conformance test suite** para validar implementaciones de broker custom.
- **OPC UA Compliance Test Tool (CTT)** para servidores OPC UA.
- **Wireshark + tshark** para captura y análisis de tráfico (MQTT, CoAP, Modbus).
- **Renode** o **QEMU** para simular boards completos en CI.

## Escenarios obligatorios cross-IoT

- **Pérdida de conectividad mid-transaction**: cortar red en medio de un publish QoS 2 → validar que tras reconexión se completa exactamente una vez.
- **Reboot del dispositivo con mensajes pendientes**: validar persistencia de queue si aplica.
- **Batería <10%**: validar modo low-power (frecuencia reducida, sin operaciones no-críticas).
- **Firmware OTA fallido a mitad de download**: validar resume o rollback.
- **Clock skew ±5 min**: validar que tokens y signatures sigan válidos dentro de tolerancia.

## Antipatrones

- Testear solo con SIL — bugs de timing y hardware aparecen solo en HIL.
- Asumir conectividad estable — el campo es lo opuesto.
- Probar QoS 0 únicamente porque "es más simple" — los clientes que requieren QoS 1/2 se rompen sin aviso.
- No validar OTA rollback — un firmware malo bricks la flota.
- Hardcodear el tiempo del host — los devices con clock skew exponen el bug en producción.
