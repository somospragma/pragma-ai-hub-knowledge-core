# Contrato de `.evidence/data-request.json`

La solicitud es un dato, no un documento. El markdown se genera; lo que se edita es esto.

Sin dependencias externas a propósito: JSON, como el resto de `.evidence/`.

## Raíz

| Clave | Obligatoria | Qué es |
|---|---|---|
| `meta` | sí | Cabecera del documento |
| `notas_generales` | no | Lista de líneas que explican el vocabulario a quien no conoce las historias |
| `historias` | sí | Catálogo de HU: alimenta la tabla de referencia y la de auditoría |
| `familias` | sí | Secciones del documento, en orden |
| `items` | sí | Los datos, uno por fila |
| `fuera_de_la_solicitud` | sí | Lo que no se pide, con su motivo |
| `puntos_a_confirmar` | no | Lo que puede no ser montable |
| `resumen` | no | Líneas del resumen. Si falta, se genera por familia |

## `meta`

| Clave | Qué es |
|---|---|
| `cliente`, `segmento` | Titulan el documento |
| `fecha`, `solicita` | Quién pide y cuándo |
| `ambiente` | **Obligatorio.** Se imprime con la negación de producción al lado |
| `alm_base_url` | Prefijo que convierte cada identificador en enlace. Sin él, los identificadores viajan sueltos y quien los lee en el ticket no puede abrirlos |
| `objetivo` | Línea de cierre |

## `historias[]`

| Clave | Qué es |
|---|---|
| `id` | Identificador en el gestor, tal cual |
| `titulo` | Descripción corta, para quien no conoce la historia |
| `casos_resumen` | Qué casos validan datos. Sale en la tabla de auditoría |
| `datos_extra` | Cómo se cubre lo que no es dato del cliente. Se anexa a la fila de auditoría |

## `familias[]`

| Clave | Qué es |
|---|---|
| `id`, `titulo` | Encabezan la sección |
| `objetivo`, `hu` | Líneas en negrita bajo el título |
| `nota` | Cita antes de la tabla. Los párrafos se separan con línea en blanco doble |
| `nota_cierre` | Cita después de la tabla |
| `columnas` | Pares `[cabecera, campo del ítem]`. Es lo que permite que la familia de estados titule su columna "Estado en el core" en vez de "Condición exacta" |
| `sub_bloque` | Título y nota del bloque de los ítems `documentar` de esta familia |

## `items[]`

| Clave | Obligatoria | Qué es |
|---|---|---|
| `id` | sí | Corto y estable: se cita en el resto del documento |
| `familia` | sí | A qué sección pertenece |
| `sujeto` | sí | **Qué** hay que habilitar |
| `condicion` | sí | **La condición exacta que debe cumplir.** No el identificador |
| `responsable` | sí | `cliente-datos` · `arquitecto` · `po-negocio` · `dev-pragma` · `qa` |
| `hu` | sí | Historias a las que sirve |
| `ca` | sí | Criterios que habilita, como `HU:CA-n`. Es lo que audita la cobertura |
| `para_que` | recomendada | Permite proponer alternativas cuando la condición no es montable |
| `derivado_de` | no | Si está poblada, el ítem **no puede ir en la solicitud** |
| `documentar` | no | `true` = lo provisiona el propio equipo. Sale en el sub-bloque, no se pide |
| `como_se_obtiene` | si `documentar` | Cómo lo consigue el equipo |
| `reutiliza` | no | Otro ítem que puede cumplir también esta condición |

Solo los ítems con `responsable: "cliente-datos"` viajan en el cuerpo de la solicitud.
Cualquier otro responsable exige `documentar: true`, o el verificador rechaza.

## `fuera_de_la_solicitud[]`

| Clave | Qué es |
|---|---|
| `que` | El dato que alguien podría echar en falta |
| `derivado_de` | Ítem del que se obtiene |
| `responsable` | Rol que lo resuelve, cuando no es derivable |
| `hu` | Historias afectadas |

Se declara uno u otro: `derivado_de` o `responsable`. Un motivo, siempre.

## Ejemplo mínimo

```json
{
  "meta": {"cliente": "…", "segmento": "…", "fecha": "2026-09-07",
           "solicita": "equipo de Calidad (QA)", "ambiente": "QA / Certificación",
           "alm_base_url": "https://…/browse/"},
  "historias": [{"id": "AA-101", "titulo": "Home de cuentas",
                 "casos_resumen": "Orden, estados, sin cuentas"}],
  "familias": [{"id": "A", "titulo": "Usuarios de acceso"}],
  "items": [
    {"id": "A1", "familia": "A",
     "sujeto": "Usuario administrador que representa UNA sola empresa",
     "condicion": "Una única empresa activa, con al menos cuatro cuentas visibles.",
     "para_que": "Caso base monoempresa.",
     "hu": ["AA-101"], "ca": ["AA-101:CA-1"], "responsable": "cliente-datos"}
  ],
  "fuera_de_la_solicitud": [
    {"que": "Usuario recién autenticado", "derivado_de": "A1", "hu": ["AA-101"]}
  ]
}
```
