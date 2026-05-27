# GitHub Actions — Workflows por Tecnología

Equivalentes a las plantillas Azure DevOps usando matrix strategy nativa de GitHub Actions y acciones del marketplace.

## Estructura recomendada

```
.github/
  workflows/
    karate-pr.yml
    playwright-pr.yml
    k6-nightly.yml
    appium-release.yml
```

## Karate

```yaml
# .github/workflows/karate-pr.yml
name: Karate PR
on:
  pull_request:
    branches: [main, develop]

jobs:
  karate:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        tag: ['@smoke', '@regression-fast']
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '17'
          cache: 'maven'

      - name: Run Karate
        run: |
          mvn -B clean test \
            -Dtest=RegressionRunner \
            -Dkarate.options="--tags ${{ matrix.tag }} --threads 4"
        env:
          BASE_URL: ${{ secrets.BASE_URL }}
          AUTH_TOKEN: ${{ secrets.AUTH_TOKEN }}

      - name: Publish JUnit
        uses: dorny/test-reporter@v1
        if: always()
        with:
          name: Karate ${{ matrix.tag }}
          path: 'target/karate-reports/*.xml'
          reporter: java-junit
          fail-on-error: true

      - name: Upload HTML report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: karate-report-${{ matrix.tag }}
          path: target/karate-reports
          retention-days: 30
```

## Playwright (matrix cross-browser + shard)

```yaml
# .github/workflows/playwright-pr.yml
name: Playwright PR
on:
  pull_request:
    branches: [main, develop]

jobs:
  playwright:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        browser: [chromium, firefox, webkit]
        shard: [1, 2, 3, 4]
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - run: npm ci
      - run: npx playwright install --with-deps ${{ matrix.browser }}

      - name: Run Playwright
        run: |
          npx playwright test \
            --project=${{ matrix.browser }} \
            --shard=${{ matrix.shard }}/4 \
            --reporter=junit,html
        env:
          BASE_URL: ${{ secrets.BASE_URL }}
          PLAYWRIGHT_JUNIT_OUTPUT_NAME: results-${{ matrix.browser }}-${{ matrix.shard }}.xml

      - name: Publish JUnit
        uses: dorny/test-reporter@v1
        if: always()
        with:
          name: Playwright ${{ matrix.browser }} shard ${{ matrix.shard }}
          path: 'results-*.xml'
          reporter: java-junit

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-${{ matrix.browser }}-${{ matrix.shard }}
          path: |
            playwright-report
            test-results
          retention-days: 30
```

## K6 (nightly, no PR)

```yaml
# .github/workflows/k6-nightly.yml
name: K6 Nightly Load
on:
  schedule:
    - cron: '0 2 * * *'  # 02:00 UTC
  workflow_dispatch:
    inputs:
      vus:
        default: '50'
      duration:
        default: '5m'

jobs:
  k6:
    runs-on: [self-hosted, load-pool]
    steps:
      - uses: actions/checkout@v4

      - uses: grafana/setup-k6-action@v1

      - name: Run K6
        run: |
          k6 run \
            --vus ${{ inputs.vus || 50 }} \
            --duration ${{ inputs.duration || '5m' }} \
            --summary-export=summary.json \
            --out json=results.json \
            load.js
        env:
          BASE_URL: ${{ secrets.BASE_URL }}
          AUTH_TOKEN: ${{ secrets.AUTH_TOKEN }}

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: k6-results
          path: |
            summary.json
            results.json
          retention-days: 90
```

## Appium (OS matrix Android + iOS)

```yaml
# .github/workflows/appium-release.yml
name: Appium Release Gate
on:
  release:
    types: [created]
  workflow_dispatch:

jobs:
  appium:
    strategy:
      fail-fast: false
      matrix:
        include:
          - os: ubuntu-latest
            platform: android
          - os: macos-latest
            platform: ios
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '17'

      - name: Gradle test
        run: ./gradlew test -Pplatform=${{ matrix.platform }} -Pprovider=browserstack
        env:
          BROWSERSTACK_USERNAME: ${{ secrets.BROWSERSTACK_USERNAME }}
          BROWSERSTACK_ACCESS_KEY: ${{ secrets.BROWSERSTACK_ACCESS_KEY }}

      - uses: dorny/test-reporter@v1
        if: always()
        with:
          name: Appium ${{ matrix.platform }}
          path: '**/build/test-results/test/*.xml'
          reporter: java-junit

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: appium-${{ matrix.platform }}
          path: build/reports/tests/test
          retention-days: 90
```

## Notas

- `dorny/test-reporter@v1` muestra el resumen JUnit en la UI del PR como check.
- `fail-on-error: true` es obligatorio para que fallos JUnit bloqueen el merge.
- Para sharding agresivo (>10 shards), usar `actions/github-script` para generar la matrix dinámicamente.
- OIDC para AWS/GCP/Azure se documenta en `secrets-in-pipelines.md`.
