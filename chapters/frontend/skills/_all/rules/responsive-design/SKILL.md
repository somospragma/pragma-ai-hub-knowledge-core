---
id: frontend-skill-responsive-design
version: "1.0"
scope: chapter
type: skill
chapter: frontend
name: responsive-design
description: Reglas de diseño responsive. Mobile, tablet y desktop. Activar siempre que se genere o modifique UI. Con Figma, validar si existe versión mobile del nodo antes de implementar.
trigger: always_on
type: rule
---
Cuando generes o modifiques cualquier componente o vista de UI, aplica estas reglas de diseño responsive:

# Reglas de Diseño Responsive

## Principio fundamental
- Todo componente o vista generado DEBE funcionar en mobile (< 768px), tablet (768px–1024px) y desktop (> 1024px).
- Mobile-first: diseñar primero para pantallas pequeñas y escalar hacia arriba.
- NUNCA asumir que un componente solo se verá en desktop.

## Breakpoints estándar

| Nombre  | Rango          | Tailwind | CSS Media Query             |
|---------|----------------|----------|-----------------------------|
| mobile  | < 768px        | (base)   | default (sin media query)   |
| tablet  | 768px – 1023px | `md:`    | `@media (min-width: 768px)` |
| desktop | ≥ 1024px       | `lg:`    | `@media (min-width: 1024px)`|

## Obligaciones en código
- SIEMPRE usar unidades relativas: `rem`, `%`, `vw`, `vh`. NUNCA `px` fijos para anchos de contenedores.
- SIEMPRE usar `max-width` en contenedores principales para no estirar en pantallas grandes.
- SIEMPRE usar CSS Grid o Flexbox para layouts — NUNCA floats ni posicionamientos absolutos para estructura.
- SIEMPRE aplicar `min-width: 0` en items de Grid/Flex para evitar overflow.
- Los textos deben escalar: títulos más pequeños en mobile, más grandes en desktop.
- Las imágenes deben tener `width: 100%; height: auto` como base.
- Touch targets mínimos: 44x44px en mobile (botones, links, íconos interactivos).
- NUNCA usar `overflow: hidden` sin verificar que no rompe el layout en pantallas pequeñas.

## Prohibiciones
- NUNCA hardcodear anchos fijos en contenedores: `width: 1200px` sin un `max-width` + `width: 100%`.
- NUNCA usar `position: fixed` sin verificar comportamiento en mobile (teclado virtual, safe-area).
- NUNCA usar `display: flex` o `display: grid` sin definir el comportamiento en mobile (wrapping, dirección).
- NUNCA generar tablas sin estrategia responsive (scroll horizontal, cards en mobile, o columnas colapsadas).
- NUNCA usar `font-size` menor a `14px` (o `0.875rem`) en mobile.
- NUNCA dejar navegación pensada solo para desktop sin versión mobile (hamburger menu, bottom nav, etc.).

## Patrones recomendados

### Columnas responsivas (Tailwind)
```html
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  <!-- items -->
</div>
```

### Columnas responsivas (CSS puro)
```css
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}
```

### Tipografía fluida
```css
h1 { font-size: clamp(1.5rem, 4vw, 2.5rem); }
p  { font-size: clamp(0.875rem, 2vw, 1rem); }
```

### Contenedor responsivo
```css
.container {
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 1rem;
}
@media (min-width: 768px) {
  .container { padding: 0 2rem; }
}
```

---

## Flujo especial: origen Figma

Cuando el componente o vista provenga de un diseño de Figma, ejecutar este flujo **antes de escribir código**:

### Paso 1 — Buscar versión mobile en el nodo Figma
Buscar en el nodo o frame si existen variantes o frames con nombres como:
`mobile`, `sm`, `375`, `390`, `iPhone`, `phone`, `tablet`, `md`, `768`, `iPad`
o cualquier frame de resolución inferior al desktop.

### Paso 2a — Si existe versión mobile en Figma
- Implementar las tres versiones (mobile, tablet, desktop) respetando el diseño.
- Respetar cambios de layout, tipografía, espaciado y visibilidad entre breakpoints.
- Si hay diferencias de componentes entre breakpoints, documentarlo con un comentario inline.

### Paso 2b — Si NO existe versión mobile en Figma
Preguntar al dev antes de proceder:

> "El diseño de Figma solo tiene versión desktop para este componente/pantalla.
> ¿Tienes la versión mobile en Figma? Si no la tienes, puedo inferir el layout
> responsive siguiendo mobile-first y mejores prácticas (colapso de columnas,
> tipografía fluida, touch targets). ¿Procedo con la inferencia o prefieres
> compartir el diseño mobile primero?"

Si el dev confirma que no hay diseño mobile, proceder con las mejores prácticas
detalladas en este documento. Documentar en comentario qué decisiones se tomaron
por inferencia vs qué viene del diseño.
