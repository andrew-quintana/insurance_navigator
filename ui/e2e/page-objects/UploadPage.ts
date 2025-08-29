import { Page, Locator, expect } from '@playwright/test';

export class UploadPage {
  readonly page: Page;
  readonly fileInput: Locator;
  readonly uploadButton: Locator;
  readonly progressBar: Locator;
  readonly successMessage: Locator;
  readonly documentList: Locator;
  readonly errorMessage: Locator;
  readonly dragDropArea: Locator;
  readonly fileValidationMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.fileInput = page.getByLabel(/upload|file/i);
    this.uploadButton = page.getByRole('button', { name: /upload/i });
    this.progressBar = page.getByRole('progressbar');
    this.successMessage = page.getByText(/upload.*complete|success/i);
    this.documentList = page.getByTestId('document-list');
    this.errorMessage = page.getByRole('alert');
    this.dragDropArea = page.getByTestId('drag-drop-area');
    this.fileValidationMessage = page.getByTestId('file-validation-message');
  }

  async goto() {
    await this.page.goto('/upload');
  }

  async uploadFile(filePath: string) {
    await this.fileInput.setInputFiles(filePath);
    await this.uploadButton.click();
  }

  async dragAndDropFile(filePath: string) {
    if (await this.dragDropArea.isVisible()) {
      // Simulate drag and drop
      await this.page.evaluate((path) => {
        // This would need to be implemented based on your drag and drop implementation
        console.log('Drag and drop file:', path);
      }, filePath);
    } else {
      // Fallback to regular file input
      await this.uploadFile(filePath);
    }
  }

  async waitForUploadComplete() {
    await expect(this.successMessage).toBeVisible({ timeout: 30000 });
  }

  async waitForUploadProgress() {
    await expect(this.progressBar).toBeVisible({ timeout: 10000 });
  }

  async expectDocumentInList(filename: string) {
    await expect(this.documentList.getByText(filename)).toBeVisible();
  }

  async expectUploadSuccess() {
    await expect(this.successMessage).toBeVisible();
  }

  async expectUploadError() {
    await expect(this.errorMessage).toBeVisible();
  }

  async expectFileValidationError() {
    await expect(this.fileValidationMessage).toBeVisible();
  }

  async getUploadProgress(): Promise<number> {
    try {
      const progressValue = await this.progressBar.getAttribute('aria-valuenow');
      return progressValue ? parseInt(progressValue) : 0;
    } catch {
      return 0;
    }
  }

  async waitForProgressComplete() {
    let progress = 0;
    const maxWaitTime = 30000; // 30 seconds
    const startTime = Date.now();
    
    while (progress < 100 && (Date.now() - startTime) < maxWaitTime) {
      progress = await this.getUploadProgress();
      if (progress < 100) {
        await this.page.waitForTimeout(1000); // Wait 1 second
      }
    }
    
    if (progress < 100) {
      throw new Error('Upload progress did not complete within timeout');
    }
  }

  async isUploadInProgress(): Promise<boolean> {
    try {
      return await this.progressBar.isVisible();
    } catch {
      return false;
    }
  }

  async cancelUpload() {
    const cancelButton = this.page.getByRole('button', { name: /cancel/i });
    if (await cancelButton.isVisible()) {
      await cancelButton.click();
    }
  }

  async retryUpload() {
    const retryButton = this.page.getByRole('button', { name: /retry|try again/i });
    if (await retryButton.isVisible()) {
      await retryButton.click();
    }
  }

  async getDocumentCount(): Promise<number> {
    try {
      const documents = await this.documentList.locator('[data-testid="document-item"]').count();
      return documents;
    } catch {
      return 0;
    }
  }

  async deleteDocument(filename: string) {
    const documentItem = this.documentList.getByText(filename).locator('..');
    const deleteButton = documentItem.getByRole('button', { name: /delete|remove/i });
    
    if (await deleteButton.isVisible()) {
      await deleteButton.click();
      
      // Confirm deletion if confirmation dialog appears
      const confirmButton = this.page.getByRole('button', { name: /confirm|yes|delete/i });
      if (await confirmButton.isVisible()) {
        await confirmButton.click();
      }
    }
  }
}
