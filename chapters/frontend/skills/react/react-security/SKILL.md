---
id: frontend-skill-react-security
version: "1.0"
scope: chapter
type: skill
chapter: frontend
stack: angular
name: react-security
description: React and Next.js specific security patterns and vulnerability prevention. Use when auditing or securing React/Next.js applications — covers JSX escaping limits, dangerouslySetInnerHTML, Server Actions, API routes, middleware auth, SSR data exposure, and hydration risks.
license: MIT
metadata:
  author: pragma-frontend-security
  version: "1.0"
  framework: "React 18+ / Next.js 14+"
---

# React & Next.js Security Patterns

Security rules specific to React and Next.js applications. Complements the shared `frontend-security` skill with React-specific APIs, Server Component boundaries, and Next.js-specific attack vectors.

---

## R-S1 — JSX Auto-Escaping & Its Limits

React's JSX escapes values by default, but there are **gaps**.

### What JSX Protects

```tsx
// ✅ Safe — JSX escapes string content automatically
<p>{userInput}</p>
// If userInput = "<script>alert('xss')</script>"
// Rendered as: &lt;script&gt;alert('xss')&lt;/script&gt;

// ✅ Safe — attributes are escaped
<div title={userInput} />
```

### Where JSX Does NOT Protect

```tsx
// ❌ dangerouslySetInnerHTML — name is the warning
<div dangerouslySetInnerHTML={{ __html: userInput }} />  // XSS!

// ❌ href with javascript: protocol — JSX does NOT block this
<a href={userInput}>Click</a>  // If userInput = "javascript:alert(1)" → XSS

// ❌ Creating elements from user input
React.createElement(userInput, props);  // Component injection

// ❌ Spreading user-controlled props
<div {...userControlledProps} />  // Could include dangerouslySetInnerHTML

// ❌ Server-side rendering unescaped data in <script> tags
<script dangerouslySetInnerHTML={{
  __html: `window.__DATA__ = ${JSON.stringify(serverData)}`
  // If serverData contains </script>, it breaks out of the tag
}} />
```

### ALWAYS Do

```tsx
// ✅ dangerouslySetInnerHTML ONLY with DOMPurify
import DOMPurify from 'dompurify';

function SafeHtml({ html }: { html: string }) {
  return (
    <div
      dangerouslySetInnerHTML={{
        __html: DOMPurify.sanitize(html, {
          ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li'],
          ALLOWED_ATTR: ['href', 'target', 'rel'],
        }),
      }}
    />
  );
}

// ✅ Validate href before rendering
function SafeLink({ href, children }: { href: string; children: React.ReactNode }) {
  const isSafe = /^(https?:|mailto:|\/(?!\/))/.test(href);
  return <a href={isSafe ? href : '#'}>{children}</a>;
}

// ✅ Never spread unvalidated props
function SafeComponent({ className, id, ...rest }: SafeComponentProps) {
  // Only pass explicitly allowed props
  return <div className={className} id={id} />;
}

// ✅ Safely embed data in SSR
<script dangerouslySetInnerHTML={{
  __html: `window.__DATA__ = ${JSON.stringify(serverData).replace(/</g, '\\u003c')}`
}} />
// Or better: use Next.js data fetching patterns (no manual script injection)
```

---

## R-S2 — Server Components & Data Exposure (Next.js)

Server Components run on the server. **But be careful what data you pass to Client Components.**

### NEVER Do

```tsx
// ❌ Passing secrets/sensitive data from Server to Client Component
// app/page.tsx (Server Component)
import { ClientDashboard } from './ClientDashboard';

export default async function Page() {
  const user = await db.users.findOne({ id: session.userId });
  // user contains: { id, name, email, passwordHash, ssn, internalNotes }

  return <ClientDashboard user={user} />;
  // ALL of user's data is serialized to the client! Including passwordHash!
}

// ❌ Exposing internal IDs, roles, or permissions that enable privilege escalation
return <AdminPanel permissions={internalPermissions} />;

// ❌ Importing server-only code in Client Components
'use client';
import { db } from '@/lib/database'; // This WILL leak to the client bundle
```

### ALWAYS Do

```tsx
// ✅ Only pass the data the client needs (DTO pattern)
// app/page.tsx (Server Component)
export default async function Page() {
  const user = await db.users.findOne({ id: session.userId });

  // Create a client-safe DTO
  const clientUser = {
    name: user.name,
    avatar: user.avatar,
    // NO: passwordHash, ssn, internalNotes, raw permissions
  };

  return <ClientDashboard user={clientUser} />;
}

// ✅ Use server-only package to prevent accidental client imports
// lib/database.ts
import 'server-only'; // Throws build error if imported in client component
import { PrismaClient } from '@prisma/client';

export const db = new PrismaClient();

// ✅ Type the client-safe data
interface ClientUser {
  name: string;
  avatar: string;
}
// Never type it as the full DB model
```

---

## R-S3 — Server Actions Security (Next.js 14+)

Server Actions are **public HTTP endpoints**. Treat them like API routes.

### NEVER Do

```tsx
// ❌ Server Action without authentication
'use server';

export async function deleteUser(userId: string) {
  await db.users.delete({ where: { id: userId } }); // Anyone can call this!
}

// ❌ Trusting the input without validation
'use server';

export async function updateProfile(formData: FormData) {
  const role = formData.get('role') as string;
  await db.users.update({
    where: { id: session.userId },
    data: { role }, // User escalates to 'admin'!
  });
}

// ❌ Returning sensitive data from Server Actions
'use server';

export async function getUser(id: string) {
  return await db.users.findOne({ id }); // Returns passwordHash, etc.
}
```

### ALWAYS Do

```tsx
// ✅ Always authenticate + authorize
'use server';

import { auth } from '@/lib/auth';
import { z } from 'zod';

const UpdateProfileSchema = z.object({
  name: z.string().min(1).max(100),
  email: z.string().email(),
  // NO role field — server decides, not the client
});

export async function updateProfile(formData: FormData) {
  // 1. Authenticate
  const session = await auth();
  if (!session?.user) {
    throw new Error('Unauthorized');
  }

  // 2. Validate input
  const result = UpdateProfileSchema.safeParse({
    name: formData.get('name'),
    email: formData.get('email'),
  });

  if (!result.success) {
    return { error: 'Invalid input' };
  }

  // 3. Authorize (can this user do this action?)
  // 4. Execute
  await db.users.update({
    where: { id: session.user.id }, // Use session ID, not user-provided ID
    data: result.data,
  });

  // 5. Return only what the client needs
  return { success: true };
}

// ✅ Use next-safe-action for type-safe Server Actions with built-in validation
import { createSafeActionClient } from 'next-safe-action';

const actionClient = createSafeActionClient({
  handleServerError(error) {
    // Never expose internal errors
    return { error: 'Something went wrong' };
  },
});

export const updateProfile = actionClient
  .schema(UpdateProfileSchema)
  .action(async ({ parsedInput, ctx }) => {
    // parsedInput is validated, ctx has session
  });
```

---

## R-S4 — API Routes Security (Next.js)

### NEVER Do

```tsx
// ❌ API route without auth
// app/api/users/route.ts
export async function DELETE(request: Request) {
  const { userId } = await request.json();
  await db.users.delete({ where: { id: userId } }); // Public delete endpoint!
  return Response.json({ ok: true });
}

// ❌ Returning full database objects
export async function GET() {
  const users = await db.users.findMany(); // Includes hashes, PII, etc.
  return Response.json(users);
}

// ❌ SQL/NoSQL injection via unvalidated params
const { search } = await request.json();
const users = await db.$queryRaw`SELECT * FROM users WHERE name = ${search}`;
// With Prisma this is safe, but with raw queries be careful
```

### ALWAYS Do

```tsx
// ✅ Authenticated, validated, authorized API routes
// app/api/users/[id]/route.ts
import { auth } from '@/lib/auth';
import { z } from 'zod';

const ParamsSchema = z.object({
  id: z.string().uuid(),
});

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  // 1. Authenticate
  const session = await auth();
  if (!session?.user) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 });
  }

  // 2. Validate params
  const result = ParamsSchema.safeParse(params);
  if (!result.success) {
    return Response.json({ error: 'Invalid request' }, { status: 400 });
  }

  // 3. Authorize
  if (session.user.id !== result.data.id && session.user.role !== 'admin') {
    return Response.json({ error: 'Forbidden' }, { status: 403 });
  }

  // 4. Return only safe fields
  const user = await db.users.findUnique({
    where: { id: result.data.id },
    select: { id: true, name: true, email: true, avatar: true },
  });

  return Response.json(user);
}

// ✅ Rate limiting
import { Ratelimit } from '@upstash/ratelimit';
import { Redis } from '@upstash/redis';

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(10, '60s'), // 10 req/min
});

export async function POST(request: Request) {
  const ip = request.headers.get('x-forwarded-for') ?? '127.0.0.1';
  const { success } = await ratelimit.limit(ip);
  if (!success) {
    return Response.json({ error: 'Too many requests' }, { status: 429 });
  }
  // ... handle request
}
```

---

## R-S5 — Middleware Authentication (Next.js)

### NEVER Do

```tsx
// ❌ Middleware that only checks cookie existence
export function middleware(request: NextRequest) {
  if (request.cookies.get('token')) {
    return NextResponse.next(); // Token could be expired, forged, or stolen
  }
}

// ❌ Heavy operations in middleware (DB queries, JWT full verification)
// Middleware runs on EVERY request — keep it light

// ❌ Relying solely on middleware for authorization
// Middleware is a FIRST GATE, not the ONLY gate
```

### ALWAYS Do

```tsx
// ✅ Middleware as first gate + route-level auth as second gate
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const PUBLIC_ROUTES = ['/login', '/register', '/forgot-password', '/'];
const AUTH_ROUTES = ['/login', '/register']; // Redirect away if already logged in

export function middleware(request: NextRequest) {
  const token = request.cookies.get('session')?.value;
  const { pathname } = request.nextUrl;

  // Public routes — always accessible
  if (PUBLIC_ROUTES.includes(pathname)) {
    // If logged in, redirect away from auth pages
    if (token && AUTH_ROUTES.includes(pathname)) {
      return NextResponse.redirect(new URL('/dashboard', request.url));
    }
    return NextResponse.next();
  }

  // Protected routes — require session cookie
  if (!token) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('returnUrl', pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Light validation only (existence + basic structure)
  // Full verification happens in the route/Server Action
  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|public).*)'],
};
```

---

## R-S6 — Hooks & State Security

### NEVER Do

```tsx
// ❌ Storing sensitive data in state that persists across routes
const [user, setUser] = useState({
  name: 'John',
  ssn: '123-45-6789', // SSN in React state = in memory + React DevTools
  creditCard: '4111...',
});

// ❌ Using URL state for sensitive data
const [searchParams, setSearchParams] = useSearchParams();
searchParams.set('token', authToken); // Token in URL = logged everywhere

// ❌ Storing secrets in context available to all components
<AuthContext.Provider value={{ user, secretKey, refreshToken }}>
  {children} {/* Every child can read secretKey */}
</AuthContext.Provider>
```

### ALWAYS Do

```tsx
// ✅ Only keep non-sensitive data in state
const [user, setUser] = useState({
  name: 'John',
  avatar: '/img/john.png',
  // NO: ssn, creditCard, passwordHash
});

// ✅ Clear sensitive data on unmount
useEffect(() => {
  return () => {
    // Clear when component unmounts (e.g., navigating away)
    setSensitiveFormData(null);
  };
}, []);

// ✅ Use refs for transient sensitive data (not in React DevTools snapshots)
const transientToken = useRef<string | null>(null);

// ✅ Minimal context — only what consumers actually need
interface AuthContextType {
  isAuthenticated: boolean;
  userName: string;
  logout: () => Promise<void>;
  // NO: raw token, refresh token, secrets
}
```

---

## R-S7 — Security Headers in Next.js

```typescript
// ✅ next.config.ts — Complete security headers
import type { NextConfig } from 'next';

const securityHeaders = [
  {
    key: 'Content-Security-Policy',
    value: [
      "default-src 'self'",
      "script-src 'self' 'nonce-{nonce}'",
      "style-src 'self' 'unsafe-inline'", // Required for CSS-in-JS / Tailwind
      "img-src 'self' data: https:",
      "font-src 'self'",
      `connect-src 'self' ${process.env.NEXT_PUBLIC_API_URL ?? ''}`,
      "frame-ancestors 'none'",
      "form-action 'self'",
      "base-uri 'self'",
      "upgrade-insecure-requests",
    ].join('; '),
  },
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'X-Frame-Options', value: 'DENY' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
  {
    key: 'Strict-Transport-Security',
    value: 'max-age=63072000; includeSubDomains; preload',
  },
];

const config: NextConfig = {
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: securityHeaders,
      },
    ];
  },
  // ✅ Disable x-powered-by header
  poweredByHeader: false,
};

export default config;
```

---

## React / Next.js Security Checklist

| Category | Check | Severity |
|----------|-------|----------|
| **XSS** | No `dangerouslySetInnerHTML` without DOMPurify | CRITICAL |
| **XSS** | Validate `href` props against `javascript:` protocol | CRITICAL |
| **XSS** | No unvalidated prop spreading (`{...userProps}`) | HIGH |
| **SSR** | Server Components don't pass sensitive data to Client Components | CRITICAL |
| **SSR** | Use `server-only` package for server-exclusive modules | HIGH |
| **SSR** | Escape data embedded in `<script>` tags during SSR | HIGH |
| **Actions** | Server Actions authenticate + validate + authorize | CRITICAL |
| **Actions** | Server Actions never return full DB objects | HIGH |
| **API Routes** | Every route validates input with Zod | HIGH |
| **API Routes** | Rate limiting on public/sensitive endpoints | HIGH |
| **API Routes** | Return only necessary fields (select/DTO) | HIGH |
| **Middleware** | Light validation only, full auth in route handlers | HIGH |
| **Middleware** | Protected routes require session, public routes listed | HIGH |
| **State** | No PII/secrets in useState, useContext, or URL params | HIGH |
| **State** | Sensitive data cleared on unmount | MEDIUM |
| **Headers** | CSP, HSTS, X-Frame-Options, X-Content-Type-Options set | HIGH |
| **Headers** | `poweredByHeader: false` in next.config | LOW |
| **Deps** | `server-only` enforced on DB/secret modules | HIGH |
