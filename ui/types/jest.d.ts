import '@testing-library/jest-dom'

declare global {
  namespace jest {
    interface Matchers<R> {
      toBeInTheDocument(): R
      toHaveClass(className: string): R
      toHaveAttribute(attr: string, value?: string): R
      toHaveTextContent(text: string | RegExp): R
      toBeVisible(): R
      toBeDisabled(): R
      toBeEnabled(): R
      toBeRequired(): R
      toHaveValue(value: string | string[] | number): R
      toHaveDisplayValue(value: string | RegExp | (string | RegExp)[]): R
      toBeChecked(): R
      toBePartiallyChecked(): R
      toHaveDescription(text: string | RegExp): R
      toHaveAccessibleName(name: string | RegExp): R
      toHaveAccessibleDescription(description: string | RegExp): R
      toHaveFocus(): R
      toHaveFormValues(expectedValues: Record<string, any>): R
      toHaveStyle(css: string | Record<string, any>): R
      toHaveValue(value: string | string[] | number): R
      toBeEmptyDOMElement(): R
      toHaveAttribute(attr: string, value?: string): R
      toHaveClass(className: string): R
      toHaveStyle(css: string | Record<string, any>): R
      toHaveTextContent(text: string | RegExp): R
      toHaveValue(value: string | string[] | number): R
      toBeInTheDocument(): R
      toBeVisible(): R
      toBeDisabled(): R
      toBeEnabled(): R
      toBeRequired(): R
      toBeChecked(): R
      toBePartiallyChecked(): R
      toHaveFocus(): R
      toHaveFormValues(expectedValues: Record<string, any>): R
      toBeEmptyDOMElement(): R
      toHaveDescription(text: string | RegExp): R
      toHaveAccessibleName(name: string | RegExp): R
      toHaveAccessibleDescription(description: string | RegExp): R
    }
  }
}

export {}


