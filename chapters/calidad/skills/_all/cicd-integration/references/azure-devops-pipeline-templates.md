# Azure DevOps — Plantillas de Pipeline por Tecnología

Azure DevOps Pipelines es la plataforma CI/CD primaria en Pragma. Esta referencia consolida templates YAML completos y reutilizables para cada framework de pruebas.

## Estructura recomendada

```
.azure-pipelines/
  templates/
    karate.yml
    playwright.yml
    k6.yml
    appium.yml
  pipeline-pr.yml
  pipeline-nightly.yml
  pipeline-release.yml
```

## Karate (Maven, parallel runner por tag)

```yaml
# .azure-pipelines/templates/karate.yml
parameters:
  - name: tags
    type: string
    default: '@regression'
  - name: threads
    type: number
    default: 4
  - name: env
    type: string
    default: 'qa'

jobs:
  - job: KarateTests
    pool:
      vmImage: 'ubuntu-latest'
    variables:
      MAVEN_OPTS: '-Xmx2048m'
    steps:
      - task: JavaToolInstaller@0
        inputs:
          versionSpec: '17'
          jdkArchitectureOption: 'x64'
          jdkSourceOption: 'PreInstalled'

      - task: Cache@2
        inputs:
          key: 'maven | "$(Agent.OS)" | **/pom.xml'
          restoreKeys: |
            maven | "$(Agent.OS)"
          path: $(MAVEN_CACHE_FOLDER)
        displayName: Cache Maven local repo

      - script: |
          mvn -B clean test \
            -Dtest=RegressionRunner \
            -Dkarate.env=${{ parameters.env }} \
            -Dkarate.options="--tags ${{ parameters.tags }} --threads ${{ parameters.threads }}" \
            -Dmaven.repo.local=$(MAVEN_CACHE_FOLDER)
        displayName: Run Karate tests
        env:
          BASE_URL: $(BASE_URL)
          AUTH_TOKEN: $(AUTH_TOKEN)

      - task: PublishTestResults@2
        condition: always()
        inputs:
          testResultsFormat: 'JUnit'
          testResultsFiles: '**/target/karate-reports/*.xml'
          failTaskOnFailedTests: true

      - task: PublishPipelineArtifact@1
        condition: always()
        inputs:
          targetPath: 'target/karate-reports'
          artifact: 'karate-html-report'
```

## Playwright (npm ci + sharding)

```yaml
# .azure-pipelines/templates/playwright.yml
parameters:
  - name: shardTotal
    type: number
    default: 4
  - name: browser
    type: string
    default: 'chromium'

jobs:
  - job: PlaywrightTests
    strategy:
      parallel: ${{ parameters.shardTotal }}
    pool:
      vmImage: 'ubuntu-latest'
    steps:
      - task: NodeTool@0
        inputs:
          versionSpec: '20.x'

      - task: Cache@2
        inputs:
          key: 'npm | "$(Agent.OS)" | package-lock.json'
          path: ~/.npm
        displayName: Cache npm

      - script: npm ci
        displayName: Install deps

      - script: npx playwright install --with-deps ${{ parameters.browser }}
        displayName: Install browsers

      - script: |
          npx playwright test \
            --project=${{ parameters.browser }} \
            --shard=$(System.JobPositionInPhase)/$(System.TotalJobsInPhase) \
            --reporter=junit,html
        displayName: Run Playwright tests
        env:
          BASE_URL: $(BASE_URL)
          PLAYWRIGHT_JUNIT_OUTPUT_NAME: 'test-results-$(System.JobPositionInPhase).xml'

      - task: PublishTestResults@2
        condition: always()
        inputs:
          testResultsFormat: 'JUnit'
          testResultsFiles: 'test-results-*.xml'

      - task: PublishPipelineArtifact@1
        condition: always()
        inputs:
          targetPath: 'playwright-report'
          artifact: 'playwright-report-$(System.JobPositionInPhase)'
```

## K6 (Docker + exit code como gate)

```yaml
# .azure-pipelines/templates/k6.yml
parameters:
  - name: scenario
    type: string
    default: 'load.js'
  - name: vus
    type: number
    default: 50
  - name: duration
    type: string
    default: '5m'

jobs:
  - job: K6LoadTest
    pool:
      name: 'self-hosted-load'  # NO usar shared pool
    steps:
      - script: |
          docker run --rm \
            -v $(System.DefaultWorkingDirectory):/scripts \
            -e BASE_URL=$(BASE_URL) \
            -e AUTH_TOKEN=$(AUTH_TOKEN) \
            grafana/k6 run \
            --vus ${{ parameters.vus }} \
            --duration ${{ parameters.duration }} \
            --summary-export=/scripts/summary.json \
            --out json=/scripts/results.json \
            /scripts/${{ parameters.scenario }}
        displayName: Run K6 load test

      - task: PublishPipelineArtifact@1
        condition: always()
        inputs:
          targetPath: 'summary.json'
          artifact: 'k6-summary'

      - task: PublishPipelineArtifact@1
        condition: always()
        inputs:
          targetPath: 'results.json'
          artifact: 'k6-raw-results'
```

El exit code de `k6 run` es no-zero si fallan los thresholds definidos en el script (`thresholds: { http_req_duration: ['p(95)<500'] }`). Esto fail-fast el pipeline sin necesidad de gates adicionales.

## Appium (Gradle + Appium Server + cloud creds)

```yaml
# .azure-pipelines/templates/appium.yml
parameters:
  - name: platform
    type: string
    default: 'android'  # android | ios
  - name: provider
    type: string
    default: 'browserstack'  # local | browserstack | saucelabs

jobs:
  - job: AppiumTests
    pool:
      vmImage: ${{ iif(eq(parameters.platform, 'ios'), 'macOS-latest', 'ubuntu-latest') }}
    steps:
      - task: JavaToolInstaller@0
        inputs:
          versionSpec: '17'
          jdkSourceOption: 'PreInstalled'

      - ${{ if eq(parameters.provider, 'local') }}:
          - script: |
              npm install -g appium@2
              appium driver install uiautomator2
              appium &
              sleep 10
            displayName: Start Appium Server

      - task: Gradle@3
        inputs:
          gradleWrapperFile: 'gradlew'
          tasks: 'test'
          options: |
            -Pplatform=${{ parameters.platform }} \
            -Pprovider=${{ parameters.provider }}
          publishJUnitResults: true
          testResultsFiles: '**/build/test-results/test/*.xml'
        env:
          BROWSERSTACK_USERNAME: $(BROWSERSTACK_USERNAME)
          BROWSERSTACK_ACCESS_KEY: $(BROWSERSTACK_ACCESS_KEY)
          SAUCE_USERNAME: $(SAUCE_USERNAME)
          SAUCE_ACCESS_KEY: $(SAUCE_ACCESS_KEY)

      - task: PublishPipelineArtifact@1
        condition: always()
        inputs:
          targetPath: 'build/reports/tests/test'
          artifact: 'appium-html-report'
```

## Pipeline orquestador (ejemplo PR)

```yaml
# .azure-pipelines/pipeline-pr.yml
trigger: none
pr:
  branches:
    include:
      - main
      - develop

variables:
  - group: qa-secrets-vault  # variable group ligado a Azure Key Vault

stages:
  - stage: FastFeedback
    jobs:
      - template: templates/karate.yml
        parameters:
          tags: '@smoke'
          threads: 4
      - template: templates/playwright.yml
        parameters:
          shardTotal: 4
          browser: 'chromium'
```

## Notas

- Para variable groups con Key Vault, ver `secrets-in-pipelines.md`.
- Para Allure aggregation post-execution, agregar stage `AllureReport` después de las suites.
- `failTaskOnFailedTests: true` es **obligatorio** en `PublishTestResults` — sin esto, el pipeline pasa aunque haya fallos.
