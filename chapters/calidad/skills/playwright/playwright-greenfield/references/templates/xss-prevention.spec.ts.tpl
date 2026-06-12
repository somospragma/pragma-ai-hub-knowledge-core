import { test, expect, Page } from '@playwright/test';

/**
 * Security smoke suite — XSS, SQLi probes, and security headers.
 * Tag: @security. Runs as part of the regression gate; non-blocking for smoke.
 *
 * Replace {{pages_with_inputs}} with the list of routes that expose user inputs,
 * and {{api_endpoint_to_probe}} with the backend URL whose response headers
 * are inspected (e.g. https://api.example.com/health).
 */

const XSS_PAYLOAD = '<script>alert(1)</script>';
const SQLI_PAYLOAD = "'; DROP TABLE users; --";

let alertFired = false;

test.describe('Security smoke - XSS & SQLi probes', { tag: ['@security'] }, () => {

  test.beforeEach(async ({ page }) => {
    alertFired = false;
    page.on('dialog', async (dialog) => {
      alertFired = true;
      await dialog.dismiss();
    });
  });

  test('XSS payload is not executed in any input - {{pages_with_inputs}}',
    async ({ page }) => {
      await page.goto('{{pages_with_inputs}}');

      const inputs = page.locator('input:not([type="hidden"]), textarea');
      const count = await inputs.count();
      expect(count, 'no inputs found to probe').toBeGreaterThan(0);

      for (let i = 0; i < count; i++) {
        const input = inputs.nth(i);
        if (!(await input.isVisible())) continue;
        await input.fill(XSS_PAYLOAD);
        await input.blur();
      }

      // No JS alert from the payload must have fired.
      expect(alertFired, 'XSS payload triggered an alert dialog').toBe(false);

      // The rendered DOM must not contain an actual <script> node from the payload.
      const injectedScripts = await page.evaluate((payload) => {
        return Array.from(document.scripts).filter((s) => s.textContent?.includes(payload)).length;
      }, 'alert(1)');
      expect(injectedScripts, 'injected <script> survived in the DOM').toBe(0);
    }
  );

  test('SQLi probe is not reflected verbatim - {{pages_with_inputs}}',
    async ({ page }) => {
      await page.goto('{{pages_with_inputs}}');

      const inputs = page.locator('input:not([type="hidden"]), textarea');
      const count = await inputs.count();

      for (let i = 0; i < count; i++) {
        const input = inputs.nth(i);
        if (!(await input.isVisible())) continue;
        await input.fill(SQLI_PAYLOAD);
        await input.blur();
      }

      const bodyHTML = await page.content();
      // The literal payload must not be rendered unescaped as an error stack trace.
      expect(bodyHTML).not.toContain('syntax error at or near');
      expect(bodyHTML).not.toContain('SQLSTATE');
    }
  );
});

test.describe('Security headers', { tag: ['@security'] }, () => {

  test('response exposes hardening headers - {{api_endpoint_to_probe}}',
    async ({ request }) => {
      const response = await request.get('{{api_endpoint_to_probe}}');
      const headers = response.headers();

      expect(headers['x-frame-options'] || headers['content-security-policy'],
        'missing X-Frame-Options or CSP frame-ancestors').toBeTruthy();
      expect(headers['content-security-policy'],
        'missing Content-Security-Policy header').toBeTruthy();
      expect(headers['strict-transport-security'],
        'missing Strict-Transport-Security header').toBeTruthy();
    }
  );
});
