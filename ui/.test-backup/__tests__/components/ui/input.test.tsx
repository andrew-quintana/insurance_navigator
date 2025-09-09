import { render, screen, fireEvent } from '@testing-library/react';
import { Input } from '@/components/ui/input';

describe('Input Component', () => {
  describe('Rendering', () => {
    it('should render input with default styles', () => {
      render(<Input placeholder="Enter text" />);
      const input = screen.getByPlaceholderText('Enter text');
      expect(input).toBeInTheDocument();
      expect(input).toHaveClass('flex', 'h-10', 'w-full', 'rounded-md', 'border', 'border-input');
    });

    it('should render input with custom className', () => {
      render(<Input className="custom-input" placeholder="Custom" />);
      const input = screen.getByPlaceholderText('Custom');
      expect(input).toHaveClass('custom-input');
    });

    it('should render input with custom type', () => {
      render(<Input type="email" placeholder="Email" />);
      const input = screen.getByPlaceholderText('Email');
      expect(input).toHaveAttribute('type', 'email');
    });

    it('should render input with custom value', () => {
      render(<Input value="test value" readOnly />);
      const input = screen.getByDisplayValue('test value');
      expect(input).toBeInTheDocument();
    });

    it('should render input with custom id', () => {
      render(<Input id="test-input" placeholder="Test" />);
      const input = screen.getByPlaceholderText('Test');
      expect(input).toHaveAttribute('id', 'test-input');
    });
  });

  describe('Props and Attributes', () => {
    it('should forward all HTML input attributes', () => {
      render(
        <Input
          placeholder="Test"
          name="test-name"
          required
          minLength={5}
          maxLength={20}
          pattern="[A-Za-z]+"
          title="Only letters allowed"
        />
      );
      
      const input = screen.getByPlaceholderText('Test');
      expect(input).toHaveAttribute('name', 'test-name');
      expect(input).toHaveAttribute('required');
      expect(input).toHaveAttribute('minLength', '5');
      expect(input).toHaveAttribute('maxLength', '20');
      expect(input).toHaveAttribute('pattern', '[A-Za-z]+');
      expect(input).toHaveAttribute('title', 'Only letters allowed');
    });

    it('should handle disabled state', () => {
      render(<Input disabled placeholder="Disabled" />);
      const input = screen.getByPlaceholderText('Disabled');
      expect(input).toBeDisabled();
    });

    it('should handle readOnly state', () => {
      render(<Input readOnly placeholder="Read only" />);
      const input = screen.getByPlaceholderText('Read only');
      expect(input).toHaveAttribute('readonly');
    });

    it('should handle required state', () => {
      render(<Input required placeholder="Required" />);
      const input = screen.getByPlaceholderText('Required');
      expect(input).toHaveAttribute('required');
    });

    it('should handle autoComplete', () => {
      render(<Input autoComplete="off" placeholder="No autocomplete" />);
      const input = screen.getByPlaceholderText('No autocomplete');
      expect(input).toHaveAttribute('autocomplete', 'off');
    });

    it('should handle autoFocus', () => {
      render(<Input autoFocus placeholder="Autofocus" />);
      const input = screen.getByPlaceholderText('Autofocus');
      expect(input).toHaveAttribute('autofocus');
    });
  });

  describe('Event Handling', () => {
    it('should call onChange when value changes', () => {
      const handleChange = jest.fn();
      render(<Input onChange={handleChange} placeholder="Change test" />);
      const input = screen.getByPlaceholderText('Change test');
      
      fireEvent.change(input, { target: { value: 'new value' } });
      expect(handleChange).toHaveBeenCalledTimes(1);
      expect(handleChange).toHaveBeenCalledWith(expect.objectContaining({
        target: expect.objectContaining({ value: 'new value' })
      }));
    });

    it('should call onFocus when focused', () => {
      const handleFocus = jest.fn();
      render(<Input onFocus={handleFocus} placeholder="Focus test" />);
      const input = screen.getByPlaceholderText('Focus test');
      
      fireEvent.focus(input);
      expect(handleFocus).toHaveBeenCalledTimes(1);
    });

    it('should call onBlur when blurred', () => {
      const handleBlur = jest.fn();
      render(<Input onBlur={handleBlur} placeholder="Blur test" />);
      const input = screen.getByPlaceholderText('Blur test');
      
      fireEvent.blur(input);
      expect(handleBlur).toHaveBeenCalledTimes(1);
    });

    it('should call onKeyDown when key is pressed', () => {
      const handleKeyDown = jest.fn();
      render(<Input onKeyDown={handleKeyDown} placeholder="Key test" />);
      const input = screen.getByPlaceholderText('Key test');
      
      fireEvent.keyDown(input, { key: 'Enter' });
      expect(handleKeyDown).toHaveBeenCalledTimes(1);
    });

    it('should call onKeyUp when key is released', () => {
      const handleKeyUp = jest.fn();
      render(<Input onKeyUp={handleKeyUp} placeholder="Key up test" />);
      const input = screen.getByPlaceholderText('Key up test');
      
      fireEvent.keyUp(input, { key: 'Enter' });
      expect(handleKeyUp).toHaveBeenCalledTimes(1);
    });

    it('should call onClick when clicked', () => {
      const handleClick = jest.fn();
      render(<Input onClick={handleClick} placeholder="Click test" />);
      const input = screen.getByPlaceholderText('Click test');
      
      fireEvent.click(input);
      expect(handleClick).toHaveBeenCalledTimes(1);
    });
  });

  describe('Value Management', () => {
    it('should update value when controlled', () => {
      const { rerender } = render(<Input value="initial" onChange={() => {}} />);
      expect(screen.getByDisplayValue('initial')).toBeInTheDocument();
      
      rerender(<Input value="updated" onChange={() => {}} />);
      expect(screen.getByDisplayValue('updated')).toBeInTheDocument();
    });

    it('should handle empty string value', () => {
      render(<Input value="" onChange={() => {}} />);
      const input = screen.getByRole('textbox');
      expect(input).toHaveValue('');
    });

    it('should handle null value', () => {
      render(<Input value={null as any} onChange={() => {}} />);
      const input = screen.getByRole('textbox');
      expect(input).toHaveValue('');
    });

    it('should handle undefined value', () => {
      render(<Input value={undefined as any} onChange={() => {}} />);
      const input = screen.getByRole('textbox');
      expect(input).toHaveValue('');
    });
  });

  describe('Styling and Classes', () => {
    it('should apply default classes correctly', () => {
      render(<Input placeholder="Default" />);
      const input = screen.getByPlaceholderText('Default');
      
      expect(input).toHaveClass(
        'flex',
        'h-10',
        'w-full',
        'rounded-md',
        'border',
        'border-input',
        'bg-background',
        'px-3',
        'py-2',
        'text-sm',
        'ring-offset-background'
      );
    });

    it('should apply custom classes in addition to defaults', () => {
      render(<Input className="custom-class" placeholder="Custom" />);
      const input = screen.getByPlaceholderText('Custom');
      
      expect(input).toHaveClass('custom-class');
      expect(input).toHaveClass('flex', 'h-10', 'w-full'); // Default classes still present
    });

    it('should handle multiple custom classes', () => {
      render(<Input className="class1 class2 class3" placeholder="Multiple" />);
      const input = screen.getByPlaceholderText('Multiple');
      
      expect(input).toHaveClass('class1', 'class2', 'class3');
    });
  });

  describe('Accessibility', () => {
    it('should support aria-label', () => {
      render(<Input aria-label="Custom label" />);
      const input = screen.getByLabelText('Custom label');
      expect(input).toBeInTheDocument();
    });

    it('should support aria-describedby', () => {
      render(
        <div>
          <Input aria-describedby="description" />
          <div id="description">Description text</div>
        </div>
      );
      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('aria-describedby', 'description');
    });

    it('should support aria-invalid', () => {
      render(<Input aria-invalid="true" placeholder="Invalid" />);
      const input = screen.getByPlaceholderText('Invalid');
      expect(input).toHaveAttribute('aria-invalid', 'true');
    });

    it('should support aria-required', () => {
      render(<Input aria-required="true" placeholder="Required" />);
      const input = screen.getByPlaceholderText('Required');
      expect(input).toHaveAttribute('aria-required', 'true');
    });

    it('should support role attribute', () => {
      render(<Input role="searchbox" placeholder="Search" />);
      const input = screen.getByRole('searchbox');
      expect(input).toBeInTheDocument();
    });
  });

  describe('Form Integration', () => {
    it('should work within a form', () => {
      render(
        <form>
          <Input name="username" placeholder="Username" />
          <Input name="password" type="password" placeholder="Password" />
        </form>
      );
      
      const usernameInput = screen.getByPlaceholderText('Username');
      const passwordInput = screen.getByPlaceholderText('Password');
      
      expect(usernameInput).toHaveAttribute('name', 'username');
      expect(passwordInput).toHaveAttribute('name', 'password');
      expect(passwordInput).toHaveAttribute('type', 'password');
    });

    it('should handle form submission', () => {
      const handleSubmit = jest.fn();
      render(
        <form onSubmit={handleSubmit}>
          <Input name="test" placeholder="Test" />
          <button type="submit">Submit</button>
        </form>
      );
      
      const form = screen.getByRole('button', { name: /submit/i }).closest('form');
      fireEvent.submit(form!);
      expect(handleSubmit).toHaveBeenCalledTimes(1);
    });
  });

  describe('Edge Cases', () => {
    it('should handle very long placeholder text', () => {
      const longPlaceholder = 'a'.repeat(1000);
      render(<Input placeholder={longPlaceholder} />);
      const input = screen.getByPlaceholderText(longPlaceholder);
      expect(input).toBeInTheDocument();
    });

    it('should handle special characters in placeholder', () => {
      const specialPlaceholder = '!@#$%^&*()_+-=[]{}|;:,.<>?';
      render(<Input placeholder={specialPlaceholder} />);
      const input = screen.getByPlaceholderText(specialPlaceholder);
      expect(input).toBeInTheDocument();
    });

    it('should handle numeric string values', () => {
      render(<Input value="12345" onChange={() => {}} />);
      const input = screen.getByDisplayValue('12345');
      expect(input).toBeInTheDocument();
    });

    it('should handle boolean values', () => {
      render(<Input value={true as any} onChange={() => {}} />);
      const input = screen.getByRole('textbox');
      expect(input).toHaveValue('true');
    });
  });

  describe('Ref Forwarding', () => {
    it('should forward refs correctly', () => {
      const ref = jest.fn();
      render(<Input ref={ref} placeholder="Ref test" />);
      expect(ref).toHaveBeenCalled();
    });

    it('should support imperative handle', () => {
      const ref = jest.fn();
      render(<Input ref={ref} placeholder="Imperative test" />);
      
      const input = screen.getByPlaceholderText('Imperative test');
      if (ref.mock.calls[0][0]) {
        ref.mock.calls[0][0].focus();
        expect(input).toHaveFocus();
      }
    });
  });
});
