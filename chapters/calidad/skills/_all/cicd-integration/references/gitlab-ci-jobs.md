# GitLab CI — Jobs por Tecnología

Equivalentes GitLab CI con `parallel:matrix`, `artifacts:reports:junit` (integración nativa con MR widget) y cache configurada por tecnología.

## Estructura recomendada

```
.gitlab-ci.yml
.gitlab/
  ci/
    karate.gitlab-ci.yml
    playwright.gitlab-ci.yml
    k6.gitlab-ci.yml
    appium.gitlab-ci.yml
```

## Karate

```yaml
# .gitlab/ci/karate.gitlab-ci.yml
karate:test:
  stage: test
  image: maven:3.9-eclipse-temurin-17
  variables:
    MAVEN_OPTS: "-Dmaven.repo.local=$CI_PROJECT_DIR/.m2/repository"
  cache:
    key: maven-$CI_COMMIT_REF_SLUG
    paths:
      - .m2/repository/
  parallel:
    matrix:
      - TAG: ['@smoke', '@regression-fast', '@regression-full']
  script:
    - mvn -B clean test
        -Dtest=RegressionRunner
        -Dkarate.options="--tags $TAG --threads 4"
  artifacts:
    when: always
    paths:
      - target/karate-reports/
    reports:
      junit: target/karate-reports/*.xml
    expire_in: 30 days
```

## Playwright (matrix browser + shard)

```yaml
# .gitlab/ci/playwright.gitlab-ci.yml
playwright:test:
  stage: test
  image: mcr.microsoft.com/playwright:v1.48.0-jammy
  cache:
    key: npm-$CI_COMMIT_REF_SLUG
    paths:
      - .npm/
  parallel:
    matrix:
      - BROWSER: [chromium, firefox, webkit]
        SHARD_INDEX: [1, 2, 3, 4]
        SHARD_TOTAL: [4]
  script:
    - npm ci --cache .npm --prefer-offline
    - npx playwright test
        --project=$BROWSER
        --shard=$SHARD_INDEX/$SHARD_TOTAL
        --reporter=junit,html
  variables:
    PLAYWRIGHT_JUNIT_OUTPUT_NAME: results-${BROWSER}-${SHARD_INDEX}.xml
  artifacts:
    when: always
    paths:
      - playwright-report/
      - test-results/
    reports:
      junit: results-*.xml
    expire_in: 30 days
```

## K6 (nightly schedule)

```yaml
# .gitlab/ci/k6.gitlab-ci.yml
k6:load:
  stage: performance
  image: grafana/k6:latest
  tags:
    - load-runner  # runner dedicado, NO shared
  only:
    - schedules
    - web
  variables:
    VUS: '50'
    DURATION: '5m'
  script:
    - k6 run
        --vus $VUS
        --duration $DURATION
        --summary-export=summary.json
        --out json=results.json
        load.js
  artifacts:
    when: always
    paths:
      - summary.json
      - results.json
    expire_in: 90 days
```

## Appium

```yaml
# .gitlab/ci/appium.gitlab-ci.yml
appium:android:
  stage: test
  image: gradle:8-jdk17
  cache:
    key: gradle-$CI_COMMIT_REF_SLUG
    paths:
      - .gradle/
  script:
    - gradle test
        -Pplatform=android
        -Pprovider=browserstack
        -g .gradle
  artifacts:
    when: always
    paths:
      - build/reports/tests/test/
    reports:
      junit: build/test-results/test/*.xml
    expire_in: 90 days

appium:ios:
  stage: test
  tags:
    - macos  # runner self-hosted macOS
  script:
    - ./gradlew test -Pplatform=ios -Pprovider=browserstack
  artifacts:
    when: always
    reports:
      junit: build/test-results/test/*.xml
    expire_in: 90 days
```

## Pipeline raíz

```yaml
# .gitlab-ci.yml
stages:
  - test
  - performance
  - report

include:
  - local: .gitlab/ci/karate.gitlab-ci.yml
  - local: .gitlab/ci/playwright.gitlab-ci.yml
  - local: .gitlab/ci/k6.gitlab-ci.yml
  - local: .gitlab/ci/appium.gitlab-ci.yml

workflow:
  rules:
    - if: $CI_PIPELINE_SOURCE == 'merge_request_event'
    - if: $CI_COMMIT_BRANCH == 'main'
    - if: $CI_PIPELINE_SOURCE == 'schedule'
```

## Notas

- `artifacts:reports:junit` activa el widget de MR con failing tests destacados — más rápido que Allure para feedback inmediato.
- `cache:key` con `$CI_COMMIT_REF_SLUG` evita cache poisoning entre branches.
- Para K6, usar siempre `tags:` para runner dedicado; NUNCA shared runner cloud (impacta otros proyectos).
- Para SAST/DAST nativo, GitLab Ultimate incluye `SAST.gitlab-ci.yml` y `DAST.gitlab-ci.yml` — combinar con `[[calidad-security-testing]]`.
