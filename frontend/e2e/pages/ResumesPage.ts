import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class ResumesPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  get fileInput(): Locator {
    return this.page.locator('input[type="file"]');
  }

  get dropzone(): Locator {
    return this.page.locator('div:has-text("Drag & drop your resume")').first();
  }

  get browseButton(): Locator {
    return this.page.locator('button:has-text("Browse Files")');
  }

  get resumeCards(): Locator {
    return this.page.locator('.grid > div.bg-white, div.rounded-2xl:has-text(".pdf"), div.rounded-2xl:has-text(".docx"), div.rounded-2xl:has-text(".txt")');
  }

  async goto(): Promise<void> {
    await this.page.goto('/resumes');
    await this.waitForPageLoaded();
  }

  async uploadResume(filePath: string): Promise<void> {
    await this.fileInput.setInputFiles(filePath);
  }

  async activateResume(filename: string): Promise<void> {
    const card = this.page.locator(`div:has-text("${filename}")`).first();
    const activateBtn = card.locator('button:has-text("Set Active")');
    if (await activateBtn.isVisible()) {
      await activateBtn.click();
    }
  }

  async deleteResume(filename: string): Promise<void> {
    const card = this.page.locator(`div:has-text("${filename}")`).first();
    const deleteBtn = card.locator('button:has(svg.lucide-trash-2), button[title*="Delete"]');
    if (await deleteBtn.isVisible()) {
      await deleteBtn.click();
    }
  }

  async getUploadedFilenames(): Promise<string[]> {
    const cards = this.page.locator('h3.font-bold');
    return await cards.allTextContents();
  }
}
