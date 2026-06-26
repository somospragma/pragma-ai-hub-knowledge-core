---
id: calidad-seo-technical
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Auditoría técnica SEO agnóstica de tecnología: rastreabilidad, indexabilidad, seguridad, estructura de URLs, mobile, JavaScript rendering, crawl budget, faceted navigation, Service Workers, protocolo IndexNow, gestión de crawlers IA y cobertura multi-motor (Google, Bing, Yandex, Baidu, AI Search). Activar cuando se mencione 'SEO técnico', 'robots.txt', 'indexación', 'canonical', 'redirects', 'HTTPS', 'headers de seguridad', 'mobile-first', 'JavaScript SEO', 'crawl budget' o cualquier aspecto de infraestructura."
tags: [seo, web, tecnico, indexacion, crawl]
---

# SEO Técnico — Auditoría de Infraestructura

## Principio Agnóstico

Todos los checks se evalúan sobre el **output HTTP/HTML observable**, no sobre la implementación interna.
El stack tecnológico (framework JS, CMS, SSG, servidor) es irrelevante — importa lo que recibe el bot.

---

## 1. Rastreabilidad (Crawlability)

### robots.txt

**¿Qué debe existir?**
```
GET /robots.txt → HTTP 200
Content-Type: text/plain

User-agent: *
Allow: /
Disallow: /buscar/
Disallow: /carrito/
Disallow: /admin/
Sitemap: https://dominio.com/sitemap.xml
```

**Checks:**
- [ ] 🤖 Existe y responde HTTP 200
- [ ] 🤖 No bloquea recursos críticos: CSS, JS, imágenes, fuentes
- [ ] 🤖 No tiene `Disallow: /` para `User-agent: *` (bloqueo total accidental)
- [ ] 🤖 Referencia el sitemap con directiva `Sitemap:`
- [ ] 👁 Reglas intencionales vs accidentales verificadas manualmente

**Herramienta:** `curl -A "Googlebot" https://dominio.com/robots.txt` + Google Search Console → robots.txt Tester

---

### Profundidad de Rastreo

- [ ] 👁 Páginas estratégicas accesibles en ≤3 clics desde la homepage
- [ ] 🤖 Sin rutas circulares de navegación (A→B→C→A)
- [ ] 👁 Menú principal enlaza a todas las secciones principales

---

### JavaScript Rendering

Googlebot, Bingbot y la mayoría de crawlers ejecutan JavaScript — pero con demora (Googlebot puede tardar días en renderizar).

**Reglas críticas (actualización Google diciembre 2025):**

| Situación | Comportamiento del bot |
|-----------|----------------------|
| Canonical en HTML inicial ≠ canonical inyectado por JS | Google puede usar cualquiera |
| `noindex` en HTML inicial, JS lo elimina | Google puede respetar el `noindex` del HTML |
| Página retorna non-200 (4xx, 5xx) | Google NO renderiza JS — meta tags JS invisibles |
| JSON-LD inyectado solo por JS | Procesamiento retrasado para schema time-sensitive |

**Checks:**
- [ ] 🤖 Contenido principal (H1, párrafos, listas) visible en HTML inicial (`curl` sin JS)
- [ ] 🤖 Canonical en HTML inicial = canonical en DOM renderizado
- [ ] 🤖 `noindex` en HTML inicial NO es eliminado por JS
- [ ] 🤖 Páginas de error retornan HTTP 4xx/5xx, no HTTP 200 con contenido de error

**Verificación manual:**
```bash
# Ver HTML que recibe un bot (sin renderizar JS)
curl -A "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)" https://dominio.com/
```

---

### Service Workers

Los Service Workers pueden interceptar peticiones y entregar HTML obsoleto a los bots.

- [ ] 👁 El Service Worker no hace cache agresivo de páginas HTML (solo assets estáticos)
- [ ] 👁 Bots reciben la versión actualizada del contenido, no una versión cacheada del SW
- [ ] 👁 Si hay offline-first, verificar que el `Cache-Control` de HTML es `no-cache` o corto

---

### Crawl Budget y Faceted Navigation

Relevante para sitios con >1.000 URLs o con filtros/facetas.

- [ ] 👁 Sin rutas infinitas: filtros de URL, parámetros de ordenamiento, calendar pages
- [ ] 👁 Faceted navigation: URLs de filtros bloqueadas en `robots.txt` o con `noindex` + `canonical` a la categoría principal
- [ ] 👁 Paginación: `rel="next"` / `rel="prev"` implementados o método load-more con canonical
- [ ] 👁 URLs de sesión, tokens y parámetros de tracking excluidos o canonicalizados
- [ ] 🤖 Páginas de búsqueda interna bloqueadas con `noindex` o en `robots.txt`

**Patrón recomendado para faceted navigation:**
```html
<!-- Categoría principal: indexable -->
<link rel="canonical" href="https://dominio.com/productos/zapatos/" />

<!-- URL con filtros: canonical a la categoría padre -->
<!-- /productos/zapatos/?color=rojo&talla=42 -->
<link rel="canonical" href="https://dominio.com/productos/zapatos/" />
<meta name="robots" content="noindex, follow" />
```

---

## 2. Indexabilidad

- [ ] 🤖 Canonical tags: presentes en todas las páginas, URLs absolutas, sin conflicto con `noindex`
- [ ] 🤖 `www` vs no-`www`: uno redirige al otro — consistente en todo el sitio
- [ ] 🤖 `http` vs `https`: `http` siempre redirige a `https`
- [ ] 🤖 URLs con parámetros duplicados: tienen canonical o `noindex`
- [ ] 🤖 Sin index bloat: páginas de búsqueda interna, tags sin contenido, paginación sin valor — con `noindex`
- [ ] 👁 Tags `noindex` son intencionales — páginas de negocio no están bloqueadas accidentalmente

---

## 3. HTTPS y Seguridad

### HTTPS

- [ ] 🤖 Certificado SSL válido y no expirado
- [ ] 🤖 `http://` → `https://` redirección forzada (HTTP 301)
- [ ] 🤖 Sin contenido mixto: todos los recursos (imágenes, scripts, iframes, fuentes) por HTTPS
- [ ] 🤖 Sin mixed content warnings en Chrome DevTools → Network

**Impacto multi-motor:**
- Google: HTTPS es factor de ranking confirmado desde 2014
- Bing: HTTPS es requisito básico explícito en Bing Webmaster Guidelines
- Yandex: prioriza HTTPS en sus algoritmos de ranking

---

### Headers de Seguridad

Verificar directamente con `curl -I`:

```bash
# Obtener todos los response headers
curl -sI https://dominio.com/

# Filtrar solo los security headers relevantes
curl -sI https://dominio.com/ | grep -iE \
  "strict-transport|content-security-policy|x-frame-options|x-content-type-options|referrer-policy|permissions-policy"
```

**Output esperado (al menos estos tres):**
```
strict-transport-security: max-age=31536000; includeSubDomains
x-content-type-options: nosniff
x-frame-options: SAMEORIGIN
```

| Header | Valor recomendado | Impacto SEO |
|--------|-------------------|-------------|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Previene mixed content, mejora TTFB en visitas recurrentes |
| `Content-Security-Policy` | Política restrictiva (iniciar en Report-Only) | Previene inyección de scripts de terceros maliciosos |
| `X-Frame-Options` | `DENY` o `SAMEORIGIN` | Previene clickjacking |
| `X-Content-Type-Options` | `nosniff` | Previene MIME sniffing |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Controla datos de referrer |
| `Permissions-Policy` | Limitar features no usadas | Reduce superficie de ataque |

- [ ] 🤖 `Strict-Transport-Security` presente
- [ ] 🤖 `X-Content-Type-Options: nosniff` presente
- [ ] 🤖 `X-Frame-Options` presente
- [ ] 👁 CSP implementado (al menos en Report-Only si no está en enforce)

---

## 4. Estructura de URLs

- [ ] 🤖 URLs descriptivas: `/servicios/desarrollo-software/` no `/?p=42`
- [ ] 🤖 Uso de guiones como separador de palabras, no guiones bajos
- [ ] 🤖 Sin mayúsculas en URLs — minúsculas consistentes
- [ ] 🤖 Sin caracteres especiales ni acentos en la URL (solo en el `<title>` y headings)
- [ ] 🤖 Sin parámetros de sesión o tokens en URLs indexadas
- [ ] 🤖 Trailing slash consistente — elegir uno y redirigir el otro
- [ ] ⚠️ Alertar URLs >100 caracteres; crítico >150 caracteres
- [ ] 🤖 Redirects: máximo 1 salto — sin cadenas (A→B→C debe simplificarse a A→C)

---

## 5. Mobile Optimization

**100% mobile-first indexing desde julio 5, 2024** — Google indexa exclusivamente con Googlebot móvil.
Bingbot también tiene variante mobile. El contenido solo en desktop puede no ser indexado.

- [ ] 🤖 `<meta name="viewport" content="width=device-width, initial-scale=1">` presente
- [ ] 🤖 Sin scroll horizontal en viewport 375px
- [ ] 🤖 Fuente body mínimo 16px CSS
- [ ] 🤖 Touch targets mínimo 48×48px con 8px de separación (WCAG 2.2 nuevo criterio)
- [ ] 👁 El contenido visible en desktop también está en la versión mobile (no `display:none` en mobile para contenido principal)
- [ ] 🤖 Lighthouse mobile score auditable automáticamente

---

## 6. Protocolo IndexNow

IndexNow notifica instantáneamente a múltiples motores cuando una URL se crea, actualiza o elimina.
Motores participantes en 2026: **Bing, Yandex, Naver, seznam.cz, yep.com, Brave Search**.

> Google NO participa en IndexNow — usa su propio sistema (Search Console Indexing API).

**Implementación:**
1. Generar una API key (string alfanumérico)
2. Alojar el archivo de verificación: `https://dominio.com/{api-key}.txt`
3. Enviar notificación cuando hay cambios:

```http
POST https://api.indexnow.org/IndexNow
Content-Type: application/json; charset=utf-8

{
  "host": "dominio.com",
  "key": "tu-api-key",
  "urlList": [
    "https://dominio.com/nuevo-articulo/",
    "https://dominio.com/pagina-actualizada/"
  ]
}
```

- [ ] 👁 IndexNow implementado y enviando notificaciones en publicaciones/actualizaciones
- [ ] 🤖 Archivo de verificación accesible: `GET /{api-key}.txt → HTTP 200`

---

## 7. Ecosistema Completo de Crawlers

### Motores de Búsqueda Tradicionales

| Motor | Crawler | Mercado | Particularidades |
|-------|---------|---------|-----------------|
| Google | Googlebot | Global dominante | Mobile-first, renderiza JS, sigue canonical |
| Google Mobile | Googlebot Smartphone | Subvariante móvil | Es el indexador principal desde jul 2024 |
| Bing | Bingbot | Global, EEUU 3% | Alimenta Yahoo, DuckDuckGo, Copilot AI |
| Yandex | YandexBot | Rusia, CIS | Tiene sus propias directivas meta, soporta IndexNow |
| Baidu | Baiduspider | China | No usa schema.org — usa su propio vocabulario |
| Naver | NaverBot | Corea del Sur | Soporta IndexNow |
| Brave | BraveBot | Creciendo | Índice independiente, soporta IndexNow |
| DuckDuckGo | DuckDuckBot | 2-3% global | Usa principalmente índice Bing |
| Apple | Applebot | iOS/macOS | Alimenta Siri Suggestions, Spotlight, Safari |
| Ecosia | EcosiaBot | Europa | Usa índice Bing |

### Crawlers de IA (Entrenamiento y Búsqueda Aumentada)

| Crawler | Organización | Propósito | Distinción clave |
|---------|-------------|-----------|-----------------|
| GPTBot | OpenAI | Entrenamiento de modelos | Bloquearlo ≠ bloquear ChatGPT browsing |
| OAI-SearchBot | OpenAI | ChatGPT búsqueda en tiempo real | Distinto a GPTBot |
| ChatGPT-User | OpenAI | Navegación de usuarios en ChatGPT | User-triggered, puede ignorar robots.txt |
| ClaudeBot | Anthropic | Entrenamiento Claude | Respeta robots.txt |
| PerplexityBot | Perplexity | Índice de búsqueda IA + entrenamiento | Motor de búsqueda + IA |
| Google-Extended | Google | Entrenamiento Gemini | NO afecta ranking en Google Search |
| CCBot | Common Crawl | Dataset abierto para LLMs | Usado por muchos modelos de IA |
| Bytespider | ByteDance | Features IA TikTok/Douyin | Alto volumen de crawling |
| Amazonbot | Amazon | Entrenamiento Alexa/LLMs | Bajo volumen |
| Petalbot | Huawei | Petal Search | Mercados asia/europa |
| YouBot | You.com | Motor de búsqueda IA | Motor independiente |
| FacebookExternalHit | Meta | Previsualizaciones de links | No para entrenamiento de IA |

### Política Recomendada en robots.txt

**Estrategia: Visible en búsqueda, control sobre entrenamiento IA**

```
# =============================================
# MOTORES DE BÚSQUEDA — siempre permitir
# =============================================
User-agent: Googlebot
Allow: /

User-agent: Bingbot
Allow: /

User-agent: YandexBot
Allow: /

User-agent: Applebot
Allow: /

# =============================================
# CRAWLERS IA — decisión estratégica
# =============================================

# OpenAI — separar entrenamiento de búsqueda en tiempo real
User-agent: GPTBot
Disallow: /       # Bloquea entrenamiento de modelos

User-agent: OAI-SearchBot
Allow: /          # Permite aparición en ChatGPT Search

# Entrenamiento Gemini (NO afecta Google Search)
User-agent: Google-Extended
Disallow: /

# Dataset abierto — usado por muchos LLMs
User-agent: CCBot
Disallow: /

# ByteDance
User-agent: Bytespider
Disallow: /

# =============================================
# REGLA GENERAL
# =============================================
User-agent: *
Allow: /
Disallow: /admin/
Disallow: /buscar/

Sitemap: https://dominio.com/sitemap.xml
```

> ⚠️ Bloquear `PerplexityBot` impide aparecer en resultados de Perplexity AI — considerar estratégicamente.
> ⚠️ Bloquear `CCBot` reduce la probabilidad de que el contenido sea citado por modelos de lenguaje.

---

## 8. llms.txt — Nuevo Estándar para IA

Chrome Lighthouse incluyó verificación de `llms.txt` en 2025. Compañías como Stripe, Zapier, y Cloudflare ya lo implementan.

**¿Qué es?**
Un archivo en texto simple ubicado en la raíz que describe al sitio para agentes IA y LLMs, similar a como `robots.txt` describe el sitio para bots de búsqueda.

**Formato básico:**
```
GET /llms.txt → HTTP 200
Content-Type: text/plain

# Empresa
> Consultoría de tecnología B2B especializada en transformación digital, desarrollo de software y cloud.

## Contenido público
- [Servicios](https://dominio.com/servicios/): Descripción de todos los servicios
- [Blog](https://dominio.com/blog/): Artículos técnicos y de industria
- [Casos de Éxito](https://dominio.com/casos-exito/): Proyectos realizados con clientes

## Uso permitido
Los agentes IA pueden usar este contenido para responder preguntas, citar y enlazar de vuelta al sitio original.
```

- [ ] 👁 `llms.txt` implementado y accesible en la raíz (recomendado, no obligatorio)
- [ ] 🤖 `GET /llms.txt → HTTP 200` si está implementado

---

## 9. Metaetiquetas Específicas por Motor

### Bing / Microsoft

```html
<!-- Verificación de sitio en Bing Webmaster Tools -->
<meta name="msvalidate.01" content="[CODIGO-VERIFICACION]" />

<!-- Bing respeta meta robots estándar -->
<meta name="robots" content="index, follow" />
```

### Yandex

```html
<!-- Verificación de sitio en Yandex Webmaster -->
<meta name="yandex-verification" content="[CODIGO-VERIFICACION]" />

<!-- Yandex tiene su propio set de meta tags para comportamiento específico -->
<!-- Yandex-turbo para AMP-like pages en Yandex -->
```

### Apple (Applebot / Siri)

```html
<!-- Apple no requiere meta tags especiales — usa Open Graph y Schema.org -->
<!-- Applebot usa og:image para previsualizaciones en Safari -->
<!-- Verificar que og:image existe y es accesible -->
```

### Baidu (mercado chino)

```html
<!-- Baidu usa su propio vocabulario — no schema.org -->
<!-- Requiere servidor alojado en China o ICP license para rankear bien -->
<!-- Baidu Mobile-first: el sitio debe cargarse en <2s en redes 3G -->
<!-- Baidu no renderiza JS de forma fiable — SSR/SSG es crítico -->
```

---

## 10. Output

### Score Técnico: XX/100

### Desglose por Categoría

| Categoría | Estado | Score | Issues |
|-----------|--------|-------|--------|
| Rastreabilidad | ✅/⚠️/❌ | XX/100 | N |
| Indexabilidad | ✅/⚠️/❌ | XX/100 | N |
| HTTPS / Seguridad | ✅/⚠️/❌ | XX/100 | N |
| Estructura de URLs | ✅/⚠️/❌ | XX/100 | N |
| Mobile | ✅/⚠️/❌ | XX/100 | N |
| JavaScript Rendering | ✅/⚠️/❌ | XX/100 | N |
| Crawl Budget | ✅/⚠️/❌ | XX/100 | N |
| Service Workers | ✅/⚠️/❌ | XX/100 | N/A |
| IndexNow | ✅/⚠️/❌ | — | — |
| Gestión crawlers IA | ✅/⚠️/❌ | — | — |
| llms.txt | ✅/❌ | — | Opcional |

### Issues por Prioridad

**🔴 Crítico** — bloqueo accidental de rastreo, `noindex` accidental en páginas de negocio, HTTPS no forzado, contenido crítico solo en JS
**🟠 Alto** — headers de seguridad ausentes, cadenas de redirect, rutas infinitas consumiendo crawl budget
**🟡 Medio** — IndexNow no implementado, política de crawlers IA no definida, llms.txt ausente
**🟢 Bajo** — URLs subóptimas (mejorable pero funcional), trailing slash inconsistente

---

## Automatización en QA Pipeline

| Check | Herramienta CLI | Tipo |
|-------|-----------------|------|
| robots.txt accesible y válido | `curl` + `playwright` | 🤖 |
| sitemap.xml HTTP 200 | `curl` / `playwright` | 🤖 |
| HTTPS forzado | `curl -I http://dominio.com` | 🤖 |
| Headers de seguridad | `curl -I` + grep por header | 🤖 |
| noindex accidental | `lighthouse` / `playwright` | 🤖 |
| Canonical presente | `playwright` | 🤖 |
| Mobile viewport | `lighthouse --preset=mobile` | 🤖 |
| JS rendering gap | `playwright` (comparar DOM vs source) | 🔬 |
| Crawl budget / rutas infinitas | `playwright` (inspeccionar hrefs internos) | 👁 |

```javascript
// Playwright — checks técnicos automatizables

test('HTTPS forzado: http:// redirige a https://', async ({ request }) => {
  const response = await request.get('http://dominio.com/', { maxRedirects: 0 });
  expect([301, 302, 308]).toContain(response.status());
  const location = response.headers()['location'];
  expect(location).toMatch(/^https:\/\//);
});

test('Security headers obligatorios presentes', async ({ request }) => {
  const response = await request.get('/');
  const headers = response.headers();
  expect(headers['strict-transport-security']).toBeDefined();
  expect(headers['x-content-type-options']).toBe('nosniff');
  expect(headers['x-frame-options']).toBeDefined();
});

test('robots.txt no bloquea recursos críticos', async ({ request }) => {
  const response = await request.get('/robots.txt');
  expect(response.status()).toBe(200);
  const text = await response.text();
  // Detectar bloqueos accidentales de assets
  const blockedAssets = ['/css', '/js', '/assets', '/static', '/fonts', '/images'];
  for (const path of blockedAssets) {
    const blocked = text.match(new RegExp(`Disallow:\\s*${path.replace('/', '\\/')}`, 'i'));
    expect(blocked, `robots.txt bloquea ${path}`).toBeNull();
  }
  expect(text).toContain('Sitemap:');
});

test('Sin noindex accidental en páginas de negocio', async ({ page }) => {
  const businessPages = ['/', '/servicios/', '/nosotros/', '/contacto/'];
  for (const path of businessPages) {
    await page.goto(path);
    const metaRobots = await page.locator('meta[name="robots"]').getAttribute('content');
    if (metaRobots) {
      expect(metaRobots.toLowerCase()).not.toContain('noindex');
    }
    // También verificar en HTTP headers
    const response = await page.request.get(path);
    const xRobotsTag = response.headers()['x-robots-tag'];
    if (xRobotsTag) {
      expect(xRobotsTag.toLowerCase()).not.toContain('noindex');
    }
  }
});

test('Crawl budget: sin URLs con profundidad excesiva (>5 segmentos)', async ({ page }) => {
  await page.goto('/');
  const internalLinks = await page.locator('a[href]').evaluateAll(links =>
    links
      .map(l => l.getAttribute('href'))
      .filter(href => href && href.startsWith('/') && !href.startsWith('//'))
  );
  const deepUrls = internalLinks.filter(href => {
    const segments = href.split('/').filter(Boolean);
    return segments.length > 5;
  });
  expect(
    deepUrls.length,
    `URLs con profundidad excesiva (posible crawl budget issue): ${deepUrls.slice(0, 5).join(', ')}`
  ).toBeLessThan(10);
});

test('Canonical en HTML inicial (no solo inyectado por JS)', async ({ request }) => {
  // Verificar que el canonical está en el HTML crudo del servidor
  const response = await request.get('/');
  const html = await response.text();
  expect(html).toMatch(/<link[^>]+rel=["']canonical["']/i);
});
```

---

## Integración con Otros Skills

| Necesidad | Skill |
|-----------|-------|
| JSON-LD en HTML inicial | `/seo-schema` |
| Imágenes en HTTPS | `/seo-images` |
| Sitemap cobertura y exclusiones | `/seo-sitemap` |
| Performance servidor (TTFB) | `/seo-performance` |
| Hreflang canonical coherencia | `/seo-hreflang` |