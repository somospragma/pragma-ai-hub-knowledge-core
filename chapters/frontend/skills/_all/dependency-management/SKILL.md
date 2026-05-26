---
id: frontend-skill-dependency-management
version: "1.0"
scope: chapter
type: skill
chapter: frontend
name: dependency-management
description: Frontend dependency management, supply chain security, and package auditing. Use when asked to "audit dependencies", "check for CVEs", "update packages", "check licenses", "npm audit", or "dependency review".
license: MIT
metadata:
  author: pragma-frontend-security
  version: "1.0"
  scope: "npm, yarn, pnpm ecosystems"
---

# Dependency Management — Complete Knowledge Base

Best practices for managing frontend dependencies securely and efficiently. Covers supply chain security, CVE detection, license compliance, version strategies, and package health evaluation.

---

## D1 — Supply Chain Attack Prevention

### Attack Vectors

| Vector | Description | Example |
|--------|-------------|---------|
| **Typosquatting** | Packages with similar names to popular ones | `lodahs` instead of `lodash` |
| **Dependency Confusion** | Public package matching a private package name | Attacker publishes `@company/internal-lib` to npm |
| **Compromised Maintainer** | Maintainer account hacked, malicious version published | `event-stream` incident (2018) |
| **Install Scripts** | `postinstall` scripts execute arbitrary code | Mining crypto in `postinstall` |
| **Protestware** | Maintainer intentionally adds destructive code | `colors` and `faker` incident (2022) |

### Prevention

```bash
# ✅ Always commit lock files
git add package-lock.json  # or yarn.lock or pnpm-lock.yaml

# ✅ Use lockfile-lint to detect unauthorized registries
npx lockfile-lint \
  --path package-lock.json \
  --type npm \
  --allowed-hosts npm \
  --validate-https

# ✅ Disable install scripts for untrusted packages
npm config set ignore-scripts true
# Then explicitly allow trusted ones in .npmrc:
# @angular/cli:install-script=true

# ✅ Use npm ci in CI/CD (respects lock file exactly)
npm ci  # NOT npm install

# ✅ Pin exact versions for critical dependencies
npm install --save-exact react@19.0.0

# ✅ Use provenance verification (npm v9.5+)
npm audit signatures
```

### .npmrc Security Configuration

```ini
# .npmrc
# Enforce lock file usage
package-lock=true

# Prevent publishing by accident
access=restricted

# Disable lifecycle scripts from untrusted packages
ignore-scripts=true

# Enforce strict SSL
strict-ssl=true

# Set registry explicitly
registry=https://registry.npmjs.org/

# For private packages
@company:registry=https://npm.company.com/
//npm.company.com/:_authToken=${NPM_TOKEN}
```

---

## D2 — CVE Detection & Resolution

### Audit Commands

```bash
# ✅ npm built-in audit
npm audit                    # Show all vulnerabilities
npm audit --audit-level=high # Only high and critical
npm audit fix                # Auto-fix compatible versions
npm audit fix --force        # Force major version updates (REVIEW CHANGES!)

# ✅ Better audit with audit-ci (for CI pipelines)
npx audit-ci --moderate      # Fail CI on moderate+ severity

# ✅ Snyk (more comprehensive, requires account)
npx snyk test                # Test for vulnerabilities
npx snyk monitor             # Add to continuous monitoring

# ✅ OSV-Scanner (Google's free vulnerability scanner)
npx osv-scanner --lockfile=package-lock.json
```

### CVE Severity Decision Matrix

| Severity | Action | Timeline |
|----------|--------|----------|
| **CRITICAL** | Stop and fix immediately | Same day |
| **HIGH** | Fix in current sprint | This week |
| **MEDIUM** | Plan fix, assess impact | Next sprint |
| **LOW** | Document, fix when convenient | Backlog |

### Resolution Strategies

```typescript
// Strategy 1: Direct update (preferred)
// Check if newer version fixes the CVE
npm update vulnerable-package

// Strategy 2: Override nested dependency
// package.json — force a specific version of a transitive dependency
{
  "overrides": {
    "vulnerable-transitive-dep": ">=2.0.1"
  }
}
// yarn:
{
  "resolutions": {
    "vulnerable-transitive-dep": ">=2.0.1"
  }
}
// pnpm:
{
  "pnpm": {
    "overrides": {
      "vulnerable-transitive-dep": ">=2.0.1"
    }
  }
}

// Strategy 3: Replace package entirely
// If no fix exists, find an alternative
npm uninstall vulnerable-package
npm install secure-alternative

// Strategy 4: Mitigate if no fix available
// Document the risk and apply compensating controls
// e.g., CSP headers, input sanitization, WAF rules
```

---

## D3 — License Compliance

### License Risk Matrix

| License | Risk | Commercial Use | Copyleft | Action |
|---------|------|---------------|----------|--------|
| MIT | ✅ Low | Yes | No | Safe to use |
| Apache-2.0 | ✅ Low | Yes | No | Safe, patent grant |
| BSD-2/3 | ✅ Low | Yes | No | Safe to use |
| ISC | ✅ Low | Yes | No | Safe to use |
| GPL-2.0 | 🔴 High | Conditional | Yes | **Review with legal** |
| GPL-3.0 | 🔴 High | Conditional | Yes | **Review with legal** |
| AGPL-3.0 | 🔴 Critical | Conditional | Yes + Network | **Avoid in SaaS** |
| LGPL-2.1/3.0 | 🟡 Medium | Yes (with rules) | Partial | OK for dynamic linking |
| Unlicensed | 🔴 Critical | Unknown | Unknown | **Never use** |
| WTFPL | 🟡 Medium | Yes | No | Not legally tested |

### Audit Licenses

```bash
# ✅ List all dependency licenses
npx license-checker --summary

# ✅ Fail on problematic licenses
npx license-checker \
  --failOn "GPL-2.0;GPL-3.0;AGPL-3.0" \
  --excludePackages "dev-only-internal-tool"

# ✅ Generate license report (compliance)
npx license-checker --csv --out licenses.csv

# ✅ Alternative: license-report
npx license-report --only=prod --output=table
```

---

## D4 — Package Health Evaluation

Before installing ANY new package, evaluate:

### Health Checklist

| Criterion | Green Flag | Red Flag |
|-----------|-----------|----------|
| **Downloads/week** | >10,000 | <100 |
| **Last publish** | <6 months | >2 years |
| **Maintainers** | >1 active | 1 inactive |
| **GitHub stars** | >500 | <10 |
| **Open issues** | Actively triaged | 100+ abandoned |
| **Dependencies** | <5 direct deps | 50+ deep chain |
| **Bundle size** | Reasonable for function | Unexpectedly large |
| **TypeScript** | Native or @types | No types available |
| **Test coverage** | Has CI/tests | No test suite |
| **Security policy** | SECURITY.md exists | No reporting process |

### Bundle Impact Analysis

```bash
# ✅ Check bundle size before installing
# Use bundlephobia.com or:
npx bundle-phobia <package-name>

# ✅ Analyze current bundle
npx @next/bundle-analyzer   # Next.js
npx webpack-bundle-analyzer  # Webpack
npx vite-bundle-visualizer   # Vite

# ✅ Import cost in IDE (install "Import Cost" extension)
import { debounce } from 'lodash';        // 70KB! ❌
import debounce from 'lodash/debounce';    // 1KB  ✅
import { debounce } from 'lodash-es';      // Tree-shakeable ✅
```

---

## D5 — Version Strategy

### Semantic Versioning

```
MAJOR.MINOR.PATCH
  ^     ^     ^
  |     |     └── Bug fixes (safe to update)
  |     └──────── New features (usually safe)
  └────────────── Breaking changes (REVIEW REQUIRED)
```

### Version Pinning Strategy

```json
{
  "dependencies": {
    // ✅ Pin exact for critical deps (React, Angular, Next)
    "react": "19.0.0",
    "next": "15.2.0",

    // ✅ Allow patch updates for stable libs
    "zod": "~3.23.0",

    // ✅ Allow minor updates for well-maintained utility libs
    "clsx": "^2.1.0",

    // ❌ NEVER use
    "some-lib": "*",      // Installs any version
    "some-lib": "latest"  // Same problem
  }
}
```

### Update Strategy

```bash
# ✅ Check for outdated packages
npm outdated

# ✅ Interactive update (ncu — npm-check-updates)
npx npm-check-updates --interactive

# ✅ Update strategy by category:
# 1. Security patches: immediately
# 2. Patch versions: weekly
# 3. Minor versions: bi-weekly (with tests)
# 4. Major versions: planned, with migration guide review

# ✅ Renovate / Dependabot for automated PRs
# .github/dependabot.yml
```

### Dependabot Configuration

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    groups:
      # Group minor/patch updates together
      minor-and-patch:
        update-types:
          - "minor"
          - "patch"
    # Review major versions individually
    ignore:
      - dependency-name: "*"
        update-types: ["version-update:semver-major"]
```

---

## D6 — Monorepo Dependency Management

```bash
# ✅ Nx — single version policy
# nx.json
{
  "workspaceLayout": {
    "appsDir": "apps",
    "libsDir": "libs"
  }
}
# All projects share the same dependency versions

# ✅ pnpm workspaces — efficient monorepo deps
# pnpm-workspace.yaml
packages:
  - 'apps/*'
  - 'packages/*'

# ✅ Check for version mismatches across workspace
npx syncpack list-mismatches
npx syncpack fix-mismatches
```

---

## Quick Reference — Dependency Checklist

| Category | Check | Severity |
|----------|-------|----------|
| **Supply Chain** | Lock file committed and CI uses `npm ci` | CRITICAL |
| **Supply Chain** | lockfile-lint validates registry origins | HIGH |
| **Supply Chain** | Install scripts disabled for untrusted packages | HIGH |
| **CVEs** | `npm audit` returns 0 critical/high | CRITICAL |
| **CVEs** | CI pipeline fails on moderate+ vulnerabilities | HIGH |
| **CVEs** | Transitive dependency overrides documented | MEDIUM |
| **Licenses** | No GPL/AGPL in production dependencies | HIGH |
| **Licenses** | License audit passes in CI | MEDIUM |
| **Health** | New packages evaluated against health checklist | HIGH |
| **Health** | Bundle size impact assessed before install | MEDIUM |
| **Versions** | Critical deps pinned exact | HIGH |
| **Versions** | Automated update PRs (Dependabot/Renovate) | MEDIUM |
| **Versions** | No `*` or `latest` version ranges | CRITICAL |
| **Monorepo** | Version sync across workspaces | HIGH |
