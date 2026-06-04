# Appium Inspector REST API — Extracción de view hierarchy

Esta referencia documenta cómo conversar directamente con el servidor Appium vía su REST API para extraer la jerarquía de vistas de la app, identificar elementos clickables y ejecutar gestos (tap/swipe) durante el crawling.

## Endpoints base

Asumimos `BASE_URL = http://127.0.0.1:4723`. En Appium 2.x el prefijo `/wd/hub` es opcional según configuración; se documentan ambas variantes — preferir sin prefijo si el server fue arrancado con `--base-path /`.

### Crear sesión

`POST /wd/hub/session`

Body JSON:

```json
{
  "capabilities": {
    "alwaysMatch": {
      "platformName": "Android",
      "appium:automationName": "UiAutomator2",
      "appium:deviceName": "Android Emulator",
      "appium:appPackage": "com.example.app",
      "appium:appActivity": ".MainActivity",
      "appium:noReset": true,
      "appium:newCommandTimeout": 120
    }
  }
}
```

Respuesta exitosa retorna `value.sessionId`. Persistir en variable `SESSION_ID` para todas las llamadas siguientes.

### Capturar view hierarchy

`GET /wd/hub/session/{SESSION_ID}/source`

Retorna XML (envuelto en JSON `value`) con la estructura completa de la pantalla actual.

### Buscar elemento

`POST /wd/hub/session/{SESSION_ID}/element`

Body:

```json
{ "using": "id", "value": "com.example.app:id/login_button" }
```

Estrategias `using` soportadas: `id`, `accessibility id`, `xpath`, `-android uiautomator`.

### Tap en elemento

`POST /wd/hub/session/{SESSION_ID}/element/{ELEMENT_ID}/click`

Body vacío `{}`. Respuesta `value: null` indica éxito.

### Swipe / gestures

`POST /wd/hub/session/{SESSION_ID}/touch/perform`

Body con secuencia de acciones (press → moveTo → release). En Appium 2.x preferir W3C Actions:

`POST /wd/hub/session/{SESSION_ID}/actions`

```json
{
  "actions": [
    {
      "type": "pointer",
      "id": "finger1",
      "parameters": {"pointerType": "touch"},
      "actions": [
        {"type": "pointerMove", "duration": 0, "x": 500, "y": 1500},
        {"type": "pointerDown", "button": 0},
        {"type": "pointerMove", "duration": 500, "x": 500, "y": 500},
        {"type": "pointerUp", "button": 0}
      ]
    }
  ]
}
```

### Botón back

`POST /wd/hub/session/{SESSION_ID}/back`

Body vacío. Equivalente a presionar back físico/sistema.

### Cerrar sesión (OBLIGATORIO)

`DELETE /wd/hub/session/{SESSION_ID}`

Siempre invocar al final del crawling, incluso en excepción (ver `safety-and-cleanup.md`).

## Snippets

### curl — crear sesión

```bash
SESSION_ID=$(curl -s -X POST http://127.0.0.1:4723/session \
  -H 'Content-Type: application/json' \
  -d '{"capabilities":{"alwaysMatch":{"platformName":"Android","appium:automationName":"UiAutomator2","appium:appPackage":"com.example.app","appium:appActivity":".MainActivity"}}}' \
  | jq -r '.value.sessionId')
echo "$SESSION_ID"
```

### curl — capturar source

```bash
curl -s http://127.0.0.1:4723/session/$SESSION_ID/source | jq -r '.value' > screen.xml
```

### python — wrapper mínimo

```python
import requests

BASE = "http://127.0.0.1:4723"

def create_session(app_package, app_activity):
    payload = {
        "capabilities": {
            "alwaysMatch": {
                "platformName": "Android",
                "appium:automationName": "UiAutomator2",
                "appium:appPackage": app_package,
                "appium:appActivity": app_activity,
                "appium:noReset": True,
                "appium:newCommandTimeout": 120
            }
        }
    }
    r = requests.post(f"{BASE}/session", json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["value"]["sessionId"]

def get_source(session_id):
    r = requests.get(f"{BASE}/session/{session_id}/source", timeout=30)
    r.raise_for_status()
    return r.json()["value"]

def find_element(session_id, using, value):
    r = requests.post(
        f"{BASE}/session/{session_id}/element",
        json={"using": using, "value": value}, timeout=15
    )
    r.raise_for_status()
    return r.json()["value"]["ELEMENT"]

def tap(session_id, element_id):
    r = requests.post(
        f"{BASE}/session/{session_id}/element/{element_id}/click",
        json={}, timeout=15
    )
    r.raise_for_status()

def back(session_id):
    requests.post(f"{BASE}/session/{session_id}/back", json={}, timeout=15)

def delete_session(session_id):
    requests.delete(f"{BASE}/session/{session_id}", timeout=15)
```

## Estructura del XML retornado por `/source`

Raíz `<hierarchy>` con nodos `<android.widget.*>` (o el class real del View). Atributos relevantes por nodo:

| Atributo | Significado |
|---|---|
| `class` | Clase Java del View (`android.widget.Button`, `android.widget.EditText`, etc.) |
| `resource-id` | ID semántico declarado en el layout (`com.example.app:id/login_button`). Preferido como locator. |
| `content-desc` | Accessibility label. Segundo preferido. |
| `text` | Texto visible. Frágil por i18n. |
| `bounds` | Rectángulo `[x1,y1][x2,y2]` para calcular centro de tap. |
| `clickable` | `true`/`false`. Filtrar candidatos para crawl. |
| `enabled` | `true`/`false`. Skipear si `false`. |
| `displayed` | `true`/`false`. Skipear si `false`. |
| `focusable`, `scrollable`, `password` | Metadatos auxiliares. |

Parsear con `xml.etree.ElementTree` (Python) o `org.w3c.dom` (Java). Recorrer en DFS y emitir lista de candidatos clickables.

## Lifecycle obligatorio

```
create_session → loop {get_source → find_element → tap → get_source} → delete_session
```

NUNCA omitir `delete_session`. Si una excepción interrumpe el loop, capturar y delegar el cleanup al bloque finally documentado en `safety-and-cleanup.md`.
