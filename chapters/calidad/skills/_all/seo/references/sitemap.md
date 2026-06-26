# Sitemap XML — Guía de Rastreo Multi-Motor

## Cobertura Multi-Motor

| Motor | Cómo usa el sitemap |
|-------|---------------------|
| Google | Descubrimiento de URLs, `<lastmod>` para re-rastreo |
| Bing | Descubrimiento de URLs — también soporta IndexNow que es más rápido |
| Yandex | Descubrimiento de URLs, soporta IndexNow |
| DuckDuckGo | Usa principalmente índice Bing — beneficiario indirecto |
| Naver | Descubrimiento de URLs, soporta IndexNow |
| Crawlers IA | PerplexityBot, GPTBot y otros usan el sitemap para descubrir URLs |

> El sitemap no garantiza indexación — solo asegura que el motor puede descubrir la URL. La indexación depende de la calidad del contenido, la autoridad del sitio y otros factores.

---

## 1. Verificaciones Básicas

### Accesibilidad

```bash
# Verificar que el sitemap existe y responde correctamente
curl -I https://dominio.com/sitemap.xml
# Esperado: HTTP/2 200, Content-Type: application/xml o text/xml

# Ver contenido
curl https://dominio.com/sitemap.xml | head -50
```

**Checks:**
- [ ] 🤖 `GET /sitemap.xml` retorna HTTP 200
- [ ] 🤖 Content-Type es `text/xml`, `application/xml` o `application/x-sitemap`
- [ ] 🤖 Sin redirect a otra URL antes de responder
- [ ] 🤖 Referenciado en `robots.txt`: `Sitemap: https://dominio.com/sitemap.xml`

---

## 2. Estructura XML Válida

### Sitemap Simple (para sitios <50.000 URLs)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">

  <url>
    <loc>https://dominio.com/</loc>
    <lastmod>2025-06-15</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>

  <url>
    <loc>https://dominio.com/servicios/</loc>
    <lastmod>2025-05-20</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>

  <url>
    <loc>https://dominio.com/blog/titulo-articulo/</loc>
    <lastmod>2025-06-10</lastmod>
    <changefreq>never</changefreq>
    <priority>0.6</priority>
  </url>

</urlset>
```

**Checks:**
- [ ] 🤖 Namespace correcto: `http://www.sitemaps.org/schemas/sitemap/0.9`
- [ ] 🤖 Todas las `<loc>` son URLs absolutas con `https://`
- [ ] 🤖 `<lastmod>` en formato ISO 8601: `YYYY-MM-DD` o `YYYY-MM-DDTHH:MM:SS±HH:MM`
- [ ] 🤖 XML bien formado (sin errores de parseo)

---

### Sitemap Index (para sitios con >1.000 páginas o para organizar por sección)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">

  <sitemap>
    <loc>https://dominio.com/sitemap-paginas.xml</loc>
    <lastmod>2025-06-15</lastmod>
  </sitemap>

  <sitemap>
    <loc>https://dominio.com/sitemap-blog.xml</loc>
    <lastmod>2025-06-20</lastmod>
  </sitemap>

  <sitemap>
    <loc>https://dominio.com/sitemap-servicios.xml</loc>
    <lastmod>2025-06-10</lastmod>
  </sitemap>

</sitemapindex>
```

**Límites del protocolo:**
- Máximo 50.000 URLs por archivo sitemap
- Máximo 50MB por archivo sitemap (descomprimido)
- Si se supera cualquier límite → usar sitemap index

---

## 3. Reglas de Inclusión/Exclusión

### ✅ Incluir

- Páginas que retornan HTTP 200
- Páginas con `<meta name="robots" content="index, follow">` (o sin meta robots — default es indexable)
- Todas las páginas estratégicas del sitio (homepage, servicios, blog, nosotros, contacto)
- La URL canónica (no las variantes con parámetros)

### ❌ Excluir Obligatoriamente

| Tipo de página | Razón |
|----------------|-------|
| Páginas con `noindex` | Contradicción — si no quieres que se indexe, no la pongas en el sitemap |
| Redirects (301, 302) | Solo incluir la URL de destino final |
| Páginas de error (4xx, 5xx) | Sin valor — Google reporta esto como error en Search Console |
| URLs con parámetros duplicados | Solo la URL canónica |
| Páginas de búsqueda interna | Sin valor SEO |
| Páginas de confirmación/gracias | Sin valor SEO |
| Páginas de admin/login | Riesgo de seguridad |
| URLs de paginación (opcional) | Depende — incluir si cada página tiene contenido único valioso |

```python
# Pseudocódigo agnóstico — lógica de inclusión
def debe_incluir_en_sitemap(url, page):
    if page.status_code != 200:
        return False
    if page.has_noindex:
        return False
    if page.is_redirect:
        return False
    if page.canonical != url:  # Solo la versión canónica
        return False
    return True
```

---

## 4. `<lastmod>` — Fecha de Última Modificación

| Práctica | Descripción |
|----------|-------------|
| ✅ Usar fecha real | La fecha en que el contenido principal fue actualizado por última vez |
| ✅ Omitir si desconocida | Mejor no tener `<lastmod>` que tener una fecha falsa |
| ❌ Fecha de generación | No poner la fecha/hora en que se generó el sitemap |
| ❌ Misma fecha para todo | No actualizar todos los `<lastmod>` a hoy indiscriminadamente |

> Google aprende el historial de cambios y ajusta la frecuencia de rastreo según `<lastmod>`. Fechas falsas destruyen esta señal.

---

## 5. `<changefreq>` y `<priority>`

Ambos son **indicativos** — Google y Bing pueden ignorarlos. Sin embargo, son útiles para Yandex y otros motores.

| `<changefreq>` | Cuándo usar |
|----------------|-------------|
| `always` | Tiempo real (raramente apropiado) |
| `hourly` | Feeds de noticias en tiempo real |
| `daily` | Homepage, blog index |
| `weekly` | Páginas de servicios activas |
| `monthly` | Páginas de servicios estables |
| `yearly` | Páginas muy estables (legal, about) |
| `never` | Archivos históricos inmutables |

| `<priority>` | Páginas |
|--------------|---------|
| 1.0 | Homepage |
| 0.9 | Servicios principales, secciones críticas |
| 0.8 | Servicios secundarios, casos de éxito |
| 0.7 | Blog index, about, categorías |
| 0.6 | Artículos de blog individuales |
| 0.5 | Legal, FAQ, soporte |

---

## 6. Hreflang en Sitemap

Para sitios con variantes de idioma/región, el sitemap es el método más escalable para implementar hreflang:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset
  xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
  xmlns:xhtml="http://www.w3.org/1999/xhtml">

  <!-- Versión Colombia -->
  <url>
    <loc>https://dominio.com/servicios/</loc>
    <xhtml:link rel="alternate" hreflang="es-CO" href="https://dominio.com/servicios/" />
    <xhtml:link rel="alternate" hreflang="es-MX" href="https://dominio.com/mx/servicios/" />
    <xhtml:link rel="alternate" hreflang="x-default" href="https://dominio.com/servicios/" />
    <lastmod>2025-06-01</lastmod>
  </url>

  <!-- Versión México -->
  <url>
    <loc>https://dominio.com/mx/servicios/</loc>
    <xhtml:link rel="alternate" hreflang="es-CO" href="https://dominio.com/servicios/" />
    <xhtml:link rel="alternate" hreflang="es-MX" href="https://dominio.com/mx/servicios/" />
    <xhtml:link rel="alternate" hreflang="x-default" href="https://dominio.com/servicios/" />
    <lastmod>2025-06-01</lastmod>
  </url>

</urlset>
```

---

## 7. Generación Automática (Principio Agnóstico)

El sitemap debe generarse automáticamente a partir de las URLs del sitio. **Nunca mantener un sitemap de forma manual.**

**Output esperado** independientemente del framework/CMS:
```
GET /sitemap.xml → HTTP 200
Content-Type: text/xml; charset=utf-8

XML con:
- Todas las URLs indexables del sitio
- lastmod real por cada URL
- Actualizado automáticamente cuando se publica/actualiza contenido
```

**Señales de que el sitemap es manual (alerta roja):**
- Todas las URLs tienen el mismo `<lastmod>`
- El `<lastmod>` es la fecha de generación del archivo, no del contenido
- URLs de páginas eliminadas aún aparecen
- Páginas nuevas tardaron días en aparecer

---

## 8. Integración con IndexNow

Complementar el sitemap con IndexNow para indexación inmediata en Bing, Yandex y Naver.

Cuando se publica o actualiza una URL, además de regenerar el sitemap, enviar notificación IndexNow:

```http
POST https://api.indexnow.org/IndexNow
Content-Type: application/json; charset=utf-8

{
  "host": "dominio.com",
  "key": "[API-KEY]",
  "urlList": [
    "https://dominio.com/nuevo-servicio/",
    "https://dominio.com/blog/nuevo-articulo/"
  ]
}
```

**El sitemap y IndexNow son complementarios:**
- Sitemap → descubrimiento de todas las URLs (crawler las encuentra a su ritmo)
- IndexNow → notificación inmediata de cambios (indexación en ~8 minutos en Bing)

---

## 9. Verificación en Herramientas de Webmaster

### Google Search Console

1. Ir a GSC → Sitemaps
2. Ingresar URL del sitemap
3. Revisar: "URLs enviadas" vs "URLs descubiertas"
4. Si hay brecha grande → investigar páginas excluidas

### Bing Webmaster Tools

1. Ir a Bing WMT → Sitemaps
2. Enviar el sitemap
3. Revisar IndexNow Insights para verificar notificaciones

### Yandex Webmaster

1. Ir a Yandex.Webmaster → Indexing → Sitemap files
2. Agregar el sitemap
3. Verificar estado de procesamiento

---

## Output

### Score Sitemap: XX/100

### Verificaciones

| Check | Estado | Detalle |
|-------|--------|---------|
| `GET /sitemap.xml` → HTTP 200 | ✅/❌ | — |
| Referenciado en `robots.txt` | ✅/❌ | — |
| XML válido sin errores de parseo | ✅/❌ | — |
| Sin URLs con `noindex` | ✅/⚠️/❌ | N URLs problemáticas |
| Sin URLs con redirect | ✅/⚠️/❌ | N redirects |
| Sin URLs 4xx/5xx | ✅/⚠️/❌ | N URLs con error |
| `lastmod` presente y real | ✅/⚠️/❌ | — |
| Generación automática (no manual) | ✅/⚠️/❌ | — |
| Cobertura de páginas estratégicas | ✅/⚠️/❌ | N de N páginas presentes |

---

## Automatización en QA Pipeline

```javascript
// Playwright — verificaciones de sitemap

test('sitemap.xml es accesible', async ({ request }) => {
  const response = await request.get('/sitemap.xml');
  expect(response.status()).toBe(200);
  const contentType = response.headers()['content-type'];
  expect(contentType).toMatch(/xml/);
});

test('sitemap.xml es XML válido con namespace correcto', async ({ request }) => {
  const response = await request.get('/sitemap.xml');
  const xml = await response.text();
  expect(xml).toContain('http://www.sitemaps.org/schemas/sitemap/0.9');
  expect(xml).toContain('<url>');
  expect(xml).toContain('<loc>');
});

test('sitemap.xml está referenciado en robots.txt', async ({ request }) => {
  const response = await request.get('/robots.txt');
  const text = await response.text();
  expect(text).toContain('Sitemap:');
  expect(text).toMatch(/Sitemap:\s*https?:\/\//i);
});

test('URLs en sitemap son absolutas con https', async ({ request }) => {
  const response = await request.get('/sitemap.xml');
  const xml = await response.text();
  const locMatches = xml.match(/<loc>(.*?)<\/loc>/g) || [];
  for (const loc of locMatches) {
    const url = loc.replace(/<\/?loc>/g, '');
    expect(url).toMatch(/^https:\/\//);
  }
});
```

---

## Integración con Otros Skills

| Necesidad | Skill |
|-----------|-------|
| Verificar que URLs del sitemap no tienen `noindex` | `/seo-technical` |
| Hreflang en sitemap para variantes | `/seo-hreflang` |
| IndexNow para indexación rápida en Bing/Yandex | `/seo-technical` |
