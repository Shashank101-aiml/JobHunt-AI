import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export interface ManualJobData {
  title?: string;
  company?: string;
  location?: string;
  employmentType?: string;
  description: string;
  sourceUrl?: string;
}

export class JobsPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  get tabBrowse(): Locator {
    return this.page.locator('button:has-text("Browse Jobs")');
  }

  get tabManual(): Locator {
    return this.page.locator('button:has-text("Manual Input")');
  }

  get tabScrape(): Locator {
    return this.page.locator('button:has-text("Scrape URL")');
  }

  // Manual Form Locators
  get inputTitle(): Locator {
    return this.page.locator('input[placeholder*="Senior Backend Engineer"]');
  }

  get inputCompany(): Locator {
    return this.page.locator('input[placeholder*="Stripe, Acme Corp"]');
  }

  get inputLocation(): Locator {
    return this.page.locator('input[placeholder*="Remote, San Francisco"]');
  }

  get selectEmpType(): Locator {
    return this.page.locator('form select');
  }

  get textareaDescription(): Locator {
    return this.page.locator('textarea[placeholder*="Paste the full job posting"]');
  }

  get inputSourceUrl(): Locator {
    return this.page.locator('input[placeholder*="https://jobs.example.com"]');
  }

  get submitManualBtn(): Locator {
    return this.page.locator('button:has-text("Save & Normalize Job")');
  }

  // Scrape Form Locators
  get inputScrapeUrl(): Locator {
    return this.page.locator('input[placeholder*="boards.greenhouse.io"]');
  }

  get submitScrapeBtn(): Locator {
    return this.page.locator('button:has-text("Retrieve Job Posting")');
  }

  // Job List
  get jobCards(): Locator {
    return this.page.locator('div.rounded-2xl:has(h3.font-bold)');
  }

  async goto(): Promise<void> {
    await this.page.goto('/jobs');
    await this.waitForPageLoaded();
  }

  async submitManualJob(data: ManualJobData): Promise<void> {
    await this.tabManual.click();
    if (data.title) await this.inputTitle.fill(data.title);
    if (data.company) await this.inputCompany.fill(data.company);
    if (data.location) await this.inputLocation.fill(data.location);
    if (data.employmentType) await this.selectEmpType.selectOption(data.employmentType);
    if (data.sourceUrl) await this.inputSourceUrl.fill(data.sourceUrl);
    await this.textareaDescription.fill(data.description);
    await this.submitManualBtn.click();
  }

  async submitScrapeJob(url: string): Promise<void> {
    await this.tabScrape.click();
    await this.inputScrapeUrl.fill(url);
    await this.submitScrapeBtn.click();
  }
}
