# Diagnóstico de fallos de ejecución

## Tabla de diagnóstico

| Sintoma | Causa probable | Solución |
|---|---|---|
| `[ENV] usando valores por defecto` | Modo mal escrito o `.env.<m>` faltante | Verificar nombre del archivo y argumento `--mode` |
| `Modo "movil" requiere --platform` | Falta flag de plataforma | Agregar `--platform=android` o `ios` |
| `unknown driver` en Appium | Driver no instalado | `npx appium driver install <driver>` |
| Tests web pasan local pero no en CI | `HEADLESS=false` en local, headless implícito en CI | Forzar `HEADLESS=true` y usar `--headless=new` |
| `connect ECONNREFUSED 127.0.0.1:4723` | Appium no arrancó | Verificar `services: ['appium', ...]` en config |
| Chrome no abre / DevToolsActivePort | Falta `--no-sandbox` o usuario no tiene permisos | Ya está en `wdio.web.conf.ts` |
| iOS WDA falla al instalar | Cert/team ID inválidos | Validar `IOS_XCODE_ORG_ID` y firmar WDA con Xcode |
| `app not found` Android | Path relativo mal resuelto | Usar `path.resolve(...)` (ya hecho en `wdio.android.conf.ts`) |

## Checklist antes de ejecutar

- [ ] El `.env.*` correspondiente existe y tiene los valores necesarios
- [ ] (Mobile) emulador/dispositivo levantado
- [ ] (Mobile) drivers Appium instalados globalmente
- [ ] (iOS) certificados y team ID configurados
- [ ] (Web) navegador con versión compatible con WebDriver instalada
- [ ] La carpeta `target/` no tiene resultados viejos (`npm run serenity:clean`)
- [ ] Si se va a correr `--mode=all`, hay tiempo suficiente y todos los entornos listos
