import { test, expect } from '@playwright/test';
import { JobsPage } from '../pages/JobsPage';

test.describe('Workflow 2: Job Discovery & Manual Submission', () => {
  let jobsPage: JobsPage;

  test.beforeEach(async ({ page }) => {
    jobsPage = new JobsPage(page);
    await jobsPage.goto();
  });

  test('should successfully submit a manual job description and parse details', async () => {
    const uniqueCompany = `Apex Systems ${Date.now()}`;
    await jobsPage.submitManualJob({
      title: 'Senior Distributed Systems Engineer',
      company: uniqueCompany,
      location: 'Remote',
      employmentType: 'Full-Time',
      description: (
        'Title: Senior Distributed Systems Engineer\n' +
        `Company: ${uniqueCompany}\n` +
        'Requirements:\n' +
        '- 5+ years of experience in Python and FastAPI\n' +
        '- Expertise with PostgreSQL databases, Redis caching, and Docker\n' +
        'Responsibilities:\n' +
        '- Architect resilient distributed services'
      ),
      sourceUrl: `https://apex-${Date.now()}.example.com/careers/101`
    });

    await expect(jobsPage.successAlert).toBeVisible({ timeout: 15000 });
    const msg = await jobsPage.getSuccessMessage();
    expect(msg).toContain('Successfully saved and normalized job');
  });

  test('should reject short job descriptions with less than 20 characters', async () => {
    await jobsPage.submitManualJob({
      title: 'Developer',
      description: 'Too short text'
    });

    await expect(jobsPage.errorAlert).toBeVisible({ timeout: 10000 });
    const msg = await jobsPage.getErrorMessage();
    expect(msg).toContain('at least 20 characters long');
  });

  test('should gracefully handle restricted domain scraping attempt', async () => {
    await jobsPage.submitScrapeJob('https://www.linkedin.com/jobs/view/12345678');
    await expect(jobsPage.errorAlert).toBeVisible({ timeout: 15000 });
    const msg = await jobsPage.getErrorMessage();
    expect(msg).toContain('linkedin.com');
  });
});
