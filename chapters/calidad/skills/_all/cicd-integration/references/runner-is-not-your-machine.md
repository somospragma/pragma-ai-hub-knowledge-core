# El runner no es tu máquina

Una suite que pasa en local y falla en el pipeline casi nunca falla "porque el pipeline está mal configurado". Falla porque el runner es un entorno distinto en tres dimensiones concretas, y ninguna se descubre leyendo el YAML.

## 1. Renderiza por software: es mucho más lento en interfaz

El runner no tiene aceleración gráfica. Cualquier interfaz que dibuje sobre un lienzo —aplicaciones construidas sobre motores de renderizado propios, animaciones, gráficos— se pinta por CPU. La diferencia no es del 20%: un flujo de autenticación medido en 25 segundos sobre una máquina de escritorio superó los 60 en el runner, con el backend habiendo respondido a los 23.

Consecuencias:

- **Un timeout calibrado en local está mal calibrado para el pipeline.** No por descuido: son entornos distintos.
- **La conclusión "la aplicación no avanza" es insegura en un runner.** Ahí es donde el estado observable —un botón en carga, un indicador de progreso— vale más que el reloj. Ver `[[calidad-playwright-greenfield]] (consultar `references/multi-outcome-waits-and-honest-failures.md` en su subfolder)`.

**El timeout se declara como piso configurable por variable de entorno**, no editando cada archivo que lo menciona:

```typescript
const timeout = options.timeout ?? envNumber('FLOW_TIMEOUT_MS', DEFAULT_TIMEOUT);
```

Así el pipeline sube el piso sin tocar código, y la variable queda en la plantilla de variables del proyecto y en su guía de diagnóstico. Un timeout que solo se puede cambiar editando veintisiete archivos no se cambia: se vive con él o se desactiva la prueba.

## 2. Su red no es tu red

El runner suele tener egreso restringido, y la aplicación bajo prueba y su API viven habitualmente en dominios distintos. El resultado típico: **la aplicación carga y la API es inalcanzable**. Desde una máquina de desarrollo con la red corporativa activa los dos resuelven, así que el caso no se reproduce localmente jamás.

Esto exige que el diagnóstico distinga *petición rechazada* de *petición que nunca obtuvo respuesta*: una request que muere por resolución de nombres, cortafuegos, proxy o negociación segura **no produce una respuesta con código de error**, produce un fallo de red. Un diagnóstico que solo mira códigos de estado reporta esto como lentitud.

Se clasifica como `environment_blocked_network` de `[[calidad-environment-blocker-evidence]]`, no como fallo de la suite.

## 3. Arranca limpio, siempre

Sin caché caliente, sin aplicación ya instalada, sin sesión previa, sin la primera compilación hecha. Todo lo que en local se paga una vez, en el runner se paga en cada corrida. Los arranques en frío pertenecen al presupuesto de tiempo del pipeline, no son una anomalía.

## Antes de declarar un problema del pipeline

Orden de descarte, del lado más barato al más caro:

1. **La red del propio puesto de quien diagnostica.** Verificado en campo: se declaró "el ambiente no está montando la aplicación" cuando lo que estaba apagado era la conexión corporativa de la máquina local. Ver `[[calidad-environment-blocker-evidence]]`.
2. **Las capturas de la corrida del runner**, no el mensaje de error. Son lo único que dice qué había en pantalla. Ver `[[calidad-test-evidence-and-traceability]]`.
3. **Las tres dimensiones de arriba**, una por una y con el dato: cronología de la red, estado observable de la interfaz, y si hubo peticiones sin respuesta.
4. Recién entonces, la configuración del pipeline.

Saltarse los tres primeros produce cambios de YAML que no arreglan nada y una corrida de veinte minutos por intento.

## Cross-links

- `quality-gates.md` — el gate estático del PR sobre el código de pruebas.
- `secrets-in-pipelines.md` — variables y secretos del runner.
- `[[calidad-environment-blocker-evidence]]` — categorías cerradas de bloqueo de entorno.
- `[[calidad-test-evidence-and-traceability]]` — las capturas se miran antes de concluir.
