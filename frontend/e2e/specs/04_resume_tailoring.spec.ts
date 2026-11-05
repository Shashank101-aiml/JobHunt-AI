import { test, expect } from '@playwright/test';
import { TailorPage } from '../pages/TailorPage';

test.describe('Workflow 4: AI Resume Tailoring & Generation', () => {
  let tailorPage: TailorPage;

  test.beforeEach(async ({ page }) => {
    tailorPage = new TailorPage(page);
    await tailorPage.goto();
  });

  test('should trigger tailoring workflow and display generated application package', async () => {
    const jobDescription = (
      'Title: Python Cloud Platform Architect\n' +
      'Company: Nimbus Systems\n' +
      'Requirements:\n' +
      '- Python, FastAPI, Docker, Kubernetes, PostgreSQL\n' +
      '- 5+ years experience designing cloud microservices'
    );

    await tailorPage.triggerTailoring(jobDescription);

    // Verify loading spinner or process completion
    await expect(tailorPage.tailoredResumeTextarea).toBeVisible({ timeout: 40000 });
    const tailoredContent = await tailorPage.tailoredResumeTextarea.inputValue();
    expect(tailoredContent.length).toBeGreaterThan(50);

    // Verify cover letter was also generated
    await expect(tailorPage.coverLetterTextarea).toBeVisible();
    const coverLetterContent = await tailorPage.coverLetterTextarea.inputValue();
    expect(coverLetterContent.length).toBeGreaterThan(50);
  });

  test('should validate custom job text length before allowing generation', async () => {
    const toggle = tailorPage.buttonToggleCustomJob;
    if (await toggle.isVisible()) {
      const text = await toggle.textContent();
      if (text && text.includes('+ Custom Job Text')) {
        await toggle.click();
      }
    }
    await tailorPage.textareaCustomJob.fill('Too short');
    await tailorPage.startTailoringBtn.click();

    await expect(tailorPage.errorAlert).toBeVisible({ timeout: 10000 });
    const errorMsg = await tailorPage.getErrorMessage();
    expect(errorMsg).toContain('at least 20 characters');
  });
});
