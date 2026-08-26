---
id: calidad-platform-parameterised-steps
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
applies_to_stacks: [playwright, appium-core, appium-wdio, appium-serenity]
description: "Una sola implementación de steps para varias plataformas conservando un escenario por sistema operativo en el .feature, que es lo que el ALM exige: la plataforma como parámetro, locators declarados por familia, capa de gestos y la guarda contra el fallo silencioso que esto habilita."
tags: [multiplataforma, steps, gherkin, locators, gestos, duplicacion]
---

# Steps Unificados por Parámetro de Plataforma

## Cuándo aplicar

Al diseñar o extender un arquetipo que cubre varias plataformas con la misma
suite: web y móvil, Android e iOS, teléfono y tablet.

Señal de que hace falta: el mismo step implementado varias veces con el cuerpo
casi idéntico. Un caso medido: **331 archivos de steps para unos 450 casos de
negocio**, con el mismo step implementado hasta cinco veces.

## Instrucción

El costo no es la duplicación inicial. Es que **un arreglo hay que hacerlo cuatro
veces, y cuando se hacen tres, la cuarta queda con otro comportamiento que nadie
nota hasta que falla** — semanas después y en otro escenario. Ver
`[[calidad-cross-platform-learning-propagation]]`.

La restricción que **no** se puede quitar es que el ALM necesita un caso de
prueba por sistema operativo, así que el `.feature` sí debe llevar un escenario
por plataforma. Se separa entonces lo que el ALM obliga a duplicar —el
escenario— de lo que no hay ninguna razón para duplicar —la implementación.

### 1. La plataforma es un parámetro del step, no parte de su texto

Dos escenarios, dos claves de ALM, **una implementación**:

```gherkin
@NT-1 @android
  When accede a la aplicación en Android
@NT-2 @ios
  When accede a la aplicación en iOS
```

El step se registra una vez, con la plataforma como parámetro tipado.

### 2. Los locators se declaran juntos, por familia

Con archivos separados por plataforma **la deriva es invisible**: si alguien
agrega un elemento a una familia y olvida la otra, nada lo detecta hasta que un
escenario falla mucho después. Declarándolos juntos:

- la ausencia se ve al abrir el archivo;
- el resolver la convierte en un error que **nombra el elemento, la familia y el
  archivo**, en vez de un "no encontrado" genérico.

Las variantes de tamaño resuelven por su familia base: es la misma aplicación,
solo cambia la pantalla.

### 3. Las diferencias de interacción viven en una capa de gestos

Un contrato con una implementación por familia. El caso canónico: ocultar el
teclado funciona en el driver de Android y en el de Apple falla o no hace nada.
Esa divergencia va **en la capa de gestos**, no repartida por los steps.

### 4. El Screen Object nunca pregunta en qué plataforma está

Para divergencias reales de **flujo** —una pantalla que solo existe en una
plataforma— usa un helper explícito que deje la divergencia **declarada y
localizada**, en vez de dispersa en condicionales.

Si la divergencia aparece en muchos sitios, la pregunta correcta no es cómo
organizarla: es **si los escenarios de ambas plataformas deberían ser el mismo**.

## El fallo silencioso que esto habilita, y cómo se cierra

Si un escenario lleva el tag de una plataforma pero su step dice otra, **el step
se ejecuta contra la plataforma del tag y pasa**: el parámetro describe, no
dirige. Queda un caso verde en el ALM que certifica la redacción equivocada — un
verde que no distingue entre lo correcto y lo incorrecto.

Se cierra por dos vías, a propósito redundantes:

1. **En ejecución**: comparar la etiqueta escrita en el step con la plataforma
   real de la sesión y fallar con un mensaje explícito.
2. **En CI**: una regla del gate que lo detecte **antes** de ejecutar nada.

La redundancia no sobra: la primera protege las corridas locales, la segunda
impide que el error llegue a la rama.

## Restricciones

- **NUNCA elimines el escenario por plataforma del `.feature`** para "quitar
  duplicación": es lo que el ALM exige para tener un caso por sistema operativo.
- **NUNCA repartas por los steps una diferencia de interacción** que corresponde
  a la capa de gestos.
- **NUNCA dejes la plataforma como texto libre dentro de la frase del step.**
- **NUNCA entregues steps parametrizados sin la guarda de coincidencia** entre la
  etiqueta escrita y la plataforma real: sin ella el parámetro es decorativo.

## Cross-links

- `[[calidad-cucumber-bdd-conventions]]` — sufijo de plataforma y ambigüedad de steps.
- `[[calidad-cross-platform-learning-propagation]]` — arreglar una vez, aplicar en todas.
- `[[calidad-flutter-locators-and-gestures]]` — qué es realmente compartido y qué no,
  cuando la aplicación es Flutter.
