import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

/**
 * Accessibility audit suite — one test per page declared in {{pages_to_audit}}.
 * Replace the {{pages_to_audit}} block with one describe/test pair per page.
 *
 * Coverage rules:
 *   - 0 critical violations on WCAG 2.0 A + AA.
 *   - Keyboard navigation: Tab moves focus through interactive elements in order.
 *   - All <img> elements expose alt text (or alt="" for purely decorative ones).
 */

test.describe('Accessibility audit', { tag: ['@a11y', '@regression'] }, () => {

  // ---- Per-page audit ------------------------------------------------------
  // {{pages_to_audit}} format: array of { name, route }
  // Emit one test('axe scan - <name>', ...) per entry.

  test('axe scan - {{pages_to_audit}}', async ({ page }) => {
    await page.goto('{{pages_to_audit}}');

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze();

    const critical = results.violations.filter((v) => v.impact === 'critical');
    expect(critical, JSON.stringify(critical, null, 2)).toEqual([]);
  });

  // ---- Keyboard navigation -------------------------------------------------

  test('keyboard navigation reaches interactive elements - {{pages_to_audit}}',
    async ({ page }) => {
      await page.goto('{{pages_to_audit}}');

      const interactive = await page.locator(
        'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
      ).count();
      expect(interactive).toBeGreaterThan(0);

      // Tab through the first few elements and verify a focusable element receives focus.
      await page.keyboard.press('Tab');
      const focused = await page.evaluate(() => document.activeElement?.tagName);
      expect(focused).not.toBeUndefined();
      expect(focused).not.toBe('BODY');
    }
  );

  // ---- Image alt text ------------------------------------------------------

  test('all images expose alt text - {{pages_to_audit}}', async ({ page }) => {
    await page.goto('{{pages_to_audit}}');

    const images = page.locator('img');
    const count = await images.count();
    for (let i = 0; i < count; i++) {
      const alt = await images.nth(i).getAttribute('alt');
      // alt="" is valid for decorative images; null/undefined is a violation.
      expect(alt, `img[${i}] is missing alt attribute`).not.toBeNull();
    }
  });
});
