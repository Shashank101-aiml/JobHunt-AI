import { test, expect } from '@playwright/test';
import { ResumesPage } from '../pages/ResumesPage';
import { JobsPage } from '../pages/JobsPage';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const FIXTURES_DIR = path.resolve(__dirname, '../fixtures/test_resumes');

test.describe('Workflow 7: System Resilience & Error Handling', () => {
  test('should gracefully surface network error when backend is unreachable', async ({ page }) => {
    // Intercept backend API and simulate connection failure
    await page.route('**/api/v1/resumes', (route) => route.abort('failed'));

    const resumesPage = new ResumesPage(page);
    await resumesPage.goto();

    await expect(resumesPage.errorAlert).toBeVisible({ timeout: 15000 });
    const errorText = await resumesPage.getErrorMessage();
    expect(errorText).toMatch(/Unable to connect|Network Error|failed/i);
  });

  test('should display actionable error when backend returns 500 error', async ({ page }) => {
    await page.route('**/api/v1/jobs*', (route) => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Simulated internal server error during job catalog sync' })
      });
    });

    const jobsPage = new JobsPage(page);
    await jobsPage.goto();

    await expect(jobsPage.errorAlert).toBeVisible({ timeout: 15000 });
    const errorText = await jobsPage.getErrorMessage();
    expect(errorText).toContain('Simulated internal server error');
  });

  test('should handle non-existent application review gracefully', async ({ page }) => {
    await page.goto('/applications/999999/review');
    await expect(page.locator('text=Application not found')).toBeVisible({ timeout: 15000 });
    const returnLink = page.locator('button:has-text("Return to Applications")');
    await expect(returnLink).toBeVisible();
  });
});
