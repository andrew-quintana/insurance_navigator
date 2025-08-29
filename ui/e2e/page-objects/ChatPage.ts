import { Page, Locator, expect } from '@playwright/test';

export class ChatPage {
  readonly page: Page;
  readonly messageInput: Locator;
  readonly sendButton: Locator;
  readonly chatHistory: Locator;
  readonly lastMessage: Locator;
  readonly typingIndicator: Locator;
  readonly agentResponse: Locator;
  readonly conversationList: Locator;
  readonly newConversationButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.messageInput = page.getByLabel(/message|chat/i);
    this.sendButton = page.getByRole('button', { name: /send/i });
    this.chatHistory = page.getByTestId('chat-history');
    this.lastMessage = this.chatHistory.locator('.message').last();
    this.typingIndicator = page.getByTestId('typing-indicator');
    this.agentResponse = page.getByTestId('agent-response');
    this.conversationList = page.getByTestId('conversation-list');
    this.newConversationButton = page.getByRole('button', { name: /new.*conversation|start.*chat/i });
  }

  async goto() {
    await this.page.goto('/chat');
  }

  async sendMessage(message: string) {
    await this.messageInput.fill(message);
    await this.sendButton.click();
  }

  async waitForResponse() {
    await expect(this.lastMessage).toBeVisible({ timeout: 10000 });
  }

  async waitForAgentResponse() {
    await expect(this.agentResponse).toBeVisible({ timeout: 15000 });
  }

  async waitForTypingIndicator() {
    await expect(this.typingIndicator).toBeVisible({ timeout: 5000 });
  }

  async expectMessageInHistory(text: string) {
    await expect(this.chatHistory.getByText(text)).toBeVisible();
  }

  async expectAgentResponse() {
    await expect(this.agentResponse).toBeVisible();
  }

  async expectTypingIndicator() {
    await expect(this.typingIndicator).toBeVisible();
  }

  async expectNoTypingIndicator() {
    await expect(this.typingIndicator).not.toBeVisible();
  }

  async getMessageCount(): Promise<number> {
    try {
      return await this.chatHistory.locator('.message').count();
    } catch {
      return 0;
    }
  }

  async getLastMessageText(): Promise<string> {
    try {
      return await this.lastMessage.textContent() || '';
    } catch {
      return '';
    }
  }

  async getAgentResponseText(): Promise<string> {
    try {
      return await this.agentResponse.textContent() || '';
    } catch {
      return '';
    }
  }

  async startNewConversation() {
    if (await this.newConversationButton.isVisible()) {
      await this.newConversationButton.click();
    }
  }

  async selectConversation(conversationName: string) {
    const conversationItem = this.conversationList.getByText(conversationName);
    if (await conversationItem.isVisible()) {
      await conversationItem.click();
    }
  }

  async clearMessageInput() {
    await this.messageInput.clear();
  }

  async isMessageInputEmpty(): Promise<boolean> {
    const value = await this.messageInput.inputValue();
    return value === '';
  }

  async isSendButtonEnabled(): Promise<boolean> {
    try {
      return !(await this.sendButton.isDisabled());
    } catch {
      return false;
    }
  }

  async waitForConversationLoad() {
    await this.page.waitForLoadState('networkidle');
  }

  async scrollToBottom() {
    await this.page.evaluate(() => {
      window.scrollTo(0, document.body.scrollHeight);
    });
  }

  async expectDocumentContext(documentName: string) {
    // Check if the chat interface shows document context
    const contextElement = this.page.getByText(documentName);
    await expect(contextElement).toBeVisible();
  }

  async expectCitationInResponse() {
    // Check if agent response includes citations
    const citationElement = this.page.getByTestId('citation');
    await expect(citationElement).toBeVisible();
  }

  async getResponseTime(): Promise<number> {
    const startTime = Date.now();
    await this.waitForAgentResponse();
    return Date.now() - startTime;
  }

  async isConversationPersisted(): Promise<boolean> {
    try {
      // Check if conversation is saved by refreshing the page
      const currentUrl = this.page.url();
      await this.page.reload();
      await this.page.waitForLoadState('networkidle');
      
      // Check if we're still in the same conversation
      return this.page.url() === currentUrl;
    } catch {
      return false;
    }
  }
}
