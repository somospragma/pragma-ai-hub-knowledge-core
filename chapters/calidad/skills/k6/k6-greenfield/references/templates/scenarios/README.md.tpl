# scenarios/

Logica HTTP reusable. Cada archivo exporta una funcion `default` que ejecuta la secuencia de pasos de un flujo (auth, main, cleanup) usando `group()`, `http.*`, `check()` y `sleep()`.

## Reglas

- **No** definir `options` aqui. La curva de carga la decide el workload (`workloads/*.js`).
- Importar configuracion desde `../shared/config.js` y helpers desde `../shared/utils.js`.
- Si el flow requiere autenticacion, delegar a `auth.js` (`import { login } from './auth.js'`), no inlinear login.
- Etiquetar requests y checks con `tags: { endpoint, step }` para segmentar metricas.
- Usar `sleep(randomIntBetween(1, 5))` entre pasos para simular think-time realista.

## Composicion

Un scenario se combina con un workload en `tests/{escenario}/main.js`:

```javascript
export { options } from '../../workloads/linea-base.js';
export { default } from '../../scenarios/{{main-flow}}.js';
export { handleSummary } from '../../shared/handle-summary.js';
```

El mismo scenario se reutiliza para linea-base, carga y estres cambiando solo el workload importado.

Detalle en `[[k6-modular-architecture]]`.
