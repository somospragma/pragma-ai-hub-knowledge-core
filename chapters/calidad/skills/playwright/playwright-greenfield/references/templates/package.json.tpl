{
  "name": "{{project_name}}",
  "version": "1.0.0",
  "private": true,
  "description": "Playwright E2E test suite for {{project_name}}",
  "scripts": {
    "test": "playwright test --grep @live",
    "test:live": "playwright test --grep @live",
    "test:mocked": "playwright test --grep @mocked",
    "test:hybrid": "playwright test --grep @hybrid",
    "test:all": "playwright test",
    "test:headed": "playwright test --headed",
    "test:ui": "playwright test --ui",
    "test:debug": "playwright test --debug",
    "test:visual": "playwright test tests/visual.spec.ts",
    "test:a11y": "playwright test tests/a11y-audit.spec.ts",
    "test:security": "playwright test --grep @security",
    "report": "playwright show-report",
    "lint": "eslint ."
  },
  "devDependencies": {
    "@playwright/test": "^1.45.0",
    "@axe-core/playwright": "^4.9.0",
    "@typescript-eslint/eslint-plugin": "^7.0.0",
    "@typescript-eslint/parser": "^7.0.0",
    "eslint": "^8.57.0",
    "eslint-plugin-playwright": "^1.6.0",
    "typescript": "^5.4.0"
  },
  "eslintConfig": {
    "root": true,
    "parser": "@typescript-eslint/parser",
    "plugins": ["@typescript-eslint", "playwright"],
    "extends": [
      "eslint:recommended",
      "plugin:@typescript-eslint/recommended",
      "plugin:playwright/recommended"
    ],
    "rules": {
      "no-restricted-syntax": ["error", {
        "selector": "MemberExpression[property.name='waitForTimeout']",
        "message": "Prohibido waitForTimeout. Usa waitForResponse, waitFor({state:'visible'}) o expect().not.toHaveText()."
      }],
      "playwright/no-skipped-test": "error",
      "playwright/no-focused-test": "error",
      "playwright/no-wait-for-timeout": "error"
    }
  }
}
