# Troubleshooting de reportes

## Sintoma: target/site/serenity/index.html no se genera

| Causa | Fix |
|---|---|
| `serenity-bdd run` no ejecutado | `npm run serenity:report` |
| Falta el JAR | `npm run serenity:update` |
| `ArtifactArchiver` no en crew | Verificar `wdio.shared.conf.ts` |
| `outputDirectory` mal configurado | Debe ser `target/site/serenity` |

## Sintoma: reporte sin screenshots

| Causa | Fix |
|---|---|
| `Photographer` no añadido en config web | Agregar al crew de `wdio.web.conf.ts` |
| Estrategia muy restrictiva | Cambiar a `TakePhotosOfInteractions` temporalmente |
| `Photographer` activado en mobile | Removerlo del crew mobile (rompe sesión) |

## Sintoma: Allure vacío

| Causa | Fix |
|---|---|
| `@wdio/allure-reporter` no en `reporters` | Agregarlo al config |
| `outputDir` mal configurado | Debe coincidir con el comando `allure generate <dir>` |
| `allure-results/` no se limpió | `rm -rf allure-results` antes de correr |

## Sintoma: video no se genera

| Causa | Fix |
|---|---|
| ffmpeg no instalado | `brew install ffmpeg` (macOS) |
| `videoRenderTimeout` muy bajo | Subir a `60` o más para tests largos |
| Mobile session sin video | Video reporter es solo web; en mobile usar Appium video plugin |

## Comandos auxiliares

```bash
npm run serenity:update    # descarga el JAR de Serenity BDD si falta
npm run serenity:report    # regenera el reporte sin re-correr tests
npm run serenity:clean     # limpia ./target completo

npx allure generate allure-results --clean -o allure-report
npx allure open allure-report
npx allure serve allure-results   # genera y abre en un solo paso

ffmpeg -version            # verificar que ffmpeg está instalado
```
