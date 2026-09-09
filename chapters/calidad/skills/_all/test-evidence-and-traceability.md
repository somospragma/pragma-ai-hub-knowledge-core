---
id: calidad-test-evidence-and-traceability
version: 1.2.0
scope: chapter
type: skill
chapter: calidad
description: Configura evidencia (reportes, traces, summaries) y trazabilidad requisito → test → resultado por framework.
tags: [evidence, traceability, reports, karate, k6, playwright, appium, serenity]
---

# Test Evidence and Traceability — Reportes y Tags por Framework

## Cuándo aplicar

Aplica este skill como paso final de la generación (paso 7 de `[[calidad-route-test-generation]]`), una vez que los archivos de prueba y la infraestructura están persistidos.

Su propósito doble:

1. **Evidencia**: que cada ejecución produzca artefactos auditables (reportes HTML, traces, videos, JSON summaries) en rutas conocidas y consistentes.
2. **Trazabilidad**: que cada test enlace requisito → caso → ejecución → decisión, vía tags explícitos.

## Evidencia por framework

### Karate

- Reportes: `target/karate-reports/` (HTML por feature + `karate-summary.html`).
- Activar JUnit XML: `karate.options="--output-junit=target/karate-reports"` (configurado en `TestRunner.java`).
- Cada `Feature` declara tags `@user-story:HUT-123` para enlazar con Jira u otra herramienta ALM.
- Para CI: publicar `target/karate-reports/karate-summary.html` como artifact.

### K6

- Implementar `handleSummary()` en cada script para exportar JSON con timestamp a `results/`.
- Formato de archivo: `${ISO}-summary.json` (ej. `2026-05-27T14-32-10-summary.json`).
- Snippet de referencia:

```javascript
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.2/index.js';

export function handleSummary(data) {
  const iso = new Date().toISOString().replace(/[:.]/g, '-');
  return {
    [`results/${iso}-summary.json`]: JSON.stringify(data, null, 2),
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
  };
}
```

- Thresholds en `options` para que K6 marque la ejecución como fallida si se superan SLAs (ej. `http_req_duration: ['p(95)<500']`).

### Playwright

- En `playwright.config.ts`:

```ts
export default defineConfig({
  reporter: [['html', { outputFolder: 'playwright-report', open: 'never' }]],
  use: {
    trace: 'on-first-retry',
    video: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
});
```

- Reporte: `npx playwright show-report` abre `playwright-report/index.html`.
- Traces (`trace.zip`) se abren con `npx playwright show-trace path/to/trace.zip` — clave para auditoría de fallos en CI.

### Appium + Serenity (Screenplay, V2)

- `./gradlew aggregate` genera el reporte single-page Serenity en `target/site/serenity/index.html`.
- Cada método anotado con `@Step("...")` aparece como paso narrado en el reporte.
- Configuración en `serenity.properties`:

```properties
serenity.project.name=${project_name}
serenity.report.encoding=UTF-8
serenity.take.screenshots=AFTER_EACH_STEP
serenity.test.root=com.client.qa.mobile
```

- Las screenshots se asocian automáticamente a cada `@Step` y quedan visibles en el reporte agregado.

## Trazabilidad — Convención de tags

Aplica la misma convención de tags **en todos los frameworks** (Karate `@`, Cucumber `@`, Playwright `test.describe.parallel('@tag', ...)` o `test('... @tag', ...)`, K6 vía `tags` en `options`):

| Tag                       | Propósito                                                       | Ejemplo                  |
|---------------------------|-----------------------------------------------------------------|--------------------------|
| `@user-story:<ID>`        | Liga el test a la historia de usuario en Jira/ALM               | `@user-story:HUT-123`    |
| `@requirement:<ID>`       | Liga a un requisito funcional formal                            | `@requirement:RF-045`    |
| `@smoke`                  | Suite mínima de humo, ejecutable en cada commit                 | `@smoke`                 |
| `@regression`             | Suite completa de regresión                                     | `@regression`            |
| `@critical`               | Camino crítico de negocio (transferencias, pagos, autenticación) | `@critical`              |
| `@negative`               | Escenario de validación de error o regla de negocio             | `@negative`              |
| `@performance`            | (K6) marca tipo de prueba (load/stress/spike/soak)              | `@performance:load`      |

## Los screenshots del reporte se miran antes de concluir

La evidencia visual no es un adjunto para el informe: es **la fuente que corrige las conclusiones equivocadas**. Un mensaje de error dice qué se rompió; el screenshot dice qué estaba pasando en pantalla, que casi nunca es lo mismo.

Verificado en campo, dos veredictos publicados y falsos que se cayeron al abrir las imágenes del mismo reporte que ya se tenía:

| Veredicto por texto y reloj | Lo que mostraba el screenshot |
|---|---|
| "El backend respondió hace 37 s y la app sigue en login: es un rechazo silencioso" | El botón con el spinner girando: la aplicación seguía procesando, el entorno era lento |
| "El escenario falla al buscar el elemento" | El escritorio del sistema con un diálogo del sistema operativo encima de la aplicación |

**Regla dura: ningún diagnóstico se cierra sin haber incorporado lo que muestran las capturas de la corrida que se está diagnosticando.** Aplica al reporte propio y al que llega de un pipeline ajeno. Cuando la captura contradice la hipótesis, gana la captura.

### El agente no puede abrir imágenes, y por eso la regla anterior necesita un mecanismo

Esta es la parte que se omitía y que hacía la regla inaplicable. **Las herramientas de archivo de un agente devuelven texto: no abren binarios ni imágenes.** Una captura sólo entra a su razonamiento cuando una persona la adjunta a la conversación, por la vía multimodal. Verificado en campo, y de la forma más costosa: tras varias sesiones de conjeturas, la persona pegó la captura en el chat y el problema se resolvió en un turno.

De ahí una consecuencia que hay que aceptar en vez de pelear: **"abre la imagen y mírala" no es una instrucción ejecutable por el agente.** Escribirla produce lo que produjo aquí — la regla se declara, no se cumple, y nadie entiende por qué.

Las tres vías que sí funcionan, en orden de preferencia:

1. **Extraer la información visual como texto en el instante del fallo.** Es la vía principal, no depende de nadie y **es trabajo de herramienta, no de razonamiento**: el finalizador de fallo emite el paquete siempre, igual, sin que nadie se acuerde de pedirlo. Si el proyecto no lo tiene, se construye una vez según `[[calidad-deterministic-work-to-tooling]]`. El finalizador que produce la evidencia de la corrida roja emite, junto a la captura: el árbol de accesibilidad o la capa semántica de ese instante, el **texto reconocido** de la imagen cuando el árbol no expone los rótulos, y la **geometría** de lo que hay en pantalla — qué elementos existen, en qué posición, cuáles caen dentro del marco visible y cuáles están montados pero sin renderizar. Con eso, el agente "ve" lo que necesita sin abrir un solo píxel.
2. **La descripción de la persona.** Una línea —dónde quedó la pantalla y qué se veía— resuelve lo que el reconocimiento de texto no alcanza, sobre todo cuando la interfaz se dibuja sobre lienzo y no expone rótulos. Es un campo obligatorio de la ficha de `[[calidad-human-fix-request-protocol]]`.
3. **La imagen pegada en la conversación.** Cuando las dos anteriores no explican el fallo, el agente **pide** la captura con una pregunta concreta en lugar de seguir iterando. Un turno de petición cuesta menos que una tanda de intentos a ciegas.

**Firma de pantalla.** El resumen de una línea que hace legible todo lo anterior y que conviene emitir siempre:

```
home | 3 tarjetas visibles | "Ver más" de cuentas y=186 | "Ver más" de tarjetas y=566 | destino montado en y=0 (sin renderizar)
```

Esa sola línea es la que, en campo, distinguió entre "el elemento no existe" y "el elemento existe pero está fuera del render" — dos diagnósticos con correcciones opuestas.

### Cómo llegar a las imágenes cuando el reporte es un archivo único

Los reportes autocontenidos embeben las imágenes en base64 y pesan decenas de megabytes, lo que hace inviable leerlos enteros. Se extraen a archivos y se miran uno por uno:

```bash
# Localizar las imágenes embebidas sin abrir el archivo completo
grep -o 'data:image/[a-z]*;base64,[A-Za-z0-9+/=]*' reporte.html | head
```

Cada bloque se decodifica a su archivo. Los dos que siempre importan son **la captura del step que falló** y **la del cierre del escenario**, segundos después: la diferencia entre ambas es la que revela si la aplicación avanzaba, si apareció una pantalla no contemplada o si quedó algo encima. Extraerlas es trabajo del agente; **interpretarlas requiere alguna de las tres vías de arriba**, porque el archivo extraído sigue siendo una imagen.

Cuando el reporte no trae capturas del momento del fallo, eso es un hallazgo en sí mismo y se corrige antes de seguir diagnosticando: sin ellas, cada fallo cuesta una sesión de conjeturas.

Lo mismo vale, y con más fuerza, cuando el reporte trae la captura pero **no** su equivalente en texto: el paquete de evidencia está incompleto y se arregla antes de seguir. Una captura que nadie puede leer no es evidencia para quien tiene que diagnosticar.

### Toda evidencia lleva su instante y su dispositivo

Una captura sin marca de tiempo no se puede contrastar contra el hecho que se
quiere afirmar, y una captura sin dispositivo no se puede atribuir. Las dos
etiquetas son parte del artefacto, no metadatos opcionales — ver el paso 0 de
`[[calidad-failure-triage-and-classification]]`.

## Escenarios con más de un dispositivo o sesión

Cuando un escenario maneja un dispositivo además del que está bajo prueba —un
portador de semilla, un segundo navegador, una sesión de administración—, **toda**
la instrumentación de diagnóstico los recorre todos y **etiqueta cada artefacto
con cuál es**: capturas, volcados de jerarquía, vídeo y logs.

El síntoma de no hacerlo es cruel: la evidencia muestra una pantalla impecable,
porque es la del dispositivo que **no** falló. En campo, un volcado decía "el
login está perfecto" mientras el fallo era exactamente que no aparecía el
login… en el otro teléfono. Y las capturas seguían al driver principal, así que
mostraban siempre el aparato equivocado.

**Y se captura antes de cerrar las sesiones auxiliares.** Hay un detalle de orden
que cuesta otra corrida descubrir: si el hook que cierra el dispositivo portador
corre antes que el teardown que vuelca la evidencia, la evidencia del dispositivo
auxiliar **no llega a generarse nunca**.

## Un verde certifica el build que lo produjo

Dos consecuencias, y las dos se anotan:

1. **La cobertura no se hereda entre versiones del artefacto.** Todo resultado se
   registra con la **versión del artefacto que lo produjo**. Al cambiar el build,
   la cobertura acumulada vuelve a cero hasta reejecutar; el reflejo de
   "revalidar solo lo rojo" deja en verde escenarios que ya no prueban nada.
2. **Un step que atraviesa un estado sin aserarlo no protege ese estado.** Un
   escenario que pasa por una pantalla intermedia relevante sin comprobar cuál es
   tiene un verde compatible con la pantalla equivocada. **Un verde que no
   distingue entre lo correcto y lo incorrecto no es cobertura.** Caso medido:
   los escenarios de reinicio de contador pasaban por la pantalla de rechazo del
   token sin verificar su contenido, y seguían verdes cuando el mensaje era otro.

## La evidencia de una corrida roja la produce un finalizador, no el camino de éxito

El modo de fallo más caro de toda esta capacidad: **la evidencia existe en las
corridas verdes y falta justo en las rojas**, que son las únicas que hay que
mirar.

Ocurre porque el paso que aparta o consolida los artefactos se engancha a un
gancho que **no corre cuando la tarea falla**. En local nadie lo nota, porque en
local la corrida iba en verde. En la canalización, el reporte de la corrida
fallida sencillamente no está, y la herramienta que lo publica dice que no
encontró nada.

| Síntoma | Causa | Arreglo |
|---|---|---|
| «0 archivos encontrados» solo en las corridas rojas | El paso que mueve los artefactos corre en el camino de éxito | Engancharlo como **finalizador**: corre haya pasado lo que haya pasado |
| La tarea de publicación aborta antes de generar nada | Comprueba que el directorio de salida exista | Crearlo vacío junto con el otro |
| Un fallo dice solo el nombre de la clase del ejecutor | El runner descarta el detalle de la excepción, que **es** el mensaje de cada escenario fallido | Configurar el formato completo de excepción; el detalle estaba ahí desde siempre |
| La pestaña de pruebas dice «1 test, 1 failed» | El ejecutor reporta un único caso agregado | Emitir el XML por escenario, que el motor de pruebas ya sabe generar |

**Que un pipeline en rojo diga qué falló y contra qué host** es una propiedad que
se diseña, no una que se tiene. Y se verifica **forzando un rojo** — con una
aserción imposible— y comprobando que el artefacto sale igual.

> Cuidado con el volcado completo de peticiones y respuestas al log: útil para
> un canario, inmanejable en una regresión. Va detrás de un interruptor.

### El resumen tiene que ser autocontenido

Un reporte HTML de varias páginas que carga hojas de estilo, scripts e iconos
desde una carpeta hermana **no se puede enseñar dentro de la interfaz de la
canalización**: se incrusta en un marco con política de contenido y llega sin
estilos y con los enlaces rotos.

Lo que sí viaja: un **único archivo** con el CSS incrustado y **cero peticiones a
nada**, que se ve bien abierto desde el artefacto y también dentro del marco
precisamente porque no carga recursos. Y, mejor aún, el mecanismo **nativo** de
resumen de la canalización, que renderiza texto en la portada de la corrida sin
depender de que un administrador instale una extensión.

Y la advertencia de método: **antes de escribir un generador de reportes propio,
buscar el empaquetado.** En un caso medido se sustituyeron 470 líneas de código
propio por una tarea que ya existía; lo que se pierde es un formato a medida, lo
que se gana es no mantenerlo. Es la misma señal de alarma de siempre: si cada
iteración **añade** un artefacto en vez de quitar uno, el remedio se está
persiguiendo en el sitio equivocado.

### El resumen dice de dónde salió cada variable

Es lo que permite contrastar por qué la misma petición devuelve un código desde
una máquina y otro desde el agente. De las direcciones se guarda el valor; de lo
demás **solo si llegó**, porque ahí hay claves y contraseñas y el resumen acaba
publicado. Detalle en `[[calidad-execution-profile-and-config-provenance]]`.

## Cadena requisito → test → resultado → decisión

1. **Requisito**: documentado en Jira/Confluence con ID estable (`HUT-123`, `RF-045`).
2. **Test**: nombrado y tagueado con esos IDs (`@user-story:HUT-123`).
3. **Resultado**: reporte ejecutado (`karate-reports/`, `playwright-report/`, `results/*-summary.json`, `target/site/serenity/`) con timestamp y commit.
4. **Decisión**: el equipo (lead QA, dev lead, PO) consume el reporte y decide bloquear/promover el release. Esta decisión queda registrada en el ticket de Jira referenciado.

## Restricciones

- **NUNCA** entregar tests sin tags de trazabilidad: como mínimo `@user-story` o `@requirement`.
- **NUNCA** desactivar reportes para "ahorrar tiempo de CI": son la única evidencia auditable.
- **NUNCA** reportar "todo verde" si solo corrió `@smoke`. Documenta qué suite se ejecutó.
- **NUNCA** registrar un resultado sin la versión del artefacto que lo produjo, ni heredar cobertura entre builds.
- **NUNCA** instrumentar solo el dispositivo principal en un escenario que maneja varios: la foto tranquilizadora es la del que no importa.
- En clientes con políticas de retención (compliance, auditoría externa, certificaciones ISO/SOC), los reportes y summaries deben **archivarse** (S3, artifactory, o equivalente) según política de retención del cliente.
- Encadena con `[[calidad-route-test-generation]]` como paso final.
- **Dónde se escribe** cada artefacto de evidencia —la convención universal de carpetas por categoría y fecha— es `[[calidad-results-structure-universal]]`. Este skill dice qué capturar; ése, dónde dejarlo.
