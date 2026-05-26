---
id: frontend-skill-frontend-security
version: "1.0"
scope: chapter
type: skill
chapter: frontend
name: frontend-security
description: Frontend security best practices and vulnerability prevention. Use when asked to "security audit", "fix vulnerabilities", "secure the app", "OWASP frontend", "prevent XSS", "token storage", or "security review".
license: MIT
metadata:
  author: pragma-frontend-security
  version: "1.0"
  owasp_reference: "OWASP Top 10 2021 + OWASP Client-Side Security"
---

# Frontend Security — Complete Knowledge Base

Security rules and patterns for web frontend applications. Covers OWASP Top 10 adapted to client-side, secure coding patterns, and anti-patterns that introduce vulnerabilities.

---

## S1 — Cross-Site Scripting (XSS) Prevention

XSS is the #1 frontend vulnerability. Three types: Stored, Reflected, DOM-based.

### NEVER Do

```typescript
// ❌ DOM-based XSS — injecting unsanitized HTML
element.innerHTML = userInput;

// ❌ React — dangerouslySetInnerHTML without sanitization
<div dangerouslySetInnerHTML={{ __html: userInput }} />

// ❌ Angular — bypassing sanitizer without justification
this.sanitizer.bypassSecurityTrustHtml(userInput);

// ❌ eval() — code injection
eval(userInput);
new Function(userInput)();

// ❌ document.write — classic XSS vector
document.write(userInput);

// ❌ Unescaped URL construction
window.location.href = userInput;
```

### ALWAYS Do

```typescript
// ✅ React — use textContent or JSX (auto-escaped)
<p>{userInput}</p>  // JSX escapes by default

// ✅ If you MUST render HTML, sanitize first
import DOMPurify from 'dompurify';
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(userInput) }} />

// ✅ Angular — trust the built-in sanitizer, let it work
// Angular auto-sanitizes bindings. Don't bypass it.
<div [innerHTML]="userContent"></div>  // Angular sanitizes this

// ✅ Use textContent instead of innerHTML in vanilla JS
element.textContent = userInput;

// ✅ Validate URLs before navigation
const isValidUrl = (url: string): boolean => {
  try {
    const parsed = new URL(url, window.location.origin);
    return ['http:', 'https:'].includes(parsed.protocol);
  } catch {
    return false;
  }
};
```

### DOMPurify Configuration (when HTML rendering is unavoidable)

```typescript
import DOMPurify from 'dompurify';

const SANITIZE_CONFIG = {
  ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li'],
  ALLOWED_ATTR: ['href', 'target', 'rel'],
  ALLOW_DATA_ATTR: false,
  ADD_ATTR: ['rel'],           // Force rel on links
  FORBID_TAGS: ['script', 'style', 'iframe', 'object', 'embed', 'form'],
  FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover'],
};

// Hook: force safe link targets
DOMPurify.addHook('afterSanitizeAttributes', (node) => {
  if (node.tagName === 'A') {
    node.setAttribute('target', '_blank');
    node.setAttribute('rel', 'noopener noreferrer');
  }
});

export const sanitizeHtml = (dirty: string): string =>
  DOMPurify.sanitize(dirty, SANITIZE_CONFIG);
```

---

## S2 — Authentication & Token Management

### Token Storage — Decision Matrix

| Storage | XSS Vulnerable | CSRF Vulnerable | Recommendation |
|---------|---------------|----------------|----------------|
| `localStorage` | ✅ YES — JS can read it | ❌ No | **NEVER for auth tokens** |
| `sessionStorage` | ✅ YES — JS can read it | ❌ No | **NEVER for auth tokens** |
| `HttpOnly Cookie` | ❌ No — JS can't read it | ✅ YES (mitigable) | **PREFERRED** |
| Memory (variable) | ❌ No (dies on refresh) | ❌ No | **Good for short-lived tokens** |

### NEVER Do

```typescript
// ❌ Storing JWT in localStorage — any XSS reads it
localStorage.setItem('token', jwt);

// ❌ Storing tokens in sessionStorage
sessionStorage.setItem('auth_token', token);

// ❌ Token in URL parameters — logged in server logs, browser history, referrer
window.location.href = `/dashboard?token=${jwt}`;

// ❌ Token in global variable accessible to third-party scripts
window.__AUTH_TOKEN__ = jwt;

// ❌ Logging tokens
console.log('Token:', token);
console.log('User:', JSON.stringify(user)); // May contain sensitive data
```

### ALWAYS Do

```typescript
// ✅ Backend sets HttpOnly cookie (frontend never touches the token)
// Backend response:
// Set-Cookie: access_token=xxx; HttpOnly; Secure; SameSite=Strict; Path=/api

// ✅ Frontend just makes requests — cookie is sent automatically
const response = await fetch('/api/data', {
  credentials: 'include', // Sends cookies
});

// ✅ If you MUST handle tokens client-side (SPA with third-party API):
// Store in memory, refresh via HttpOnly refresh cookie
class TokenManager {
  private accessToken: string | null = null;

  setToken(token: string): void {
    this.accessToken = token;
    // Schedule refresh before expiration
    this.scheduleRefresh(token);
  }

  getToken(): string | null {
    return this.accessToken;
  }

  clear(): void {
    this.accessToken = null;
  }

  private scheduleRefresh(token: string): void {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const expiresIn = payload.exp * 1000 - Date.now();
    const refreshAt = expiresIn - 60_000; // 1 min before expiry
    setTimeout(() => this.refresh(), Math.max(refreshAt, 0));
  }

  private async refresh(): Promise<void> {
    const res = await fetch('/api/auth/refresh', {
      method: 'POST',
      credentials: 'include', // HttpOnly refresh cookie
    });
    if (res.ok) {
      const { accessToken } = await res.json();
      this.setToken(accessToken);
    } else {
      this.clear();
      window.location.href = '/login';
    }
  }
}
```

### Logout Checklist

```typescript
async function logout(): Promise<void> {
  // 1. Clear in-memory token
  tokenManager.clear();

  // 2. Tell backend to invalidate refresh token
  await fetch('/api/auth/logout', {
    method: 'POST',
    credentials: 'include',
  });

  // 3. Clear any cached data
  queryClient?.clear(); // TanStack Query
  sessionStorage.clear(); // Clear non-sensitive session data

  // 4. Redirect to login
  window.location.href = '/login'; // Full navigation, not SPA route
}
```

---

## S3 — Cross-Site Request Forgery (CSRF) Prevention

### When You're Vulnerable

CSRF applies when:
- Authentication via cookies (not Bearer tokens in headers)
- State-changing requests (POST, PUT, DELETE, PATCH)
- No CSRF token validation

### NEVER Do

```typescript
// ❌ State-changing GET requests
<a href="/api/delete-account">Delete Account</a>
<img src="/api/transfer?amount=1000&to=attacker" />

// ❌ Forms without CSRF tokens
<form action="/api/update-profile" method="POST">
  <input name="email" />
  <button type="submit">Update</button>
</form>
```

### ALWAYS Do

```typescript
// ✅ Use SameSite cookies (backend)
// Set-Cookie: session=xxx; SameSite=Strict; Secure; HttpOnly

// ✅ Include CSRF token in requests
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

const response = await fetch('/api/update-profile', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRF-Token': csrfToken ?? '',
  },
  credentials: 'include',
  body: JSON.stringify(data),
});

// ✅ Double-submit cookie pattern
// Backend sets: Set-Cookie: csrf=abc123; SameSite=Strict
// Frontend reads cookie and sends in header — attacker can't read the cookie
function getCsrfFromCookie(): string {
  const match = document.cookie.match(/csrf=([^;]+)/);
  return match?.[1] ?? '';
}

// ✅ Verify origin on backend for critical operations
// Check Origin and Referer headers match your domain
```

---

## S4 — Secrets & Sensitive Data Exposure

### NEVER Do

```typescript
// ❌ API keys in frontend code
const API_KEY = 'sk-live-abc123xyz789';
const STRIPE_SECRET = 'sk_live_xxxxx';

// ❌ Secrets in environment variables that get bundled
// .env
NEXT_PUBLIC_SECRET_KEY=my-secret  // NEXT_PUBLIC_ = exposed to browser!
VITE_SECRET_KEY=my-secret         // VITE_ = exposed to browser!

// ❌ Database connection strings in frontend
const DB_URL = 'postgres://user:pass@host:5432/db';

// ❌ Hardcoded credentials
const admin = { username: 'admin', password: 'admin123' };

// ❌ Secrets in comments
// TODO: API key is abc123, change in production

// ❌ Sensitive data in error messages shown to users
catch (error) {
  alert(`Database error: ${error.message}`); // Leaks internals
}
```

### ALWAYS Do

```typescript
// ✅ Public keys only in frontend (never secret keys)
// .env
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_xxxxx  // Publishable = OK
NEXT_PUBLIC_API_URL=https://api.myapp.com          // URL = OK

// ✅ Proxy secrets through your backend
// Frontend calls your API → Your API calls third-party with secret key
const data = await fetch('/api/payment/create-intent', {
  method: 'POST',
  body: JSON.stringify({ amount }),
});

// ✅ Runtime environment config (never bundled secrets)
// Use server-only env vars in Next.js API routes / Server Actions
// app/api/payment/route.ts
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!); // No NEXT_PUBLIC_ prefix

// ✅ Sanitize error messages
catch (error) {
  console.error(error); // Log full error server-side only
  showToast('Something went wrong. Please try again.');
}

// ✅ Use .env.example with placeholder values (commit this)
// .env.example
NEXT_PUBLIC_API_URL=https://api.example.com
STRIPE_SECRET_KEY=sk_test_replace_me

// ✅ .gitignore secrets files
// .env.local
// .env.production
// *.pem
// *.key
```

### Environment Variable Safety

| Prefix | Bundled in Client? | Safe for Secrets? |
|--------|-------------------|------------------|
| `NEXT_PUBLIC_` | ✅ YES | ❌ NO |
| `VITE_` | ✅ YES | ❌ NO |
| `REACT_APP_` (CRA) | ✅ YES | ❌ NO |
| No prefix (Next.js) | ❌ Server only | ✅ YES |
| No prefix (Vite) | ❌ Server only | ✅ YES |

---

## S5 — Input Validation & Sanitization

### Client-Side Validation (UX, not security)

Client validation improves UX but is **NEVER a security boundary**. An attacker bypasses it with DevTools.

### ALWAYS Do

```typescript
// ✅ Validate with Zod (type-safe, runtime validation)
import { z } from 'zod';

const ContactFormSchema = z.object({
  name: z.string()
    .min(1, 'Name is required')
    .max(100, 'Name too long')
    .regex(/^[\p{L}\p{M}\s'-]+$/u, 'Invalid characters'),
  email: z.string()
    .email('Invalid email')
    .max(254, 'Email too long'),
  phone: z.string()
    .regex(/^\+?[\d\s()-]{7,20}$/, 'Invalid phone')
    .optional(),
  message: z.string()
    .min(10, 'Too short')
    .max(5000, 'Too long'),
  website: z.string()
    .url('Invalid URL')
    .refine(
      (url) => ['http:', 'https:'].includes(new URL(url).protocol),
      'Only HTTP/HTTPS URLs allowed'
    )
    .optional(),
});

type ContactForm = z.infer<typeof ContactFormSchema>;

// ✅ Validate on submit
function handleSubmit(data: unknown): void {
  const result = ContactFormSchema.safeParse(data);
  if (!result.success) {
    // Show validation errors to user
    return;
  }
  // result.data is typed and validated
  submitToApi(result.data);
}

// ✅ Limit input length at HTML level too (defense in depth)
<input name="name" maxLength={100} />
<textarea name="message" maxLength={5000} />

// ✅ Restrict file uploads
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf'];
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB

function validateFile(file: File): boolean {
  if (!ALLOWED_TYPES.includes(file.type)) return false;
  if (file.size > MAX_FILE_SIZE) return false;
  return true;
}
```

### NEVER Do

```typescript
// ❌ Trust client-side validation as security
// The real validation MUST happen on the server

// ❌ Use regex for email validation (use Zod or built-in)
const emailRegex = /^[a-zA-Z0-9...]{100 chars}$/; // Fragile, incomplete

// ❌ Allow unrestricted file uploads
<input type="file" /> // No type or size restriction

// ❌ Render user input without encoding in URLs
const searchUrl = `/search?q=${userInput}`; // URL injection
// ✅ Use encodeURIComponent
const searchUrl = `/search?q=${encodeURIComponent(userInput)}`;
```

---

## S6 — Content Security Policy (CSP)

### Minimum CSP for Modern SPAs

```html
<!-- Next.js — next.config.ts -->
<meta http-equiv="Content-Security-Policy" content="
  default-src 'self';
  script-src 'self' 'nonce-{random}';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  font-src 'self';
  connect-src 'self' https://api.yourdomain.com;
  frame-src 'none';
  object-src 'none';
  base-uri 'self';
  form-action 'self';
  upgrade-insecure-requests;
">
```

```typescript
// ✅ Next.js — Security headers in next.config.ts
const securityHeaders = [
  {
    key: 'Content-Security-Policy',
    value: `
      default-src 'self';
      script-src 'self' 'nonce-{nonce}';
      style-src 'self' 'unsafe-inline';
      img-src 'self' data: https:;
      connect-src 'self' ${process.env.NEXT_PUBLIC_API_URL};
      frame-ancestors 'none';
      form-action 'self';
    `.replace(/\n/g, ''),
  },
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'X-Frame-Options', value: 'DENY' },
  { key: 'X-XSS-Protection', value: '0' }, // Deprecated, rely on CSP
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
  {
    key: 'Strict-Transport-Security',
    value: 'max-age=63072000; includeSubDomains; preload',
  },
];

// next.config.ts
const nextConfig = {
  async headers() {
    return [{ source: '/(.*)', headers: securityHeaders }];
  },
};
```

### NEVER Do with CSP

```
❌ script-src 'unsafe-eval'     — allows eval(), defeats XSS protection
❌ script-src 'unsafe-inline'   — allows inline scripts, defeats XSS protection
❌ default-src *                 — allows everything, useless CSP
❌ connect-src *                 — allows data exfiltration to any domain
```

---

## S7 — Secure Communication

### NEVER Do

```typescript
// ❌ HTTP in production
fetch('http://api.example.com/data');

// ❌ Ignoring CORS errors by proxying everything
// "Just add a proxy to bypass CORS" — this disables a security control

// ❌ Sending sensitive data in GET parameters
fetch(`/api/login?username=${user}&password=${pass}`);

// ❌ window.postMessage without origin verification
window.addEventListener('message', (event) => {
  processData(event.data); // Accepts messages from ANY origin
});
```

### ALWAYS Do

```typescript
// ✅ HTTPS everywhere
fetch('https://api.example.com/data');

// ✅ Verify postMessage origin
window.addEventListener('message', (event) => {
  const ALLOWED_ORIGINS = ['https://trusted-domain.com'];
  if (!ALLOWED_ORIGINS.includes(event.origin)) return;
  processData(event.data);
});

// ✅ Proper CORS configuration (backend)
// Only allow your frontend domain, not *
// Access-Control-Allow-Origin: https://app.example.com

// ✅ Certificate pinning for critical APIs (mobile/desktop webviews)
// Implement at the HTTP client level
```

---

## S8 — Third-Party Dependencies

### NEVER Do

```typescript
// ❌ Install packages without checking
npm install random-cool-lib  // 0 downloads, 1 contributor?

// ❌ Use * for versions
"dependencies": {
  "some-lib": "*"  // Could install a compromised version
}

// ❌ Ignore npm audit warnings
// ❌ Copy-paste code from unknown sources without review
// ❌ Load scripts from untrusted CDNs without SRI
<script src="https://cdn.example.com/lib.js"></script>
```

### ALWAYS Do

```typescript
// ✅ Pin exact versions or use lock files
"dependencies": {
  "react": "19.0.0"
}
// Commit package-lock.json or yarn.lock or pnpm-lock.yaml

// ✅ Audit regularly
npm audit
npx audit-ci --moderate  // CI pipeline fails on moderate+ vulnerabilities

// ✅ Use Subresource Integrity (SRI) for external scripts
<script
  src="https://cdn.example.com/lib.min.js"
  integrity="sha384-oqVuAfXRKap7fdgcCY5uykM6+R9GqQ8K/uxy9rx7HNQlGYl1kPzQho1wx4JwY8w"
  crossorigin="anonymous"
></script>

// ✅ Before installing a package, check:
// 1. Downloads per week (>10k is baseline)
// 2. Last publish date (<1 year)
// 3. Number of maintainers (>1)
// 4. Known vulnerabilities (npm audit, Snyk)
// 5. License compatibility
// 6. Bundle size impact (bundlephobia.com)

// ✅ Use lockfile-lint to prevent supply chain attacks
npx lockfile-lint --path package-lock.json --type npm --allowed-hosts npm
```

---

## S9 — Sensitive Data in the Browser

### NEVER Do

```typescript
// ❌ Store PII in localStorage/sessionStorage
localStorage.setItem('user', JSON.stringify({ ssn: '123-45-6789', ccn: '4111...' }));

// ❌ Log sensitive data to console (production)
console.log('User data:', user);
console.log('Payment info:', paymentDetails);

// ❌ Expose data in URL (visible in history, logs, analytics)
router.push(`/profile?ssn=${ssn}&dob=${dob}`);

// ❌ Cache sensitive API responses
// Cache-Control: public (on sensitive endpoints)

// ❌ Leave sensitive data in hidden form fields
<input type="hidden" name="creditCard" value="4111-1111-1111-1111" />
```

### ALWAYS Do

```typescript
// ✅ Mask sensitive data in UI
const maskSSN = (ssn: string): string => `***-**-${ssn.slice(-4)}`;
const maskCard = (card: string): string => `**** **** **** ${card.slice(-4)}`;
const maskEmail = (email: string): string => {
  const [user, domain] = email.split('@');
  return `${user[0]}***@${domain}`;
};

// ✅ Clear sensitive data when no longer needed
useEffect(() => {
  return () => {
    // Cleanup on unmount
    sensitiveDataRef.current = null;
  };
}, []);

// ✅ Disable autocomplete on sensitive fields
<input type="password" autoComplete="new-password" />
<input name="cc-number" autoComplete="off" />

// ✅ Prevent caching of sensitive pages
// Backend: Cache-Control: no-store, no-cache, must-revalidate, private
// Meta: <meta http-equiv="Cache-Control" content="no-store" />

// ✅ Strip console.logs in production builds
// vite.config.ts
export default defineConfig({
  esbuild: {
    drop: ['console', 'debugger'],
  },
});

// next.config.ts (with webpack)
webpack: (config, { isServer }) => {
  if (!isServer) {
    config.optimization.minimizer.forEach((minimizer) => {
      if (minimizer.constructor.name === 'TerserPlugin') {
        minimizer.options.terserOptions.compress.drop_console = true;
      }
    });
  }
  return config;
},
```

---

## S10 — Open Redirects & URL Manipulation

### NEVER Do

```typescript
// ❌ Redirect to user-supplied URL without validation
const redirectUrl = searchParams.get('redirect');
window.location.href = redirectUrl!;  // Attacker: ?redirect=https://evil.com

// ❌ Href from user input without validation
<a href={userProvidedUrl}>Click here</a>  // Could be javascript:alert(1)
```

### ALWAYS Do

```typescript
// ✅ Validate redirect URLs — allowlist of domains or relative only
function safeRedirect(url: string, fallback = '/'): string {
  // Only allow relative paths
  if (url.startsWith('/') && !url.startsWith('//')) {
    return url;
  }

  // Or allowlist specific domains
  try {
    const parsed = new URL(url);
    const ALLOWED_HOSTS = ['app.example.com', 'example.com'];
    if (ALLOWED_HOSTS.includes(parsed.hostname)) {
      return url;
    }
  } catch {
    // Invalid URL
  }

  return fallback;
}

// ✅ Validate href values
function isSafeHref(href: string): boolean {
  if (href.startsWith('/') && !href.startsWith('//')) return true;
  try {
    const url = new URL(href);
    return ['http:', 'https:', 'mailto:'].includes(url.protocol);
  } catch {
    return false;
  }
}

// Usage
<a href={isSafeHref(url) ? url : '#'}>Link</a>

// ✅ Use target="_blank" with rel="noopener noreferrer"
<a href={externalUrl} target="_blank" rel="noopener noreferrer">
  External Link
</a>
```

---

## Quick Reference — Security Checklist

| Category | Check | Severity |
|----------|-------|----------|
| **XSS** | No `innerHTML`, `dangerouslySetInnerHTML` without DOMPurify | CRITICAL |
| **XSS** | No `eval()`, `new Function()`, `document.write()` | CRITICAL |
| **Auth** | Tokens in HttpOnly cookies, NOT localStorage | CRITICAL |
| **Auth** | Proper logout (clear memory + invalidate server session) | HIGH |
| **CSRF** | SameSite cookies + CSRF token on state-changing requests | HIGH |
| **Secrets** | No API keys, passwords, or secrets in frontend code | CRITICAL |
| **Secrets** | No `NEXT_PUBLIC_` / `VITE_` / `REACT_APP_` for secrets | CRITICAL |
| **Secrets** | No `console.log` of tokens or user data | HIGH |
| **Input** | Zod/Yup validation + HTML maxLength + backend validation | HIGH |
| **Input** | File uploads restricted (type + size) | MEDIUM |
| **CSP** | Content-Security-Policy header configured | HIGH |
| **CSP** | No `unsafe-eval` or `unsafe-inline` in script-src | HIGH |
| **Headers** | X-Content-Type-Options, X-Frame-Options, HSTS set | MEDIUM |
| **Comms** | HTTPS everywhere, no HTTP in production | CRITICAL |
| **Comms** | postMessage validates origin | HIGH |
| **Deps** | Lock files committed, `npm audit` clean | HIGH |
| **Deps** | External scripts use SRI | MEDIUM |
| **Data** | PII masked in UI, not in localStorage | HIGH |
| **Data** | console.log stripped in production builds | MEDIUM |
| **URLs** | Redirects validated (relative or allowlisted domains) | HIGH |
| **URLs** | No `javascript:` protocol in href | CRITICAL |
