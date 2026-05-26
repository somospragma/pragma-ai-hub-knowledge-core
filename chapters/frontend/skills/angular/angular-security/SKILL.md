---
id: frontend-skill-angular-security
version: "1.0"
scope: chapter
type: skill
chapter: frontend
stack: angular
name: angular-security
description: Angular-specific security patterns and vulnerability prevention. Use when auditing or securing Angular applications — covers built-in sanitizer, DomSanitizer bypass risks, CSP with Angular, HttpClient security, route guards, and template injection.
license: MIT
metadata:
  author: pragma-frontend-security
  version: "1.0"
  framework: "Angular 17+"
---

# Angular Security Patterns

Security rules specific to Angular applications. Complements the shared `frontend-security` skill with Angular-specific APIs, built-in protections, and framework-specific attack vectors.

---

## A-S1 — Angular's Built-in Sanitizer

Angular sanitizes values in templates automatically. **This is your first line of defense — never bypass it without justification.**

### How It Works

```
Angular marks these contexts as unsafe and sanitizes:
  - innerHTML  → sanitizes HTML
  - [src]      → sanitizes URLs
  - [href]     → sanitizes URLs
  - [style]    → sanitizes CSS
```

### NEVER Do

```typescript
// ❌ Bypassing sanitizer without a real reason
import { DomSanitizer } from '@angular/platform-browser';

constructor(private sanitizer: DomSanitizer) {}

// These methods DISABLE Angular's protection:
this.sanitizer.bypassSecurityTrustHtml(userInput);      // ❌
this.sanitizer.bypassSecurityTrustScript(userInput);     // ❌ NEVER
this.sanitizer.bypassSecurityTrustUrl(userInput);        // ❌
this.sanitizer.bypassSecurityTrustResourceUrl(userInput); // ❌
this.sanitizer.bypassSecurityTrustStyle(userInput);      // ❌

// ❌ Template injection via string concatenation
const template = `<div>${userInput}</div>`;
```

### WHEN Bypass Is Acceptable (with safeguards)

```typescript
// ✅ Only bypass for KNOWN SAFE content (e.g., from your own CMS, after server-side sanitization)
@Pipe({ name: 'safeHtml', standalone: true })
export class SafeHtmlPipe implements PipeTransform {
  constructor(private sanitizer: DomSanitizer) {}

  transform(value: string): SafeHtml {
    // FIRST: sanitize with DOMPurify
    const clean = DOMPurify.sanitize(value, {
      ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li'],
      ALLOWED_ATTR: ['href', 'target', 'rel'],
    });
    // THEN: bypass Angular's sanitizer on already-clean content
    return this.sanitizer.bypassSecurityTrustHtml(clean);
  }
}

// Usage in template:
// <div [innerHTML]="cmsContent | safeHtml"></div>
```

### Document Every Bypass

```typescript
/**
 * SECURITY: DomSanitizer bypass
 * Reason: Content from internal CMS, server-side sanitized
 * Mitigations: DOMPurify pre-sanitization, allowlisted tags only
 * Reviewed by: [security team member]
 * Date: [date]
 */
```

---

## A-S2 — HttpClient Security

### NEVER Do

```typescript
// ❌ Building URLs with string concatenation (injection risk)
const url = `${baseUrl}/users/${userId}`; // If userId = "../admin" → path traversal
this.http.get(url);

// ❌ Disabling SSL verification in development and forgetting to re-enable
// ❌ Sending credentials to every domain
this.http.get('https://third-party.com/api', { withCredentials: true });

// ❌ Logging request/response with sensitive data
intercept(req, next) {
  console.log('Request:', req.body); // May contain passwords
  return next(req);
}
```

### ALWAYS Do

```typescript
// ✅ Use HttpParams for query parameters (auto-encoded)
const params = new HttpParams()
  .set('search', userInput)  // Auto-encoded
  .set('page', '1');
this.http.get('/api/users', { params });

// ✅ Validate path parameters
private sanitizePath(segment: string): string {
  // Remove path traversal attempts
  return segment.replace(/[^a-zA-Z0-9_-]/g, '');
}

// ✅ CSRF interceptor
@Injectable()
export class CsrfInterceptor implements HttpInterceptor {
  intercept(req: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(req.method)) {
      const csrfToken = this.getCsrfToken();
      if (csrfToken) {
        req = req.clone({
          setHeaders: { 'X-CSRF-Token': csrfToken }
        });
      }
    }
    return next.handle(req);
  }

  private getCsrfToken(): string | null {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ?? null;
  }
}

// ✅ Auth interceptor — only send credentials to YOUR API
@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  private readonly API_BASE = environment.apiUrl;

  intercept(req: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    // Only attach auth to your own API
    if (req.url.startsWith(this.API_BASE)) {
      req = req.clone({ withCredentials: true });
    }
    return next.handle(req);
  }
}

// ✅ Error interceptor — sanitize error messages
@Injectable()
export class ErrorInterceptor implements HttpInterceptor {
  intercept(req: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    return next.handle(req).pipe(
      catchError((error: HttpErrorResponse) => {
        // Never expose raw server error to user
        const userMessage = this.getUserFriendlyMessage(error.status);
        // Log full error only in non-production
        if (!environment.production) {
          console.error('HTTP Error:', error);
        }
        return throwError(() => new Error(userMessage));
      })
    );
  }
}
```

---

## A-S3 — Route Guards & Authorization

### NEVER Do

```typescript
// ❌ Guard that only checks localStorage
canActivate(): boolean {
  return !!localStorage.getItem('token'); // Attacker sets this in DevTools
}

// ❌ Hiding UI as security (button hidden but route accessible)
<button *ngIf="isAdmin" routerLink="/admin">Admin Panel</button>
// User navigates directly to /admin → no guard = access granted

// ❌ Client-only role checking without server verification
canActivate(): boolean {
  const user = JSON.parse(localStorage.getItem('user')!);
  return user.role === 'admin'; // Attacker modifies localStorage
}
```

### ALWAYS Do

```typescript
// ✅ Functional guard pattern (Angular 17+)
export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAuthenticated()) {
    return true;
  }

  // Store attempted URL for post-login redirect
  return router.createUrlTree(['/login'], {
    queryParams: { returnUrl: state.url },
  });
};

// ✅ Role-based guard that validates with server
export const roleGuard: CanActivateFn = (route) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  const requiredRoles = route.data['roles'] as string[];

  // Validate roles from server-verified token (not localStorage)
  return authService.validateSession().pipe(
    map((session) => {
      if (requiredRoles.some((role) => session.roles.includes(role))) {
        return true;
      }
      return router.createUrlTree(['/unauthorized']);
    }),
    catchError(() => of(router.createUrlTree(['/login'])))
  );
};

// ✅ Apply guards at route level
const routes: Routes = [
  {
    path: 'admin',
    canActivate: [authGuard, roleGuard],
    data: { roles: ['admin'] },
    loadComponent: () => import('./admin/admin.component'),
  },
  {
    path: 'dashboard',
    canActivate: [authGuard],
    loadComponent: () => import('./dashboard/dashboard.component'),
  },
];

// ✅ ALWAYS enforce authorization on the backend too
// Guards are UX — the API must verify permissions independently
```

---

## A-S4 — Template Security

### NEVER Do

```typescript
// ❌ Dynamic template compilation from user input
@Component({
  template: userProvidedTemplate, // Template injection!
})

// ❌ Using [innerHTML] with unsanitized content from API
<div [innerHTML]="apiResponse.htmlContent"></div>
// Angular sanitizes this, but complex payloads can sometimes slip through

// ❌ Binding to href without validation
<a [href]="userProvidedUrl">Link</a> // Could be javascript:alert(1)
```

### ALWAYS Do

```typescript
// ✅ Let Angular's template engine handle rendering (auto-escaped)
<p>{{ userInput }}</p>  <!-- Angular escapes this -->

// ✅ For HTML content, use DOMPurify + SafeHtml pipe (see A-S1)
<div [innerHTML]="trustedContent | safeHtml"></div>

// ✅ Validate URLs before binding
@Pipe({ name: 'safeUrl', standalone: true })
export class SafeUrlPipe implements PipeTransform {
  transform(url: string): string {
    try {
      const parsed = new URL(url, window.location.origin);
      if (['http:', 'https:', 'mailto:'].includes(parsed.protocol)) {
        return url;
      }
    } catch {}
    return '#'; // Fallback to safe value
  }
}

// <a [href]="externalUrl | safeUrl">Link</a>

// ✅ Use Angular's built-in URL sanitization for routerLink
<a [routerLink]="['/user', userId]">Profile</a>
// routerLink handles encoding automatically
```

---

## A-S5 — CSP with Angular

Angular requires `unsafe-inline` for styles by default (ViewEncapsulation). Mitigate with nonces.

```typescript
// ✅ angular.json — enable CSP nonce support
{
  "projects": {
    "app": {
      "architect": {
        "build": {
          "options": {
            "security": {
              "autoCsp": true  // Angular 17+ automatic CSP nonce
            }
          }
        }
      }
    }
  }
}

// ✅ Server-side: generate nonce per request
// Express middleware example:
app.use((req, res, next) => {
  const nonce = crypto.randomBytes(16).toString('base64');
  res.locals.nonce = nonce;
  res.setHeader('Content-Security-Policy',
    `default-src 'self'; script-src 'self' 'nonce-${nonce}'; style-src 'self' 'nonce-${nonce}';`
  );
  next();
});

// ✅ In index.html, Angular reads the nonce automatically with autoCsp
// <script nonce="{{nonce}}" src="main.js"></script>
```

---

## Angular Security Checklist

| Category | Check | Severity |
|----------|-------|----------|
| **Sanitizer** | No `bypassSecurityTrust*` without DOMPurify + documentation | CRITICAL |
| **Sanitizer** | `[innerHTML]` only with sanitized content | HIGH |
| **HttpClient** | URL params via HttpParams, not string concatenation | HIGH |
| **HttpClient** | CSRF interceptor for state-changing requests | HIGH |
| **HttpClient** | Auth interceptor scoped to your API domain only | HIGH |
| **HttpClient** | Error interceptor sanitizes error messages | MEDIUM |
| **Guards** | Auth guard validates with server, not localStorage | CRITICAL |
| **Guards** | Role guard checks server-verified roles | CRITICAL |
| **Guards** | Backend enforces same authorization independently | CRITICAL |
| **Templates** | No dynamic template compilation from user input | CRITICAL |
| **Templates** | URLs validated before href binding | HIGH |
| **Templates** | Use routerLink over manual href construction | MEDIUM |
| **CSP** | autoCsp enabled (Angular 17+) | HIGH |
| **CSP** | Nonce-based script/style policy in production | HIGH |
| **General** | No `console.log` in production (use environment check) | MEDIUM |
| **General** | Lazy-loaded routes still protected by guards | HIGH |
