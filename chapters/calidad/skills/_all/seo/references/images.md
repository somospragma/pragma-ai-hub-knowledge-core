# SEO Imágenes — Optimización Técnica

## Cobertura Multi-Motor

Las imágenes afectan SEO de forma transversal:

| Aspecto | Motor | Impacto |
|---------|-------|---------|
| Alt text | Google, Bing, Yandex | Señal de relevancia para búsqueda de imágenes + búsqueda web |
| LCP de imagen | Google (CWV ranking factor), Bing | Peso directo en rankings |
| CLS por imágenes | Google (CWV ranking factor) | Peso directo en rankings |
| `og:image` | Todos los motores + redes sociales | Vista previa en resultados y al compartir |
| Nombres de archivo | Google, Bing | Señal de relevancia menor |
| Accesibilidad (alt) | Applebot, AI crawlers | Citabilidad en IA search |

---

## 1. Alt Text

**El atributo `alt` es obligatorio para accesibilidad (WCAG 2.2) y señal SEO.**

### Reglas por Tipo de Imagen

| Tipo | Atributo `alt` | Ejemplo |
|------|----------------|---------|
| Imagen de contenido (foto, ilustración informativa) | Descripción de lo que muestra | `alt="Equipo de desarrollo en sesión de arquitectura"` |
| Imagen decorativa (separador, fondo, ícono sin significado) | Vacío | `alt=""` con `role="presentation"` |
| Logo | Nombre de la empresa | `alt="NombreEmpresa"` |
| Botón/enlace imagen | Destino o acción | `alt="Ir a la página de servicios"` |
| Imagen con texto visible | El mismo texto de la imagen | `alt="Descuento 20% en todos los servicios"` |
| Infografía compleja | Descripción breve + `figcaption` para detalle | `alt="Proceso de desarrollo en 5 fases"` |

```html
<!-- Imagen de contenido — correcto -->
<img src="sesion-arquitectura.webp" alt="Equipo de desarrollo en sesión de diseño de arquitectura cloud" />

<!-- Imagen decorativa — correcto -->
<img src="wave-divider.svg" alt="" role="presentation" />

<!-- Logo — correcto -->
<img src="logo.svg" alt="NombreEmpresa" />

<!-- Incorrecto — alt ausente -->
<img src="foto-equipo.webp" />

<!-- Incorrecto — keyword stuffing -->
<img src="foto.webp" alt="empresa tecnologia software desarrollo medellin colombia" />

<!-- Incorrecto — no descriptivo -->
<img src="foto.webp" alt="imagen" />
```

**Nota Bing:** Bing tiene un motor de búsqueda de imágenes significativo. El alt text es el factor principal de indexación de imágenes en Bing Images.

**Nota AI Search:** Los crawlers de IA (GPTBot, ClaudeBot, PerplexityBot) leen el alt text para entender el contexto visual del contenido al construir respuestas.

**Checks:**
- [ ] 🤖 Sin `<img>` sin atributo `alt` (ni siquiera vacío)
- [ ] 🤖 Imágenes decorativas tienen `alt=""` (no ausente)
- [ ] 👁 Alt text es descriptivo — no genérico, no keyword stuffing
- [ ] 👁 Longitud recomendada: 80–125 caracteres para imágenes informativas

---

## 2. Formatos de Imagen

### Orden de Preferencia

| Formato | Cuándo | Ventajas | Soporte |
|---------|--------|----------|---------|
| **AVIF** | Fotografías y contenido fotorrealista | >50% más ligero que JPEG, HDR support | Chrome 85+, Firefox 93+, Safari 16+ |
| **WebP** | Uso general — formato principal | 30% más ligero que JPEG, lossy + lossless | Todos los navegadores modernos |
| **SVG** | Logos, íconos, ilustraciones vectoriales | Infinitamente escalable, muy liviano | Todos los navegadores |
| **JPEG** | Fallback para WebP/AVIF en legacy | — | Universal |
| **PNG** | Solo si requiere transparencia y SVG no aplica | — | Universal |

> **Nota OG image excepción:** `og:image` debe ser JPEG o PNG — algunos scrapers de redes sociales y motores no soportan WebP para previsualizaciones.

### Implementación con Elemento `<picture>`

Permite servir el formato más moderno con fallback automático — funciona en cualquier framework/CMS:

```html
<picture>
  <!-- AVIF para navegadores compatibles -->
  <source srcset="/assets/imagen.avif" type="image/avif" />
  <!-- WebP para navegadores sin AVIF -->
  <source srcset="/assets/imagen.webp" type="image/webp" />
  <!-- JPEG como fallback universal -->
  <img
    src="/assets/imagen.jpg"
    alt="[Descripción de la imagen]"
    width="800"
    height="450"
    loading="lazy"
  />
</picture>
```

**Checks:**
- [ ] 👁 Imágenes de contenido en WebP o AVIF (o elemento `<picture>` con fallback)
- [ ] 🤖 Sin imágenes PNG usadas como fotografías (reemplazar por JPEG/WebP)
- [ ] 👁 Logos e íconos en SVG cuando sea posible
- [ ] 👁 `og:image` en JPEG o PNG (no WebP)

---

## 3. Peso y Compresión

| Umbral | Estado | Acción |
|--------|--------|--------|
| <100KB | ✅ Óptimo | — |
| 100–200KB | ✅ Aceptable | Opcional: comprimir más |
| 200–400KB | ⚠️ Alto | Comprimir o convertir a WebP/AVIF |
| >400KB | ❌ Crítico | Impacto directo en LCP — corregir |

**Herramientas de compresión (agnósticas de framework):**

| Herramienta | Uso | Integración |
|-------------|-----|-------------|
| Squoosh | Web/CLI — conversión y compresión | Manual o CI |
| Sharp (Node.js) | Procesamiento en build | Webpack, Vite, Astro |
| ImageMagick | CLI universal | Cualquier pipeline |
| libavif / cwebp | Conversión oficial AVIF/WebP | CLI en CI |
| Cloudinary / imgix | CDN con transformación on-the-fly | Cualquier stack via URL params |

**Checks:**
- [ ] 🤖 Lighthouse: "Properly size images" sin warnings
- [ ] 🤖 Lighthouse: "Efficiently encode images" sin warnings
- [ ] 🤖 Lighthouse: "Serve images in next-gen formats" sin warnings

---

## 4. Dimensiones Explícitas — Prevención de CLS

**Siempre** definir `width` y `height` en el HTML. Sin estas dimensiones, el navegador no puede reservar espacio antes de que la imagen cargue → el layout se desplaza → CLS alto.

```html
<!-- Correcto — dimensiones explícitas -->
<img src="diagrama.webp" alt="Diagrama de arquitectura de microservicios" width="800" height="450" />

<!-- Incorrecto — sin dimensiones → CLS -->
<img src="diagrama.webp" alt="Diagrama de arquitectura de microservicios" />
```

Las dimensiones en HTML no fuerzan tamaño fijo en diseño responsivo si el CSS incluye:
```css
img {
  max-width: 100%;
  height: auto;
}
```

**Checks:**
- [ ] 🤖 Todos los `<img>` tienen `width` y `height` definidos
- [ ] 🤖 Lighthouse: "Image elements do not have explicit width and height" = 0 issues
- [ ] 🤖 CLS causado por imágenes = 0

---

## 5. Estrategia de Carga (Loading Strategy)

### Matriz de Decisión

| Posición en página | Atributo `loading` | Atributo `fetchpriority` |
|--------------------|--------------------|-----------------------------|
| Imagen LCP (hero, primera imagen visible) | `loading="eager"` o ausente | `fetchpriority="high"` |
| Above-the-fold pero no LCP | `loading="eager"` | `fetchpriority="low"` |
| Below-the-fold (requiere scroll para ver) | `loading="lazy"` | — |

> **Regla crítica:** NUNCA usar `loading="lazy"` en la imagen LCP. Retrasa la carga hasta que el layout está completo — impacto catastrófico en LCP.

> **Regla crítica:** No usar `data-src` para lazy loading manual con JS — Googlebot NO puede crawlear URLs en `data-src`. Usar siempre `loading="lazy"` nativo.

```html
<!-- Imagen LCP — carga prioritaria -->
<img
  src="/assets/hero.webp"
  alt="[Descripción del hero]"
  width="1440"
  height="600"
  loading="eager"
  fetchpriority="high"
/>

<!-- Imagen below-the-fold — carga diferida -->
<img
  src="/assets/caso-exito.webp"
  alt="[Descripción del caso]"
  width="600"
  height="400"
  loading="lazy"
/>

<!-- INCORRECTO — lazy manual con data-src, Googlebot no puede crawlear -->
<img data-src="/assets/imagen.webp" class="lazy" />
```

**Checks:**
- [ ] 🤖 Imagen LCP no tiene `loading="lazy"`
- [ ] 🤖 Imagen LCP tiene `fetchpriority="high"`
- [ ] 🤖 Imágenes below-the-fold tienen `loading="lazy"`
- [ ] 🤖 Sin uso de `data-src` — solo `loading="lazy"` nativo

---

## 6. Imágenes Responsivas (`srcset` y `sizes`)

Sirve el tamaño correcto según el viewport — evita cargar imágenes de 1440px en un móvil de 375px:

```html
<img
  src="/assets/imagen-800.webp"
  srcset="
    /assets/imagen-400.webp  400w,
    /assets/imagen-800.webp  800w,
    /assets/imagen-1200.webp 1200w,
    /assets/imagen-1600.webp 1600w
  "
  sizes="
    (max-width: 480px) 100vw,
    (max-width: 1024px) 50vw,
    800px
  "
  alt="[Descripción]"
  width="800"
  height="450"
  loading="lazy"
/>
```

**Checks:**
- [ ] 🤖 Lighthouse: "Properly size images" = 0 issues
- [ ] 👁 Imágenes de contenido principal con al menos 3 variantes de tamaño en `srcset`
- [ ] 👁 `sizes` refleja el tamaño visual real en diferentes viewports

---

## 7. Nombres de Archivo

- Descriptivos en minúsculas
- Palabras separadas por guiones
- Sin caracteres especiales, tildes, espacios ni acentos
- Sin nombres genéricos (`img001.jpg`, `photo.png`)

```
✅ equipo-desarrollo-sesion-remota.webp
✅ diagrama-arquitectura-microservicios.svg
❌ IMG_3421.jpg
❌ foto equipo.jpg
❌ image1.png
❌ DSC00123.jpg
```

**Checks:**
- [ ] 👁 Sin nombres genéricos en imágenes de contenido

---

## 8. OG Image (Vista Previa en Redes y Motores)

La imagen Open Graph controla la vista previa al compartir en LinkedIn, WhatsApp, Twitter/X, Facebook, Slack, Teams, Discord, Telegram, iMessage y en rich results de algunos motores.

**Especificaciones:**
- Dimensiones: **1200×630px** (proporción 1.91:1)
- Formato: **JPEG o PNG** — NOT WebP (scrapers no universalmente compatibles)
- Peso: <1MB (recomendado <300KB)
- `alt` para accesibilidad: `<meta property="og:image:alt" content="...">`

```html
<meta property="og:image" content="https://dominio.com/assets/og/pagina-servicio.jpg" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:image:alt" content="[Descripción de la imagen OG]" />
<meta property="og:image:type" content="image/jpeg" />
```

**Checks:**
- [ ] 🤖 `og:image` presente con URL absoluta HTTPS
- [ ] 👁 Imagen es 1200×630 en JPEG o PNG
- [ ] 👁 Una imagen OG por página estratégica (no la misma en todo el sitio)
- [ ] 👁 `og:image:alt` presente

---

## Checklist de Auditoría Completo

### Por Cada Imagen en Páginas de Muestra

- [ ] ¿Tiene atributo `alt`?
- [ ] ¿El `alt` es descriptivo (no genérico, no keyword stuffing)?
- [ ] ¿Está en WebP o AVIF (o `<picture>` con fallback)?
- [ ] ¿Pesa menos de 200KB?
- [ ] ¿Tiene `width` y `height` definidos?
- [ ] ¿Tiene `loading` apropiado (lazy/eager) según posición?
- [ ] ¿La imagen LCP tiene `fetchpriority="high"`?
- [ ] ¿El nombre de archivo es descriptivo?
- [ ] ¿NO usa `data-src` para lazy loading?

### Para la OG Image de Cada Página

- [ ] ¿Está en JPEG o PNG?
- [ ] ¿Es 1200×630?
- [ ] ¿Está referenciada con URL absoluta HTTPS en `og:image`?

---

## Output

### Score Imágenes: XX/100

### Inventario de Issues

| URL Página | Issue | Imágenes Afectadas | Severidad |
|------------|-------|-------------------|-----------|
| / | Alt text faltante | 3 imágenes | 🟠 Alto |
| /servicios/ | JPEG pesado (450KB) | Imagen hero | 🔴 Crítico |

### Issues por Prioridad

**🔴 Crítico** — imagen LCP >400KB, imagen LCP con `loading="lazy"`, imágenes con `data-src`
**🟠 Alto** — imágenes sin `alt`, imágenes sin dimensiones (CLS activo)
**🟡 Medio** — JPEG de >150KB que puede ser WebP, imágenes sin `loading="lazy"` below-fold
**🟢 Bajo** — OG image en WebP (en lugar de JPEG), nombres de archivo no descriptivos

---

## Automatización en QA Pipeline

```javascript
// Playwright — checks de imágenes automatizables

test('Todas las imágenes tienen atributo alt', async ({ page }) => {
  await page.goto('/');
  // Excluir imágenes decorativas que deben tener alt=""
  const imgsSinAlt = await page.locator('img:not([alt])').count();
  expect(imgsSinAlt).toBe(0);
});

test('Imagen LCP no tiene loading=lazy', async ({ page }) => {
  await page.goto('/');
  const heroImg = page.locator('main img, .hero img').first();
  const loading = await heroImg.getAttribute('loading');
  expect(loading).not.toBe('lazy');
});

test('Todas las imágenes tienen width y height', async ({ page }) => {
  await page.goto('/');
  const imgsConDimensiones = await page.locator('img:not([width]):not([height])').count();
  expect(imgsConDimensiones).toBe(0);
});

test('Sin uso de data-src para lazy loading', async ({ page }) => {
  await page.goto('/');
  const dataSrcImgs = await page.locator('img[data-src]').count();
  expect(dataSrcImgs, 'data-src hace imágenes no rastreables por Googlebot').toBe(0);
});
```

---

## Integración con Otros Skills

| Necesidad | Skill |
|-----------|-------|
| LCP — imagen LCP impacta el score | `/seo-performance` |
| CLS — imágenes sin dimensiones | `/seo-performance` |
| Alt text como señal de accesibilidad | `/seo-accessibility` |
| OG image referenciada en meta tags | `/seo-on-page` |
| JSON-LD `ImageObject` en artículos | `/seo-schema` |
