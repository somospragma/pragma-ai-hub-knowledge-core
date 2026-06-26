---
id: calidad-seo-performance
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Auditoría de rendimiento agnóstica de tecnología: Core Web Vitals (LCP, INP, CLS), TTFB, HTTP/2 y HTTP/3, compresión, caché, fuentes web, scripts de terceros, resource hints y presupuesto de rendimiento para CI/CD. Válido para cualquier stack tecnológico y cualquier motor de búsqueda. Usar cuando se mencione 'velocidad', 'Core Web Vitals', 'LCP', 'INP', 'CLS', 'PageSpeed', 'Lighthouse', 'performance' o 'tiempo de carga'."
tags: [seo, web, performance, core-web-vitals]
---

# Performance SEO — Rendimiento Web y Core Web Vitals

## Cobertura Multi-Motor

El rendimiento es factor de ranking **explícito** en múltiples motores:

| Motor | Señal de rendimiento |
|-------|---------------------|
| Google | Core Web Vitals (LCP, INP, CLS) — ranking factor oficial desde 2021 |
| Bing | "Slow page loading" es factor de penalización explícito en Bing Guidelines |
| Yandex | "Page Speed" como señal de calidad |
| Perplexity/ChatGPT | Priorizan páginas que cargan correctamente y sin errores |

---

## Core Web Vitals — Umbrales Actuales

Google usa el **percentil 75 de usuarios reales** (datos CrUX), no datos de laboratorio.
LCP e INP son ahora **Baseline Newly Available** (diciembre 2025) — soportados en todos los navegadores modernos.

| Métrica | Bueno | Necesita Mejora | Malo | Evaluación |
|---------|-------|-----------------|------|------------|
| **LCP** (Largest Contentful Paint) | <2.5s | 2.5–4.0s | >4.0s | 75th percentil campo |
| **INP** (Interaction to Next Paint) | <200ms | 200–500ms | >500ms | 75th percentil campo |
| **CLS** (Cumulative Layout Shift) | <0.1 | 0.1–0.25 | >0.25 | 75th percentil campo |
| **TTFB** (Time to First Byte) | <800ms | 800–1800ms | >1800ms | Tiempo respuesta servidor |

> **INP reemplazó FID el 12 de marzo de 2024.** FID fue completamente eliminado de todas las herramientas (CrUX, PageSpeed Insights, Lighthouse) en septiembre 2024. No referenciar FID en ningún reporte o código.

> **Dato 2025:** 85.6% de los sitios tienen buen INP, 67.6% buen LCP. LCP sigue siendo la métrica más difícil de optimizar.

---

## 1. LCP — Largest Contentful Paint

### Identificar el Elemento LCP

El elemento LCP es típicamente:
- Imagen hero (`<img>` o CSS `background-image`)
- Texto H1 o párrafo introductorio grande
- Video thumbnail

Herramienta: Chrome DevTools → Performance → LCP marker

### Checklist LCP

- [ ] 🤖 Imagen LCP con `loading="eager"` (o sin `loading`) — NUNCA `loading="lazy"` en imagen LCP
- [ ] 🤖 Imagen LCP con `fetchpriority="high"` en el `<img>`
- [ ] 🤖 `<link rel="preload">` para la imagen LCP en el `<head>`:
  ```html
  <link rel="preload" as="image" href="/assets/hero.webp" fetchpriority="high" />
  ```
- [ ] 🤖 Imagen LCP con URL descubrible en HTML inicial — NO usando `data-src` (no crawlable por Googlebot)
- [ ] 🤖 Imagen LCP en formato WebP o AVIF (no JPEG de >150KB)
- [ ] 👁 CDN configurado y sirviendo la imagen LCP desde el edge más cercano
- [ ] 👁 Si LCP es texto: fuente web cargada sin bloquear render

### Patrón HTML Correcto para LCP

```html
<head>
  <!-- Preload en el <head> — descubierto inmediatamente -->
  <link
    rel="preload"
    as="image"
    href="/assets/hero-imagen.webp"
    imagesrcset="/assets/hero-400.webp 400w, /assets/hero-800.webp 800w, /assets/hero-1440.webp 1440w"
    imagesizes="100vw"
    fetchpriority="high"
  />
</head>
<body>
  <!-- Imagen LCP: eager, fetchpriority alto, dimensiones explícitas -->
  <img
    src="/assets/hero-imagen.webp"
    srcset="/assets/hero-400.webp 400w, /assets/hero-800.webp 800w, /assets/hero-1440.webp 1440w"
    sizes="100vw"
    alt="[Descripción del hero]"
    width="1440"
    height="600"
    loading="eager"
    fetchpriority="high"
  />
</body>
```

---

## 2. INP — Interaction to Next Paint

### Qué Mide

Tiempo desde que el usuario interactúa (clic, tap, teclado) hasta que el navegador muestra la respuesta visual. El 85.6% de sitios tienen buen INP en 2025.

### Causas de INP Alto

- Event handlers con trabajo síncrono pesado en el main thread
- Long Tasks (>50ms) bloqueando el main thread
- Heavy hydration en frameworks (React, Vue, Angular, Svelte)
- Scripts de terceros ejecutándose en el main thread
- Animaciones CSS usando propiedades que causan relayout

### Checklist INP

- [ ] 🤖 Sin Long Tasks >200ms en Performance Profiler (Chrome DevTools)
- [ ] 🤖 Animaciones CSS usando solo `transform` y `opacity` (no `top`, `left`, `width`, `height`)
- [ ] 👁 Scripts de terceros cargados con `async` — no bloquean main thread
- [ ] 👁 Hydration de framework: no hidrata todo en el primer render (lazy hydration donde sea posible)

---

## 3. CLS — Cumulative Layout Shift

### Causas de CLS

- Imágenes sin `width`/`height` explícitos
- Fuentes web sin `font-display: swap` o `optional`
- Contenido inyectado dinámicamente sobre contenido existente
- Iframes sin dimensiones fijas
- Banners o pop-ups que empujan contenido hacia abajo

### Checklist CLS

- [ ] 🤖 Todos los `<img>` tienen `width` y `height` definidos
- [ ] 🤖 Todos los `<video>` e `<iframe>` tienen dimensiones fijas o usan aspect-ratio CSS
- [ ] 🤖 Fuentes web con `font-display: swap` o `font-display: optional`
- [ ] 👁 Sin contenido inyectado sobre contenido existente (banners, modales, cookiebars)
- [ ] 👁 Cookiebar/consent banner: reserva espacio o aparece como overlay, no empujando contenido

```css
/* Reservar aspect-ratio para imágenes responsivas — previene CLS */
img {
  aspect-ratio: attr(width) / attr(height);
  width: 100%;
  height: auto;
}

/* Fuente web sin FOIT/CLS */
@font-face {
  font-family: 'NombreFuente';
  src: url('/fonts/fuente.woff2') format('woff2');
  font-display: swap;
}
```

---

## 4. TTFB — Time to First Byte

Tiempo hasta que el navegador recibe el primer byte de la respuesta del servidor. Señal de rendimiento del servidor y de la red.

### Checklist TTFB

- [ ] 🤖 TTFB <800ms en PageSpeed Insights (datos de campo)
- [ ] 👁 CDN configurado para servir HTML desde el edge (Edge Side Rendering o caché HTML)
- [ ] 👁 Servidor de base de datos en la misma región que el servidor web
- [ ] 👁 Sin N+1 queries en el backend que aumenten el tiempo de respuesta
- [ ] 👁 HTTP/2 o HTTP/3 habilitado en el servidor

---

## 5. HTTP/2 y HTTP/3

**HTTP/2** multiplexea múltiples requests sobre una sola conexión — reduce drásticamente la latencia en sitios con muchos recursos.
**HTTP/3** (sobre QUIC) mejora aún más en redes con pérdida de paquetes (mobile, WiFi pública).

**Verificar:**
```bash
# Verificar versión HTTP
curl -I --http2 https://dominio.com/
# Buscar en la respuesta: HTTP/2 (o HTTP/3)

# Alternativa: Chrome DevTools → Network → Protocol column
```

- [ ] 🤖 HTTP/2 habilitado (mínimo recomendado)
- [ ] 👁 HTTP/3 habilitado (mejora especialmente en mobile)

---

## 6. Compresión de Respuestas

```bash
# Verificar compresión Brotli
curl -H "Accept-Encoding: br" -I https://dominio.com/ | grep content-encoding
# Esperado: content-encoding: br

# Verificar Gzip como fallback
curl -H "Accept-Encoding: gzip" -I https://dominio.com/ | grep content-encoding
# Esperado: content-encoding: gzip
```

- [ ] 🤖 Brotli habilitado para HTML, CSS, JS, SVG, JSON
- [ ] 🤖 Gzip como fallback para navegadores sin soporte Brotli
- [ ] 👁 No comprimir imágenes ya comprimidas (WebP, AVIF, JPEG)

---

## 7. Caché HTTP

Estrategia de caché correcta por tipo de recurso:

| Tipo de Recurso | `Cache-Control` Recomendado | Justificación |
|-----------------|----------------------------|---------------|
| HTML | `no-cache, must-revalidate` | El HTML cambia frecuentemente |
| CSS/JS con hash | `max-age=31536000, immutable` | Hash cambia con cada build |
| CSS/JS sin hash | `max-age=86400` | Caché corta — puede cambiar |
| Imágenes estáticas | `max-age=2592000, stale-while-revalidate=86400` | Cambios poco frecuentes |
| Fuentes web | `max-age=31536000, immutable` | Rara vez cambian |
| API responses | `no-store` o corto | Depende del contenido |

```bash
# Verificar headers de caché
curl -I https://dominio.com/assets/main.css | grep -i cache-control
```

- [ ] 🤖 Assets con hash en nombre de archivo tienen caché de 1 año (`immutable`)
- [ ] 🤖 HTML tiene caché corta o `no-cache`
- [ ] 🤖 Fuentes tienen caché larga

---

## 8. Fuentes Web — FOIT y CLS

El **FOIT** (Flash of Invisible Text) y el **FOUT** (Flash of Unstyled Text) impactan negativamente la experiencia percibida y pueden causar CLS.

### Checklist Fuentes

- [ ] 🤖 `font-display: swap` en todos los `@font-face` (evita FOIT)
- [ ] 🤖 `<link rel="preload">` para fuentes críticas (above-the-fold):
  ```html
  <link
    rel="preload"
    href="/fonts/fuente-regular.woff2"
    as="font"
    type="font/woff2"
    crossorigin
  />
  ```
- [ ] 🤖 Formato `woff2` (mejor compresión, soporte universal moderno)
- [ ] 👁 Usar system font stack como fallback que sea visualmente similar (reduce FOUT)
- [ ] 👁 Limitar el número de fuentes diferentes a ≤3 familias

### Fuentes de Google Fonts — Impacto en TTFB

Si se usan Google Fonts, la conexión externa añade latencia:
```html
<!-- Optimizar con preconnect -->
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
```

**Opción más rápida:** Descargar las fuentes y servirlas desde el mismo dominio.

---

## 9. Scripts de Terceros

Los scripts de analytics, chat, mapas, redes sociales y publicidad frecuentemente degradan INP y LCP.

### Checklist Scripts de Terceros

- [ ] 🤖 Scripts no críticos con `defer` o `async`
- [ ] 👁 Scripts de analytics: `async` (no bloquean el parser)
- [ ] 👁 Scripts de chat/soporte: diferidos hasta primera interacción del usuario
- [ ] 🔬 Auditar impacto en Long Tasks con Chrome DevTools → Performance

### Patrón de Carga Diferida

```html
<!-- async: se descarga sin bloquear, ejecuta cuando está listo -->
<script async src="https://www.googletagmanager.com/gtm.js?id=GTM-XXXX"></script>

<!-- defer: se descarga en paralelo, ejecuta después del HTML -->
<script defer src="/scripts/no-critico.js"></script>
```

```javascript
// Diferir scripts de terceros no críticos hasta primera interacción
window.addEventListener('scroll', loadChatWidget, { once: true });
window.addEventListener('click', loadChatWidget, { once: true });

function loadChatWidget() {
  const script = document.createElement('script');
  script.src = 'https://chat-provider.com/widget.js';
  script.async = true;
  document.head.appendChild(script);
}
```

---

## 10. Resource Hints

```html
<!-- preconnect: establecer conexión TCP/TLS anticipada a dominios críticos -->
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://cdn.ejemplo.com" crossorigin />

<!-- dns-prefetch: resolver DNS anticipadamente (menos agresivo que preconnect) -->
<link rel="dns-prefetch" href="https://www.google-analytics.com" />

<!-- preload: cargar recurso crítico antes de que el parser lo descubra -->
<link rel="preload" href="/fonts/fuente.woff2" as="font" type="font/woff2" crossorigin />
<link rel="preload" href="/assets/hero.webp" as="image" fetchpriority="high" />

<!-- prefetch: cargar en baja prioridad para navegación futura probable -->
<link rel="prefetch" href="/servicios/" />
```

- [ ] 🤖 `preconnect` a dominios de terceros críticos (fonts, CDN, analytics)
- [ ] 🤖 `preload` para imagen LCP y fuentes críticas above-the-fold

---

## 11. Recursos Render-Blocking

CSS y JS que bloquean el render retrasan el LCP y la primera pintura visible.

```html
<!-- CSS crítico inline (above-the-fold) -->
<style>
  /* Solo los estilos necesarios para el contenido visible sin scroll */
  body { margin: 0; font-family: system-ui, sans-serif; }
  .header { ... }
  .hero { ... }
</style>

<!-- CSS no crítico: cargar de forma asíncrona -->
<link
  rel="preload"
  href="/styles/main.css"
  as="style"
  onload="this.onload=null;this.rel='stylesheet'"
/>
<noscript><link rel="stylesheet" href="/styles/main.css" /></noscript>

<!-- JS: siempre defer o async excepto si es absolutamente crítico -->
<script src="/scripts/app.js" defer></script>
```

- [ ] 🤖 Lighthouse: "Eliminate render-blocking resources" → 0 o mínimo
- [ ] 👁 CSS crítico inline si el bundle total supera 14KB (tamaño inicial TCP window)

---

## Presupuesto de Performance para CI/CD

### Configuración `lighthouserc.json` Recomendada

```json
{
  "ci": {
    "collect": {
      "numberOfRuns": 3,
      "settings": {
        "preset": "desktop"
      }
    },
    "assert": {
      "assertions": {
        "categories:performance": ["warn", { "minScore": 0.75 }],
        "categories:seo": ["error", { "minScore": 0.90 }],
        "largest-contentful-paint": ["error", { "maxNumericValue": 4000 }],
        "total-blocking-time": ["warn", { "maxNumericValue": 600 }],
        "cumulative-layout-shift": ["error", { "maxNumericValue": 0.25 }],
        "uses-optimized-images": ["warn", { "minScore": 0 }],
        "render-blocking-resources": ["warn", { "minScore": 0.5 }],
        "uses-long-cache-ttl": ["warn", { "minScore": 0 }],
        "uses-text-compression": ["error", { "minScore": 0 }]
      }
    },
    "upload": {
      "target": "temporary-public-storage"
    }
  }
}
```

### Herramientas de Referencia

| Herramienta | Datos | Cuándo usar | Costo |
|-------------|-------|-------------|-------|
| PageSpeed Insights | Campo (CrUX) + Laboratorio | Referencia principal — datos reales | Gratuita |
| Lighthouse CLI | Laboratorio | CI/CD — detectar regresiones | Open source |
| Chrome DevTools Performance | Laboratorio | Debugging detallado y filmstrip | Gratuita |
| CrUX API | Campo histórico | Tendencias y monitoreo real de usuarios | Gratuita |
| web-vitals JS library | Campo (desde el código) | RUM — monitoreo desde el propio sitio | Open source |

> **Priorizar datos de campo (CrUX) sobre laboratorio.** Lighthouse puede mostrar 90/100 mientras los usuarios reales experimentan LCP >4s en conexiones lentas.

---

## Output

### Score Performance: XX/100

### Core Web Vitals (Datos de Campo — si disponibles)

| Métrica | Valor P75 | Distribución Bueno | Estado |
|---------|-----------|-------------------|--------|
| LCP | Xs | XX% | ✅/⚠️/❌ |
| INP | Xms | XX% | ✅/⚠️/❌ |
| CLS | X.XX | XX% | ✅/⚠️/❌ |
| TTFB | Xms | — | ✅/⚠️/❌ |

### Oportunidades

| Oportunidad | Impacto Estimado | Esfuerzo | Responsable |
|-------------|-----------------|----------|-------------|
| Agregar `fetchpriority="high"` a imagen LCP | Alto (LCP) | Bajo | Frontend |
| Convertir imágenes hero a WebP/AVIF | Alto (LCP) | Medio | Frontend |
| Agregar `width`/`height` a imágenes | Alto (CLS) | Bajo | Frontend |
| Habilitar Brotli en servidor | Medio (TTFB) | Bajo | DevOps |
| HTTP/2 en servidor | Medio (TTFB) | Bajo | DevOps |
| Diferir scripts de terceros | Medio (INP, LCP) | Medio | Frontend |

---

## Integración con Otros Skills

| Necesidad | Skill |
|-----------|-------|
| Imágenes sin dimensiones (CLS) | `/seo-images` |
| Imagen LCP discovery (debe estar en HTML inicial) | `/seo-technical` |
| Fuentes y contraste (font-display) | `/seo-accessibility` |