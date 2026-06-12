import { test as setup, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const STORAGE_STATE = path.resolve('.auth/user.json');

setup('authenticate', async ({ page }) => {
  // Ensure .auth/ directory exists before saving storage state.
  fs.mkdirSync(path.dirname(STORAGE_STATE), { recursive: true });

  await page.goto('{{login_url}}');

  // Use semantic locators. Adjust labels to the real UI of the SUT.
  await page.getByLabel(/email|usuario|correo/i).fill('{{email}}');
  await page.getByLabel(/password|contraseña/i).fill('{{password}}');
  await page.getByRole('button', { name: /log\s*in|ingresar|iniciar sesi[oó]n/i }).click();

  // Wait for the post-login URL or a stable DOM signal — NEVER waitForTimeout.
  await page.waitForURL('{{expected_url_after_login}}');
  await expect(page).toHaveURL('{{expected_url_after_login}}');

  // Persist auth cookies + localStorage so tests can reuse the session.
  await page.context().storageState({ path: STORAGE_STATE });
});
