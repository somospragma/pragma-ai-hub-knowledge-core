# K6 Discovery Checklist — Inputs específicos de performance

Esta referencia extiende los inputs base de `[[calidad-mandatory-inputs-protocol]]` con los campos que K6 necesita para generar una suite realista, ejecutable y con thresholds defendibles.

Aplicar este checklist **inmediatamente después** de validar los inputs base (intent, project_name, output_path, spec) y antes de pasar al pre-flight.

## Campos obligatorios K6

### 1. Perfil de carga por escenario

Para cada escenario (Línea Base, Carga, Estrés, y opt-in Spike/Soak si aplica), confirmar:

- **Ramp-up**: duración de la subida (ej: `2m`).
- **Steady-state**: duración del plano estable (ej: `10m`).
- **Ramp-down**: duración del descenso (ej: `2m`).
- **Target VUs**: pico de virtual users (ej: `50`).

Si el usuario no provee, sugerir defaults derivados de `[[k6-five-script-types]]` y confirmar explícitamente antes de generar `options.stages`.

### 2. Dependencias externas

- **Auth provider**: URL del IdP, tipo (OAuth2 client_credentials, OIDC password grant, API key, JWT firmado externamente, mTLS, AWS SigV4). Si el token se obtiene out-of-band, declararlo.
- **Bases de datos**: motor, host, si el test toca DB directa o solo via API.
- **Servicios upstream**: lista de servicios que el SUT invoca y su SLA conocido (la carga sobre el SUT propaga al upstream).

### 3. Disponibilidad objetivo

SLA de disponibilidad en porcentaje (ej: `99.5%`, `99.9%`, `99.99%`). Determina el threshold de `http_req_failed` y el tier (`[[k6-thresholds-three-tiers]]`).

### 4. Data de prueba

- **Usuarios concurrentes**: cantidad de cuentas/credenciales distintas disponibles para el test (impacta a si se puede usar 1 usuario en N VUs o si hay que rotar pool).
- **Tipo de payloads**: realistas (capturados de prod), sintéticos (faker), híbridos.
- **Refresh strategy**: cada cuánto rotar/recrear datos (por iteración, por VU, por sesión, manual entre runs).

### 5. Endpoint objetivo vs auxiliares

Distinguir explícitamente:

- **SUT real**: el endpoint cuyo desempeño se quiere medir (lo que aparece en thresholds y reports).
- **Endpoints auxiliares**: auth, setup, teardown, listados que solo sirven para llegar al SUT. NO deben contar en thresholds principales y se etiquetan como `setup`/`teardown` en métricas.

### 6. Volumen esperado

- **Peak QPS**: queries por segundo en hora pico.
- **Usuarios concurrentes en pico**: concurrent users esperados.
- **Hora pico estacional**: ventana horaria/calendario donde el tráfico pico ocurre (ej: lunes 10:00-12:00, último día del mes, Black Friday).

Estos números determinan los `target VUs` de Carga y Estrés y la decisión de activar Spike.

### 7. Restricciones de ambiente

- **WAF activo**: marca/política. Riesgo de bloqueos por rate-limit o por patrones de bot.
- **Rate limits**: declarados a nivel API gateway, IdP o WAF (ej: `1000 req/min por IP`).
- **Networking restringido**: VPN, allow-lists por IP, ambientes sin egreso a internet, puertos cerrados.
- **Ventana de mantenimiento**: si el test solo puede correr en horarios o ambientes específicos.

## Flujo de aplicacion

1. Tras confirmar los inputs base, pasar este checklist al usuario en bloque (no fragmentar).
2. Para cada campo faltante, indicar exactamente QUÉ falta. NO asumir defaults sin confirmación explícita.
3. Persistir la respuesta del usuario en `.evidence/k6-discovery.json` antes de invocar el pre-flight.
4. Si algún campo crítico (Volumen esperado, Disponibilidad, Auth provider) queda sin respuesta, degradar a `scaffold-only` y documentar el blocker.

## Cross-links

- `[[calidad-mandatory-inputs-protocol]]`
- `[[k6-greenfield]]`
- `[[k6-thresholds-three-tiers]]`
- `[[k6-five-script-types]]`
- `[[calidad-pre-generation-protocol]]`
