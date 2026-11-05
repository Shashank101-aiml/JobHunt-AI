import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class ApplicationReviewPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  // 3 Mandatory Human Review Checkboxes
  get checklistCheckboxes(): Locator {
    return this.page.locator('.bg-indigo-900 input[type="checkbox"]');
  }

  get checkContact(): Locator {
    return this.checklistCheckboxes.nth(0);
  }

  get checkTruth(): Locator {
    return this.checklistCheckboxes.nth(1);
  }

  get checkRequirements(): Locator {
    return this.checklistCheckboxes.nth(2);
  }

  // Content Editors
  get tailoredResumeEditor(): Locator {
    return this.page.locator('div.bg-white:has(h3:has-text("Tailored Resume Content")) > textarea');
  }

  get coverLetterEditor(): Locator {
    return this.page.locator('div.bg-white:has(h3:has-text("Personalized Cover Letter")) > textarea');
  }

  get notesInput(): Locator {
    return this.page.locator('input[placeholder*="personal notes"]');
  }

  get saveChangesBtn(): Locator {
    return this.page.locator('button:has-text("Save Changes")');
  }

  get exportDocxBtn(): Locator {
    return this.page.locator('button:has-text("Export DOCX")');
  }

  // Submission Selectors
  get optionManualSubmission(): Locator {
    return this.page.locator('div:has-text("Manual Portal Submission")').first();
  }

  get optionEmailSubmission(): Locator {
    return this.page.locator('div:has-text("SMTP Email Delivery")').first();
  }

  get preparePackageBtn(): Locator {
    return this.page.locator('button:has-text("Prepare Submission Package")');
  }

  get confirmSubmittedBtn(): Locator {
    return this.page.locator('button:has-text("Confirm I Have Submitted")');
  }

  // Audit Events
  get auditTimeline(): Locator {
    return this.page.locator('h3:has-text("Audit Trail & Activity History")');
  }

  get statusBadge(): Locator {
    return this.page.locator('.flex.items-center.gap-2 span.rounded-full');
  }

  async goto(appId: number): Promise<void> {
    await this.page.goto(`/applications/${appId}/review`);
    await this.waitForPageLoaded();
  }

  async completeHumanChecklist(): Promise<void> {
    const count = await this.checklistCheckboxes.count();
    for (let i = 0; i < count; i++) {
      const cb = this.checklistCheckboxes.nth(i);
      if (!(await cb.isChecked())) {
        await cb.check();
      }
    }
  }
}
