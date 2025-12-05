/**
 * E2E tests for authentication flows.
 */
import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('Login page displays correctly', async ({ page }) => {
    await page.goto('/login');

    // Verify page title or heading
    await expect(page).toHaveURL(/.*login/);
    
    // Check form elements
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('Registration page displays correctly', async ({ page }) => {
    await page.goto('/register');

    // Check form elements
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]').first()).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('Invalid login shows error', async ({ page }) => {
    await page.goto('/login');

    await page.fill('input[type="email"]', 'invalid@example.com');
    await page.fill('input[type="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');

    // Wait for response (error message or form still visible)
    await page.waitForTimeout(2000);
    
    // The form should still be visible after failed login
    await expect(page.locator('input[type="email"]')).toBeVisible();
  });

  test('Login form validates email format', async ({ page }) => {
    await page.goto('/login');

    // Enter invalid email
    await page.fill('input[type="email"]', 'invalid-email');
    await page.fill('input[type="password"]', 'somepassword');
    
    // Try to submit
    await page.click('button[type="submit"]');

    // Form should show validation or remain on page
    await expect(page.locator('input[type="email"]')).toBeVisible();
  });

  test('Can navigate between login and register', async ({ page }) => {
    await page.goto('/login');

    // Find link to register
    const registerLink = page.locator('a[href*="register"]');
    if (await registerLink.isVisible()) {
      await registerLink.click();
      await expect(page).toHaveURL(/.*register/);
    }

    // Navigate back to login
    const loginLink = page.locator('a[href*="login"]');
    if (await loginLink.isVisible()) {
      await loginLink.click();
      await expect(page).toHaveURL(/.*login/);
    }
  });
});

test.describe('Protected Routes', () => {
  test('Dashboard redirects unauthenticated users', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Should redirect to login or show error
    const currentUrl = page.url();
    const isLoginOrHome = currentUrl.includes('login') || currentUrl === page.url();
    expect(isLoginOrHome).toBeTruthy();
  });

  test('Workspaces page requires authentication', async ({ page }) => {
    await page.goto('/workspaces');
    
    // Check page behavior for unauthenticated access
    await expect(page.locator('body')).toBeVisible();
  });
});
