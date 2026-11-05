import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class ApplicationsPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  get searchInput(): Locator {
    return this.page.locator('input[placeholder*="Search applications"]');
  }

  get filterStatusSelect(): Locator {
    return this.page.locator('select').first();
  }

  get applicationCards(): Locator {
    return this.page.locator('div.rounded-2xl:has(h3.font-bold)');
  }

  get newApplicationBtn(): Locator {
    return this.page.locator('button:has-text("New Application / Tailor")');
  }

  async goto(): Promise<void> {
    await this.page.goto('/applications');
    await this.waitForPageLoaded();
  }

  async filterByStatus(status: string): Promise<void> {
    await this.filterStatusSelect.selectOption(status);
  }
}
