---
id: calidad-seo-schema
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Detección, validación y generación de datos estructurados (JSON-LD) con cobertura multi-motor: Google Rich Results, Bing, Yahoo, Yandex, Apple y motores de búsqueda potenciados por IA (Perplexity, ChatGPT, Copilot). Schema.org fue creado por Google, Bing, Yahoo y Yandex — funciona en todos. Usar cuando se mencione 'schema', 'datos estructurados', 'JSON-LD', 'rich results', 'marcado estructurado', 'resultados enriquecidos' o 'IA search'."
tags: [seo, web, schema, json-ld, datos-estructurados]
---

# Schema / Datos Estructurados — Multi-Motor

## Por Qué Schema Importa Más que Nunca en 2026

Schema.org fue fundado conjuntamente por **Google, Microsoft (Bing), Yahoo y Yandex** — el vocabulario funciona para todos estos motores simultáneamente.

> Un experimento controlado de Search Engine Land (2025) encontró que solo la página con schema bien implementado apareció en AI Overviews de Google — la página sin schema ni siquiera fue indexada.

**Impacto por motor:**
- **Google:** Rich results (sitelinks, breadcrumbs, artículos, eventos, empleo)
- **Bing/Copilot:** Rich results + alimenta respuestas de Microsoft Copilot AI
- **Yahoo:** Usa índice Bing — mismos beneficios
- **Yandex:** Tiene su propio sistema de rich snippets basado en schema.org
- **Perplexity / ChatGPT Search:** Parsean JSON-LD para entender y citar contenido
- **Apple/Siri:** Applebot parsea schema para Spotlight y Siri Suggestions

---

## Principios de Implementación

1. **Formato:** JSON-LD exclusivamente — preferido por todos los motores principales
2. **Posición:** en el HTML inicial del servidor — NO inyectado solo por JavaScript
3. **Validación:** sin errores antes de publicar
4. **Veracidad:** solo datos reales — sin placeholders en producción
5. **Múltiples tipos:** una página puede tener varios bloques `<script type="application/ld+json">`

```html
<!-- Posición correcta: en <head> o al final de <body>, en HTML servidor-rendered -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  ...
}
</script>
```

---

## Tipos Activos y Recomendados (a junio 2026)

### Organization (Obligatorio — layout global o todas las páginas)

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "[Nombre de la empresa]",
  "url": "https://dominio.com",
  "logo": {
    "@type": "ImageObject",
    "url": "https://dominio.com/assets/logo.png",
    "width": 200,
    "height": 60
  },
  "description": "[Descripción de la empresa en 1-2 oraciones]",
  "foundingDate": "YYYY",
  "address": {
    "@type": "PostalAddress",
    "addressLocality": "[Ciudad]",
    "addressRegion": "[Departamento/Estado]",
    "addressCountry": "CO"
  },
  "contactPoint": {
    "@type": "ContactPoint",
    "contactType": "customer service",
    "url": "https://dominio.com/contacto/"
  },
  "sameAs": [
    "https://www.linkedin.com/company/[empresa]",
    "https://twitter.com/[empresa]",
    "https://github.com/[empresa]"
  ]
}
```

---

### WebSite (Solo en homepage — habilita Sitelinks Search Box)

```json
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "[Nombre del sitio]",
  "url": "https://dominio.com",
  "potentialAction": {
    "@type": "SearchAction",
    "target": {
      "@type": "EntryPoint",
      "urlTemplate": "https://dominio.com/buscar/?q={search_term_string}"
    },
    "query-input": "required name=search_term_string"
  }
}
```

---

### Service (Por cada página de servicio B2B)

```json
{
  "@context": "https://schema.org",
  "@type": "Service",
  "name": "[Nombre del servicio]",
  "description": "[Descripción detallada del servicio]",
  "provider": {
    "@type": "Organization",
    "name": "[Empresa]",
    "url": "https://dominio.com"
  },
  "serviceType": "[Tipo de servicio]",
  "areaServed": [
    {
      "@type": "Country",
      "name": "Colombia"
    }
  ],
  "url": "https://dominio.com/servicios/[nombre-servicio]/"
}
```

---

### BreadcrumbList (En páginas internas — muestra ruta en resultados)

Soportado por Google, Bing, Yandex y parseable por motores IA.

```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Inicio",
      "item": "https://dominio.com/"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "Servicios",
      "item": "https://dominio.com/servicios/"
    },
    {
      "@type": "ListItem",
      "position": 3,
      "name": "[Servicio específico]"
    }
  ]
}
```

---

### Article / BlogPosting (Entradas de blog)

```json
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "[Título del artículo — máx 110 caracteres]",
  "description": "[Descripción breve del artículo]",
  "image": {
    "@type": "ImageObject",
    "url": "https://dominio.com/blog/assets/[imagen].jpg",
    "width": 1200,
    "height": 630
  },
  "author": {
    "@type": "Person",
    "name": "[Nombre del Autor]",
    "url": "https://dominio.com/autores/[slug]/"
  },
  "publisher": {
    "@type": "Organization",
    "name": "[Empresa]",
    "logo": {
      "@type": "ImageObject",
      "url": "https://dominio.com/assets/logo.png"
    }
  },
  "datePublished": "2025-01-15",
  "dateModified": "2025-03-01",
  "url": "https://dominio.com/blog/[slug]/"
}
```

---

### Person + ProfilePage (Páginas de autores — fortalece E-E-A-T)

E-E-A-T (Experience, Expertise, Authoritativeness, Trust) es evaluado por Google, Bing y motores IA.

```json
{
  "@context": "https://schema.org",
  "@type": "ProfilePage",
  "mainEntity": {
    "@type": "Person",
    "name": "[Nombre del Autor]",
    "jobTitle": "[Cargo]",
    "worksFor": {
      "@type": "Organization",
      "name": "[Empresa]"
    },
    "url": "https://dominio.com/autores/[slug]/",
    "sameAs": [
      "https://www.linkedin.com/in/[perfil]"
    ]
  }
}
```

---

### Event (Webinars, conferencias, meetups)

```json
{
  "@context": "https://schema.org",
  "@type": "Event",
  "name": "[Nombre del evento]",
  "description": "[Descripción del evento]",
  "startDate": "2025-09-15T18:00:00-05:00",
  "endDate": "2025-09-15T20:00:00-05:00",
  "eventStatus": "https://schema.org/EventScheduled",
  "eventAttendanceMode": "https://schema.org/OnlineEventAttendanceMode",
  "location": {
    "@type": "VirtualLocation",
    "url": "https://dominio.com/eventos/[slug]/"
  },
  "organizer": {
    "@type": "Organization",
    "name": "[Empresa]",
    "url": "https://dominio.com"
  }
}
```

---

### JobPosting (Si el sitio publica vacantes)

```json
{
  "@context": "https://schema.org",
  "@type": "JobPosting",
  "title": "[Título del cargo]",
  "description": "[Descripción detallada del puesto]",
  "datePosted": "2025-06-01",
  "validThrough": "2025-07-31",
  "hiringOrganization": {
    "@type": "Organization",
    "name": "[Empresa]",
    "url": "https://dominio.com"
  },
  "jobLocation": {
    "@type": "Place",
    "address": {
      "@type": "PostalAddress",
      "addressLocality": "[Ciudad]",
      "addressCountry": "CO"
    }
  },
  "employmentType": "FULL_TIME",
  "workHours": "Lunes a Viernes, 8am-6pm"
}
```

---

### SoftwareApplication (Para productos de software propios)

```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "[Nombre del software]",
  "operatingSystem": "Web",
  "applicationCategory": "BusinessApplication",
  "description": "[Descripción del software]",
  "url": "https://dominio.com/producto/[nombre]/",
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "USD"
  }
}
```

---

### QAPage (Páginas de preguntas y respuestas)

> **FAQ vs QAPage:** FAQ rich results fueron eliminados de Google el 7 de mayo de 2026.
> `QAPage` es distinto — es para páginas de tipo Q&A con respuestas de la comunidad.
> Bing y Yahoo (basado en Bing) aún pueden mostrar rich results para ambos tipos.

```json
{
  "@context": "https://schema.org",
  "@type": "QAPage",
  "mainEntity": {
    "@type": "Question",
    "name": "[Pregunta principal de la página]",
    "acceptedAnswer": {
      "@type": "Answer",
      "text": "[Respuesta directa y completa]"
    }
  }
}
```

---

## Estado de Tipos por Motor (junio 2026)

### ✅ Activos en Google — implementar libremente

Organization, WebSite, Service, BreadcrumbList, Article, NewsArticle, BlogPosting, Review, AggregateRating, Person, ProfilePage, Event, JobPosting, SoftwareApplication, WebApplication, Product, Offer, VideoObject, ImageObject, Course

### ⚠️ Eliminados de Google Rich Results — pero válidos en Bing/Yahoo/Yandex

| Tipo | Estado en Google | Estado en Bing/Yandex |
|------|-----------------|----------------------|
| `FAQPage` | ❌ Eliminado el 7 mayo 2026 | ✅ Puede mostrar rich results |
| `HowTo` | ❌ Eliminado sept 2023 | ✅ Bing puede mostrarlos |
| `Dataset` | ❌ Eliminado de rich results | ✅ Parseable para AI search |
| `QAPage` | ⚠️ Sin rich result propio | ✅ Bing soporta |

> **Decisión:** Mantener `FAQPage` y `HowTo` si hay beneficio para Bing/Yandex y no genera confusión. Solo evitar para Google si busca evitar falsos positivos en GSC.

### ❌ Completamente deprecados — no implementar en ningún motor

| Tipo | Motivo |
|------|--------|
| `SpecialAnnouncement` | Deprecado julio 2025 |
| `CourseInfo` | Retirado junio 2025 |
| `ClaimReview` | Retirado junio 2025 |
| `EstimatedSalary` | Retirado |
| `LearningVideo` | Retirado junio 2025 |
| `VehicleListing` | Retirado junio 2025 |
| `Practice Problem` | Retirado tarde 2025 |

---

## Baidu (Mercado Chino)

Baidu no usa schema.org — tiene su propio vocabulario llamado **"Baidu Open Platform"**.
Si el sitio apunta al mercado chino, se requiere implementación separada específica para Baidu.
Para la mayoría de sitios fuera de China: no es relevante.

---

## Schema para Visibilidad en IA (AEO/GEO)

Los motores de búsqueda potenciados por IA (Perplexity, ChatGPT Search, Copilot, Google AI Overviews) parsean JSON-LD para entender y citar contenido de forma estructurada.

**Impacto de schema en IA search:**
- `Organization` con `sameAs` → el motor IA puede verificar la identidad de la empresa
- `Article` con `author` y `datePublished` → el motor IA puede citar el artículo como fuente verificable
- `Service` con `description` → facilita que el motor IA entienda la propuesta de valor
- `FAQPage` (si está implementado) → aún parseable por modelos de IA aunque no genere rich results en Google

---

## Validación

### Herramientas

| Herramienta | Uso | URL |
|-------------|-----|-----|
| Google Rich Results Test | Validar para rich results Google | `search.google.com/test/rich-results` |
| Schema.org Validator | Validar sintaxis schema | `validator.schema.org` |
| Bing Markup Validator | Validar para Bing | Bing Webmaster Tools → Markup Validator |
| JSON-LD Playground | Debug de JSON-LD | `json-ld.org/playground/` |

### Errores Frecuentes

| Error | Corrección |
|-------|-----------|
| `@context` ausente | Agregar `"@context": "https://schema.org"` |
| URL relativa en campo `url` | Usar URL absoluta con `https://` |
| Fecha no en ISO 8601 | `YYYY-MM-DD` o `YYYY-MM-DDTHH:MM:SS±HH:MM` |
| Texto placeholder en producción | Reemplazar `[...]` con datos reales |
| Schema inyectado solo por JS | Mover al HTML servidor-rendered |
| `FAQPage` generando error GSC en Google | Normal si se eliminó el soporte — no es error crítico para otros motores |

---

## Checklist de Auditoría

- [ ] 🤖 `Organization` presente en todas las páginas (o al menos homepage)
- [ ] 🤖 `WebSite` con `SearchAction` en homepage
- [ ] 🤖 `BreadcrumbList` en páginas internas
- [ ] 🤖 `Article`/`BlogPosting` en entradas de blog
- [ ] 🤖 `Person` + `ProfilePage` en páginas de autores
- [ ] 🤖 Todos los JSON-LD validan sin errores en Rich Results Test
- [ ] 🤖 JSON-LD presente en HTML inicial (verificar con `curl`)
- [ ] 🤖 Sin tipos deprecados o removidos
- [ ] 👁 Propiedades opcionales importantes incluidas (imagen, fecha, autor)
- [ ] 👁 URLs absolutas en todos los campos de URL

---

## Output

### Reporte de Schema

| Página | Tipos Detectados | Completitud | Válido Google | Válido Bing | Issues |
|--------|-----------------|-------------|---------------|-------------|--------|
| / | Organization, WebSite | XX% | ✅/⚠️/❌ | ✅/⚠️/❌ | — |
| /servicios/[slug]/ | Service, BreadcrumbList | XX% | ✅/⚠️/❌ | ✅/⚠️/❌ | — |
| /blog/[slug]/ | BlogPosting, Person | XX% | ✅/⚠️/❌ | ✅/⚠️/❌ | — |

---

## Automatización en QA Pipeline

```javascript
// Playwright: verificar que JSON-LD existe en HTML inicial
test('Homepage tiene JSON-LD de Organization', async ({ page }) => {
  await page.goto('/');
  const ldJson = await page.locator('script[type="application/ld+json"]').all();
  expect(ldJson.length).toBeGreaterThan(0);

  // Parsear y verificar tipo
  const firstScript = await ldJson[0].textContent();
  const schema = JSON.parse(firstScript);
  expect(['Organization', 'WebSite'].some(t =>
    JSON.stringify(schema).includes(t)
  )).toBeTruthy();
});

// Verificar que JSON-LD está en HTML inicial (no solo en DOM post-JS)
test('JSON-LD existe en HTML inicial de servidor', async ({ request }) => {
  const response = await request.get('/');
  const html = await response.text();
  expect(html).toContain('application/ld+json');
});
```

---

## Integración con Otros Skills

| Necesidad | Skill |
|-----------|-------|
| Schema en HTML inicial (JS rendering) | `/seo-technical` |
| Imagen del artículo optimizada | `/seo-images` |
| Breadcrumbs HTML coherentes con schema | `/seo-on-page` |