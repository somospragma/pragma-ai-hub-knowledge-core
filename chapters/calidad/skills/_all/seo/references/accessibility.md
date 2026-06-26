# Accesibilidad y HTML Semántico — Señales de Calidad SEO

## Por Qué Importa para SEO Multi-Motor

WCAG 2.2 es ahora el estándar **ISO/IEC 40500:2025** — obligatorio bajo la European Accessibility Act (en vigor desde junio 28, 2025) y objeto de litigios en EEUU bajo ADA.

**Impacto en motores de búsqueda:**

| Aspecto | Impacto SEO |
|---------|-------------|
| HTML semántico | Googlebot, Bingbot y crawlers IA entienden mejor la estructura del contenido |
| `<html lang>` | Señal de idioma para Google, Bing, Yandex y motores IA |
| Headings | Estructura temática — todos los motores la usan para entender el contenido |
| Alt text | Ranking en búsqueda de imágenes (Google Images, Bing Images, Yahoo Images) |
| Contraste | Señal de calidad UX — impacto indirecto en métricas de engagement que influyen rankings |
| Foco visible | Señal de calidad de página — impacta métricas de uso de teclado |

> Un estudio de 2025 encontró 40–50% de overlap entre los requisitos de accesibilidad WCAG 2.2 y las mejores prácticas SEO.

---

## 1. Declaración de Idioma

**Impacto:** Señal directa de idioma para todos los motores de búsqueda. Sin `lang`, el motor adivina el idioma — aumenta errores de servir la versión incorrecta a usuarios.

```html
<!-- Correcto — español Colombia -->
<html lang="es-CO">

<!-- Correcto — español genérico -->
<html lang="es">

<!-- Correcto — inglés -->
<html lang="en">

<!-- Incorrecto — ausente -->
<html>

<!-- Fragmentos en otro idioma dentro del contenido -->
<p>La metodología <span lang="en">Agile</span> permite...</p>
```

**Checks:**
- [ ] 🤖 `<html lang="...">` presente con código ISO válido
- [ ] 🤖 Código de idioma coincide con el contenido de la página
- [ ] 👁 Coherente con `hreflang` si está implementado

---

## 2. Estructura Semántica HTML5

Los elementos semánticos reemplazan `<div>` genéricos — le dicen a los bots qué rol tiene cada sección.

### Landmarks Obligatorios

```html
<body>
  <!-- Skip link — primer elemento del body -->
  <a href="#contenido-principal" class="skip-link">Ir al contenido principal</a>

  <header>
    <!-- Logo, navegación principal, breadcrumb -->
    <nav aria-label="Navegación principal">
      <ul>
        <li><a href="/servicios/">Servicios</a></li>
        <li><a href="/blog/">Blog</a></li>
        <li><a href="/contacto/">Contacto</a></li>
      </ul>
    </nav>
  </header>

  <main id="contenido-principal">
    <!-- Todo el contenido principal va aquí — SOLO UN <main> por página -->

    <article>
      <!-- Contenido independiente y autónomo: artículos, casos de éxito -->
      <h1>Título de la Página</h1>
    </article>

    <section aria-labelledby="servicios-heading">
      <!-- Sección temática — solo si tiene su propio heading -->
      <h2 id="servicios-heading">Nuestros Servicios</h2>
    </section>

    <aside aria-label="Contenido relacionado">
      <!-- Contenido secundario relacionado -->
    </aside>
  </main>

  <footer>
    <nav aria-label="Navegación secundaria">...</nav>
  </footer>
</body>
```

### Guía de Elementos Semánticos

| Elemento | Cuándo usar | Error común |
|----------|-------------|-------------|
| `<header>` | Encabezado de página o de `<article>` / `<section>` | Usarlo múltiples veces sin contexto |
| `<nav>` | Grupos de enlaces de navegación | Sin `aria-label` cuando hay múltiples en la página |
| `<main>` | Contenido principal — uno por página | Más de uno por página |
| `<article>` | Contenido independiente (post, caso de éxito, tarjeta) | Usarlo para cualquier `<div>` |
| `<section>` | Sección temática con heading propio | Sin `aria-labelledby` o `aria-label` |
| `<aside>` | Contenido complementario no esencial | Usarlo para popups o publicidad |
| `<footer>` | Pie de página o sección | Múltiples `<footer>` sin contexto |
| `<figure>` + `<figcaption>` | Imagen, diagrama o código con descripción | Olvidar el `<figcaption>` |
| `<time datetime>` | Fechas y horas | Sin atributo `datetime` |

**Checks:**
- [ ] 🤖 Exactamente un `<main>` por página
- [ ] 🤖 `<nav>` con `aria-label` único si hay múltiples navegaciones
- [ ] 🤖 Sin `<div>` usados donde debería ir `<header>`, `<main>`, `<footer>`, `<nav>`
- [ ] 👁 Estructura semántica lógica y coherente con el contenido

---

## 3. Jerarquía de Headings

- [ ] 🤖 Exactamente un `<h1>` por página
- [ ] 🤖 Sin saltos de nivel (`<h1>` → `<h3>` sin `<h2>` intermedio)
- [ ] 👁 Headings descriptivos del contenido de su sección
- [ ] 👁 No usar headings por estilo tipográfico (usar CSS en `<p>` o `<span>`)

```html
<!-- Correcto — jerarquía continua -->
<h1>Servicios de Transformación Digital</h1>
  <h2>Desarrollo de Software</h2>
    <h3>Arquitectura Cloud-Native</h3>
    <h3>APIs y Microservicios</h3>
  <h2>Consultoría Cloud</h2>

<!-- Incorrecto — salto de nivel -->
<h1>Servicios</h1>
<h3>Desarrollo de Software</h3>  <!-- ← falta h2 -->
```

---

## 4. Contraste de Color (WCAG 2.2 AA)

**Requisitos mínimos:**

| Tipo de texto | Relación de contraste mínima |
|---------------|------------------------------|
| Texto normal (<18px regular o <14px bold) | 4.5:1 |
| Texto grande (≥18px regular o ≥14px bold) | 3:1 |
| Elementos de UI activos (bordes de inputs, íconos) | 3:1 |
| Texto decorativo (logos, texto en imagen sin info) | Sin requisito |

**Herramientas:**
```bash
# Chrome DevTools → Inspect Element → Color → ver ratio automático
# WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
# axe DevTools: detecta automáticamente violaciones de contraste
```

**Checks:**
- [ ] 🤖 axe-core: sin violaciones `color-contrast`
- [ ] 👁 Texto sobre imágenes de fondo tiene overlay o suficiente contraste

---

## 5. Foco de Teclado Visible (WCAG 2.2 — Criterio 2.4.11)

WCAG 2.2 añadió el criterio **Focus Appearance (2.4.11)** — el indicador de foco debe ser visible y suficientemente grande.

```css
/* Correcto — foco visible para usuarios de teclado */
:focus-visible {
  outline: 3px solid #0066CC;
  outline-offset: 2px;
}

/* Correcto — ocultar solo para usuarios de mouse */
:focus:not(:focus-visible) {
  outline: none;
}

/* INCORRECTO — elimina el foco para todos */
* { outline: none; }
*:focus { outline: none; }
```

**Checks:**
- [ ] 🤖 axe-core: sin violaciones `focus-visible`
- [ ] 👁 Navegar el sitio solo con Tab/Shift+Tab — todos los elementos interactivos deben recibir foco visible
- [ ] 👁 Sin `outline: none` en `*` o `*:focus` en el CSS global

---

## 6. Skip Link (WCAG 2.4.1)

Permite a usuarios de teclado saltar la navegación repetida en cada página:

```html
<!-- Primer elemento del <body> — antes del <header> -->
<a href="#contenido-principal" class="skip-link">
  Ir al contenido principal
</a>
```

```css
.skip-link {
  position: absolute;
  top: -48px;
  left: 16px;
  padding: 8px 16px;
  background: #000000;
  color: #ffffff;
  border-radius: 4px;
  z-index: 9999;
  text-decoration: none;
  transition: top 0.2s;
}

.skip-link:focus {
  top: 16px;
}
```

**Check:**
- [ ] 🤖 axe-core: audita esto automáticamente como `bypass`
- [ ] 👁 Skip link visible al recibir foco con Tab (primer Tab al cargar la página)

---

## 7. Touch Targets (WCAG 2.2 — Criterio 2.5.8 — NUEVO)

WCAG 2.2 añadió el criterio de tamaño mínimo de targets táctiles:

- Tamaño mínimo: **24×24 CSS pixels** (AA)
- Tamaño recomendado: **44×44 CSS pixels** (para mejor usabilidad)
- Separación: si el target es <44px, debe haber al menos **24px de espacio libre** alrededor

```css
/* Botones con tamaño mínimo garantizado */
.button {
  min-height: 44px;
  min-width: 44px;
  padding: 8px 16px;
}

/* Links inline con área de toque ampliada */
.link-inline {
  padding: 4px 0;
  display: inline-block;
  min-height: 24px;
}
```

**Checks:**
- [ ] 🤖 Lighthouse: "Tap targets are not sized appropriately" = 0 issues
- [ ] 👁 Botones en mobile tienen al menos 44px de alto

---

## 8. Formularios Accesibles

Cada campo de formulario debe tener:
1. `<label>` asociado al `<input>` via `for`/`id` o como padre
2. `aria-required` en campos obligatorios
3. Mensajes de error asociados con `aria-describedby`
4. `autocomplete` en campos estándar (nombre, email, teléfono)

```html
<form>
  <div class="campo">
    <label for="nombre">Nombre completo</label>
    <input
      type="text"
      id="nombre"
      name="nombre"
      required
      aria-required="true"
      autocomplete="name"
    />
  </div>

  <div class="campo">
    <label for="email">
      Correo electrónico
      <span aria-hidden="true">*</span>
    </label>
    <input
      type="email"
      id="email"
      name="email"
      required
      aria-required="true"
      aria-describedby="email-error"
      autocomplete="email"
    />
    <span
      id="email-error"
      role="alert"
      aria-live="polite"
      class="error-message"
    ></span>
  </div>

  <button type="submit">Enviar mensaje</button>
</form>
```

**Checks:**
- [ ] 🤖 axe-core: sin violaciones `label` o `form-field-multiple-labels`
- [ ] 🤖 axe-core: sin violaciones `autocomplete-valid`
- [ ] 👁 Mensajes de error son descriptivos (no solo "Campo requerido")
- [ ] 👁 Errores se asocian al campo con `aria-describedby`

---

## 9. Botones vs Links

| Elemento | Cuándo | Error |
|----------|--------|-------|
| `<a href="...">` | Navegar a otra URL | Usarlo para acciones sin href real |
| `<button>` | Ejecutar acción (enviar, abrir modal, toggle) | Usar `<div>` o `<span>` en lugar de `<button>` |
| `<button type="button">` | Acción que no envía formulario | — |

```html
<!-- Correcto -->
<a href="/servicios/">Ver nuestros servicios</a>
<button type="button" aria-expanded="false" aria-controls="menu">Abrir menú</button>

<!-- Incorrecto — link sin href usado como botón -->
<a onclick="openModal()">Ver más</a>

<!-- Incorrecto — div no es interactivo para teclado -->
<div onclick="toggleMenu()">Menú</div>
```

**Checks:**
- [ ] 🤖 axe-core: sin violaciones `interactive-supports-focus`
- [ ] 👁 Sin `<div>` u `<span>` con `onclick` usados como botones

---

## 10. Imágenes (Complemento de `/seo-images`)

Desde la perspectiva de accesibilidad:
- Imágenes informativas: `alt` que transmite el mismo significado visual
- Imágenes decorativas: `alt=""` AND `role="presentation"`
- Imágenes complejas (infografías): `alt` breve + `<figcaption>` extendido
- Íconos interactivos: `aria-label` si no hay texto visible

```html
<!-- Infografía con descripción completa -->
<figure>
  <img
    src="proceso.webp"
    alt="Proceso de desarrollo de Pragma en 5 fases"
    aria-describedby="proceso-descripcion"
    width="800"
    height="500"
  />
  <figcaption id="proceso-descripcion">
    El proceso comienza con Discovery (2 semanas), continúa con Diseño de
    Arquitectura (1 semana), Desarrollo Iterativo (N sprints de 2 semanas
    cada uno), QA Continuo integrado, y culmina con Entrega y Transición.
  </figcaption>
</figure>

<!-- Ícono interactivo sin texto visible -->
<button type="button" aria-label="Cerrar modal">
  <svg aria-hidden="true" focusable="false">...</svg>
</button>
```

---

## 11. Tablas de Datos (No Layout)

```html
<table>
  <caption>Comparativa de tecnologías por tipo de proyecto</caption>
  <thead>
    <tr>
      <th scope="col">Tecnología</th>
      <th scope="col">Ideal para</th>
      <th scope="col">Escalabilidad</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">Node.js</th>
      <td>APIs en tiempo real</td>
      <td>Alta</td>
    </tr>
  </tbody>
</table>
```

- [ ] 🤖 axe-core: sin violaciones `td-headers-attr` o `th-has-data-cells`
- [ ] 👁 Sin tablas usadas para layout visual

---

## Herramientas de Auditoría Automatizada

### axe-core (Recomendado para CI/CD)

axe-core detecta en promedio el 57% de las violaciones WCAG automáticamente.

```javascript
// Integración con Playwright
const { injectAxe, checkA11y } = require('axe-playwright');

test('Homepage no tiene violaciones axe WCAG 2.2 AA', async ({ page }) => {
  await page.goto('/');
  await injectAxe(page);
  await checkA11y(page, null, {
    runOnly: {
      type: 'tag',
      values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'],
    },
    detailedReport: true,
    detailedReportOptions: { html: true },
  });
});

// Con jest-axe (para pruebas unitarias de componentes)
const { axe, toHaveNoViolations } = require('jest-axe');
expect.extend(toHaveNoViolations);

test('Componente de formulario de contacto es accesible', async () => {
  const { container } = render(<FormularioContacto />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

### Lighthouse CI

```json
// lighthouserc.json
{
  "ci": {
    "assert": {
      "assertions": {
        "categories:accessibility": ["error", { "minScore": 0.90 }]
      }
    }
  }
}
```

### Pa11y (Alternativa CLI)

```bash
# Auditar una URL
pa11y https://dominio.com/ --standard WCAG2AA

# Auditar múltiples páginas con configuración
pa11y-ci --config .pa11yci.json
```

```json
// .pa11yci.json
{
  "standard": "WCAG2AA",
  "urls": [
    "https://dominio.com/",
    "https://dominio.com/servicios/",
    "https://dominio.com/contacto/"
  ],
  "threshold": 0
}
```

---

## Output

### Score Accesibilidad: XX/100

### Resumen de Verificaciones

| Check | Estado | Herramienta | Issues |
|-------|--------|-------------|--------|
| `<html lang>` declarado | ✅/❌ | axe / Playwright | — |
| Estructura semántica | ✅/⚠️/❌ | axe | N issues |
| Un solo `<main>` | ✅/❌ | axe / Playwright | — |
| Jerarquía headings sin saltos | ✅/⚠️/❌ | axe | N saltos |
| Contraste mínimo 4.5:1 | ✅/⚠️/❌ | axe | N elementos |
| Skip link presente | ✅/❌ | axe / manual | — |
| Foco visible | ✅/⚠️/❌ | axe / manual | N elementos |
| Touch targets ≥24px (WCAG 2.2) | ✅/⚠️/❌ | Lighthouse | N elementos |
| Formularios con labels | ✅/⚠️/❌ | axe | N campos |
| Botones/links semánticos | ✅/⚠️/❌ | axe | N elementos |

### Issues por Prioridad

**🔴 Crítico** — `lang` ausente, contraste <3:1 en texto principal, formularios sin labels
**🟠 Alto** — foco invisible, saltos de headings, `outline: none` global, `<div>` como botones
**🟡 Medio** — skip link ausente, `<main>` semántico faltante, tablas sin `scope`
**🟢 Bajo** — `figcaption` faltante en infografías, `aria-label` mejorable

---

## Integración con Otros Skills

| Necesidad | Skill |
|-----------|-------|
| Alt text en imágenes | `/seo-images` |
| `<html lang>` coherente con hreflang | `/seo-hreflang` |
| Fuentes (font-display, contraste) | `/seo-performance` |
| Breadcrumbs semánticos con `<nav>` | `/seo-on-page` |
