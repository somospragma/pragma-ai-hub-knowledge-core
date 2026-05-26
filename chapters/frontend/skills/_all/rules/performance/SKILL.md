---
id: frontend-skill-performance
version: "1.0"
scope: chapter
type: skill
chapter: frontend
name: performance
description: Reglas de performance frontend. Core Web Vitals, bundle size, rendering. Activar siempre que se genere código frontend.
trigger: always_on
type: rule
---

Cuando generes o modifiques código frontend, aplica estas reglas de rendimiento:

# Reglas de Performance Frontend

## Core Web Vitals — Prohibiciones

- NUNCA usar lazy loading en imágenes above-the-fold (LCP).
- NUNCA crear tareas síncronas >50ms en el hilo principal (INP).
- NUNCA renderizar imágenes/video sin width y height explícitos (CLS).
- NUNCA cargar datos del LCP element vía useEffect + spinner — usar SSR/SSG.

## Bundle Size — Prohibiciones

- NUNCA importar librerías completas: import _ from 'lodash'.
- NUNCA usar moment.js — reemplazar con date-fns o dayjs.
- NUNCA usar barrel imports que anulen tree shaking.
- NUNCA dejar rutas sin code-splitting.

## Rendering — Obligaciones

- SIEMPRE usar React.memo() en componentes hijos costosos.
- SIEMPRE usar useMemo/useCallback cuando se pasen como props a memorizados.
- SIEMPRE usar keys estables en listas (IDs, no índices).
- SIEMPRE usar ChangeDetectionStrategy.OnPush en Angular.
- SIEMPRE derivar estado con useMemo o computed() — NUNCA con useEffect + setState.

## Data Fetching

- NUNCA crear cascadas de fetches secuenciales cuando pueden ser paralelos.
- SIEMPRE implementar cache strategy.
- SIEMPRE usar AbortController en fetches dentro de useEffect.
