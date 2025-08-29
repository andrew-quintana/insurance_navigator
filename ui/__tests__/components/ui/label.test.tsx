import { render, screen } from '@testing-library/react';
import { Label } from '@/components/ui/label';

describe('Label Component', () => {
  describe('Rendering', () => {
    it('should render label with default styles', () => {
      render(<Label>Test Label</Label>);
      const label = screen.getByText('Test Label');
      expect(label).toBeInTheDocument();
      expect(label).toHaveClass('text-sm', 'font-medium', 'leading-none', 'peer-disabled:cursor-not-allowed');
    });

    it('should render label with custom className', () => {
      render(<Label className="custom-label">Custom Label</Label>);
      const label = screen.getByText('Custom Label');
      expect(label).toHaveClass('custom-label');
    });

    it('should render label with htmlFor attribute', () => {
      render(<Label htmlFor="test-input">For Input</Label>);
      const label = screen.getByText('For Input');
      expect(label).toHaveAttribute('for', 'test-input');
    });

    it('should render label with custom id', () => {
      render(<Label id="test-label">ID Label</Label>);
      const label = screen.getByText('ID Label');
      expect(label).toHaveAttribute('id', 'test-label');
    });
  });

  describe('Props and Attributes', () => {
    it('should forward all HTML label attributes', () => {
      render(
        <Label
          htmlFor="test-input"
          id="test-label"
          className="test-class"
          data-testid="test-label"
          aria-label="Custom label"
        >
          Test Label
        </Label>
      );
      
      const label = screen.getByTestId('test-label');
      expect(label).toHaveAttribute('for', 'test-input');
      expect(label).toHaveAttribute('id', 'test-label');
      expect(label).toHaveClass('test-class');
      expect(label).toHaveAttribute('aria-label', 'Custom label');
    });

    it('should handle htmlFor with different values', () => {
      render(<Label htmlFor="username-field">Username</Label>);
      const label = screen.getByText('Username');
      expect(label).toHaveAttribute('for', 'username-field');
    });

    it('should handle empty htmlFor', () => {
      render(<Label htmlFor="">Empty For</Label>);
      const label = screen.getByText('Empty For');
      expect(label).toHaveAttribute('for', '');
    });
  });

  describe('Styling and Classes', () => {
    it('should apply default classes correctly', () => {
      render(<Label>Default Label</Label>);
      const label = screen.getByText('Default Label');
      
      expect(label).toHaveClass(
        'text-sm',
        'font-medium',
        'leading-none',
        'peer-disabled:cursor-not-allowed',
        'peer-disabled:opacity-70'
      );
    });

    it('should apply custom classes in addition to defaults', () => {
      render(<Label className="custom-label">Custom Label</Label>);
      const label = screen.getByText('Custom Label');
      
      expect(label).toHaveClass('custom-label');
      expect(label).toHaveClass('text-sm', 'font-medium'); // Default classes still present
    });

    it('should handle multiple custom classes', () => {
      render(<Label className="class1 class2 class3">Multiple Classes</Label>);
      const label = screen.getByText('Multiple Classes');
      
      expect(label).toHaveClass('class1', 'class2', 'class3');
    });

    it('should handle empty className', () => {
      render(<Label className="">Empty Class</Label>);
      const label = screen.getByText('Empty Class');
      expect(label).toHaveClass('');
    });
  });

  describe('Content Handling', () => {
    it('should render text content', () => {
      render(<Label>Simple text content</Label>);
      const label = screen.getByText('Simple text content');
      expect(label).toBeInTheDocument();
    });

    it('should render HTML content', () => {
      render(<Label><strong>Bold text</strong> and <em>italic text</em></Label>);
      expect(screen.getByText('Bold text')).toBeInTheDocument();
      expect(screen.getByText('italic text')).toBeInTheDocument();
    });

    it('should render nested components', () => {
      render(
        <Label>
          <span data-testid="nested-span">Nested span</span>
          <div data-testid="nested-div">Nested div</div>
        </Label>
      );
      
      expect(screen.getByTestId('nested-span')).toBeInTheDocument();
      expect(screen.getByTestId('nested-div')).toBeInTheDocument();
    });

    it('should handle empty content', () => {
      render(<Label></Label>);
      const label = screen.getByRole('generic');
      expect(label).toBeInTheDocument();
    });

    it('should handle null content', () => {
      render(<Label>{null}</Label>);
      const label = screen.getByRole('generic');
      expect(label).toBeInTheDocument();
    });

    it('should handle undefined content', () => {
      render(<Label>{undefined}</Label>);
      const label = screen.getByRole('generic');
      expect(label).toBeInTheDocument();
    });

    it('should handle numeric content', () => {
      render(<Label>{42}</Label>);
      const label = screen.getByText('42');
      expect(label).toBeInTheDocument();
    });

    it('should handle boolean content', () => {
      render(<Label>{true}</Label>);
      const label = screen.getByText('true');
      expect(label).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should support aria-label', () => {
      render(<Label aria-label="Custom label">Content</Label>);
      const label = screen.getByLabelText('Custom label');
      expect(label).toBeInTheDocument();
    });

    it('should support aria-describedby', () => {
      render(
        <div>
          <Label aria-describedby="description">Label</Label>
          <div id="description">Description text</div>
        </div>
      );
      const label = screen.getByText('Label');
      expect(label).toHaveAttribute('aria-describedby', 'description');
    });

    it('should support aria-labelledby', () => {
      render(
        <div>
          <div id="title">Title</div>
          <Label aria-labelledby="title">Label</Label>
        </div>
      );
      const label = screen.getByText('Label');
      expect(label).toHaveAttribute('aria-labelledby', 'title');
    });

    it('should support role attribute', () => {
      render(<Label role="heading">Heading Label</Label>);
      const label = screen.getByRole('heading');
      expect(label).toBeInTheDocument();
    });

    it('should support tabIndex', () => {
      render(<Label tabIndex={0}>Focusable Label</Label>);
      const label = screen.getByText('Focusable Label');
      expect(label).toHaveAttribute('tabIndex', '0');
    });
  });

  describe('Form Integration', () => {
    it('should associate with input via htmlFor', () => {
      render(
        <div>
          <Label htmlFor="test-input">Test Input</Label>
          <input id="test-input" type="text" />
        </div>
      );
      
      const label = screen.getByText('Test Input');
      const input = screen.getByRole('textbox');
      
      expect(label).toHaveAttribute('for', 'test-input');
      expect(input).toHaveAttribute('id', 'test-input');
    });

    it('should work with multiple inputs', () => {
      render(
        <form>
          <Label htmlFor="username">Username</Label>
          <input id="username" type="text" />
          
          <Label htmlFor="password">Password</Label>
          <input id="password" type="password" />
        </form>
      );
      
      const usernameLabel = screen.getByText('Username');
      const passwordLabel = screen.getByText('Password');
      const usernameInput = screen.getByDisplayValue('');
      const passwordInput = screen.getByDisplayValue('');
      
      expect(usernameLabel).toHaveAttribute('for', 'username');
      expect(passwordLabel).toHaveAttribute('for', 'password');
      expect(usernameInput).toHaveAttribute('id', 'username');
      expect(passwordInput).toHaveAttribute('id', 'password');
    });

    it('should work with form validation', () => {
      render(
        <form>
          <Label htmlFor="email" aria-invalid="true">Email (Invalid)</Label>
          <input id="email" type="email" aria-invalid="true" />
        </form>
      );
      
      const label = screen.getByText('Email (Invalid)');
      const input = screen.getByRole('textbox');
      
      expect(label).toHaveAttribute('aria-invalid', 'true');
      expect(input).toHaveAttribute('aria-invalid', 'true');
    });
  });

  describe('Edge Cases', () => {
    it('should handle very long text content', () => {
      const longText = 'a'.repeat(1000);
      render(<Label>{longText}</Label>);
      const label = screen.getByText(longText);
      expect(label).toBeInTheDocument();
    });

    it('should handle special characters in content', () => {
      const specialText = '!@#$%^&*()_+-=[]{}|;:,.<>?';
      render(<Label>{specialText}</Label>);
      const label = screen.getByText(specialText);
      expect(label).toBeInTheDocument();
    });

    it('should handle unicode characters', () => {
      const unicodeText = '🚀 🌟 💫 ✨ 🎉 🎊 🎈 🎁 🎂 🎄';
      render(<Label>{unicodeText}</Label>);
      const label = screen.getByText(unicodeText);
      expect(label).toBeInTheDocument();
    });

    it('should handle mixed content types', () => {
      render(
        <Label>
          Text content
          {42}
          {true}
          {null}
          {undefined}
          <span>HTML content</span>
        </Label>
      );
      
      expect(screen.getByText('Text content')).toBeInTheDocument();
      expect(screen.getByText('42')).toBeInTheDocument();
      expect(screen.getByText('true')).toBeInTheDocument();
      expect(screen.getByText('HTML content')).toBeInTheDocument();
    });
  });

  describe('Ref Forwarding', () => {
    it('should forward refs correctly', () => {
      const ref = jest.fn();
      render(<Label ref={ref}>Ref Test</Label>);
      expect(ref).toHaveBeenCalled();
    });

    it('should support imperative handle', () => {
      const ref = jest.fn();
      render(<Label ref={ref}>Imperative Test</Label>);
      
      const label = screen.getByText('Imperative Test');
      if (ref.mock.calls[0][0]) {
        ref.mock.calls[0][0].focus();
        expect(label).toHaveFocus();
      }
    });
  });

  describe('Styling Variations', () => {
    it('should handle conditional classes', () => {
      const { rerender } = render(
        <Label className={true ? 'conditional-class' : ''}>Conditional</Label>
      );
      
      let label = screen.getByText('Conditional');
      expect(label).toHaveClass('conditional-class');
      
      rerender(
        <Label className={false ? 'conditional-class' : ''}>Conditional</Label>
      );
      
      label = screen.getByText('Conditional');
      expect(label).not.toHaveClass('conditional-class');
    });

    it('should handle dynamic classes', () => {
      const dynamicClass = 'dynamic-class-' + Date.now();
      render(<Label className={dynamicClass}>Dynamic</Label>);
      
      const label = screen.getByText('Dynamic');
      expect(label).toHaveClass(dynamicClass);
    });
  });
});
