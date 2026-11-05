import { test, expect } from '@playwright/test';
import { ApplicationReviewPage } from '../pages/ApplicationReviewPage';
import fs from 'fs';
import path from 'path';

test.describe('Workflow 6: Tailored Resume DOCX Export & Verification', () => {
  test('should trigger DOCX download and verify file integrity', async ({ page, request }) => {
    // 1. Ensure an application with tailored resume text exists
    const uniqueId = Date.now();
    const appResp = await request.post('http://localhost:8000/api/v1/apply?sync_execution=true', {
      data: {
        job_text: (
          `Title: Senior Platform Engineer ${uniqueId}\n` +
          `Company: VectorEdge Inc ${uniqueId}\n` +
          'Requirements: Python, FastAPI, Docker, PostgreSQL'
        )
      }
    });
    expect(appResp.ok()).toBeTruthy();
    const appData = await appResp.json();
    const appId = appData.id;

    // 2. Navigate to Application Review page
    const reviewPage = new ApplicationReviewPage(page);
    await reviewPage.goto(appId);

    // 3. Trigger DOCX export and intercept the download event
    const [download] = await Promise.all([
      page.waitForEvent('download', { timeout: 20000 }),
      reviewPage.exportDocxBtn.click()
    ]);

    // 4. Validate filename and extension
    const filename = download.suggestedFilename();
    expect(filename).toMatch(/\.docx$/i);
    expect(filename).toContain(`tailored_resume_app_${appId}`);

    // 5. Verify file is not empty
    const downloadPath = await download.path();
    expect(downloadPath).toBeTruthy();
    if (downloadPath) {
      const stats = fs.statSync(downloadPath);
      expect(stats.size).toBeGreaterThan(1000); // Valid DOCX document has headers and XML parts > 1KB
    }
  });
});
