# Diálogos del sistema operativo y contaminación entre escenarios

## El fallo que no se parece a su causa

Un escenario descarga un archivo. El sistema operativo abre el selector de aplicación ("Abrir con…", con la lista de aplicaciones capaces de abrirlo). El escenario termina, el diálogo **queda encima de la aplicación**, y el escenario siguiente arranca tapado: su primer elemento no aparece y el error habla de un selector que no encuentra nada.

El síntoma apunta al test siguiente. La causa está en el anterior. Sin mirar las capturas —que muestran el escritorio del sistema con un diálogo encima, no la aplicación— el diagnóstico se va a los selectores y no vuelve.

Familia completa de diálogos que producen esto: selector de aplicación tras abrir o descargar un archivo, hoja de compartir, instalador de paquetes, permisos pedidos a mitad de flujo, avisos de la tienda de aplicaciones, y cualquier actividad de otra aplicación lanzada por un enlace.

## Defensa en el cierre: mientras el foco no sea la aplicación, retroceder

Barata, genérica y no depende de qué diálogo apareció:

```typescript
/**
 * Cierra con BACK cualquier diálogo del sistema que haya quedado sobre la app
 * (selector "Abrir con" tras una descarga, hoja de compartir, instalador de
 * paquetes). Mientras el paquete en foco no sea el de la app, sigue retrocediendo.
 */
async function dismissSystemDialogs(world: HookWorld, maxIntentos = 3): Promise<void> {
  for (let intento = 0; intento < maxIntentos; intento++) {
    let paqueteEnFoco = '';
    try {
      paqueteEnFoco = await world.driver.getCurrentPackage();
    } catch {
      return;                                   // sesión ya cerrada: nada que limpiar
    }
    if (!paqueteEnFoco || paqueteEnFoco === appPackage) return;
    try {
      await world.driver.back();
      await world.driver.pause(500);
    } catch {
      return;
    }
  }
}
```

Detalles que no son adorno:

- **El tope de intentos es obligatorio.** Sin él, una pantalla que no responde a retroceder deja el cierre en bucle.
- **Se compara el paquete en foco, no el aspecto de la pantalla.** Es el único dato fiable sobre quién está adelante.
- **Los fallos se tragan y se retorna.** Esto corre en el cierre: si la sesión ya murió, insistir convierte un escenario fallido en un cierre fallido y se pierde la evidencia del fallo real.

Medido en campo sobre el escenario que quedaba tapado: de 3 escenarios con 2 fallidos y 13 steps ejecutados, a 3 escenarios en verde con 39 steps.

## Lo anterior mitiga; la regla de fondo es que el escenario cierra lo que abre

El retroceso defensivo es una red, no la solución. **El escenario que provoca el diálogo es el que debe cerrarlo**, dentro de su propio alcance, porque es el único que sabe qué abrió y cuándo. Dejarlo para el cierre general significa que entre medias el escenario siguiente ya arrancó contaminado en cualquier corrida donde el orden cambie.

Dos cosas que **no** son solución, aunque lo parezcan:

- **Dejar una sola aplicación instalada** capaz de abrir ese tipo de archivo, para que el selector no aparezca. No viaja con el repositorio, se pierde al reinstalar el dispositivo, no aplica al pipeline y esconde el problema en vez de resolverlo. Es configuración de una máquina disfrazada de arreglo.
- **Deshabilitar aplicaciones por línea de comandos** en el arranque de la suite. Es lo mismo con más pasos, y deja el dispositivo en un estado que nadie recuerda haber cambiado.

## Verificar el efecto de un archivo descargado

Cuando el escenario descarga algo, la tentación es verificarlo en disco. En Android moderno el archivo suele generarse en el almacenamiento **privado** de la aplicación y compartirse por un proveedor de contenido, así que no aparece en las carpetas públicas y el almacenamiento privado no es accesible salvo que la aplicación sea depurable.

```bash
adb shell ls /sdcard/Download                    # solo lo público
adb shell run-as <paquete> ls files              # falla si la app no es depurable
```

Consecuencia práctica: **la aserción se hace sobre lo que la aplicación expone**, no sobre el sistema de archivos — que el diálogo de compartir aparezca con el nombre esperado, que la pantalla confirme la descarga, que el registro quede listado. Afirmar "el archivo se descargó" sin poder verlo es una aserción que no verifica nada, y cae en la regla de aserciones contractuales de `contractual-assertions.md`.

## Cross-links

- `mobile-interactions-catalog.md` — pantallas condicionales y estado entre escenarios.
- `contractual-assertions.md` — por qué "apareció algo" no es una aserción.
- `[[calidad-step-isolation-pattern]]` — cuando el paso que falta es de setup y lo comparten N escenarios, se arregla en el punto común.
- `[[calidad-test-evidence-and-traceability]]` — las capturas del reporte son las que revelan este fallo.
