# Esperas con varios desenlaces y fallos que dicen la verdad

## El problema: una espera que conoce un solo destino

```typescript
await page.waitForURL('**/home**', { timeout: 30000 });
```

Esta línea espera **un** desenlace. Cuando cualquier otra cosa ocurre, el mensaje es siempre el mismo:

```
page.waitForURL: Timeout 30000ms exceeded.
```

Medido contra un ambiente real, ese mensaje único cubría **cinco** situaciones distintas:

| Causa real | Dónde quedó la app | Qué decía la red |
|---|---|---|
| La aplicación pidió aceptar una política antes de continuar | `#/privacy-policies` | autenticación → 200 |
| Lo mismo, pero **sin cambiar la URL** | `#/login` | autenticación → 200 |
| El backend rechazó la autenticación | `#/login` | `sessions/initiate` → **500** |
| El runner **no alcanza** la API (otro dominio, egreso restringido) | `#/login` | **ninguna respuesta**: la request falló sin respuesta |
| El flujo tardó más que el timeout | `#/login` | autenticación → 200, y la app seguía pintando |

Las tres son acciones completamente distintas: modelar un desenlace legítimo que faltaba, escalar un blocker de ambiente, o subir un timeout mal calibrado. El mensaje no distingue ninguna, así que **cada aparición del fallo se re-diagnostica desde cero**, y quien lo recibe —el compañero de pipeline, el equipo de la célula— no tiene forma de saber si el problema es suyo.

El costo no es el test rojo: es que el test rojo no informa.

## El patrón: sondear desenlaces y escuchar la red

Dos piezas. La primera, registrar lo que pasa en la red mientras se espera. **Dos listeners, no uno**: escuchar solo `response` deja ciego el caso más común en un runner de integración continua.

```typescript
const trace = { calls: [] as AuthCall[], networkErrors: [] as string[] };

// Respuestas: cada una con su status, su ruta y el milisegundo en que llegó.
const onResponse = (response: Response): void => {
  if (!AUTH_ENDPOINT.test(response.url())) return;
  trace.calls.push({
    status: response.status(),
    path: new URL(response.url()).pathname,
    at: Date.now() - trace.startedAt
  });
};

// Requests que NUNCA obtienen respuesta: DNS, firewall, proxy o TLS. No
// disparan 'response', asi que sin este listener un runner que no alcanza la
// API falla con el mismo mensaje que un flujo lento.
const onRequestFailed = (request: Request): void => {
  if (!AUTH_ENDPOINT.test(request.url())) return;
  trace.networkErrors.push(
    `${request.failure()?.errorText ?? 'error de red'} ${request.method()} ${request.url()}`
  );
};

trace.startedAt = Date.now();          // el reloj arranca ANTES de la accion
page.on('response', onResponse);
page.on('requestfailed', onRequestFailed);
try {
  await submitAndWaitForDestination(page, timeout, trace);
} finally {
  page.off('response', onResponse);    // los listeners no sobreviven al step
  page.off('requestfailed', onRequestFailed);
}
```

**Por qué `requestfailed` importa tanto en CI y casi nunca en local:** la aplicación y su API suelen vivir en dominios distintos. Desde una máquina de desarrollo con la red corporativa activa los dos resuelven; desde un runner con egreso restringido, la aplicación carga y la API no se alcanza. Sin este listener, el diagnóstico dice "el flujo tardó demasiado" cuando la verdad es que ninguna request salió jamás.

**El reloj arranca antes de la acción, no después.** Si se inicializa después del clic, una respuesta que llegue durante el clic queda con un `at` incoherente y el cálculo de inactividad final miente.

La segunda, sondear en vez de esperar un único destino, para poder distinguir los desenlaces:

```typescript
while (Date.now() < deadline) {
  if (isDestination(page.url())) return;                  // llegó

  if (trace.networkErrors.length > 0) {                   // la red no alcanza la API
    throw new Error(
      `No se pudo alcanzar el backend (${trace.networkErrors[0]}). ` +
      `Ninguna request de autenticación obtuvo respuesta. Es un bloqueo de red del entorno.`
    );
  }

  if (trace.calls.some((c) => c.status >= 400)) {         // el backend rechazó
    throw new Error(
      `El backend rechazó la autenticación (${describe(trace.calls)}). ` +
      `La aplicación permanece en ${page.url()}. No es un problema del test ni del navegador.`
    );
  }

  if (!consentAccepted && (await isConsentVisible(page))) {  // desenlace legítimo
    consentAccepted = await acceptConsent(page);
  }

  await page.waitForTimeout(POLL_INTERVAL);
}
throw new Error(buildDiagnosis(page, trace, timeout));
```

### El desenlace puede no cambiar la URL

`isConsentVisible` sondea **presencia de elementos**, no la ruta. Verificado en campo: una pantalla de consentimiento post-login se pintaba dejando la URL en `#/login`, así que cualquier detección por ruta estaba condenada de entrada. Y el sondeo baja hasta el texto visible, porque la capa semántica puede no haber terminado de publicarse:

```typescript
async function isConsentVisible(page: Page): Promise<boolean> {
  if ((await page.locator(CONSENT_BUTTON_SELECTOR).count()) > 0) return true;
  return (await page.getByText(/S[ií],\s*autorizo/i).count()) > 0;   // sin capa semántica
}
```

**Regla general:** un desenlace se detecta por lo que hay en pantalla. La URL es una señal más, no la definición.

**Sobre el `waitForTimeout` del sondeo**: la política de esperas lo prohíbe como sustituto de una condición (`waits-policy.md`), y esto no lo es. Acá el intervalo es el paso de un bucle que evalúa varias condiciones excluyentes, cosa que ninguna espera nativa de un solo destino puede hacer. Es la excepción, va comentada como tal, y no habilita `waitForTimeout` en ningún otro lugar.

## Los tres mensajes que hay que poder emitir

Un fallo útil nombra la capa responsable. Comparados:

```
page.waitForURL: Timeout 30000ms exceeded.                                    <- inútil
```

```
No se pudo alcanzar el backend (net::ERR_NAME_NOT_RESOLVED POST .../sessions/initiate).
Ninguna request de autenticación obtuvo respuesta. Es un bloqueo de red del entorno.
```

```
El backend rechazó la autenticación (500 POST .../sessions/initiate).
La aplicación permanece en .../#/login. No es un problema del test ni del navegador.
```

```
No se llegó al Home tras 60000ms. URL actual: .../#/privacy-policies.
La aplicación quedó en un paso de consentimiento que el flujo no contempla.
```

El segundo caso es además un **blocker de ambiente**, no un fallo de la suite: se reporta con la categoría `environment_auth_fail` de `[[calidad-environment-blocker-evidence]]` y el delivery gate cierra en `partial`, nunca en `success`. Un 500 del backend enmascarado como timeout del test es la forma más cara de perder esa distinción. Cuando ninguna request obtuvo respuesta, la categoría es `environment_blocked_network`.

## El estado observable manda sobre el reloj

Tentación fuerte y equivocada: deducir el veredicto de la cronología. *"La última respuesta llegó hace 37 segundos y la app sigue en login, luego no es lentitud: la app rechazó la sesión."* Suena riguroso y es una inferencia.

Verificado en campo contra un runner de integración continua: las tres llamadas de autenticación terminaron a los 22.9 s, la espera venció a los 60 s, y **el screenshot mostraba el botón con el spinner girando**. La aplicación seguía trabajando. El veredicto derivado del reloj era falso, y el runner renderizaba por software —sin aceleración gráfica— a una fracción de la velocidad de una máquina de escritorio.

```typescript
// "Hace rato que respondió el backend" NO implica rechazo. El estado del boton
// manda sobre el reloj: si sigue en carga, la aplicacion esta procesando.
const veredicto = procesando
  ? 'el entorno va lento y la aplicación sigue procesando'
  : 'la aplicación no aceptó la sesión: rechazo silencioso';
```

La regla, que aplica más allá de este caso: **cuando exista un estado observable que responda la pregunta, se observa; no se infiere de tiempos.** Un botón en carga, un spinner, un indicador de progreso valen más que cualquier cálculo de inactividad. Y el paso que evita publicar la conclusión equivocada es mirar los screenshots del reporte antes de escribirla — ver `[[calidad-test-evidence-and-traceability]]`.

## El timeout del runner no es el timeout local

Del mismo hallazgo se sigue algo operativo: un flujo que en una máquina de escritorio tarda 25 s puede tardar el triple en un runner sin aceleración gráfica. Subir el timeout editando cada archivo que lo declara no escala —y garantiza que la próxima vez quede desparejo.

**El timeout se declara como un piso configurable por variable de entorno**, con un valor por defecto razonable para desarrollo y la posibilidad de elevarlo desde el pipeline sin tocar código:

```typescript
const timeout = options.timeout ?? envNumber('WEB_LOGIN_TIMEOUT', DEFAULT_TIMEOUT);
```

La variable se documenta en la plantilla de variables del proyecto y en su guía de diagnóstico, o nadie sabrá que existe cuando el pipeline falle.

## Reglas derivadas

### 1. Los desenlaces legítimos se modelan, no se parchean

Un modal de consentimiento, una política pendiente de aceptar, un paso de verificación: si la aplicación puede ir ahí legítimamente, es **un destino del flujo**, no una excepción. El anti-patrón habitual:

```typescript
try {
  await page.locator(privacySel).first().waitFor({ state: 'attached', timeout: 15000 });
  await page.locator(privacySel).first().click({ force: true });
} catch {
  /* no apareció, continuar */
}
```

Tiene dos defectos. El `catch` vacío no distingue "no apareció porque no tocaba" de "no apareció porque el selector cambió". Y los 15 s estaban mal calibrados contra una navegación que tarda ~20 s: el modal aparecía **después** de que la espera se rindiera.

### 2. El timeout sale de una medición, no de un número redondo

Medir el flujo varias veces y derivar el timeout de lo observado:

| Dato | Valor |
|---|---|
| Duración medida del flujo | 15 s a 26 s |
| Timeout que había | 30 s |
| Margen real | entre 4 y 15 s |

Un margen de 4 segundos sobre un flujo de red no es un timeout, es una moneda al aire. La regla: **medir, tomar el peor caso observado y dejar holgura suficiente para el ambiente más lento donde va a correr** — que casi nunca es la máquina donde se midió.

Un timeout duplicado en tres valores distintos por el mismo repositorio (30 s, 60 s, 90 s para el mismo flujo) no es una calibración: es la huella de que nadie midió, y de que el flujo está copiado en vez de compartido.

### 3. Una interacción condicional sin rama alternativa es un no-op silencioso

```typescript
const box = await loginBtn.boundingBox();
if (box) await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
```

Cuando `boundingBox()` devuelve `null`, **no se hace clic y nadie se entera**. El fallo aparece 30 segundos después, en la espera siguiente, describiendo un síntoma que no tiene relación con la causa.

La forma correcta tiene siempre rama alternativa, y falla ruidosamente si ninguna aplica:

```typescript
await button.waitFor({ state: 'visible', timeout: 30000 });

const box = await button.boundingBox();
if (box) {
  await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
  return;
}
await button.click({ force: true });     // ya no se salta el clic en silencio
```

La regla es general y aplica igual en mobile: **ningún `if` alrededor de una interacción puede quedarse sin `else`**. O se actúa, o se falla diciendo por qué.

### 4. Un flujo repetido es un helper

Cuando el mismo bloque —clic, esperar destino, manejar consentimiento— aparece decenas de veces con variantes divergentes, el problema deja de ser cada copia. Un inventario real: 35 bloques del mismo flujo, de los cuales 14 no contemplaban el paso de consentimiento, 14 lo hacían en línea con una espera mal calibrada y 3 usaban un objeto de página. Corregir el patrón en un helper es un cambio; corregirlo en 35 copias no se hace nunca.

La migración de esas copias tiene su propia disciplina en `[[calidad-brownfield-vs-greenfield]]`.

## Cuando el ambiente se degrada a mitad de la medición

Un aviso que vale para cualquier experimento contra un ambiente compartido. Midiendo variantes de este flujo, tras una quincena de ejecuciones seguidas el backend empezó a devolver 500 de forma sostenida. Las variantes medidas después de ese punto dieron 0 de 3 — un resultado que parecía concluyente y no significaba nada.

**Los datos posteriores a la degradación se descartan, no se reportan.** Y el reporte declara explícitamente qué quedó sin medir y por qué. Presentar 0/3 contaminado como evidencia contra una variante es peor que no haberla medido: instala una conclusión falsa que nadie va a volver a cuestionar.

## Cross-links

- `waits-policy.md` — la política general de esperas, y por qué el sondeo de este documento es su excepción acotada.
- `auth-storage-state.md` — cuándo el login deja de ejecutarse por UI en cada escenario.
- `[[calidad-environment-blocker-evidence]]` — categorías cerradas de blocker de ambiente y el schema de evidencia.
- `[[calidad-failure-triage-and-classification]]` — clasificar el fallo antes de corregirlo.
- `[[calidad-brownfield-vs-greenfield]]` — cómo se migra un patrón repetido en un repositorio existente.
