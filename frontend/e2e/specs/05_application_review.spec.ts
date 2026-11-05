import { test, expect } from '@playwright/test';
import { ApplicationReviewPage } from '../pages/ApplicationReviewPage';

test.describe('Workflow 5: Human-in-the-Loop Application Review & Confirmation', () => {
  let reviewPage: ApplicationReviewPage;

  test('should enforce mandatory human review checklist before submission', async ({ page, request }) => {
    // 1. Create a fresh application via backend API to have an active application to review
    const uniqueId = Date.now();
    const appResp = await request.post('http://localhost:8000/api/v1/apply?sync_execution=true', {
      data: {
        job_text: (
          `Title: Lead Site Reliability Engineer ${uniqueId}\n` +
          `Company: CyberFortress Global ${uniqueId}\n` +
          'Requirements: Python, Linux, Docker, PostgreSQL'
        )
      }
    });
    expect(appResp.ok()).toBeTruthy();
    const appData = await appResp.json();
    const appId = appData.id;

    // 2. Open review page for this application
    reviewPage = new ApplicationReviewPage(page);
    await reviewPage.goto(appId);

    // 3. Verify submission buttons are disabled BEFORE checking the verification checklist
    await expect(reviewPage.confirmSubmittedBtn).toBeDisabled();
    await expect(reviewPage.preparePackageBtn).toBeDisabled();

    // 4. Complete the 3 mandatory checklist items
    await reviewPage.completeHumanChecklist();
    await expect(reviewPage.confirmSubmittedBtn).toBeEnabled();

    // 5. Edit tailored resume and cover letter
    await reviewPage.tailoredResumeEditor.fill('Alex Rivera - Verified & Tailored Resume for CyberFortress');
    await reviewPage.coverLetterEditor.fill('Dear CyberFortress Hiring Team,\n\nI am thrilled to apply for the SRE role.');
    await reviewPage.notesInput.fill('Completed technical alignment review.');

    // 6. Save edits
    await reviewPage.saveChangesBtn.click();
    await expect(reviewPage.successAlert).toBeVisible({ timeout: 15000 });
    const successMsg = await reviewPage.getSuccessMessage();
    expect(successMsg).toContain('successfully saved');

    // 7. Confirm submission with verified candidate action
    await reviewPage.confirmSubmittedBtn.click();
    await expect(reviewPage.successAlert).toBeVisible({ timeout: 15000 });

    // 8. Verify audit trail logs the activity
    await expect(reviewPage.auditTimeline).toBeVisible();
    const timelineText = await reviewPage.auditTimeline.textContent();
    expect(timelineText).toContain('Audit Trail');
  });
});
