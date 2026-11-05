import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class MatchPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  get selectResume(): Locator {
    return this.page.locator('form select').first();
  }

  get selectJob(): Locator {
    return this.page.locator('form select').nth(1);
  }

  get buttonToggleCustomJob(): Locator {
    return this.page.locator('button:has-text("+ Paste Custom JD"), button:has-text("Select from Saved Jobs")');
  }

  get textareaCustomJob(): Locator {
    return this.page.locator('textarea[placeholder*="Paste direct job description text"]');
  }

  get evaluateButton(): Locator {
    return this.page.locator('button:has-text("Calculate ATS Match Score")');
  }

  get scoreDisplay(): Locator {
    return this.page.locator('.rounded-full.border-4 span.text-3xl');
  }

  get subscoresBreakdown(): Locator {
    return this.page.locator('h3:has-text("Transparent Subscore Breakdown")');
  }

  get matchedSkillsList(): Locator {
    return this.page.locator('h3:has-text("Matched Skills & Requirements")');
  }

  get recommendationsList(): Locator {
    return this.page.locator('h3:has-text("Actionable ATS Improvement Recommendations")');
  }

  async goto(): Promise<void> {
    await this.page.goto('/match');
    await this.waitForPageLoaded();
  }

  async triggerEvaluation(customJobText?: string): Promise<void> {
    if (customJobText) {
      const toggleBtn = this.buttonToggleCustomJob;
      if (await toggleBtn.isVisible()) {
        const text = await toggleBtn.textContent();
        if (text && text.includes('+ Paste Custom JD')) {
          await toggleBtn.click();
        }
      }
      await this.textareaCustomJob.fill(customJobText);
    }
    await this.evaluateButton.click();
  }
}
