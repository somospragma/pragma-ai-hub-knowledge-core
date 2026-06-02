# DAST con OWASP ZAP en CI

OWASP ZAP es el escáner DAST por defecto del chapter para APIs y aplicaciones web. Se integra en CI mediante imagen Docker y se ejecuta contra ambientes no productivos (staging/QA) con autorización previa.

## Ejecución en pipeline

Imagen oficial: `owasp/zap2docker-stable` (alias `softwaresecurityproject/zap-stable` para la versión mantenida).

Para APIs con OpenAPI, el script recomendado es `zap-api-scan.py`. Para aplicaciones web con UI, `zap-full-scan.py`. Para una pasada rápida, `zap-baseline.py`.

```bash
docker run --rm \
  -v $(pwd)/zap-out:/zap/wrk:rw \
  -t owasp/zap2docker-stable \
  zap-api-scan.py \
    -t https://api-staging.example.com/openapi.json \
    -f openapi \
    -r zap-report.html \
    -J zap-report.json \
    -w zap-report.md \
    -z "-config api.disablekey=true" \
    -I
```

Flags clave:

- `-t`: URL del OpenAPI (debe ser accesible desde el runner).
- `-f openapi`: formato del contrato.
- `-r`/`-J`/`-w`: reportes HTML, JSON y Markdown.
- `-I`: no fallar inmediatamente por warnings (los gates los aplica el step siguiente).
- `-z`: opciones avanzadas del scanner (ej. desactivar API key del propio ZAP).

## Thresholds y gating

Política por defecto del chapter:

| Severidad | Acción                                  |
|-----------|-----------------------------------------|
| High      | **Fallar build** (`exit 1`)             |
| Medium    | Warning + comentario en PR              |
| Low       | Reportar, no bloquear                   |
| Info      | Sólo registrar                          |

Snippet de evaluación (parsea `zap-report.json`):

```bash
HIGH=$(jq '[.site[].alerts[] | select(.riskcode == "3")] | length' zap-out/zap-report.json)
if [ "$HIGH" -gt 0 ]; then
  echo "ZAP encontró $HIGH vulnerabilidades High. Build fallido."
  exit 1
fi
```

## Integración con Karate (ZAP como proxy)

Para reusar la suite Karate funcional como motor de tráfico de DAST, configura ZAP como proxy delante de las peticiones de Karate. En `karate-config.js`:

```javascript
function fn() {
  const env = karate.env || 'dev';
  const config = {
    baseUrl: 'https://api-staging.example.com',
  };

  if (karate.properties['security.scan'] === 'true') {
    karate.configure('proxy', {
      uri: 'http://localhost:8080',
      nonProxyHosts: ['localhost'],
    });
    karate.configure('ssl', true);
  }

  return config;
}
```

Ejecución en CI:

```bash
# 1. Levanta ZAP en modo daemon
docker run -d --name zap -p 8080:8080 owasp/zap2docker-stable \
  zap.sh -daemon -host 0.0.0.0 -port 8080 \
  -config api.disablekey=true -config api.addrs.addr.regex=true -config api.addrs.addr.name=".*"

# 2. Corre la suite Karate atravesando el proxy
mvn test -Dkarate.options="--tags @security" -Dsecurity.scan=true

# 3. Pide a ZAP el reporte
curl "http://localhost:8080/JSON/core/jsonreport/" -o zap-report.json
curl "http://localhost:8080/OTHER/core/other/htmlreport/" -o zap-report.html
```

Beneficios: la cobertura funcional se transforma en tráfico real para el escáner pasivo de ZAP, sin duplicar mantenimiento.

## Modos de escaneo

- **Baseline** (`zap-baseline.py`): sólo passive scan. Rápido, seguro para correr en cada PR.
- **API scan** (`zap-api-scan.py`): active scan dirigido por OpenAPI. Recomendado en pipeline nightly.
- **Full scan** (`zap-full-scan.py`): active scan + spider completo. Sólo en ambiente dedicado y ventana coordinada.

## Artefactos a publicar

- `zap-report.html` — auditoría humana.
- `zap-report.json` — máquina (consumido por gates y dashboards).
- `zap-report.md` — comentario en PR.

Encadena con `[[calidad-test-evidence-and-traceability]]` para archivar los reportes en el storage de evidencias.

## Restricciones

- Active scan **sólo con autorización escrita** y en ambiente no productivo.
- Coordina ventana con operaciones del cliente: ZAP puede generar tráfico significativo.
- No commitees la API key del propio ZAP ni tokens del sistema bajo prueba (ver `secrets-management.md`).
