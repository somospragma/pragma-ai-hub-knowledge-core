# On-Page SEO — Elementos HTML por Página

## Principio Agnóstico

Todos los checks se evalúan sobre el HTML que recibe el bot, no sobre cómo se genera.
Cualquier framework, CMS o generador que produzca el HTML correcto supera el check.

**Output esperado** en el `<head>` de cada página:
```html
<head>
  <title>Título descriptivo de la página | Marca</title>
  <meta name="description" content="Descripción útil de 140-160 caracteres con CTA implícito." />
  <link rel="canonical" href="https://dominio.com/url-de-esta-pagina/" />
  <meta name="robots" content="index, follow" />
  <meta property="og:title" content="Título descriptivo de la página" />
  <meta property="og:description" content="Descripción para redes sociales." />
  <meta property="og:image" content="https://dominio.com/assets/og-imagen.jpg" />
  <meta property="og:url" content="https://dominio.com/url-de-esta-pagina/" />
  <meta property="og:type" content="website" />
  <meta name="twitter:card" content="summary_large_image" />
  <!-- Verificación de motores (solo en homepage o layout global) -->
  <meta name="msvalidate.01" content="[CÓDIGO-BING]" />
  <meta name="yandex-verification" content="[CÓDIGO-YANDEX]" />
</head>
```

---

## 1. Title Tag

**Impacto:** Factor de ranking en Google, Bing, Yandex y DuckDuckGo. Afecta CTR directamente.

| Aspecto | Regla | Umbral |
|---------|-------|--------|
| Longitud | 50–60 caracteres | Alerta <30 o >65 |
| Keyword primaria | Incluida de forma natural | Preferiblemente antes de la mitad |
| Unicidad | Diferente en cada URL | Sin duplicados |
| Marca | Puede incluirse al final con separador ` | ` | No obligatorio en todas |

```html
<!-- Correcto -->
<title>Desarrollo de Software a Medida | Empresa</title>

<!-- Incorrecto — muy genérico, sin keyword -->
<title>Servicios</title>

<!-- Incorrecto — demasiado largo (truncado) -->
<title>Servicios de Desarrollo de Software a Medida para Empresas en Colombia y Latinoamérica</title>
```

**Nota Bing:** Bing usa el title tag igual que Google. Bing es más estricto con titles que coincidan exactamente con la query del usuario.

**Nota Yandex:** Yandex prioriza titles que son exactamente iguales a queries de búsqueda frecuentes en su índice.

**Nota IA Search:** Perplexity y ChatGPT Search usan el title tag para identificar el tema de la página al citar como fuente.

**Check:**
- [ ] 🤖 Title presente y no vacío
- [ ] 🤖 Longitud 30–65 caracteres
- [ ] 🤖 Sin duplicados en el sitio
- [ ] 👁 Keyword objetivo incluida de forma natural

---

## 2. Meta Description

**Impacto:** No es factor de ranking directo, pero afecta CTR → el CTR sí es señal de ranking. Bing dice explícitamente que meta description afecta el CTR que usa como señal.

| Aspecto | Regla |
|---------|-------|
| Longitud | 140–160 caracteres |
| Unicidad | Diferente en cada página |
| CTA implícito | "Descubre...", "Conoce...", "Solicita..." |
| Keyword | Incluida de forma natural (se resalta en bold en resultados) |

```html
<!-- Correcto -->
<meta name="description" content="Desarrollamos software a medida con equipos ágiles y arquitectura cloud-native. Conoce nuestro proceso y casos de éxito." />

<!-- Incorrecto — demasiado corta -->
<meta name="description" content="Software a medida." />

<!-- Ausente — Google genera automáticamente una, frecuentemente mala -->
```

**Check:**
- [ ] 🤖 Meta description presente y no vacía
- [ ] 🤖 Longitud 100–170 caracteres
- [ ] 🤖 Sin duplicados en el sitio
- [ ] 👁 Incluye beneficio o CTA implícito

---

## 3. Estructura de Headings (H1–H6)

**Impacto:** Google, Bing, Yandex y crawlers IA usan los headings para entender la estructura temática de la página.

| Regla | Descripción |
|-------|-------------|
| H1 único | Exactamente uno por página |
| Jerarquía sin saltos | No pasar de H1 a H3 sin H2 intermedio |
| Descriptivos | Cada heading describe el contenido de su sección |
| Sin decorativos | No usar headings para efectos tipográficos — usar CSS |

```html
<!-- Correcto — jerarquía lógica -->
<h1>Desarrollo de Software a Medida</h1>
  <h2>Nuestro Proceso</h2>
    <h3>Fase de Descubrimiento</h3>
    <h3>Diseño de Arquitectura</h3>
  <h2>Tecnologías</h2>
    <h3>Backend</h3>
    <h3>Frontend</h3>

<!-- Incorrecto — múltiples H1 -->
<h1>Inicio</h1>
<h1>Servicios</h1>

<!-- Incorrecto — salto de nivel -->
<h1>Título principal</h1>
<h3>Subtítulo (falta H2)</h3>
```

**Check:**
- [ ] 🤖 Exactamente un H1 por página
- [ ] 🤖 Sin saltos de nivel en jerarquía de headings
- [ ] 👁 H1 alineado con la keyword objetivo de la página
- [ ] 👁 H2 y H3 descriptivos del contenido de sus secciones

---

## 4. Canonical Tag

**Impacto:** Señal directa de URL preferida para Google, Bing y Yandex.

```html
<!-- Correcto — URL absoluta, autorreferencial -->
<link rel="canonical" href="https://dominio.com/servicios/desarrollo-software/" />

<!-- Incorrecto — URL relativa -->
<link rel="canonical" href="/servicios/desarrollo-software/" />

<!-- Incorrecto — conflicto con noindex -->
<meta name="robots" content="noindex" />
<link rel="canonical" href="https://dominio.com/servicios/desarrollo-software/" />
<!-- Una página no puede tener noindex Y canonical a otra URL simultáneamente -->
```

**Alerta JavaScript (actualización Google diciembre 2025):**
Si el HTML inicial tiene un canonical y JavaScript inyecta otro diferente, Google puede usar cualquiera de los dos. Garantizar que sean idénticos.

**Check:**
- [ ] 🤖 Canonical presente en todas las páginas
- [ ] 🤖 URL absoluta con `https://`
- [ ] 🤖 Sin conflicto entre canonical y noindex
- [ ] 🔬 Canonical en HTML inicial = canonical en DOM renderizado (verificar via `curl` vs browser)

---

## 5. Meta Robots

```html
<!-- Default — se puede omitir (es el comportamiento por defecto) -->
<meta name="robots" content="index, follow" />

<!-- Solo para páginas que NO deben aparecer en ningún buscador -->
<meta name="robots" content="noindex, follow" />

<!-- Para bloquear solo un motor específico -->
<meta name="googlebot" content="noindex" />      <!-- Solo Google -->
<meta name="bingbot" content="noindex" />         <!-- Solo Bing -->

<!-- Evitar que Google muestre "En caché" -->
<meta name="robots" content="noarchive" />

<!-- Evitar que Google use la página como fuente para AI Overviews -->
<meta name="robots" content="nosnippet" />
```

**Directivas específicas por motor:**

| Directiva | Google | Bing | Yandex |
|-----------|--------|------|--------|
| `noindex` | ✅ Soportado | ✅ Soportado | ✅ Soportado |
| `nofollow` | ✅ Soportado | ✅ Soportado | ✅ Soportado |
| `noarchive` | ✅ Soportado | ✅ Soportado | ✅ Soportado |
| `nosnippet` | ✅ Soportado | ✅ Soportado | ⚠️ Parcial |
| `noimageindex` | ✅ Soportado | ✅ Soportado | ⚠️ Parcial |
| `max-snippet: -1` | ✅ Soportado | ⚠️ Puede ignorar | — |

**Check:**
- [ ] 🤖 Sin `noindex` accidental en páginas de negocio
- [ ] 👁 `noindex` solo en páginas correctas (confirmación, búsqueda interna, admin)

---

## 6. Open Graph (Redes Sociales y Vista Previa)

Open Graph controla la vista previa al compartir en LinkedIn, Facebook, WhatsApp, Slack, Teams, Discord, Telegram.

```html
<meta property="og:title" content="[Título de la página]" />
<meta property="og:description" content="[Descripción de 1-2 oraciones]" />
<meta property="og:image" content="https://dominio.com/assets/og/[pagina].jpg" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:image:alt" content="[Descripción de la imagen]" />
<meta property="og:url" content="https://dominio.com/[url-de-esta-pagina]/" />
<meta property="og:type" content="website" />  <!-- o "article" para blog -->
<meta property="og:locale" content="es_CO" />
<meta property="og:site_name" content="[Nombre del sitio]" />
```

**Especificaciones de og:image:**
- Dimensiones: **1200×630px** (proporción 1.91:1)
- Formato: **JPEG o PNG** — WebP no es soportado universalmente por scrapers
- Peso: <1MB (recomendado <300KB)
- Única por página estratégica (al menos por sección)

**Nota:** Apple (iMessage, Safari) usa Open Graph para previsualizaciones. Microsoft Teams y Slack también.

**Check:**
- [ ] 🤖 `og:title` presente y no vacío
- [ ] 🤖 `og:description` presente
- [ ] 🤖 `og:image` con URL absoluta HTTPS
- [ ] 🤖 `og:url` presente
- [ ] 👁 `og:image` es 1200×630 en JPEG/PNG

---

## 7. Twitter/X Card

```html
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="[Título]" />
<meta name="twitter:description" content="[Descripción corta]" />
<meta name="twitter:image" content="https://dominio.com/assets/og/[pagina].jpg" />
<meta name="twitter:image:alt" content="[Descripción de imagen]" />
<meta name="twitter:site" content="@[handle]" />
```

**Check:**
- [ ] 🤖 `twitter:card` presente
- [ ] 🤖 `twitter:image` con URL absoluta

---

## 8. Metaetiquetas de Verificación de Motores

Deben estar en el `<head>` de la homepage (o en el layout global, lo que sea más fácil de mantener):

```html
<!-- Bing Webmaster Tools — necesario para acceder a datos de Bing -->
<meta name="msvalidate.01" content="[CÓDIGO-VERIFICACION-BING]" />

<!-- Yandex Webmaster — para datos de tráfico de Yandex -->
<meta name="yandex-verification" content="[CÓDIGO-VERIFICACION-YANDEX]" />

<!-- Google Search Console — también puede ser via DNS o archivo -->
<meta name="google-site-verification" content="[CÓDIGO-VERIFICACION-GOOGLE]" />
```

> Alternativas: verificación por DNS TXT record (más estable), o subir un archivo HTML de verificación.

**Check:**
- [ ] 👁 Google Search Console verificado (meta tag o DNS o archivo)
- [ ] 👁 Bing Webmaster Tools verificado
- [ ] 👁 Yandex Webmaster verificado (si el mercado es relevante)

---

## 9. Breadcrumbs HTML

```html
<!-- Implementación semántica — necesaria para complementar BreadcrumbList schema -->
<nav aria-label="Breadcrumb">
  <ol>
    <li><a href="/">Inicio</a></li>
    <li><a href="/servicios/">Servicios</a></li>
    <li aria-current="page">Desarrollo de Software</li>
  </ol>
</nav>
```

**Check:**
- [ ] 🤖 Breadcrumbs presentes en páginas de nivel 2+ (no en homepage)
- [ ] 👁 Coherentes con la estructura de URL y con `BreadcrumbList` schema

---

## 10. Paginación

Para listados con múltiples páginas (blog, casos de éxito, catálogos):

```html
<!-- En página 2 de /blog/ -->
<link rel="prev" href="https://dominio.com/blog/" />
<link rel="next" href="https://dominio.com/blog/page/3/" />
```

**Check:**
- [ ] 🤖 `rel="prev"` / `rel="next"` en listados paginados
- [ ] 👁 URL canónica de cada ítem apunta a su página individual (no a la página del listado)

---

## 11. Enlazado Interno

**Impacto:** Google, Bing y motores IA descubren contenido y entienden la jerarquía del sitio a través de links internos.

```html
<!-- Correcto — anchor text descriptivo -->
<a href="/servicios/desarrollo-software/">servicios de desarrollo de software a medida</a>

<!-- Incorrecto — anchor text genérico -->
<a href="/servicios/desarrollo-software/">clic aquí</a>
<a href="/servicios/desarrollo-software/">ver más</a>
```

**Check:**
- [ ] 👁 Anchor text descriptivo — no "clic aquí", "ver más", "leer más"
- [ ] 👁 Sin páginas huérfanas: páginas importantes tienen al menos 1 enlace entrante interno
- [ ] 🤖 Todos los `<a>` tienen `href` con URL válida (no `javascript:void(0)` en navegación)
- [ ] 👁 Navegación principal enlaza a todas las secciones estratégicas del sitio

---

## Páginas a Auditar (Sample Mínimo)

| Tipo de Página | Prioridad |
|----------------|-----------|
| Homepage | Alta |
| 3 páginas de servicios principales | Alta |
| 1 página de blog index | Media |
| 2 artículos de blog recientes | Media |
| Página "Sobre nosotros" / "Empresa" | Media |
| Página de contacto | Media |

---

## Output

### Score On-Page: XX/100

### Revisión por Página

| URL | Title | Meta Desc | H1 | Canonical | OG | Score |
|-----|-------|-----------|----|-----------|----|-------|
| / | ✅/⚠️/❌ | ✅/⚠️/❌ | ✅/⚠️/❌ | ✅/⚠️/❌ | ✅/⚠️/❌ | XX/100 |

### Issues por Prioridad

**🔴 Crítico** — titles/metas ausentes, H1 faltante, `noindex` accidental en páginas de negocio
**🟠 Alto** — titles/metas duplicados, canonical incorrecto, `og:image` ausente
**🟡 Medio** — títulos subóptimos, meta descriptions cortas, breadcrumbs faltantes
**🟢 Bajo** — anchor text mejorable, meta Twitter incompleta

---

## Automatización en QA Pipeline

```javascript
// Playwright — checks on-page automatizables

test('Title tag tiene longitud válida', async ({ page }) => {
  await page.goto('/');
  const title = await page.title();
  expect(title.length).toBeGreaterThan(29);
  expect(title.length).toBeLessThanOrEqual(65);
});

test('Meta description presente y no vacía', async ({ page }) => {
  await page.goto('/');
  const metaDesc = await page.locator('meta[name="description"]').getAttribute('content');
  expect(metaDesc).not.toBeNull();
  expect(metaDesc!.trim().length).toBeGreaterThan(50);
});

test('Exactamente un H1 por página', async ({ page }) => {
  const paginas = ['/', '/servicios/', '/contacto/'];
  for (const url of paginas) {
    await page.goto(url);
    const h1Count = await page.locator('h1').count();
    expect(h1Count, `${url} debe tener exactamente 1 H1`).toBe(1);
  }
});

test('Canonical tiene URL absoluta', async ({ page }) => {
  await page.goto('/servicios/');
  const canonical = await page.locator('link[rel="canonical"]').getAttribute('href');
  expect(canonical).toMatch(/^https?:\/\//);
});

test('og:image tiene URL absoluta', async ({ page }) => {
  await page.goto('/');
  const ogImage = await page.locator('meta[property="og:image"]').getAttribute('content');
  expect(ogImage).toMatch(/^https:\/\//);
});
```

---

## Integración con Otros Skills

| Necesidad | Skill |
|-----------|-------|
| `BreadcrumbList` schema coherente con HTML | `/seo-schema` |
| Canonical coherente entre HTML y JS | `/seo-technical` |
| `og:image` optimizada | `/seo-images` |
| `hreflang` coherente con canonical | `/seo-hreflang` |
