import { Page, Locator, expect } from '@playwright/test';

export class AuthPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly loginButton: Locator;
  readonly registerButton: Locator;
  readonly errorMessage: Locator;
  readonly logoutButton: Locator;
  readonly welcomeMessage: Locator;
  readonly dashboardContent: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.getByLabel(/email/i);
    this.passwordInput = page.getByLabel(/password/i);
    this.loginButton = page.getByRole('button', { name: /login|sign in/i });
    this.registerButton = page.getByRole('button', { name: /register|sign up/i });
    this.errorMessage = page.getByRole('alert');
    this.logoutButton = page.getByRole('button', { name: /logout|sign out/i });
    this.welcomeMessage = page.getByText(/welcome|dashboard/i);
    this.dashboardContent = page.getByTestId('dashboard-content');
  }

  async goto() {
    await this.page.goto('/auth/login');
  }

  async gotoRegister() {
    await this.page.goto('/auth/register');
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.loginButton.click();
  }

  async register(email: string, password: string) {
    await this.gotoRegister();
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.registerButton.click();
  }

  async logout() {
    if (await this.logoutButton.isVisible()) {
      await this.logoutButton.click();
    }
  }

  async expectLoggedIn() {
    await expect(this.welcomeMessage).toBeVisible({ timeout: 10000 });
  }

  async expectLoggedOut() {
    await expect(this.loginButton).toBeVisible();
  }

  async expectError(message: RegExp) {
    await expect(this.errorMessage).toContainText(message);
  }

  async expectOnLoginPage() {
    await expect(this.page).toHaveURL(/auth.*login|login/i);
  }

  async expectOnRegisterPage() {
    await expect(this.page).toHaveURL(/auth.*register|register/i);
  }

  async expectOnDashboard() {
    await expect(this.page).toHaveURL(/dashboard|welcome/i);
  }

  async waitForLoginSuccess() {
    await this.page.waitForURL(/dashboard|welcome/i, { timeout: 10000 });
  }

  async waitForRegistrationSuccess() {
    await this.page.waitForURL(/dashboard|verify|welcome/i, { timeout: 10000 });
  }

  async waitForLogoutSuccess() {
    await this.page.waitForURL(/auth.*login|login/i, { timeout: 10000 });
  }

  async clearForm() {
    await this.emailInput.clear();
    await this.passwordInput.clear();
  }

  async isFormValid(): Promise<boolean> {
    try {
      // Check if form validation allows submission
      const isEmailValid = await this.emailInput.evaluate(el => (el as HTMLInputElement).validity.valid);
      const isPasswordValid = await this.passwordInput.evaluate(el => (el as HTMLInputElement).validity.valid);
      return isEmailValid && isPasswordValid;
    } catch {
      return false;
    }
  }
}
