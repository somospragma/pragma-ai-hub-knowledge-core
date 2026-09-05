---
id: calidad-test-data-management
version: 1.2.0
scope: chapter
type: skill
chapter: calidad
description: "Estrategia de gestión de datos de prueba: builders, factories, anonimización, seeding, cleanup, datos sintéticos."
tags: [test-data, builders, factory, anonymization, hipaa, ccpa, ley-1581, lgpd, faker, synthetic-data]
---

# Test Data Management — Datos de Prueba Reproducibles y Conformes

## Cuándo aplicar

Aplica este skill **cada vez que se diseñe una suite que requiera datos consistentes, reproducibles y conformes a normativa** — es decir, prácticamente toda suite no trivial.

Es especialmente crítico en clientes regulados de LATAM y Estados Unidos:

| Jurisdicción | Marco principal |
|---|---|
| Estados Unidos | HIPAA (salud), CCPA/CPRA (California), SOX (financiero público), GLBA (financiero), FedRAMP (gobierno) |
| Brasil | LGPD (Lei 13.709) |
| Colombia | Ley 1581 / Decreto 1377 |
| México | LFPDPPP |
| Argentina | Ley 25.326 |
| Chile | Ley 19.628 / Ley 21.719 (2024) |
| Perú | Ley 29.733 |
| Otras LATAM (Centroamérica, Caribe, Uruguay, Bolivia, Ecuador, Paraguay, Venezuela) | Aplicar marco análogo local + estándares internacionales (ISO 27001, SOC 2, PCI-DSS) como mínimo común |

Estos marcos prohíben usar datos productivos en ambientes de prueba sin anonimización. Este skill define la estrategia para evitar esa exposición y al mismo tiempo garantizar **reproducibilidad** (mismo seed → mismo dataset → mismos resultados).

Activa este skill en paralelo con `[[calidad-karate-greenfield]]`, `[[calidad-karate-brownfield]]`, `[[calidad-playwright-greenfield]]`, `[[calidad-k6-greenfield]]` o `[[calidad-appium-screenplay-android]]`. Coordina con `[[calidad-mandatory-inputs-protocol]]` para obtener catálogo de datasets disponibles del cliente.

## Instrucción

0. **Confirmar disponibilidad de datos PRIMERO y respetar la precedencia de fuentes** — La pregunta del `[[calidad-sut-readiness-gate]]` (¿existen datos de prueba o catálogo del cliente?) se hace AL INICIO, no como último recurso. Precedencia estricta:
   1. **Data real / catálogo del cliente** (con anonimización cuando aplique).
   2. **`examples` del spec y valores de la firma** — son parte del contrato; se usan tal cual.
   3. **Sintética determinista** (Faker + seed fijo, pasos 2-4) para todo lo que 1 y 2 no cubran.

   **PROHIBIDO el camino observado en pruebas de campo**: "inventar" datos con criterio del agente cuando el spec no trae examples. Un dato improvisado sin seed no es reproducible entre corridas — rompe el determinismo que es el objetivo de toda esta capacidad. Si falta un dato y ninguna fuente lo provee, se genera con Faker + seed (reproducible) o se pregunta; nunca se improvisa.

   Si NO hay datos (`data_strategy: synthetic`), la ausencia NO detiene la construcción de la suite: si hay mock de servicios (`[[calidad-service-virtualization-mockoon]]`), el mismo seed y locale alimentan sus data buckets para que test y mock sean coherentes end-to-end. El switchover a datos reales es parte del plan de certificación, no un cambio de código.
0.5. **Evaluar SUFICIENCIA, no solo existencia** — Que haya datos no significa que sirvan: los que existen son los que necesitaron las pruebas anteriores. Una vez planificados los escenarios y **antes** de emitir la estrategia, derivar de ellos la matriz de datos requeridos —entidad, **estado que exige**, si existe en el ambiente, quién lo gestiona y para cuándo— y comunicar al QA en el chat, de forma explícita y accionable, lo que falta gestionar. Contra mocks el dato faltante se sintetiza y se declara como sintético; **contra software ya desarrollado es un bloqueo con fecha**, porque conseguirlo puede exigir trámite o intervención de otro equipo. Procedimiento completo, plantilla del mensaje y validación cruzada contra el catálogo en `references/data-sufficiency-gate.md`.
1. **Definir alcance** — ¿el dato es para unit, integration, e2e o performance? La estrategia cambia drásticamente. Matriz en `references/test-data-strategies.md`.
2. **Elegir estrategia** — `synthetic` (generado on-the-fly, default) vs `anonymized prod-like` (snapshot prod pasado por pipeline de anonimización, sólo cuando volumen/realismo lo exija). Anonimización detallada en `references/anonymization-pii.md`.
3. **Diseñar el patrón de construcción** — Object Mother, Test Data Builder o Factory según contexto. Snippets canónicos por lenguaje en `references/builder-factory-objectmother-patterns.md`.
4. **Integrar Faker con seeds deterministas** — Elegir locales según jurisdicción del cliente dentro del alcance del Chapter: `en_US`, `es_CO`, `es_MX`, `es_AR`, `es_CL`, `es_PE`, `pt_BR`, y `es` genérico para Centroamérica + Caribe + otros donde no haya locale dedicado. Seed fijo en CI. Reglas y anti-patrones en `references/synthetic-data-faker.md`.
5. **Seeding y cleanup transaccional** — Por framework: Karate `Setup.feature`, k6 `setup()/teardown()`, Playwright `globalSetup/globalTeardown`, Spring `@Transactional` rollback. Patrones en `references/seeding-cleanup-transactional.md`.
6. **Anonimizar por columna** — Reglas por tipo de dato: cédulas, RUT, teléfono, email, dirección, tarjeta (Luhn-valid pero fake), IBAN. Ver `references/anonymization-pii.md`.
7. **Catalogar datasets versionados** — Naming, almacenamiento (git LFS, DVC, S3 con tags), regeneración cuando cambia el esquema. Estrategia en `references/datasets-versioning.md`. Para perf, consideraciones específicas en `references/data-for-perf-testing.md`.

## Un usuario de pruebas compartido es un recurso con estado, no un dato de configuración

Un alias en un catálogo de usuarios **parece** configuración y se comporta como
un recurso: tiene estado en el sistema bajo prueba, y ese estado cambia cuando un
escenario lo usa.

**Dos escenarios que comparten cuenta no pueden ejecutarse en paralelo.** Y una
precondición que borra o reinicia el estado de la cuenta —desafiliar un token,
limpiar un carrito, revocar una sesión— **deja la cuenta inservible para
cualquier otro escenario mientras dura**.

Caso medido: dos escenarios lanzados en paralelo para ganar tiempo, ambos con el
mismo usuario. La precondición de uno borraba la afiliación del token para volver
a crearla; el otro llegó al paso de desbloqueo justo dentro de esa ventana y
falló por un estado que le fabricó su compañero. Lo caro no fue el rojo: fue que
**parecía un hallazgo sobre la plataforma web** y estuvo a punto de reportarse
como que el flujo web no pedía segundo factor.

**Antes de paralelizar, listar qué recursos con estado comparten los escenarios.**
Si comparten cuenta, paralelizar exige darle a cada corrida la suya. Y esto
alcanza a los runners: un ejecutor multiplataforma que paralelice por defecto
**no es utilizable** para un feature cuyos escenarios comparten la cuenta de
pruebas, por más que sea el recurso recomendado. Verificarlo en
`[[calidad-repo-capability-discovery]]` es parte del barrido, no un detalle.

## La procedencia del dato se escribe dentro del valor

Un dato de prueba tiene dos preguntas: **qué forma tiene** y **de dónde sale**.
La primera la resuelve la estructura del archivo; la segunda **la resuelve el
propio valor**, para que el nombre de la variable y su respaldo queden en la
misma línea y no en un archivo paralelo que hay que mantener sincronizado.

```
"ultimosDigitos":       "${TDC_PRINCIPAL:-6267}"
"ultimosDigitos.local": "0000"
```

| Forma | Qué hace |
|---|---|
| `${VARIABLE}` | Solo la variable. Sin ella, falla **nombrándola** |
| `${VARIABLE:-respaldo}` | La variable si viene; si no, el respaldo del repositorio |
| valor literal | Siempre ese valor |
| `<campo>.local` | Solo en el perfil simulado |

Con esto, **que la canalización pise el valor del repositorio sale gratis**: la
variable se busca en el entorno del proceso, que ya trae aplicada la precedencia
de `[[calidad-execution-profile-and-config-provenance]]`, sin una línea de código
para ello.

### El respaldo simulado es una clave aparte, nunca el respaldo del `:-`

Es la decisión menos obvia y la que más protege. Sería más compacto escribir
`${TDC:-0000}` y que el valor sintético hiciera de respaldo — pero entonces **un
perfil real al que le falte la variable usaría el dato sintético contra el
ambiente real, en verde y sin avisar a nadie**.

Al ser claves separadas, la resolución es **asimétrica a propósito**:

- En el perfil simulado, si hay `.local` se usa y **no se mira el entorno**: el
  sintético no puede viajar.
- En los perfiles reales, las claves `.local` **no existen**: el dato real no se
  contamina.

Las dos mitades merecen comprobación propia, porque su fallo es silencioso — ver
el criterio en `[[calidad-execution-profile-and-config-provenance]]`.

### Un secreto no admite respaldo en el repositorio

Todo dato admite respaldo salvo uno. Una contraseña real como respaldo es una
**credencial versionada**: filtrada en cuanto alguien clone, y rotarla pasa a ser
un cambio de código.

```
"clave":       "${BANCA_PASSWORD}"    ← real: el nombre, sin respaldo
"clave.local": "Demo1234"             ← simulado: literal, porque es falso
```

Y esto se hace cumplir, no se pide: el gate rechaza un literal o un respaldo
`:-` en cualquier campo cuyo nombre termine en `clave`, `password`, `secret`,
`token`, `pin` o `apikey`, **salvo en su clave `.local`**. Bloquea solo el caso
peligroso.

> Detalle que decide si la regla sirve: la comparación va **con límites de
> palabra**. Sin eso, un dato como `6267` salta dentro de `162679` y la regla se
> vuelve ruido que alguien acaba desactivando.

### Un sujeto, un archivo

Cuando el dato de un usuario está repartido en tres archivos —su alias en uno,
sus productos reales en otro, los sintéticos en un tercero— pasan tres cosas, y
ninguna es de estilo: nada ata el producto a su dueño, los datos de negocio no
admiten venir del ambiente, y los dos archivos hermanos hay que mantenerlos en
paralelo estando idénticos en la mitad de sus campos.

**Un archivo por sujeto, con todo lo suyo dentro.** Añadir un usuario es copiar
un archivo. Los productos anidan como anidan en el negocio, a la profundidad que
haga falta.

Y los campos **se descubren del archivo, no se declaran en el código**: añadir un
campo hace que exista tipado, que la verificación de ambiente empiece a pedir su
variable —marcándola opcional si trae respaldo— y que el gate lo vigile dentro
de los escenarios, sin tocar una línea de código. Un campo mal escrito falla al
compilar, no en ejecución.

### La limpieza por hooks cubre los finales, no las interrupciones

Los hooks de limpieza corren cuando el escenario **termina**, bien o mal. No
corren cuando el proceso **muere**: una cancelación manual, un `SIGKILL` del
runner, una sesión remota cerrada por inactividad o un timeout del orquestador
dejan el recurso compartido exactamente como lo dejó el escenario a mitad.

Y las interrupciones no son excepcionales. Caso medido: se abortó una corrida en
vuelo a petición del usuario, y la cuenta quedó con el acceso bloqueado por
intentos fallidos acumulados. **El daño es diferido y silencioso: no lo paga
quien interrumpe, lo paga el siguiente que use la cuenta**, sin ninguna pista de
por qué. Lo reportó un compañero dos días después.

Dos obligaciones que se derivan:

- **Toda suite con estado compartido lleva un comando de restauración explícito**
  —un `restore` de un solo paso— que devuelva el recurso a su punto de partida
  sin depender de que alguien recuerde cómo se hace ni tenga que escribir un
  script suelto. Se documenta junto al catálogo de usuarios.
- **Interrumpir una corrida obliga a restaurar a mano.** No es opcional ni se
  deja para después: el estado compartido no tiene dueño.

### Una limpieza que sólo comprueba que la llamada se hizo no es una limpieza

Verificar que la petición se procesó —un código de estado correcto— no verifica
que el estado quedó como debía. Caso medido: el endpoint de desbloqueo responde
`200` con un campo en el cuerpo que indica si de verdad desbloqueó; un `200` con
ese campo en falso habría pasado en silencio y la cuenta habría seguido
bloqueada.

**La limpieza comprueba el efecto, no la llamada.** Y si el efecto no se puede
observar, eso es un hallazgo que se reporta, no algo que se supone.

## Restricciones

- **NUNCA** paralelizar escenarios que comparten un usuario de pruebas, ni asumir que un runner no paraleliza porque el escenario "parece corto".
- **NUNCA** usar datos productivos sin anonimización en ningún ambiente que no sea producción. Es una violación legal en LATAM y Estados Unidos bajo los marcos listados arriba y un riesgo reputacional grave.
- **NUNCA** commitear datasets que contengan PII real, ni siquiera "para que sea más fácil reproducir un bug". Si un dataset llegó a la rama, debe purgarse del historial (`git filter-repo`) y se debe notificar al cliente.
- **SIEMPRE** documentar la política de retención de los datasets sintéticos/anonimizados: por defecto se rotan cada release.
- **SIEMPRE** usar seed fijo en CI (`FAKER_SEED=12345`) para garantizar reproducibilidad. Local puede usar seed aleatorio sólo si se loguea el seed usado para poder reproducir.
- **NUNCA** mezclar cleanup transaccional con cleanup por API admin en la misma suite sin documentarlo: confunde la traza.
- **NUNCA** escribir la limpieza como un step del escenario. Un step posterior sólo corre si todos los anteriores pasaron, así que corre justo cuando no hace falta y se salta cuando sí. Va en el hook de ciclo de vida — ver `[[calidad-cucumber-bdd-conventions]]`.
- **NUNCA** dar una limpieza por hecha porque la llamada devolvió un código de éxito.
- **NUNCA** abandonar una corrida interrumpida sin restaurar el recurso compartido, ni cerrar la sesión sin decirlo.
- **NUNCA** uses el respaldo del `:-` para el dato sintético: un perfil real sin la variable lo usaría contra el ambiente real, en verde.
- **NUNCA** pongas un secreto real como respaldo en el repositorio. Es una credencial versionada.
- **NUNCA** repartas el dato de un sujeto entre archivos hermanos que hay que mantener en paralelo.
- Cuando varios escenarios compartan sesión además del dato, el contrato de reuso y reset es `[[calidad-session-reuse-and-isolation]]`: compartir sin verificar el reset produce fallos dependientes del orden, donde **el escenario que falla no es el que causó el problema**.
- Encadena con `[[calidad-test-evidence-and-traceability]]` para que el `seed`, el ID del dataset y la versión queden registrados en cada reporte.
- Sigue `[[calidad-mandatory-inputs-protocol]]` para confirmar al inicio: ¿hay catálogo de datasets del cliente? ¿qué framework de anonimización usa? ¿qué políticas de retención aplican?
- Con `data_strategy: synthetic` + mock de servicios: las aserciones de los tests validan contrato y reglas de negocio (formato, presencia, eco del request), NUNCA valores literales que solo existen en el dataset sintético del mock — de lo contrario el switchover a datos reales rompe la suite.
- Si el cliente requiere snapshot prod-like, exige el dataset anonimizado por el equipo de datos del cliente; **no** anonimices tú dumps productivos.

## Cross-links

- `references/test-data-strategies.md`
- `references/builder-factory-objectmother-patterns.md`
- `references/anonymization-pii.md`
- `references/synthetic-data-faker.md`
- `references/seeding-cleanup-transactional.md`
- `references/datasets-versioning.md`
- `references/data-for-perf-testing.md`
