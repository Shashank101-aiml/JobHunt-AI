import { test, expect } from '@playwright/test';
import { MatchPage } from '../pages/MatchPage';

test.describe('Workflow 3: ATS Score Evaluation & Gap Analysis', () => {
  let matchPage: MatchPage;

  test.beforeEach(async ({ page }) => {
    matchPage = new MatchPage(page);
    await matchPage.goto();
  });

  test('should evaluate ATS match and display score, subscores, and recommendations', async () => {
    const jobDescription = (
      'Title: Senior Backend Developer\n' +
      'Company: CloudNova Labs\n' +
      'Requirements:\n' +
      '- 4+ years of Python and FastAPI production experience\n' +
      '- PostgreSQL database optimization\n' +
      '- Docker containerization\n' +
      'Nice to have: Redis caching'
    );

    await matchPage.triggerEvaluation(jobDescription);

    // Assert score breakdown card is visible
    await expect(matchPage.scoreDisplay).toBeVisible({ timeout: 20000 });
    const scoreText = await matchPage.scoreDisplay.textContent();
    expect(scoreText).toMatch(/\d+/);

    // Verify subscores breakdown
    await expect(matchPage.subscoresBreakdown).toBeVisible();

    // Verify recommendations are surfaced
    await expect(matchPage.recommendationsList).toBeVisible();
  });

  test('should validate input requirements before triggering evaluation', async () => {
    const toggle = matchPage.buttonToggleCustomJob;
    if (await toggle.isVisible()) {
      const text = await toggle.textContent();
      if (text && text.includes('+ Paste Custom JD')) {
        await toggle.click();
      }
    }
    await matchPage.textareaCustomJob.fill('Short text');
    await matchPage.evaluateButton.click();

    await expect(matchPage.errorAlert).toBeVisible({ timeout: 10000 });
    const errorMsg = await matchPage.getErrorMessage();
    expect(errorMsg).toContain('at least 20 characters');
  });
});
