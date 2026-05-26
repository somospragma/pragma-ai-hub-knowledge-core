---
id: frontend-skill-frontend-performance
version: "1.0"
scope: chapter
type: skill
chapter: frontend
name: frontend-performance
description: Frontend performance optimization for Angular and React/Next.js. Use when asked to "optimize performance", "improve Core Web Vitals", "reduce bundle size", "fix re-renders", "lazy loading", "lighthouse score", or "speed up the app".
license: MIT
metadata:
  author: pragma-frontend-performance
  version: "1.0"
  reference: "web.dev/performance, Core Web Vitals"
---

# Frontend Performance — Complete Knowledge Base

Performance optimization patterns for modern frontend applications. Covers Core Web Vitals, rendering optimization, bundle analysis, lazy loading, caching, images, fonts, and framework-specific patterns.

---

## P1 — Core Web Vitals

| Metric | What It Measures | Good | Needs Improvement | Poor |
|--------|-----------------|------|-------------------|------|
| **LCP** (Largest Contentful Paint) | Loading performance | ≤2.5s | 2.5s–4.0s | >4.0s |
| **INP** (Interaction to Next Paint) | Responsiveness | ≤200ms | 200ms–500ms | >500ms |
| **CLS** (Cumulative Layout Shift) | Visual stability | ≤0.1 | 0.1–0.25 | >0.25 |

### LCP Optimization

```typescript
// ❌ LCP killers
<img src={heroImage} />              // No preload, no sizing
const HeroSection = lazy(() => import('./Hero')); // Don't lazy-load above-the-fold

// ✅ Optimize LCP element
// 1. Preload the LCP image
<link rel="preload" as="image" href="/hero.webp" fetchPriority="high" />

// 2. Use priority on LCP image (Next.js)
<Image src="/hero.webp" priority alt="Hero" width={1200} height={600} />

// 3. Angular — NgOptimizedImage
<img ngSrc="/hero.webp" priority width="1200" height="600" alt="Hero" />

// 4. Inline critical CSS
// Avoid render-blocking stylesheets for above-the-fold content

// 5. Avoid client-side data fetching for LCP content
// Use SSR/SSG for the main content, not useEffect + loading spinner
```

### INP Optimization

```typescript
// ❌ Long tasks on main thread
function handleClick() {
  // 500ms of synchronous work → blocks interaction
  const result = heavyComputation(data);
  setResult(result);
}

// ✅ Break long tasks
function handleClick() {
  // Yield to main thread between chunks
  requestIdleCallback(() => {
    const result = heavyComputation(data);
    setResult(result);
  });
}

// ✅ Use web workers for heavy computation
const worker = new Worker('/workers/heavy-task.js');
worker.postMessage(data);
worker.onmessage = (e) => setResult(e.data);

// ✅ Use startTransition for non-urgent updates (React)
import { startTransition } from 'react';
function handleInput(value: string) {
  setInputValue(value);                    // Urgent: update input
  startTransition(() => {
    setFilteredResults(filter(value));       // Non-urgent: can be deferred
  });
}

// ✅ Debounce expensive handlers
import { useDebouncedCallback } from 'use-debounce';
const handleSearch = useDebouncedCallback((term: string) => {
  fetchResults(term);
}, 300);
```

### CLS Optimization

```typescript
// ❌ CLS causes
<img src={url} />                 // No width/height → layout shift on load
{isLoaded && <div>Content</div>}  // Content appears and pushes things down
<div style={{ height: dynamicHeight }} /> // Height changes after render

// ✅ Always set dimensions on media
<img src={url} width={400} height={300} alt="Product" />
<video width={640} height={360} />
<iframe width={560} height={315} />

// ✅ Use aspect-ratio for responsive media
<div className="aspect-video">
  <img src={url} className="object-cover w-full h-full" alt="" />
</div>

// ✅ Reserve space for dynamic content
// Use skeleton UI (same dimensions as final content)
{isLoading ? <ProductCardSkeleton /> : <ProductCard data={product} />}

// ✅ Use CSS contain for isolated layout sections
.sidebar { contain: layout style; }

// ✅ Avoid injecting content above existing content
// Banners, ads, cookie consent → use fixed/sticky positioning
```

---

## P2 — Bundle Size Optimization

### Analysis

```bash
# ✅ Analyze bundle
npx @next/bundle-analyzer        # Next.js
npx webpack-bundle-analyzer      # Webpack projects
npx vite-bundle-visualizer       # Vite projects
npx source-map-explorer dist/**/*.js  # Any project with source maps

# ✅ Check import cost
npx import-cost                  # IDE extension alternative
```

### Common Bloaters

| Package | Bloat | Fix |
|---------|-------|-----|
| `lodash` (full) | ~70KB | Use `lodash-es` or individual imports |
| `moment` | ~290KB | Replace with `date-fns` (~7KB per function) or `dayjs` (~2KB) |
| `axios` | ~13KB | Use native `fetch` (0KB) |
| Barrel files (`index.ts`) | Pulls entire module | Import specific file paths |
| Icon libraries (full) | ~500KB+ | Import individual icons only |
| `@mui/material` (full) | ~300KB | Use path imports: `@mui/material/Button` |

### Tree Shaking

```typescript
// ❌ Imports that defeat tree shaking
import _ from 'lodash';                    // Imports everything
import * as utils from './utils';          // Imports everything
import { Button } from '@mui/material';    // Barrel file pulls all

// ✅ Tree-shakeable imports
import debounce from 'lodash-es/debounce'; // Only debounce
import { formatDate } from './utils/date'; // Specific file
import Button from '@mui/material/Button'; // Direct path

// ✅ Mark side-effect-free in package.json
{
  "sideEffects": false
  // Or specify files with side effects:
  "sideEffects": ["*.css", "./src/polyfills.ts"]
}
```

### Code Splitting

```typescript
// ✅ React — lazy load routes
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Settings = lazy(() => import('./pages/Settings'));

function App() {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Suspense>
  );
}

// ✅ Next.js — dynamic imports for heavy components
import dynamic from 'next/dynamic';
const Chart = dynamic(() => import('@/components/Chart'), {
  loading: () => <ChartSkeleton />,
  ssr: false, // Client-only heavy component
});

// ✅ Angular — lazy load routes (built-in)
const routes: Routes = [
  {
    path: 'admin',
    loadComponent: () => import('./admin/admin.component').then(m => m.AdminComponent),
  },
];

// ✅ Angular — @defer blocks (Angular 17+)
@defer (on viewport) {
  <heavy-chart [data]="chartData" />
} @placeholder {
  <chart-skeleton />
}
```

---

## P3 — Rendering Performance

### React — Preventing Unnecessary Re-renders

```typescript
// ❌ Creating objects/functions in render (new reference every time)
function Parent() {
  return <Child style={{ color: 'red' }} onClick={() => doSomething()} />;
  //          ^ new object every render    ^ new function every render
}

// ✅ Memoize objects and callbacks
function Parent() {
  const style = useMemo(() => ({ color: 'red' }), []);
  const handleClick = useCallback(() => doSomething(), []);
  return <Child style={style} onClick={handleClick} />;
}

// ✅ Memo for expensive child components
const ExpensiveChild = memo(function ExpensiveChild({ data }: Props) {
  return <div>{/* complex rendering */}</div>;
});

// ✅ Avoid re-rendering entire lists
// Use stable keys (NOT index)
{items.map((item) => (
  <ListItem key={item.id} item={item} />  // ✅ Stable ID
  // NOT key={index}                        // ❌ Index changes on reorder
))}

// ✅ Move state down — keep state close to where it's used
// ❌ State in parent forces ALL children to re-render
function Page() {
  const [search, setSearch] = useState('');
  return (
    <>
      <SearchBar value={search} onChange={setSearch} />
      <ExpensiveList />  {/* Re-renders on every keystroke! */}
      <ExpensiveChart /> {/* Re-renders on every keystroke! */}
    </>
  );
}

// ✅ Extract state into its own component
function Page() {
  return (
    <>
      <SearchSection /> {/* State lives here, isolated */}
      <ExpensiveList />  {/* Not affected */}
      <ExpensiveChart /> {/* Not affected */}
    </>
  );
}
```

### Angular — Change Detection

```typescript
// ✅ Use OnPush change detection (default for standalone components)
@Component({
  selector: 'app-product-card',
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: true,
  template: `<div>{{ product().name }}</div>`,
})
export class ProductCardComponent {
  product = input.required<Product>();
}

// ✅ Use signals instead of subjects for reactive state
// Signals trigger fine-grained updates, not full tree checks
readonly count = signal(0);
readonly doubled = computed(() => this.count() * 2);

// ✅ Use trackBy in @for loops
@for (item of items(); track item.id) {
  <app-item [item]="item" />
}

// ✅ Use @defer for below-the-fold content
@defer (on viewport) {
  <app-heavy-section />
} @placeholder {
  <section-skeleton />
}
```

---

## P4 — Image & Font Optimization

### Images

```typescript
// ✅ Next.js Image component (automatic optimization)
import Image from 'next/image';
<Image
  src="/product.jpg"
  alt="Product"
  width={400}
  height={300}
  placeholder="blur"
  blurDataURL={blurHash}
  sizes="(max-width: 768px) 100vw, 400px"
/>

// ✅ Angular NgOptimizedImage
<img ngSrc="/product.jpg" width="400" height="300" alt="Product"
     placeholder loading="lazy" />

// ✅ Modern formats (WebP, AVIF) — 30-50% smaller than JPEG
// Next.js does this automatically
// For other frameworks:
<picture>
  <source srcset="/img.avif" type="image/avif" />
  <source srcset="/img.webp" type="image/webp" />
  <img src="/img.jpg" alt="Fallback" width="400" height="300" loading="lazy" />
</picture>

// ✅ Lazy load below-the-fold images
<img src="/product.jpg" loading="lazy" alt="" />

// ❌ Don't lazy load LCP/above-the-fold images
<img src="/hero.jpg" fetchPriority="high" alt="" />  // Eager load, high priority
```

### Fonts

```typescript
// ✅ Next.js — automatic font optimization
import { Inter } from 'next/font/google';
const inter = Inter({ subsets: ['latin'], display: 'swap' });

// ✅ Self-host fonts (avoid third-party requests)
// Download from google-webfonts-helper, host locally

// ✅ Preload critical fonts
<link rel="preload" href="/fonts/Inter.woff2" as="font" type="font/woff2" crossOrigin="" />

// ✅ Use font-display: swap (show text immediately, swap when loaded)
@font-face {
  font-family: 'Inter';
  src: url('/fonts/Inter.woff2') format('woff2');
  font-display: swap;
}

// ✅ Subset fonts (only include characters you need)
// Use unicode-range or tools like glyphhanger
```

---

## P5 — Caching & Data Fetching

```typescript
// ✅ React/Next.js — cache server data
// TanStack Query (recommended)
const { data } = useQuery({
  queryKey: ['products', filters],
  queryFn: () => fetchProducts(filters),
  staleTime: 5 * 60 * 1000,     // 5 min — don't refetch if fresh
  gcTime: 30 * 60 * 1000,        // 30 min — keep in cache
});

// ✅ Next.js — fetch caching
const data = await fetch('https://api.example.com/products', {
  next: { revalidate: 3600 }, // Revalidate every hour
});

// ✅ Avoid waterfall fetches
// ❌ Sequential (waterfall)
const user = await fetchUser(id);
const posts = await fetchPosts(user.id);
const comments = await fetchComments(posts[0].id);

// ✅ Parallel when possible
const [user, products, notifications] = await Promise.all([
  fetchUser(id),
  fetchProducts(),
  fetchNotifications(),
]);

// ✅ Angular — use resource() for data fetching (Angular 19+)
readonly productResource = resource({
  request: () => this.productId(),
  loader: ({ request: id }) => fetchProduct(id),
});

// ✅ Service Worker caching for offline/repeat visits
// Use Workbox for production-grade caching strategies
```

---

## P6 — Third-Party Script Impact

```typescript
// ✅ Load third-party scripts without blocking render
// Next.js Script component
import Script from 'next/script';
<Script src="https://analytics.example.com/script.js" strategy="lazyOnload" />

// strategy options:
// "beforeInteractive" — critical scripts (auth, polyfills)
// "afterInteractive" — default (analytics, chat) — loads after hydration
// "lazyOnload" — low-priority (ads, social widgets) — loads when idle
// "worker" — runs in web worker (Partytown)

// ✅ Use Partytown to run analytics in a web worker
// Main thread stays free for user interactions
import { Partytown } from '@builder.io/partytown/react';
<Partytown forward={['dataLayer.push']} />

// ✅ Measure third-party impact
// Chrome DevTools → Performance → Bottom-Up → Group by Domain
// Identify which domains contribute most to main-thread blocking
```

---

## P7 — Performance Monitoring

### Lighthouse CI

```bash
# ✅ Run Lighthouse in CI
npm install -g @lhci/cli
lhci autorun --config=lighthouserc.json

# lighthouserc.json
{
  "ci": {
    "assert": {
      "assertions": {
        "categories:performance": ["error", { "minScore": 0.9 }],
        "categories:accessibility": ["error", { "minScore": 0.9 }],
        "first-contentful-paint": ["error", { "maxNumericValue": 1500 }],
        "largest-contentful-paint": ["error", { "maxNumericValue": 2500 }],
        "cumulative-layout-shift": ["error", { "maxNumericValue": 0.1 }],
        "interactive": ["error", { "maxNumericValue": 3500 }]
      }
    }
  }
}
```

### Real User Monitoring (RUM)

```typescript
// ✅ Measure Core Web Vitals from real users
import { onLCP, onINP, onCLS } from 'web-vitals';

function reportMetric(metric: { name: string; value: number; id: string }) {
  // Send to your analytics
  fetch('/api/vitals', {
    method: 'POST',
    body: JSON.stringify(metric),
    keepalive: true, // Survives page unload
  });
}

onLCP(reportMetric);
onINP(reportMetric);
onCLS(reportMetric);

// ✅ Next.js — built-in web vitals reporting
// app/layout.tsx
export function reportWebVitals(metric: NextWebVitalsMetric) {
  // Send to analytics provider
}
```

---

## Quick Reference — Performance Checklist

| Category | Check | Impact |
|----------|-------|--------|
| **CWV-LCP** | LCP image preloaded with `priority`/`fetchPriority="high"` | CRITICAL |
| **CWV-LCP** | No lazy loading on above-the-fold content | HIGH |
| **CWV-LCP** | SSR/SSG for main content (not client-side fetch + spinner) | HIGH |
| **CWV-INP** | No long tasks (>50ms) on main thread | CRITICAL |
| **CWV-INP** | Heavy computation in Web Workers | HIGH |
| **CWV-INP** | Debounced input handlers | MEDIUM |
| **CWV-CLS** | All images/video have explicit width + height | CRITICAL |
| **CWV-CLS** | Skeleton UI reserves space for dynamic content | HIGH |
| **Bundle** | No full library imports (lodash, moment, MUI barrel) | HIGH |
| **Bundle** | Routes lazy-loaded / code-split | HIGH |
| **Bundle** | Tree shaking working (sideEffects: false) | MEDIUM |
| **Render** | React.memo on expensive children | HIGH |
| **Render** | Angular OnPush + signals | HIGH |
| **Render** | Stable keys on lists (not index) | MEDIUM |
| **Render** | State kept close to where it's used | MEDIUM |
| **Images** | WebP/AVIF formats, lazy loaded, responsive sizes | HIGH |
| **Fonts** | Self-hosted, preloaded, font-display: swap | MEDIUM |
| **Data** | Parallel fetches (no waterfalls) | HIGH |
| **Data** | Proper cache strategy (staleTime, revalidate) | MEDIUM |
| **3rd Party** | Analytics/ads loaded with lazyOnload or web worker | HIGH |
| **Monitor** | Lighthouse CI with score thresholds | HIGH |
| **Monitor** | Real User Monitoring (web-vitals) | MEDIUM |
