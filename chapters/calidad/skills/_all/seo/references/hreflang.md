# Hreflang / Internacionalización — Multi-Motor

## Cuándo Activar Este Skill

**Activar** si el sitio tiene o planea:
- Variantes por país: `/es/`, `/mx/`, `/pe/`, o subdominios `co.dominio.com`, `mx.dominio.com`
- Versiones en diferente idioma: español + inglés, español + portugués
- Contenido sustancialmente diferente según región

**No activar** si:
- El sitio sirve contenido idéntico a todos los países en el mismo idioma
- En ese caso: documentar como "hreflang no aplica — sitio monolingüe y mono-regional"

---

## Cobertura Multi-Motor

| Motor | Soporte hreflang |
|-------|-----------------|
| Google | ✅ Soportado — tratado como hint (no señal determinística) |
| Bing | ✅ Soportado — procesado de forma similar a Google |
| Yandex | ✅ Soportado — especialmente relevante para variantes `ru`, `ua`, `kz` |
| DuckDuckGo | ✅ Indirecto — usa índice Bing |
| Apple/Siri | ✅ Parsea hreflang para localización |
| AI Search | ✅ Perplexity, ChatGPT Search y otros usan hreflang para entender variantes |

> **Dato 2026 (Search Engine Land):** Google trata hreflang como hints. El 31% de sitios internacionales tienen directivas hreflang conflictivas; el 16% no tienen autorreferencia. Ambos errores invalidan el conjunto completo de anotaciones.

---

## Métodos de Implementación

Se puede usar cualquiera de los tres métodos — o combinarlos. Elegir el que sea más fácil de mantener de forma automática en el stack del proyecto.

### Método 1: `<link>` en `<head>` (Más fácil de verificar)

```html
<head>
  <!-- En la página /servicios/ (versión Colombia) -->
  <link rel="alternate" hreflang="es-CO" href="https://dominio.com/servicios/" />
  <link rel="alternate" hreflang="es-MX" href="https://dominio.com/mx/servicios/" />
  <link rel="alternate" hreflang="es-PE" href="https://dominio.com/pe/servicios/" />
  <link rel="alternate" hreflang="es"    href="https://dominio.com/servicios/" />
  <link rel="alternate" hreflang="x-default" href="https://dominio.com/servicios/" />
</head>
```

### Método 2: HTTP Header (Para PDFs y recursos no-HTML)

```http
Link: <https://dominio.com/servicios/>; rel="alternate"; hreflang="es-CO",
      <https://dominio.com/mx/servicios/>; rel="alternate"; hreflang="es-MX",
      <https://dominio.com/servicios/>; rel="alternate"; hreflang="x-default"
```

### Método 3: Sitemap XML (Más escalable para sitios grandes)

```xml
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <url>
    <loc>https://dominio.com/servicios/</loc>
    <xhtml:link rel="alternate" hreflang="es-CO"    href="https://dominio.com/servicios/" />
    <xhtml:link rel="alternate" hreflang="es-MX"    href="https://dominio.com/mx/servicios/" />
    <xhtml:link rel="alternate" hreflang="x-default" href="https://dominio.com/servicios/" />
  </url>
  <url>
    <loc>https://dominio.com/mx/servicios/</loc>
    <xhtml:link rel="alternate" hreflang="es-CO"    href="https://dominio.com/servicios/" />
    <xhtml:link rel="alternate" hreflang="es-MX"    href="https://dominio.com/mx/servicios/" />
    <xhtml:link rel="alternate" hreflang="x-default" href="https://dominio.com/servicios/" />
  </url>
</urlset>
```

---

## 5 Reglas Críticas

### Regla 1: Autorreferencia Obligatoria

Cada página **debe incluir su propia URL** en las anotaciones hreflang.

```html
<!-- En la página https://dominio.com/servicios/ -->
<link rel="alternate" hreflang="es-CO" href="https://dominio.com/servicios/" />  ← self-reference
<link rel="alternate" hreflang="es-MX" href="https://dominio.com/mx/servicios/" />
<link rel="alternate" hreflang="x-default" href="https://dominio.com/servicios/" />
```

Sin autorreferencia: **Google y Bing ignoran el conjunto completo de anotaciones para esa página.**

---

### Regla 2: Reciprocidad Bidireccional

Si la página A apunta a la página B con hreflang, la página B debe apuntar de vuelta a la página A.

```
dominio.com/servicios/     → apunta a → dominio.com/mx/servicios/ (hreflang="es-MX")
dominio.com/mx/servicios/  → DEBE apuntar a → dominio.com/servicios/ (hreflang="es-CO")
```

Sin reciprocidad: **el enlace hreflang no tiene efecto**. Es el error más común (31% de sitios).

---

### Regla 3: x-default Obligatorio

Define qué versión mostrar a usuarios cuyo idioma/región no tiene variante específica.

```html
<!-- x-default generalmente apunta a la versión principal o a una landing de selección de idioma -->
<link rel="alternate" hreflang="x-default" href="https://dominio.com/" />
```

---

### Regla 4: URLs Absolutas con HTTPS

```html
<!-- Correcto -->
<link rel="alternate" hreflang="es-MX" href="https://dominio.com/mx/servicios/" />

<!-- Incorrecto — URL relativa -->
<link rel="alternate" hreflang="es-MX" href="/mx/servicios/" />

<!-- Incorrecto — HTTP en lugar de HTTPS -->
<link rel="alternate" hreflang="es-MX" href="http://dominio.com/mx/servicios/" />
```

---

### Regla 5: Cobertura Total del Sitio

**Todas** las páginas del sitio deben tener sus anotaciones hreflang — no solo la homepage.
Una página sin hreflang puede ser tratada como contenido duplicado o mostrada en el mercado incorrecto.

→ Por esta razón, el método de sitemap XML es preferido para sitios grandes: garantiza cobertura sistemática.

---

## Códigos de Idioma y Región

| Código | Significado |
|--------|-------------|
| `es` | Español genérico |
| `es-CO` | Español — Colombia |
| `es-MX` | Español — México |
| `es-AR` | Español — Argentina |
| `es-PE` | Español — Perú |
| `es-CL` | Español — Chile |
| `es-EC` | Español — Ecuador |
| `es-VE` | Español — Venezuela |
| `es-ES` | Español — España |
| `en` | Inglés genérico |
| `en-US` | Inglés — Estados Unidos |
| `en-GB` | Inglés — Reino Unido (¡NO `en-UK`!) |
| `pt-BR` | Portugués — Brasil |
| `pt-PT` | Portugués — Portugal |
| `x-default` | Versión por defecto / fallback |

> ⚠️ Error frecuente: usar `en-UK` en lugar de `en-GB`. El código ISO correcto para Reino Unido es `GB`. `en-UK` invalida la anotación completa.

---

## Errores Comunes (y Cómo Evitarlos)

| Error | Consecuencia | Corrección |
|-------|-------------|------------|
| Falta de autorreferencia (16% sitios) | Bot ignora las anotaciones | Incluir la URL propia en hreflang |
| Falta de reciprocidad (31% sitios) | Enlace sin efecto | Verificar que cada par se apunta mutuamente |
| URL relativa | Bot puede interpretar incorrectamente | Usar siempre URL absoluta con `https://` |
| `x-default` ausente | Google no sabe qué mostrar como fallback | Agregar en todas las páginas |
| Código de región incorrecto (`en-UK`) | Anotación inválida | Usar `en-GB` para Reino Unido |
| Cobertura parcial | Páginas sin hreflang = posible contenido duplicado | Implementar en todas las páginas via sitemap |
| Inconsistencia canonical/hreflang | Señales contradictorias para el bot | La URL en `<loc>` del canonical debe coincidir con la URL en hreflang |

---

## Verificación

### Herramientas

| Herramienta | Uso | Costo |
|-------------|-----|-------|
| `curl` | Extrae `hreflang` del HTML fuente, verifica HTTP headers | Gratuita, nativa |
| Playwright | Auditoría multi-página, validación de reciprocidad | Open source |
| Google Search Console | Inspect URL → hreflang procesado por Google | Gratuita (requiere cuenta) |
| Bing Webmaster Tools | Verificar procesamiento de hreflang en Bing | Gratuita (requiere cuenta) |

### Verificación Manual con `curl`

```bash
# Verificar que los <link rel="alternate"> están en el HTML inicial de servidor
curl -s https://dominio.com/servicios/ | grep -oE 'hreflang="[^"]+"'

# Ver si hreflang está en HTTP headers (Método 2 — para PDFs)
curl -I https://dominio.com/documento.pdf | grep -i "link:"

# Verificar autorreferencia — debe aparecer la URL de la misma página
curl -s https://dominio.com/servicios/ | grep -oE 'href="https://dominio\.com/servicios/"'

# Comparar: HTML raw vs DOM renderizado (detectar hreflang inyectado solo por JS)
curl -s https://dominio.com/ | grep "hreflang"
# Si hay diferencia con lo que muestra el navegador → problema de JS rendering
```

### Auditoría Multi-Página con Playwright

El siguiente script reemplaza la necesidad de un crawler externo — audita reciprocidad bidireccional entre múltiples URLs:

```javascript
// hreflang-audit.playwright.js
// Uso: URLS='https://dominio.com/,https://dominio.com/servicios/' npx playwright test hreflang-audit

const URLS_TO_AUDIT = (process.env.URLS || '').split(',').filter(Boolean);

test('Auditoría hreflang: autorreferencia y reciprocidad multi-página', async ({ page }) => {
  const hreflangMap = {};

  // Fase 1: recolectar hreflang de cada URL
  for (const url of URLS_TO_AUDIT) {
    await page.goto(url);
    const tags = await page.locator('link[hreflang]').evaluateAll(
      links => links.map(l => ({ lang: l.getAttribute('hreflang'), href: l.getAttribute('href') }))
    );
    hreflangMap[url] = tags;

    // Verificar autorreferencia
    const selfRef = tags.find(t => t.href === url);
    expect(selfRef, `${url}: falta autorreferencia hreflang`).toBeTruthy();

    // Verificar x-default
    const xDefault = tags.find(t => t.lang === 'x-default');
    if (tags.length > 0) {
      expect(xDefault, `${url}: falta x-default`).toBeTruthy();
    }
  }

  // Fase 2: verificar reciprocidad bidireccional
  for (const [pageUrl, tags] of Object.entries(hreflangMap)) {
    for (const tag of tags) {
      if (tag.lang === 'x-default') continue;
      const targetUrl = tag.href;

      if (hreflangMap[targetUrl]) {
        // Verificar que la URL destino apunta de vuelta
        const reciprocal = hreflangMap[targetUrl].find(t => t.href === pageUrl);
        expect(
          reciprocal,
          `Falta reciprocidad: ${targetUrl} debe apuntar de vuelta a ${pageUrl}`
        ).toBeTruthy();
      }
    }
  }
});
```

---

## Generación Agnóstica (Output Esperado)

El output que cualquier tecnología debe producir:

**En el `<head>` de cada variante de página:**
```html
<link rel="alternate" hreflang="[idioma-REGION]" href="[URL-absoluta-https]" />
<!-- Repetido para cada variante, incluida la propia -->
<link rel="alternate" hreflang="x-default" href="[URL-versión-default]" />
```

**Criterios de validación del output:**
1. La URL de la página actual aparece en al menos uno de los `hreflang`
2. Todas las URLs son absolutas con `https://`
3. `x-default` está presente
4. Los códigos de idioma/región son ISO válidos
5. Cada variante referenciada existe y responde HTTP 200

---

## Output

### Estado Hreflang

| Check | Estado | Detalle |
|-------|--------|---------|
| Hreflang necesario | Sí / No / A determinar | — |
| Método implementado | `<head>` / HTTP header / Sitemap / Ausente | — |
| Autorreferencia en todas las páginas | ✅/⚠️/❌ | N páginas sin self-reference |
| x-default presente | ✅/❌ | — |
| Reciprocidad bidireccional | ✅/⚠️/❌ | N pares con error |
| URLs absolutas con HTTPS | ✅/⚠️/❌ | N URLs relativas |
| Cobertura total del sitio | ✅/⚠️/❌ | XX% de páginas con anotaciones |
| Códigos ISO correctos | ✅/⚠️/❌ | Códigos inválidos encontrados |

---

## Automatización en QA Pipeline

```javascript
// Playwright — verificación básica de hreflang

test('Homepage tiene hreflang si el sitio es multiregional', async ({ page }) => {
  await page.goto('/');
  const hreflangTags = await page.locator('link[hreflang]').count();
  // Si el sitio es multiregional, debe tener al menos 2 tags (self + x-default)
  // Si es monoregional, puede ser 0
  if (hreflangTags > 0) {
    expect(hreflangTags).toBeGreaterThanOrEqual(2);
  }
});

test('hreflang incluye x-default si hay variantes', async ({ page }) => {
  await page.goto('/');
  const hreflangTags = await page.locator('link[hreflang]').count();
  if (hreflangTags > 0) {
    const xDefault = await page.locator('link[hreflang="x-default"]').count();
    expect(xDefault, 'Debe existir x-default cuando hay variantes hreflang').toBe(1);
  }
});

test('URLs en hreflang son absolutas con HTTPS', async ({ page }) => {
  await page.goto('/');
  const hreflangLinks = await page.locator('link[hreflang]').all();
  for (const link of hreflangLinks) {
    const href = await link.getAttribute('href');
    expect(href, `hreflang href debe ser URL absoluta HTTPS`).toMatch(/^https:\/\//);
  }
});

test('Página incluye su propia URL en hreflang (autorreferencia)', async ({ page }) => {
  await page.goto('/servicios/');
  const canonicalUrl = await page.locator('link[rel="canonical"]').getAttribute('href');
  const hreflangHrefs = await page.locator('link[hreflang]').evaluateAll(
    links => links.map(l => l.getAttribute('href'))
  );
  if (hreflangHrefs.length > 0) {
    expect(hreflangHrefs).toContain(canonicalUrl);
  }
});
```

---

## Integración con Otros Skills

| Necesidad | Skill |
|-----------|-------|
| Sitemap con `xhtml:link` para variantes | `/seo-sitemap` |
| Canonical coherente con hreflang | `/seo-technical` |
| `<html lang>` declarado | `/seo-accessibility` |
