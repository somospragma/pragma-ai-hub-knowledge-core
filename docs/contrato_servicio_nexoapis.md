# Contrato de Servicio - API de Novedades NexoAPIs

**Versión:** 1.0
**Fecha:** Abril 2026
**Ambiente:** Producción
**Propietario:** Equipo de Data Services - Pragma

---

## 1. Información General

| Campo                | Valor                                                           |
| -------------------- | --------------------------------------------------------------- |
| Nombre del servicio  | NexoAPIs - Novedades                                            |
| Tipo                 | REST API                                                        |
| Protocolo            | HTTPS                                                           |
| Formato de respuesta | JSON                                                            |
| Ambiente             | Producción                                                     |
| Región AWS          | us-east-1                                                       |
| Base URL             | `https://hluve0xa3a.execute-api.us-east-1.amazonaws.com/prod` |

## 2. Endpoint

```
GET /novedades
```

**URL completa:**

```
https://hluve0xa3a.execute-api.us-east-1.amazonaws.com/prod/novedades?correo={correo_corporativo}
```

## 3. Autenticación

| Método     | Detalle       |
| ----------- | ------------- |
| Tipo        | API Key       |
| Header      | `x-api-key` |
| Obligatorio | Sí           |

La API Key será proporcionada por el equipo de Data & Analytics. Cada consumidor recibirá una API Key única asociada a un Usage Plan.

## 4. Request

### 4.1 Headers

| Header        | Valor                 | Obligatorio |
| ------------- | --------------------- | ----------- |
| `x-api-key` | API Key proporcionada | Sí         |

### 4.2 Query Parameters

| Parámetro | Tipo   | Obligatorio | Descripción                       | Ejemplo                       |
| ---------- | ------ | ----------- | ---------------------------------- | ----------------------------- |
| `correo` | string | Sí         | Correo corporativo del pragmático | `laura.bravo@pragma.com.co` |

### 4.3 Validaciones del parámetro correo

- No puede ser vacío
- Debe cumplir formato de email válido (RFC 5322)
- Se normaliza a minúsculas automáticamente

### 4.4 Ejemplo de Request

```bash
curl -X GET \
  "https://hluve0xa3a.execute-api.us-east-1.amazonaws.com/prod/novedades?correo=laura.bravo@pragma.com.co" \
  -H "x-api-key: {API_KEY}"
```

## 5. Response

### 5.1 Respuesta Exitosa (HTTP 200)

```json
{
  "data": [
    {
      "anio": "2026",
      "mes": "4",
      "sociedad": "4810",
      "id_cliente": "1556445760",
      "nombre_cliente": "PRAGMA NEXT S.A.",
      "id_proyecto": "BOM0001",
      "nombre_proyecto": "Banco Mercantil",
      "id_paquete_trabajo": "BOM0001.1.5",
      "nombre_paquete_trabajo": "Agentes IA",
      "porcentaje_asignacion": "0.5"
    },
    {
      "anio": "2026",
      "mes": "4",
      "sociedad": "4810",
      "id_cliente": "1100686290",
      "nombre_cliente": "PRAGMA, SOCIEDAD ANONIMA GUATEMALA",
      "id_proyecto": "BAM0001",
      "nombre_proyecto": "Banco Agromercantil",
      "id_paquete_trabajo": "BAM0001.1.1",
      "nombre_paquete_trabajo": "Banco Agromercantil",
      "porcentaje_asignacion": "0.5"
    }
  ],
  "count": 2
}
```

### 5.2 Campos de Respuesta

| Campo                             | Tipo    | Descripción                                               |
| --------------------------------- | ------- | ---------------------------------------------------------- |
| `data`                          | array   | Lista de asignaciones del pragmático para el mes en curso |
| `data[].anio`                   | string  | Año de la asignación                                     |
| `data[].mes`                    | string  | Mes de la asignación (1-12)                               |
| `data[].sociedad`               | string  | Código de sociedad SAP                                    |
| `data[].id_cliente`             | string  | NIT o identificador fiscal del cliente                     |
| `data[].nombre_cliente`         | string  | Razón social del cliente                                  |
| `data[].id_proyecto`            | string  | Código único del proyecto                                |
| `data[].nombre_proyecto`        | string  | Nombre del proyecto                                        |
| `data[].id_paquete_trabajo`     | string  | Código del paquete de trabajo dentro del proyecto         |
| `data[].nombre_paquete_trabajo` | string  | Nombre del paquete de trabajo                              |
| `data[].porcentaje_asignacion`  | string  | Porcentaje de dedicación (ej: "0.5" = 50%, "1.0" = 100%)  |
| `count`                         | integer | Número total de asignaciones retornadas                   |

### 5.3 Códigos de Respuesta

| HTTP Code | Descripción                                    | Body                                                                       |
| --------- | ----------------------------------------------- | -------------------------------------------------------------------------- |
| 200       | Consulta exitosa                                | `{"data": [...], "count": N}`                                            |
| 400       | Parámetro correo inválido o faltante          | `{"error": "Parámetro 'correo' requerido y debe ser un email válido"}` |
| 403       | API Key inválida o no proporcionada            | `{"message": "Forbidden"}`                                               |
| 404       | Correo no encontrado en la base de pragmáticos | `{"error": "No se encontró pragmático con ese correo"}`                |
| 429       | Límite de requests excedido                    | `{"message": "Too Many Requests"}`                                       |
| 502       | Error en la consulta al motor de datos          | `{"error": "Error al consultar los datos"}`                              |
| 500       | Error interno del servidor                      | `{"error": "Error interno del servidor"}`                                |

## 6. Reglas de Negocio

| Regla                    | Descripción                                                                                          |
| ------------------------ | ----------------------------------------------------------------------------------------------------- |
| Período de datos        | Siempre retorna datos del**mes y año en curso**                                                |
| Máximo de registros     | 5 asignaciones por consulta                                                                           |
| Fuente de identidad      | Tabla maestra de pragmáticos (correo corporativo → identificación nacional)                        |
| Fuente de asignaciones   | Tabla de novedades del Data Lake (capa analytics)                                                     |
| Personas sin asignación | Si el correo existe pero no tiene asignaciones en el mes actual, retorna `{"data": [], "count": 0}` |

## 7. Límites y Throttling

| Límite                         | Valor                     |
| ------------------------------- | ------------------------- |
| Rate limit                      | 5 requests por segundo    |
| Burst limit                     | 10 requests               |
| Quota diaria                    | 1,000 requests por día   |
| Timeout máximo                 | 29 segundos (API Gateway) |
| Máximo registros por respuesta | 5                         |

## 8. Niveles de Servicio (SLA)

| Métrica       | Objetivo                                           |
| -------------- | -------------------------------------------------- |
| Disponibilidad | 99.9% (respaldado por SLA de API Gateway + Lambda) |
| Latencia P50   | < 5 segundos                                       |
| Latencia P95   | < 15 segundos                                      |
| Latencia P99   | < 29 segundos                                      |
| Tasa de error  | < 1%                                               |

> **Nota:** La primera invocación después de un período de inactividad (cold start) puede tener mayor latencia debido a la inicialización del motor de consulta Athena.

## 9. Seguridad

| Control                 | Implementación                                                           |
| ----------------------- | ------------------------------------------------------------------------- |
| Transporte              | HTTPS/TLS obligatorio                                                     |
| Autenticación          | API Key por consumidor                                                    |
| Autorización           | Usage Plan con throttling y quota                                         |
| Headers de seguridad    | HSTS, X-Content-Type-Options: nosniff, Cache-Control: no-store            |
| Validación de entrada  | Regex de email, sanitización automática                                 |
| Datos sensibles         | No se exponen datos de identificación personal (cédula) en la respuesta |
| Encriptación en reposo | S3 SSE-KMS, Parameter Store                                               |
| Logs                    | No se registran datos personales en logs, solo correo de consulta         |

## 10. Monitoreo y Alertas

| Componente               | Herramienta             | Detalle                      |
| ------------------------ | ----------------------- | ---------------------------- |
| Logs de aplicación      | CloudWatch Logs         | Retención 30 días          |
| Access logs              | API Gateway Access Logs | Formato JSON                 |
| Tracing                  | AWS X-Ray               | Trazabilidad end-to-end      |
| Alarma de errores Lambda | CloudWatch Alarm        | Umbral: > 5 errores en 5 min |
| Alarma de errores 5XX    | CloudWatch Alarm        | Umbral: > 5 errores en 5 min |

## 11. Resultados de Pruebas

Prueba masiva ejecutada el 29 de abril de 2026 sobre el ambiente de producción:

| Métrica                             | Resultado                           |
| ------------------------------------ | ----------------------------------- |
| Personas consultadas                 | 100 (muestra representativa de 895) |
| Registros validados                  | 146 de 941                          |
| Personas con múltiples asignaciones | 41                                  |
| Personas con asignación única      | 59                                  |
| ✅ Respuestas correctas              | 100                                 |
| ❌ Discrepancias                     | 0                                   |
| ❌ Errores                           | 0                                   |
| ❌ Timeouts                          | 0                                   |
| **Tasa de éxito**             | **100.0%**                    |

## 12. Onboarding de Consumidores

Para solicitar acceso a la API:

1. Contactar al equipo de Data & Analytics
2. Se generará una API Key exclusiva para el consumidor
3. Se asociará a un Usage Plan con los límites acordados
4. Se entregará la API Key de forma segura

## 13. Soporte

| Canal              | Detalle                           |
| ------------------ | --------------------------------- |
| Equipo responsable | Data & Analytics - Pragma        |
| Escalamiento       | Arquitectura de Datos             |
| Horario de soporte | Lunes a viernes, 8:00 - 18:00 COT |

## 14. Versionamiento

| Versión | Fecha      | Cambios                                                                      |
| -------- | ---------- | ---------------------------------------------------------------------------- |
| 1.0      | Abril 2026 | Versión inicial - Endpoint GET /novedades con filtro por correo corporativo |

## 15. Ejemplos de Integración

### Python

```python
import requests

API_URL = "https://hluve0xa3a.execute-api.us-east-1.amazonaws.com/prod/novedades"
API_KEY = "{API_KEY}"

response = requests.get(
    API_URL,
    params={"correo": "nombre.apellido@pragma.com.co"},
    headers={"x-api-key": API_KEY},
)

data = response.json()
for asignacion in data["data"]:
    print(f"{asignacion['nombre_proyecto']} - {asignacion['porcentaje_asignacion']}")
```

### JavaScript (fetch)

```javascript
const API_URL = "https://hluve0xa3a.execute-api.us-east-1.amazonaws.com/prod/novedades";
const API_KEY = "{API_KEY}";

const response = await fetch(
  `${API_URL}?correo=nombre.apellido@pragma.com.co`,
  { headers: { "x-api-key": API_KEY } }
);

const { data, count } = await response.json();
data.forEach(a => console.log(`${a.nombre_proyecto} - ${a.porcentaje_asignacion}`));
```

### cURL

```bash
curl -H "x-api-key: {API_KEY}" \
  "https://hluve0xa3a.execute-api.us-east-1.amazonaws.com/prod/novedades?correo=nombre.apellido@pragma.com.co"
```