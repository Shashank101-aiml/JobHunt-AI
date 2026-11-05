import { test, expect } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';
import { ResumesPage } from '../pages/ResumesPage';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const FIXTURES_DIR = path.resolve(__dirname, '../fixtures/test_resumes');

test.describe('Workflow 1: Candidate Resume Management', () => {
  let resumesPage: ResumesPage;

  test.beforeEach(async ({ page }) => {
    resumesPage = new ResumesPage(page);
    await resumesPage.goto();
  });

  test('should successfully upload and parse a valid TXT resume', async () => {
    const txtPath = path.join(FIXTURES_DIR, 'sample_backend_resume.txt');
    await resumesPage.uploadResume(txtPath);
    await expect(resumesPage.successAlert).toBeVisible({ timeout: 15000 });
    const msg = await resumesPage.getSuccessMessage();
    expect(msg).toContain('sample_backend_resume.txt');
  });

  test('should successfully upload and parse a valid DOCX resume', async () => {
    const docxPath = path.join(FIXTURES_DIR, 'sample_fullstack_resume.docx');
    await resumesPage.uploadResume(docxPath);
    await expect(resumesPage.successAlert).toBeVisible({ timeout: 15000 });
    const msg = await resumesPage.getSuccessMessage();
    expect(msg).toContain('sample_fullstack_resume.docx');
  });

  test('should successfully upload and parse a valid PDF resume', async () => {
    const pdfPath = path.join(FIXTURES_DIR, 'sample_resume.pdf');
    await resumesPage.uploadResume(pdfPath);
    await expect(resumesPage.successAlert).toBeVisible({ timeout: 15000 });
    const msg = await resumesPage.getSuccessMessage();
    expect(msg).toContain('sample_resume.pdf');
  });

  test('should reject unsupported file formats (JPG image)', async () => {
    const invalidPath = path.join(FIXTURES_DIR, 'invalid_file.jpg');
    await resumesPage.uploadResume(invalidPath);
    await expect(resumesPage.errorAlert).toBeVisible({ timeout: 10000 });
    const errorMsg = await resumesPage.getErrorMessage();
    expect(errorMsg).toContain("Unsupported file format '.jpg'");
  });

  test('should reject empty resume files', async () => {
    const emptyPath = path.join(FIXTURES_DIR, 'empty_resume.txt');
    await resumesPage.uploadResume(emptyPath);
    await expect(resumesPage.errorAlert).toBeVisible({ timeout: 10000 });
    const errorMsg = await resumesPage.getErrorMessage();
    expect(errorMsg).toContain('Selected file is empty');
  });
});
