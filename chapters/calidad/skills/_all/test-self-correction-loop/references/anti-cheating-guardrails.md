# Anti-Cheating Guardrails

Archivo de referencia más crítico del chapter. Reglas duras que el agente debe verificar **antes** de aplicar cualquier corrección. Si cualquier regla activa una violación, el cambio se bloquea y el flujo va a `ESCALATED`.

Cada regla incluye:

1. **Enunciado** — la prohibición.
2. **Por qué** — daño concreto si se viola.
3. **Detección** — heurística automática sobre el diff.
4. **Acción** — qué hacer cuando se detecta.

> Convención: las heurísticas asumen acceso al diff candidato vs el estado del workspace previo a `FIXING`, más el contexto del test (tags, framework, archivos relacionados).

---

## Regla 1 — NO modificar assertion que verifica contrato o comportamiento de negocio

- **Por qué**: si la assertion falla, el SUT no cumple el contrato → es bug. Modificarla equivale a borrar la prueba.
- **Detección**: el diff toca líneas que contienen `expect(`, `Then `, `assertThat`, `check(`, `match `, `assert ` y modifica el valor esperado o el matcher.
- **Acción**: bloquear. Reclasificar el fallo vía `[[calidad-failure-triage-and-classification]]` como candidato a bug del SUT.

**Ejemplo antipatrón (Playwright TS):**
```ts
// antes
await expect(page.getByRole('heading')).toHaveText('Welcome, Alice');
// "corrección" prohibida
await expect(page.getByRole('heading')).toHaveText(/Welcome|Bienvenido/i);
```

---

## Regla 2 — NO cambiar valores esperados sin evidencia documentada del cambio legítimo del SUT

- **Por qué**: cambiar el "valor esperado" para que matchee con el actual es el antipatrón clásico. Solo es válido si hay release notes, PR o spec que documente el cambio.
- **Detección**: literal/constante esperada cambia en el diff y el agente no adjunta link a release notes / PR / spec actualizada en el audit log.
- **Acción**: bloquear hasta que la evidencia documental esté adjunta y sea verificable.

**Ejemplo antipatrón (Karate):**
```gherkin
# antes
And match response.status == 'CONFIRMED'
# "corrección" sin evidencia
And match response.status == 'PENDING'
```

---

## Regla 3 — NO aflojar matchers (de estricto a permisivo) sin justificación

- **Por qué**: aflojar `equals` a `contains`, `#string` a `##string`, `>=95%` a `>=80%` esconde regresiones.
- **Detección**: comparación de operadores antes/después en la línea modificada. Lista negra: `toBe`→`toContain`, `equals`→`contains`, `#string`→`##string`, `is`→`matches`, thresholds K6 con número menor que el original.
- **Acción**: bloquear. Si el comportamiento del SUT cambió legítimamente, la justificación debe documentarlo y ser revisada por humano.

**Ejemplo antipatrón (K6):**
```js
// antes
thresholds: { http_req_duration: ['p(95)<500'] }
// "corrección" prohibida
thresholds: { http_req_duration: ['p(95)<2000'] }
```

---

## Regla 4 — NO eliminar checks que detectan condiciones de error

- **Por qué**: borrar la verificación de `status === 200`, de un error message esperado, o de una validación de schema, oculta fallos del SUT.
- **Detección**: el diff elimina líneas que contienen `status`, `statusCode`, `errorCode`, `schema`, `validate`, `check(`, sin reemplazo equivalente.
- **Acción**: bloquear. Restaurar líneas eliminadas.

**Ejemplo antipatrón (Karate):**
```gherkin
# antes
Then status 201
And match response == schema
# "corrección" prohibida
# (líneas borradas)
```

---

## Regla 5 — NO añadir try/catch (o equivalente) que silencia el error

- **Por qué**: capturar la excepción y continuar oculta el fallo real. El test pasa pero el SUT estaba roto.
- **Detección**: el diff introduce `try { ... } catch`, `.catch(() => {})`, `expect.soft`, `softAssertions`, `try:` (Karate) que envuelve la operación que fallaba, sin re-lanzar ni registrar.
- **Acción**: bloquear.

**Ejemplo antipatrón (Playwright TS):**
```ts
// "corrección" prohibida
try {
  await page.getByRole('button', { name: 'Pay' }).click();
} catch { /* swallow */ }
```

---

## Regla 6 — NO incrementar timeouts sin medición real

- **Por qué**: subir el timeout es válido **solo** si se midió que el SUT genuinamente necesita más tiempo. Si no, oculta degradación de performance.
- **Detección**: el diff incrementa un timeout literal (`timeout: N` con N mayor que antes, `await page.waitFor(... , { timeout: N })`, `setTimeout(N)`, `setupTimeout` en K6). El audit log debe incluir métrica real del p95/p99 observado.
- **Acción**: bloquear si no hay medición adjunta. Si la hay, permitir hasta un cap razonable (default 2x el timeout original); más allá del cap → escalation obligada.

**Ejemplo antipatrón (Appium Java):**
```java
// antes
new WebDriverWait(driver, Duration.ofSeconds(10)).until(...);
// "corrección" sin medición
new WebDriverWait(driver, Duration.ofSeconds(120)).until(...);
```

---

## Regla 7 — NO cambiar el comportamiento del fixture para evitar setup legítimo

- **Por qué**: si el fixture deja de crear el usuario, deja de loguear, deja de sembrar datos, el test corre en un estado inválido y "pasa" por casualidad.
- **Detección**: el diff modifica archivos en `fixtures/`, `setup/`, `beforeAll`, `beforeEach`, `Background:` y elimina o degrada operaciones (DELETE, POST a /setup, login).
- **Acción**: bloquear. Solo se permite refactor que preserva semánticamente las mismas operaciones.

---

## Regla 8 — NO añadir `skip` ni `xfail` sin ticket de resolución con SLA

- **Por qué**: silenciar el test sin compromiso de arreglo lo convierte en deuda invisible.
- **Detección**: el diff introduce `test.skip`, `it.skip`, `@Ignore`, `@Disabled`, `Scenario:` precedido por `@ignore`, `test.fixme`, `xtest`, `@quarantine` sin link a ticket.
- **Acción**: bloquear hasta que el audit log incluya `ticket_id` con SLA explícito. El quarantine se rige por `references/quarantine-pattern.md` del skill `[[calidad-failure-triage-and-classification]]`.

---

## Regla 9 — NO modificar tests etiquetados `@security`, `@contract`, `@compliance`, `@regulatory`

- **Por qué**: esos suites deben fallar deterministícamente. Si fallan, **siempre** es bug. Cualquier modificación es violación regulatoria.
- **Detección**: el archivo modificado o el bloque modificado contiene cualquiera de los tags listados (escaneo regex sobre el archivo completo).
- **Acción**: bloquear absolutamente. Sin excepciones. Escalation report con flag `regulatory_violation_attempt`.

---

## Regla 10 — NO cambiar test data para simplificar el camino y evitar validación del SUT

- **Por qué**: enviar payload reducido o "happy" para esquivar validaciones que el SUT debería pasar oculta bugs de validación.
- **Detección**: el diff sobre fixtures/payloads elimina campos opcionales-pero-realistas, baja el tamaño de listas, elimina caracteres especiales, reduce edge cases. Cruzar con `[[calidad-test-data-management]]` para detectar regresión de cobertura.
- **Acción**: bloquear.

**Ejemplo antipatrón (Karate):**
```gherkin
# antes (payload con caracteres unicode/edge case)
* def body = { name: 'María Ñoño 🇨🇴', age: 30 }
# "corrección" prohibida
* def body = { name: 'Maria', age: 30 }
```

---

## Regla 11 — NO bypass de autenticación, autorización o validación en el test

- **Por qué**: saltarse el login, mockear el token, deshabilitar OAuth para que el test pase es alteración del SUT.
- **Detección**: el diff introduce `--insecure`, `--no-verify`, `process.env.SKIP_AUTH`, mocks de auth en tests de integración, headers de admin falsificados, downgrade de scope.
- **Acción**: bloquear.

---

## Regla 12 — NO modificar el comando de ejecución para excluir tests problemáticos

- **Por qué**: filtrar con `--grep '@happy'`, eliminar tags de suite, recortar el conjunto de specs ejecutado es esconder fallos.
- **Detección**: el diff toca `package.json` scripts, `pom.xml` plugins, `playwright.config.ts` projects, `karate-config.js` tags, `Makefile`, GitHub Actions workflows, y reduce el alcance de los tests que se ejecutan.
- **Acción**: bloquear.

---

## Regla 13 — NO mover tests fallidos a `@quarantine` sin pasar primero por triage completo

- **Por qué**: quarantine es para flaky con SLA de resolución, no para deterministic bugs. Mover sin triage convierte el quarantine en cementerio.
- **Detección**: el diff añade tag `@quarantine` y no existe entrada de triage previa con clasificación `flaky`.
- **Acción**: bloquear hasta que el triage esté adjunto y la clasificación sea `flaky` (no `deterministic`).

---

## Regla 14 — NO modificar `package.json`, `pom.xml`, `build.gradle` para downgrade de framework

- **Por qué**: bajar Playwright/Karate/K6/Appium a una versión donde los tests obsoletos pasan oculta deuda real y compromete seguridad.
- **Detección**: el diff sobre archivos de build/dependencies degrada una versión semver de cualquier framework del chapter o sus drivers.
- **Acción**: bloquear absolutamente.

---

## Regla 15 — NO eliminar tests para "limpiar" el suite

- **Por qué**: borrar el test que falla es la forma extrema del antipatrón.
- **Detección**: el diff elimina archivos `*.feature`, `*.spec.ts`, `*.test.ts`, `tests/*.js`, `*Test.java`, `*Steps.java` que existían antes del loop.
- **Acción**: bloquear. Salvo que exista justificación explícita del humano (no del agente) en el audit log.

---

## Detección de violaciones — heurísticas que el agente debe correr sobre su propio diff

Antes de transicionar `DIAGNOSING → FIXING`, el agente ejecuta este pipeline de checks sobre el diff candidato:

```
1. parsear diff por archivo y por hunk.
2. para cada hunk:
   2.1 detectar tags del archivo (regex @security|@contract|@compliance|@regulatory).
       si tags presentes → activar Regla 9 → bloquear → ESCALATED.
   2.2 detectar tipo de archivo:
       - test file (.spec.ts, .feature, .test.ts, *Test.java, tests/*.js)
       - fixture/setup (fixtures/, setup/, beforeAll, beforeEach, Background)
       - build/deps (package.json, pom.xml, build.gradle, *.config.*)
   2.3 ejecutar reglas aplicables según tipo:
       - test file → reglas 1, 2, 3, 4, 5, 6, 8, 10, 11, 13, 15
       - fixture → regla 7, 10, 11
       - build/deps → reglas 12, 14
3. si CUALQUIER regla activa violación:
   3.1 abortar transición a FIXING.
   3.2 generar entrada en audit log con `outcome: blocked_by_guardrail`,
       campo `violated_rules: [...]`.
   3.3 transicionar a ESCALATED con escalation report
       (ver iteration-limits-and-escalation.md).
4. si TODAS pasan:
   4.1 registrar `guardrails_checked: [...]`, `guardrails_passed: true` en el audit log.
   4.2 permitir transición a FIXING.
```

Las heurísticas son **conservadoras por diseño**: en caso de duda, bloquear y escalar. Un falso positivo significa pedir revisión humana; un falso negativo significa esconder un bug y romper el contrato del chapter.
