# Esperas con varios desenlaces y fallos que dicen la verdad

## El problema: una espera que conoce un solo destino

```typescript
await page.waitForURL('**/home**', { timeout: 30000 });
```

Esta línea espera **un** desenlace. Cuando cualquier otra cosa ocurre, el mensaje es siempre el mismo:

```
page.waitForURL: Timeout 30000ms exceeded.
```

Medido contra un ambiente real, ese mensaje único cubría tres situaciones distintas:

| Causa real | Dónde quedó la app | Qué decía la red |
|---|---|---|
| La aplicación pidió aceptar una política antes de continuar | `#/privacy-policies` | autenticación → 200 |
| El backend rechazó la autenticación | `#/login` | `sessions/initiate` → **500** |
| El login tardó más que el timeout | `#/login` | autenticación → 200 |

Las tres son acciones completamente distintas: modelar un desenlace legítimo que faltaba, escalar un blocker de ambiente, o subir un timeout mal calibrado. El mensaje no distingue ninguna, así que **cada aparición del fallo se re-diagnostica desde cero**, y quien lo recibe —el compañero de pipeline, el equipo de la célula— no tiene forma de saber si el problema es suyo.

El costo no es el test rojo: es que el test rojo no informa.

## El patrón: sondear desenlaces y escuchar la red

Dos piezas. La primera, registrar los fallos de la capa de negocio mientras se espera:

```typescript
const authFailures: string[] = [];

const onResponse = (response: Response): void => {
  const url = response.url();
  if (AUTH_ENDPOINT.test(url) && response.status() >= 400) {
    authFailures.push(`${response.status()} ${response.request().method()} ${url}`);
  }
};

page.on('response', onResponse);
try {
  await submitAndWaitForDestination(page, timeout, authFailures);
} finally {
  page.off('response', onResponse);      // el listener no sobrevive al step
}
```

La segunda, sondear en vez de esperar un único destino, para poder distinguir los desenlaces:

```typescript
while (Date.now() < deadline) {
  if (isDestination(page.url())) return;                 // llegó

  if (authFailures.length > 0) {                          // el backend falló
    throw new Error(
      `El backend rechazó la autenticación (${authFailures[0]}). ` +
      `La aplicación permanece en ${page.url()}. No es un problema del test ni del navegador.`
    );
  }

  if (!consentAccepted && isConsentStep(page.url())) {     // desenlace legítimo
    consentAccepted = await acceptConsent(page);
  }

  await page.waitForTimeout(POLL_INTERVAL);
}
throw new Error(`No se llegó al destino tras ${timeout}ms. URL actual: ${page.url()}.`);
```

**Sobre el `waitForTimeout` del sondeo**: la política de esperas lo prohíbe como sustituto de una condición (`waits-policy.md`), y esto no lo es. Acá el intervalo es el paso de un bucle que evalúa varias condiciones excluyentes, cosa que ninguna espera nativa de un solo destino puede hacer. Es la excepción, va comentada como tal, y no habilita `waitForTimeout` en ningún otro lugar.

## Los tres mensajes que hay que poder emitir

Un fallo útil nombra la capa responsable. Comparados:

```
page.waitForURL: Timeout 30000ms exceeded.                                    <- inútil
```

```
El backend rechazó la autenticación (500 POST .../sessions/initiate).
La aplicación permanece en .../#/login. No es un problema del test ni del navegador.
```

```
No se llegó al Home tras 60000ms. URL actual: .../#/privacy-policies.
La aplicación quedó en un paso de consentimiento que el flujo no contempla.
```

El segundo caso es además un **blocker de ambiente**, no un fallo de la suite: se reporta con la categoría `environment_auth_fail` de `[[calidad-environment-blocker-evidence]]` y el delivery gate cierra en `partial`, nunca en `success`. Un 500 del backend enmascarado como timeout del test es la forma más cara de perder esa distinción.

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
