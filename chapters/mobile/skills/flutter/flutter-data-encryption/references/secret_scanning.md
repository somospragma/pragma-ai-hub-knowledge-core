# Secret Scanning — CI Patterns

> **Usage note:** The script below is a reference template for a CI security scan step.
> Run it only in your CI pipeline (not interactively in production environments).
> Review and adapt the patterns to match your project's actual credential formats
> before enabling it. No secrets or live credentials are loaded by this script —
> it only searches for patterns in source files.

## Pre-commit / CI Script

```bash
#!/bin/bash
# scripts/security_scan.sh
# Reference template — adapt patterns and paths before use.
set -e

echo "=== Secret Scanning ==="

# Google API Keys
if grep -rE "AIza[0-9A-Za-z\-_]{35}" lib/ android/ ios/ \
     --include="*.dart" --include="*.xml" --include="*.plist" | grep -v test/; then
  echo "❌ FAIL: Google API key hardcoded"; exit 1
fi

# AWS Access Keys
if grep -rE "AKIA[0-9A-Z]{16}" lib/ --include="*.dart" | grep -v test/; then
  echo "❌ FAIL: AWS access key found"; exit 1
fi

# Stripe Keys
if grep -rE "(sk|pk)_(live|test)_[0-9a-zA-Z]{24,}" lib/ --include="*.dart" | grep -v test/; then
  echo "❌ FAIL: Stripe key hardcoded"; exit 1
fi

# Private Keys
if grep -r "BEGIN.*PRIVATE KEY" lib/ android/ ios/ --include="*.dart"; then
  echo "❌ FAIL: Private key in source"; exit 1
fi

# Generic secrets (password=, apiKey=, secret=, token=)
if grep -rE "(password|apiKey|api_key|secret|token)\s*[=:]\s*['\"][a-zA-Z0-9+/=]{16,}['\"]" \
     lib/ --include="*.dart" | grep -v test/ | \
     grep -v "fromEnvironment\|_key\s*=.*storage"; then
  echo "⚠️  WARNING: Possible hardcoded secret — review manually"
fi

echo "✅ Secret scan passed"
```

---

## GitHub Actions Integration

```yaml
# This step runs in CI only — requires explicit user configuration of secrets.
# GITHUB_TOKEN is a standard GitHub Actions token scoped to the current workflow.
- name: Secret scan
  run: bash scripts/security_scan.sh

- name: Gitleaks scan
  uses: gitleaks/gitleaks-action@v2
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## .gitignore — Never Commit

```gitignore
# Secrets and signing
.env
.env.*
!.env.example
android/key.properties
android/app/*.jks
android/app/*.keystore
android/keystores/
ios/Runner/GoogleService-Info.plist
ios/fastlane/report.xml
**/secrets.json
**/credentials.json
*.p12
*.mobileprovision
```
