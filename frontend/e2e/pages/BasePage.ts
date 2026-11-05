import { Page, Locator, expect } from '@playwright/test';

export class BasePage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  // Common Header & Navigation Locators
  get navResumes(): Locator {
    return this.page.locator('a[href="/resumes"], nav a:has-text("Resumes")');
  }

  get navJobs(): Locator {
    return this.page.locator('a[href="/jobs"], nav a:has-text("Jobs")');
  }

  get navMatch(): Locator {
    return this.page.locator('a[href="/match"], nav a:has-text("Match")');
  }

  get navTailor(): Locator {
    return this.page.locator('a[href="/tailor"], nav a:has-text("Tailor")');
  }

  get navApplications(): Locator {
    return this.page.locator('a[href="/applications"], nav a:has-text("Applications")');
  }

  get navSettings(): Locator {
    return this.page.locator('a[href="/settings"], nav a:has-text("Settings")');
  }

  get errorAlert(): Locator {
    return this.page.locator('div.rounded-xl.bg-rose-50');
  }

  get successAlert(): Locator {
    return this.page.locator('div.rounded-xl.bg-emerald-50');
  }

  get loadingSpinner(): Locator {
    return this.page.locator('.animate-spin');
  }

  async waitForPageLoaded(): Promise<void> {
    await this.page.waitForLoadState('domcontentloaded');
  }

  async getErrorMessage(): Promise<string | null> {
    if (await this.errorAlert.isVisible()) {
      return await this.errorAlert.textContent();
    }
    return null;
  }

  async getSuccessMessage(): Promise<string | null> {
    if (await this.successAlert.isVisible()) {
      return await this.successAlert.textContent();
    }
    return null;
  }
}
