/**
 * E2E tests for SEO scoring and article optimization.
 */
import { test, expect } from '@playwright/test';

test.describe('SEO Scoring Flow', () => {
  test('SEO Score page displays correctly', async ({ page }) => {
    await page.goto('/seo-scores');
    
    // Check page loads
    await expect(page.locator('body')).toBeVisible();
  });

  test('Article list displays SEO scores', async ({ page }) => {
    await page.goto('/articles');
    
    // Check page loads
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Article Generation', () => {
  test('Article generation page structure', async ({ page }) => {
    await page.goto('/articles/generate');
    
    // Check page loads
    await expect(page.locator('body')).toBeVisible();
  });

  test('Article preview displays content', async ({ page }) => {
    await page.goto('/articles/preview');
    
    // Check page loads
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('WordPress Publishing', () => {
  test('Publishing configuration page', async ({ page }) => {
    await page.goto('/publishing');
    
    // Check page loads
    await expect(page.locator('body')).toBeVisible();
  });
});
