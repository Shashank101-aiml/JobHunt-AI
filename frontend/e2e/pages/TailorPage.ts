import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class TailorPage extends BasePage {
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
    return this.page.locator('button:has-text("+ Custom Job Text"), button:has-text("Use Saved Job")');
  }

  get textareaCustomJob(): Locator {
    return this.page.locator('textarea[placeholder*="Paste direct job description text"]');
  }

  get startTailoringBtn(): Locator {
    return this.page.locator('button:has-text("Generate Tailored Package")');
  }

  get tailoredResumeTextarea(): Locator {
    return this.page.locator('div.bg-white:has(h3:has-text("Tailored Resume Text")) > textarea');
  }

  get coverLetterTextarea(): Locator {
    return this.page.locator('div.bg-white:has(h3:has-text("Tailored Cover Letter")) > textarea');
  }

  get saveChangesBtn(): Locator {
    return this.page.locator('button:has-text("Save Manual Edits")');
  }

  get downloadDocxBtn(): Locator {
    return this.page.locator('button:has-text("Download DOCX Resume")');
  }

  get reviewApplicationBtn(): Locator {
    return this.page.locator('button:has-text("Go to Final Submission & Review")');
  }

  async goto(): Promise<void> {
    await this.page.goto('/tailor');
    await this.waitForPageLoaded();
  }

  async triggerTailoring(customJobText?: string): Promise<void> {
    if (customJobText) {
      const toggle = this.buttonToggleCustomJob;
      if (await toggle.isVisible()) {
        const text = await toggle.textContent();
        if (text && text.includes('+ Custom Job Text')) {
          await toggle.click();
        }
      }
      await this.textareaCustomJob.fill(customJobText);
    }
    await this.startTailoringBtn.click();
  }
}
