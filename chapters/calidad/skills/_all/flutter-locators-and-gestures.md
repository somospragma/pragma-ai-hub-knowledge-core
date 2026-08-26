---
id: calidad-flutter-locators-and-gestures
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
applies_to_stacks: [playwright, appium-core, appium-wdio, appium-serenity]
description: "Automatizar aplicaciones Flutter en móvil y en web: qué ve realmente el driver, por qué la identidad de un elemento cambia con su estado, gestos por W3C Actions, tecleo con foco previo, renderizado perezoso y recorte de coordenadas. Consultar ANTES de escribir el primer locator o gesto sobre una app Flutter."
tags: [flutter, locators, gestos, accesibilidad, mobile, web, appium, playwright, mandatory]
enforcement: mandatory
---

# Flutter — Localización y Gestos en Móvil y Web

## Cuándo aplicar

Antes de escribir el primer locator o el primer gesto contra una aplicación
Flutter, en cualquier plataforma. También cuando una suite existente sobre
Flutter presente alguno de los síntomas de la tabla de diagnóstico: casi todos
se leen como otra cosa.

Cómo saber que la aplicación es Flutter sin preguntar: el árbol expone muy pocos
nodos para lo que se ve en pantalla, los identificadores son etiquetas de
accesibilidad en vez de controles, y en web hay un `canvas` que ocupa el viewport.

## Instrucción

Flutter dibuja sobre una superficie propia y **no expone una jerarquía nativa
real**. Lo que ve el driver son nodos del **árbol de accesibilidad**, no
controles. Eso invalida buena parte de lo que funciona en aplicaciones nativas, y
el modo en que falla es engañoso: **el comando no da error, simplemente no pasa
nada**.

Dos consecuencias gobiernan todo lo demás:

1. **El árbol se reconstruye según el estado.** Un selector se ancla a lo que
   existe **en reposo** —la rejilla, la etiqueta numerada, el contenedor—, nunca
   a lo que aparece por foco, por hover o por respuesta del servidor.
2. **Lo que ves no es lo que escucha.** Muchos controles exponen un nodo de
   accesibilidad que es un **proxy**: el elemento que realmente recibe la
   entrada es otro, anidado, y sin etiqueta útil.

### 1. La identidad de un elemento cambia con su estado

| Estado | Qué pasa con el árbol |
|---|---|
| En reposo | Las casillas tienen su nombre estable: `Digit 1`…`Digit 8` |
| Con foco | En iOS el campo activo se llama `_` y **solo existe mientras hay foco** |
| Tras un rechazo del servidor | El árbol se reconstruye: el campo enfocado desaparece y las casillas recuperan su nombre en reposo |

De aquí salen dos errores caros y opuestos:

- **Usar el campo enfocado como selector para *dar* el foco** es pedirle al
  escenario que empiece por donde termina. En los dispositivos donde no estaba,
  el step muere sin teclear nada.
- **Comprobar "el modal sigue disponible" apoyándose en el campo enfocado** falla
  con el modal perfectamente utilizable, porque el rechazo se llevó el foco.

### 2. Tocar el campo antes de escribir

El campo de texto que expone la capa nativa es un proxy: Flutter solo crea el
campo real cuando recibe el foco. Escribir sobre el proxy deja el valor en la
vista nativa y **Flutter nunca se entera**. En web, un `fill()` sobre el
contenedor no sirve: hay que teclear en el elemento editable anidado.

El síntoma es especialmente caro porque no falla nada de inmediato: el campo se
ve lleno, el botón de envío sigue deshabilitado, no sale ninguna llamada de red,
y la aserción que se rompe está mucho más adelante.

```
tocar el campo → localizar el elemento con foco → limpiar → escribir
```

Y **esperar a que el botón de envío se habilite** antes de pulsarlo: es la
comprobación de que el texto llegó al motor y no solo a la vista.

> Si un campo "no acepta lo que se escribe", sospecha de un proxy de
> accesibilidad **antes** que del método de escritura: mira el árbol y busca un
> elemento editable anidado.

### 3. Todo gesto sobre la superficie, por W3C Actions

| No usar | Por qué falla | Usar |
|---|---|---|
| Scroll del framework nativo Android | Necesita un contenedor nativo marcado como desplazable; Flutter no lo expone | Swipe por W3C Actions |
| Scroll del framework nativo iOS | Necesita referencia de elemento en la jerarquía nativa; sobre nodos Flutter es errático | Swipe por W3C Actions |
| Gesto de scroll por rectángulo | Pide un rectángulo en píxeles: ya admite que no hay elemento al que agarrarse | Swipe por W3C Actions |
| Click del elemento | Apunta al centro del nodo semántico, que puede no coincidir con el área que responde | Toque por coordenadas |

Incluir una **pausa breve entre el `pointerDown` y el movimiento** —del orden de
100 ms—: sin ella Flutter interpreta el gesto como un lanzamiento y desplaza una
distancia impredecible, lo que hace la prueba irrepetible.

Lo que **sí** sigue siendo específico de plataforma es lo que Flutter no dibuja:
el teclado del sistema, los diálogos de permisos y el borrado de campos. Esa es
la línea entre lo compartido y lo divergente — ver
`[[calidad-cross-platform-learning-propagation]]`.

### 4. Recortar las coordenadas contra la ventana

Flutter reporta límites que se salen de la pantalla. Medido: un botón con altura
hasta `y=2070` en una pantalla de 2064 píxeles. El centro geométrico cae en la
barra de gestos del sistema, que se traga el toque — **el gesto "funciona" y la
pantalla no cambia**.

Calcular el centro sobre la **intersección** del elemento con el viewport, con
margen para las barras de estado y de gestos.

### 5. El renderizado es perezoso

Flutter **no construye** los widgets de una lista hasta que están cerca del
viewport: un elemento más abajo **no existe en el árbol**.

Por eso **no sirve** esperar a que exista y desplazarse después: la espera nunca
se cumple. Hay que **desplazar y sondear a la vez**, concediendo una espera corta
en cada intento para que Flutter construya lo que acaba de entrar.

Este es el que más despista, porque el mensaje natural —"no se encontró el
elemento"— sugiere un selector equivocado cuando el selector es correcto.

### 6. El volcado nativo no es lo que ve el driver

El volcado de jerarquía del sistema operativo **no coincide** con la fuente de
página del driver: la capa de automatización sintetiza atributos que el volcado
no muestra. Escribir locators mirando el volcado nativo produce selectores que
parecen correctos y no encuentran nada.

**Ten siempre una herramienta que vuelque la pantalla según el driver**, no según
el sistema. En iOS hay que normalizar además el tipo de elemento: Android lo pone
en el atributo de clase y el driver de Apple usa el nombre de la etiqueta XML.

## Tabla de diagnóstico

Cada síntoma se lee de forma natural como otra cosa. Esta columna es la que
ahorra corridas.

| Síntoma | Se lee como | Suele ser |
|---|---|---|
| El campo se ve lleno y el botón sigue deshabilitado | Validación del formulario | Se escribió en el proxy, no en el campo real |
| "Elemento no encontrado" con selector correcto | Locator roto | Renderizado perezoso: aún no existe |
| El gesto se ejecuta y la pantalla no cambia | Gesto mal calculado | El toque cayó fuera del viewport |
| Timeout de treinta segundos sin mencionar el selector | Ambiente lento | `:has-text()` casó un ancestro con `pointer-events: none` |
| El elemento existía y ahora no | Regresión de la app | El árbol se reconstruyó tras una respuesta del servidor |
| Pasa en un dispositivo y falla en otro | Dispositivo defectuoso | Ancla transitoria; ver `[[calidad-data-volatility-and-assertion-anchoring]]` |

## Lo que nunca debes hacer

- **Nunca esperes `visible`** sobre un nodo semántico de Flutter en web: suelen
  tener tamaño cero o quedar tapados por el canvas, y el navegador los considera
  invisibles aunque el control se vea. La espera agota el timeout sobre elementos
  que están ahí.
- **Nunca uses `:has-text()` donde quieras `:text-is()`** en web: el primero casa
  también contenedores ancestros con `pointer-events: none`, y el síntoma es un
  timeout largo que **no menciona el selector**.
- **Nunca te fíes de que las coordenadas del elemento estén dentro de la
  pantalla.** El driver devuelve valores válidos aunque el elemento esté fuera
  del viewport, y el toque cae al vacío sin lanzar error.
- **Nunca ancles un selector a lo que aparece por foco, por hover o por respuesta
  del servidor.** Solo lo que existe en reposo sirve de ancla.
- **Nunca acoples un selector a la descripción de un dato.** Un selector que
  busca el texto de una fila funciona solo mientras la cuenta de prueba tenga esa
  descripción; con datos reales aparece otro texto. El rasgo estable de una fila
  es su estructura o su importe, no su contenido.

## Cross-links

- `[[calidad-mobile-locator-resolution]]` — resolución de locators en móvil; este
  skill cubre lo específico de Flutter y aquel lo general.
- `[[calidad-data-volatility-and-assertion-anchoring]]` — qué texto sirve de
  ancla y qué anclas desaparecen solas.
- `[[calidad-ui-locator-map-contract]]` — cuándo un elemento sin ancla estable es
  un hallazgo de instrumentación y se pide identificador al equipo de desarrollo.
