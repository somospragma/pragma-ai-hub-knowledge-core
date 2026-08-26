---
id: calidad-seo-audit-workflow
version: 1.0.0
scope: chapter
type: workflow
chapter: calidad
applies_to_stacks: [playwright]
description: "Workflow de auditoria SEO tecnica agnostica de stack para pruebas web (aplica a Playwright y futuros stacks web del chapter calidad)."
tags: [seo, web, workflow, auditoria]
---

# Workflow SEO Técnico — Auditoría de Calidad Frontend/Backend
## Sistema agnóstico de tecnología para pipelines de calidad

> **Propósito:** Definir los lineamientos completos para auditar características SEO corregibles
> desde desarrollo. Funciona con cualquier stack tecnológico: React, Vue, Angular, Svelte,
> WordPress, Webflow, Shopify, Astro, Django, Laravel, o HTML estático.
>
> **Alcance:** Solo características evaluables y corregibles desde código fuente o configuración
> de servidor. No incluye estrategia de contenido, construcción de enlaces ni análisis competitivo.

---

## 1. Principio de Agnósticismo Tecnológico

Todos los checks de este workflow se definen en términos de **output observable**, no de implementación interna:

| En lugar de... | Se evalúa... |
|----------------|--------------|
| "Configura `next.config.js`" | "El servidor responde con header `Cache-Control: max-age=31536000`" |
| "Usa el componente `<Image>`" | "El `<img>` tiene `width`, `height` y `loading` definidos" |
| "Configura `app/sitemap.js`" | "GET `/sitemap.xml` retorna HTTP 200 con XML válido" |

Cualquier tecnología que produzca el output correcto pasa la auditoría.

---

## 2. Dimensiones de Auditoría y Pesos

### Sistema de Puntuación (0–100)

| Dimensión | Peso | Skill |
|-----------|------|-------|
| SEO Técnico | 25% | `/seo-technical` |
| On-Page SEO | 20% | `/seo-on-page` |
| Performance / Core Web Vitals | 20% | `/seo-performance` |
| Schema / Datos Estructurados | 12% | `/seo-schema` |
| Imágenes | 8% | `/seo-images` |
| Accesibilidad / HTML Semántico | 8% | `/seo-accessibility` |
| Sitemap | 4% | `/seo-sitemap` |
| Hreflang / Internacionalización | 3% | `/seo-hreflang` |
| **Total** | **100%** | |

### Escala de Salud SEO

| Rango | Nivel | Acción recomendada |
|-------|-------|---------------------|
| 90–100 | Excelente | Monitoreo preventivo |
| 75–89 | Bueno | Optimización de detalles |
| 60–74 | Aceptable | Plan de mejora en 30 días |
| 45–59 | Deficiente | Sprint de corrección — próximo ciclo |
| 0–44 | Crítico | Bloqueo técnico activo — intervención inmediata |

### Niveles de Prioridad

| Prioridad | Definición | SLA de corrección |
|-----------|------------|-------------------|
| 🔴 Crítico | Bloquea indexación o penaliza activamente | <48 horas |
| 🟠 Alto | Impacta significativamente rankings o usuarios | 1 semana |
| 🟡 Medio | Oportunidad de optimización | 1 mes |
| 🟢 Bajo | Nice to have | Backlog |

---

## 3. Características de Calidad por Dimensión

### 3.1 SEO Técnico

Infraestructura de rastreo, indexación y seguridad — la base sobre la que todo lo demás funciona.

**Rastreabilidad:**
- `robots.txt` existe, es sintácticamente válido, no bloquea CSS/JS/imágenes críticas
- Profundidad de rastreo: páginas estratégicas accesibles en ≤3 clics desde la homepage
- URLs con parámetros: no generan contenido duplicado no controlado
- Presupuesto de rastreo (crawl budget): sin rutas infinitas por faceted navigation ni calendar pages

**Indexabilidad:**
- Tags `noindex` son intencionales — ninguna página de negocio está accidentalmente bloqueada
- Canonical tags: presentes, autorreferenciales por defecto, sin conflicto con `noindex`
- Contenido duplicado: controlado por canonical o `noindex`, no por robots.txt
- Index bloat: no se indexan páginas de búsqueda interna, páginas de filtros, páginas de error

**Seguridad:**
- HTTPS forzado — toda petición HTTP redirige a HTTPS
- Certificado SSL: válido, no expirado, cubre todos los subdominios usados
- Sin mixed content: todos los recursos (imágenes, scripts, iframes) se cargan por HTTPS
- Headers de seguridad: `HSTS`, `CSP`, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`

**Estructura técnica:**
- URLs descriptivas, con guiones, sin caracteres especiales ni parámetros en URLs de contenido permanente
- Redirects: 301 para cambios permanentes, máximo 1 salto (sin cadenas)
- Trailing slash: consistente en todo el sitio — uno u otro, nunca ambos para la misma URL
- Longitud de URLs: alertar si >100 caracteres

**JavaScript Rendering (crítico para SPAs y frameworks modernos):**
- Contenido principal disponible en HTML inicial de servidor (no solo después de ejecutar JS)
- Canonical en HTML inicial = canonical inyectado por JS (si difieren, Google puede usar cualquiera)
- `noindex` en HTML raw: JS no debe eliminarlo — Google puede respetar el del HTML inicial
- Páginas con error (non-200): no renderizar JS en ellas, los meta tags JS son invisibles para bots
- Datos estructurados críticos en HTML inicial, no solo JS

**Mobile (obligatorio desde julio 2024 — 100% mobile-first indexing):**
- `<meta name="viewport" content="width=device-width, initial-scale=1">`
- Sin scroll horizontal en viewport de 375px
- Fuente base mínimo 16px
- Touch targets mínimo 48×48px con 8px de separación

**Gestión de crawlers IA:**
- Política definida en `robots.txt` para `GPTBot`, `ClaudeBot`, `Google-Extended`, `PerplexityBot`
- `llms.txt`: archivo opcional pero evaluado por Chrome Lighthouse — define cómo los agentes IA deben interactuar con el sitio

**Service Workers:**
- Los Service Workers que hacen cache agresivo pueden entregar HTML cacheado a Googlebot
- Verificar que Googlebot puede ver el contenido actualizado, no versiones obsoletas del cache

---

### 3.2 On-Page SEO

Elementos HTML de cada página que señalizan relevancia y tema a Google.

- Title tag: 50–60 caracteres, keyword primaria incluida, único por página
- Meta description: 140–160 caracteres, único, con CTA implícito
- H1: exactamente uno por página, alineado con la intención de búsqueda
- H2–H6: jerarquía lógica sin saltar niveles, descriptivos
- URL de página: corta, descriptiva, incluye keyword objetivo
- Canonical tag: autorreferencial o correcto, URLs absolutas
- Meta robots: `index, follow` por defecto; `noindex` solo intencional
- Open Graph: `og:title`, `og:description`, `og:image` (1200×630 JPEG/PNG), `og:url`, `og:type`
- Twitter/X Card: `twitter:card`, `twitter:title`, `twitter:description`, `twitter:image`
- Breadcrumbs HTML: en páginas internas, coherentes con URL
- Paginación: `rel="next"` / `rel="prev"` en listados paginados
- Enlazado interno: anchor text descriptivo, sin páginas huérfanas clave

---

### 3.3 Performance / Core Web Vitals

Métricas de ranking oficial desde 2021. Google usa percentil 75 de datos de campo (CrUX).

| Métrica | Bueno | Necesita Mejora | Malo |
|---------|-------|-----------------|------|
| **LCP** | <2.5s | 2.5–4.0s | >4.0s |
| **INP** | <200ms | 200–500ms | >500ms |
| **CLS** | <0.1 | 0.1–0.25 | >0.25 |
| **TTFB** | <800ms | 800–1800ms | >1800ms |

> INP reemplazó FID el 12 de marzo de 2024. FID está completamente eliminado de todas las herramientas desde septiembre 2024. No referenciar FID en ningún reporte.

Aspectos auditables desde desarrollo:
- Imagen LCP con `fetchpriority="high"` y `<link rel="preload">`
- Imagen LCP nunca con `loading="lazy"` — masivamente perjudicial para LCP
- Dimensiones explícitas `width`/`height` en imágenes — previene CLS
- JS y CSS no crítico con `defer`/`async` — elimina render-blocking
- Compresión Brotli o Gzip en servidor
- Cache HTTP con `Cache-Control` apropiado para assets estáticos
- HTTP/2 o HTTP/3 habilitado — multiplexing reduce latencia
- Fuentes web con `font-display: swap` o `optional` — previene FOIT/CLS
- `<link rel="preconnect">` a dominios de terceros críticos
- Scripts de terceros: cargados con `async`, diferidos post-interacción si no son críticos
- Service Workers: cache correcta para no servir versiones obsoletas de assets críticos

---

### 3.4 Schema / Datos Estructurados

JSON-LD en HTML inicial de servidor. Habilita rich results en Google.

Tipos activos y recomendados (a junio 2026):
- `Organization` — señal de identidad de marca
- `WebSite` con `SearchAction` — sitelinks search box
- `Service` — para páginas de servicios B2B
- `BreadcrumbList` — muestra ruta de navegación en resultados
- `Article` / `BlogPosting` — para blog y publicaciones
- `Person` / `ProfilePage` — para páginas de autores
- `Event` — para webinars, conferencias, meetups
- `JobPosting` — para vacantes (si se publican en el sitio)
- `SoftwareApplication` — si hay productos de software propios

**Tipos completamente eliminados de Google Rich Results (nunca implementar):**
- `FAQ` — eliminado de resultados el 7 de mayo de 2026
- `HowTo` — eliminado en septiembre 2023
- `SpecialAnnouncement` — deprecado julio 2025
- `CourseInfo` — retirado junio 2025
- `ClaimReview` — retirado junio 2025
- `EstimatedSalary` — retirado
- `LearningVideo` — retirado junio 2025
- `VehicleListing` — retirado junio 2025
- `Practice Problem` — retirado tarde 2025
- `Dataset` — retirado de rich results tarde 2025

---

### 3.5 Imágenes

Alt text, formatos modernos, peso, dimensiones, loading strategy.

- Alt text descriptivo en todas las imágenes de contenido; `alt=""` en decorativas
- Formato WebP o AVIF por defecto; JPEG/PNG como fallback
- Peso: alerta >150KB, crítico >400KB
- `width` y `height` en todos los `<img>` — previene CLS
- `loading="lazy"` en imágenes below-the-fold
- `loading="eager"` + `fetchpriority="high"` en imagen LCP
- `srcset` y `sizes` para imágenes responsivas
- Nombres de archivo: descriptivos, con guiones, sin caracteres especiales
- `data-src` (lazy load manual con JS): no crawlable por Googlebot — usar `loading="lazy"` nativo
- OG image: 1200×630px, JPEG o PNG (no WebP — scrapers de redes sociales no siempre lo soportan)

---

### 3.6 Sitemap

Mapa XML que guía el rastreo de bots.

- `GET /sitemap.xml` retorna HTTP 200 con XML válido
- Referenciado en `robots.txt`: `Sitemap: https://dominio.com/sitemap.xml`
- Incluye: todas las páginas indexables con HTTP 200
- Excluye: páginas con `noindex`, redirects, errores 4xx/5xx, URLs duplicadas
- `<lastmod>`: fecha real de última modificación del contenido
- Generado automáticamente — nunca mantenido de forma manual
- Sitemap index para sitios con >1.000 páginas
- Variantes con `xhtml:link` si hay hreflang

---

### 3.7 Hreflang / Internacionalización

Señales de idioma y región para sitios multi-mercado. Activar solo si hay variantes reales.

- Implementado en `<head>`, HTTP headers, o sitemap XML
- Autorreferencia: cada página incluye su propio hreflang
- Reciprocidad: si A apunta a B, B debe apuntar a A
- `x-default`: definido para usuarios sin variante específica
- Códigos correctos: ISO 639-1 para idioma, ISO 3166-1 Alpha-2 para región
- URLs absolutas en todos los atributos hreflang
- Cobertura total: todas las páginas del sitio con sus anotaciones

> **Nota 2026:** Google trata hreflang como hints, no señales determinísticas. Los errores de reciprocidad o autorreferencia invalidan el conjunto completo — 31% de sitios internacionales tienen directivas conflictivas.

---

### 3.8 Accesibilidad / HTML Semántico

Señales de calidad de página. WCAG 2.2 es estándar ISO/IEC 40500:2025.

- `<html lang="...">` declarado con código ISO correcto
- Estructura semántica: `<header>`, `<nav>`, `<main>`, `<article>`, `<section>`, `<footer>`
- `<main>`: solo uno por página
- `<nav>`: con `aria-label` único si hay múltiples en la página
- Jerarquía de headings: sin saltar niveles (`h1` → `h3` sin `h2`)
- Contraste mínimo WCAG AA: 4.5:1 para texto normal, 3:1 para texto grande
- Foco visible: `:focus-visible` con outline visible en todos los elementos interactivos
- Skip link: "Ir al contenido principal" como primer elemento del `<body>`
- Formularios: `<label>` asociado a cada input, `aria-required` en campos obligatorios
- Botones vs links: `<button>` para acciones, `<a href>` para navegación
- Imágenes: alt descriptivo, `alt=""` en decorativas (WCAG 2.2 — nuevo criterio de touch targets)

---

## 4. Stack de Herramientas para Auditoría Automatizada

### Herramientas por Categoría

| Categoría | Herramienta | Uso | Costo |
|-----------|-------------|-----|-------|
| Performance + SEO básico | Lighthouse CLI / Lighthouse CI | Auditoría automatizable completa | Open source |
| Accesibilidad | axe-core / axe-playwright | Integración en pruebas E2E | Open source |
| Accesibilidad | Pa11y CLI | CI/CD, soporta axe-core 4.11+ | Open source |
| E2E SEO | Playwright | Meta tags, headings, canonical, hreflang | Open source |
| Performance campo | PageSpeed Insights API | Datos CrUX reales de usuarios | Gratuita |
| Performance laboratorio | Chrome DevTools | Filmstrip, traces, debugging profundo | Gratuita |
| Validación Schema | JSON.parse() en Playwright | Validar JSON-LD sin servicios externos | Open source |
| Headers HTTP | `curl -I` + `grep` | Verificar todos los security headers | Nativa |
| Sitemap | `curl` + `xmllint` | Descarga y validación XML local | Gratuita nativa |
| Hreflang multi-página | Playwright crawler | Auditoría bidireccional completa | Open source |

### Instalación del Toolchain Local

Todo lo necesario para ejecutar una auditoría completa sin herramientas externas de pago:

```bash
# 1. Lighthouse CLI
npm install -g @lhci/cli lighthouse

# 2. Playwright + axe-playwright
npm install --save-dev @playwright/test axe-playwright
npx playwright install chromium

# 3. Pa11y CLI
npm install -g pa11y

# 4. xmllint (para validación local de sitemap)
# macOS:
brew install libxml2
# Ubuntu/Debian:
apt-get install libxml2-utils
# Windows:
# Incluido en Git Bash o disponible via chocolatey: choco install libxml2

# 5. web-vitals (RUM en el propio sitio)
npm install web-vitals
```

### Comandos de Referencia Rápida (sin herramientas externas)

```bash
# --- HTTPS y redirects ---
curl -I http://dominio.com/              # Debe responder 301 → https://

# --- Security headers ---
curl -sI https://dominio.com/ | grep -iE \
  "strict-transport|content-security-policy|x-frame-options|x-content-type-options|referrer-policy|permissions-policy"

# --- robots.txt ---
curl -s https://dominio.com/robots.txt

# --- Sitemap: descarga y validación XML local ---
curl -s https://dominio.com/sitemap.xml -o /tmp/sitemap.xml
xmllint --noout /tmp/sitemap.xml && echo "XML válido" || echo "Error XML"

# --- Ver HTML inicial (sin JS) ---
curl -s https://dominio.com/ | grep -i "<title\|canonical\|noindex\|og:title\|h1"

# --- Simular Googlebot ---
curl -A "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)" \
     -s https://dominio.com/ | grep -i "noindex\|canonical"

# --- Verificar hreflang en HTML fuente ---
curl -s https://dominio.com/servicios/ | grep -oE 'hreflang="[^"]+"'

# --- Comprobar HTTP/2 ---
curl -sI --http2 https://dominio.com/ | grep "HTTP/"

# --- Comprobar compresión Brotli/Gzip ---
curl -sI -H "Accept-Encoding: br, gzip" https://dominio.com/ | grep -i "content-encoding"

# --- Lighthouse CLI (single URL) ---
npx lighthouse https://dominio.com/ \
  --only-categories=performance,seo,accessibility \
  --output json,html \
  --output-path ./lh-report

# --- Pa11y accesibilidad CLI ---
pa11y --standard WCAG2AA https://dominio.com/
```

### Thresholds de CI/CD (Recomendados)

Configuración recomendada para `lighthouserc.json`:

```json
{
  "ci": {
    "assert": {
      "assertions": {
        "categories:performance": ["warn", { "minScore": 0.75 }],
        "categories:seo": ["error", { "minScore": 0.90 }],
        "categories:accessibility": ["error", { "minScore": 0.90 }],
        "categories:best-practices": ["warn", { "minScore": 0.85 }],
        "largest-contentful-paint": ["error", { "maxNumericValue": 4000 }],
        "cumulative-layout-shift": ["error", { "maxNumericValue": 0.25 }],
        "total-blocking-time": ["warn", { "maxNumericValue": 600 }],
        "uses-long-cache-ttl": ["warn", { "minScore": 0 }],
        "render-blocking-resources": ["warn", { "minScore": 0 }]
      }
    }
  }
}
```

### Integración en Pipeline CI (agnóstica)

Patrón válido para cualquier sistema CI (GitHub Actions, GitLab CI, CircleCI, Jenkins, Bitrise):

```
Etapa 1: Build
  → Compilar el proyecto
  → Generar assets estáticos o iniciar servidor

Etapa 2: SEO Quality Gate
  → Ejecutar Lighthouse CI contra la URL de preview/staging
  → Ejecutar axe-core o Pa11y contra páginas críticas
  → Ejecutar pruebas Playwright para meta tags y canonical
  → Fallar el pipeline si score SEO < 90 o score Accesibilidad < 90

Etapa 3: Deploy (solo si Etapa 2 pasa)
```

### Pruebas Playwright para SEO (patrones agnósticos)

```javascript
// Verificar elementos SEO críticos — funciona con cualquier framework
test('Página tiene title tag no vacío y dentro de longitud', async ({ page }) => {
  await page.goto('/');
  const title = await page.title();
  expect(title.length).toBeGreaterThan(10);
  expect(title.length).toBeLessThanOrEqual(60);
});

test('Página tiene exactamente un H1', async ({ page }) => {
  await page.goto('/');
  const h1Count = await page.locator('h1').count();
  expect(h1Count).toBe(1);
});

test('Canonical apunta a sí mismo', async ({ page }) => {
  await page.goto('/servicios/');
  const canonical = await page.locator('link[rel="canonical"]').getAttribute('href');
  expect(canonical).toBe('https://pragma.co/servicios/');
});

test('Imagen LCP no usa loading=lazy', async ({ page }) => {
  await page.goto('/');
  // Identificar imagen hero / primer contenido visual grande
  const heroImg = page.locator('main img').first();
  const loading = await heroImg.getAttribute('loading');
  expect(loading).not.toBe('lazy');
});

test('Todas las imágenes de contenido tienen alt no vacío', async ({ page }) => {
  await page.goto('/');
  const images = await page.locator('img:not([role="presentation"])').all();
  for (const img of images) {
    const alt = await img.getAttribute('alt');
    expect(alt).not.toBeNull();
    expect(alt?.trim()).not.toBe('');
  }
});

test('robots.txt es accesible y no bloquea recursos críticos', async ({ request }) => {
  const response = await request.get('/robots.txt');
  expect(response.status()).toBe(200);
  const text = await response.text();
  expect(text).not.toContain('Disallow: /css');
  expect(text).not.toContain('Disallow: /js');
  expect(text).not.toContain('Disallow: /assets');
});

test('sitemap.xml responde HTTP 200', async ({ request }) => {
  const response = await request.get('/sitemap.xml');
  expect(response.status()).toBe(200);
  const contentType = response.headers()['content-type'];
  expect(contentType).toContain('xml');
});

test('Página responde con headers de seguridad', async ({ request }) => {
  const response = await request.get('/');
  const headers = response.headers();
  expect(headers['strict-transport-security']).toBeDefined();
  expect(headers['x-content-type-options']).toBe('nosniff');
});
```

### Integración axe-core para Accesibilidad

```javascript
// Con Playwright — funciona en cualquier proyecto
const { checkA11y } = require('axe-playwright');

test('Homepage no tiene violaciones axe críticas', async ({ page }) => {
  await page.goto('/');
  await checkA11y(page, null, {
    detailedReport: true,
    runOnly: {
      type: 'tag',
      values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'],
    },
  });
});
```

---

## 5. Proceso de Auditoría Manual

### Fase 0 — Reconocimiento

```
1. Verificar acceso al sitio
2. Identificar stack tecnológico (inspección de HTML, response headers, source maps)
3. Revisar robots.txt
4. Revisar sitemap.xml
5. Verificar variantes de dominio (www, http, subdomains)
6. Ejecutar Lighthouse en modo incógnito para baseline
```

### Fase 1–8 — Una por dimensión

Seguir el skill correspondiente. Comenzar por SEO Técnico — si hay bloqueos de rastreo o indexación, las demás dimensiones son irrelevantes hasta resolverlos.

### Fase 9 — Score y Entregables

```
1. Calcular score ponderado por dimensión
2. Clasificar todos los issues por prioridad
3. Generar ACTION-PLAN.md con tickets concretos
4. Generar AUDIT-REPORT.md con hallazgos y evidencia
```

---

## 6. Entregables

```
audits/<YYYY-MM-DD>/
├── AUDIT-REPORT.md       # Hallazgos completos con evidencia
├── ACTION-PLAN.md        # Tickets de desarrollo priorizados
└── METADATA.md           # Metadatos de sesión
```

### Formato de cada issue en ACTION-PLAN.md

```markdown
## [PRIORIDAD] Título del issue

**Dimensión:** [dimensión SEO]
**Automatizable:** Sí / No / Parcial
**Tool de detección:** Lighthouse / axe / Playwright / Manual
**URL(s) afectada(s):** [URLs]
**Descripción:** Qué está mal y por qué importa
**Output esperado:** Qué debe producir el código para pasar el check
**Impacto esperado:** En qué mejora al corregirse
**Responsable:** Frontend / Backend / DevOps
```

---

## 7. Exclusiones Explícitas

Fuera del scope de este workflow — no generan tickets de desarrollo:

| Excluido | Responsable alternativo |
|----------|------------------------|
| Estrategia de palabras clave | Marketing / SEO Strategist |
| Creación o edición de textos | Copywriter / Editor |
| Link building | Marketing off-page |
| Google Business Profile | Operaciones |
| Análisis de competidores | Estrategia de negocio |
| Calendario editorial | Marketing de contenido |

---

## 8. Frecuencia Recomendada

| Tipo | Frecuencia |
|------|------------|
| Auditoría completa manual | Trimestral |
| Lighthouse CI automatizado | En cada Pull Request |
| axe-core en E2E | En cada PR que toque componentes de UI |
| Revisión de CWV (PageSpeed Insights) | Mensual |
| Verificación post-deploy mayor | Tras cada release a producción |
