import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '@/components/ui/button';

describe('Button Component', () => {
  describe('Rendering', () => {
    it('should render button with default variant', () => {
      render(<Button>Click me</Button>);
      const button = screen.getByRole('button', { name: /click me/i });
      expect(button).toBeInTheDocument();
      expect(button).toHaveClass('inline-flex', 'items-center', 'justify-center');
    });

    it('should render button with custom variant', () => {
      render(<Button variant="destructive">Delete</Button>);
      const button = screen.getByRole('button', { name: /delete/i });
      expect(button).toHaveClass('bg-destructive', 'text-destructive-foreground');
    });

    it('should render button with custom size', () => {
      render(<Button size="lg">Large Button</Button>);
      const button = screen.getByRole('button', { name: /large button/i });
      expect(button).toHaveClass('h-11', 'px-8');
    });

    it('should render button with custom className', () => {
      render(<Button className="custom-class">Custom</Button>);
      const button = screen.getByRole('button', { name: /custom/i });
      expect(button).toHaveClass('custom-class');
    });

    it('should render button with all props combined', () => {
      render(
        <Button 
          variant="outline" 
          size="sm" 
          className="test-class"
          disabled
        >
          Combined
        </Button>
      );
      const button = screen.getByRole('button', { name: /combined/i });
      expect(button).toHaveClass('test-class', 'border', 'border-input');
      expect(button).toBeDisabled();
    });
  });

  describe('Variants', () => {
    it('should apply default variant styles', () => {
      render(<Button>Default</Button>);
      const button = screen.getByRole('button', { name: /default/i });
      expect(button).toHaveClass('bg-primary', 'text-primary-foreground');
    });

    it('should apply destructive variant styles', () => {
      render(<Button variant="destructive">Destructive</Button>);
      const button = screen.getByRole('button', { name: /destructive/i });
      expect(button).toHaveClass('bg-destructive', 'text-destructive-foreground');
    });

    it('should apply outline variant styles', () => {
      render(<Button variant="outline">Outline</Button>);
      const button = screen.getByRole('button', { name: /outline/i });
      expect(button).toHaveClass('border', 'border-input', 'bg-background');
    });

    it('should apply secondary variant styles', () => {
      render(<Button variant="secondary">Secondary</Button>);
      const button = screen.getByRole('button', { name: /secondary/i });
      expect(button).toHaveClass('bg-secondary', 'text-secondary-foreground');
    });

    it('should apply ghost variant styles', () => {
      render(<Button variant="ghost">Ghost</Button>);
      const button = screen.getByRole('button', { name: /ghost/i });
      expect(button).toHaveClass('hover:bg-accent', 'hover:text-accent-foreground');
    });

    it('should apply link variant styles', () => {
      render(<Button variant="link">Link</Button>);
      const button = screen.getByRole('button', { name: /link/i });
      expect(button).toHaveClass('text-primary', 'underline-offset-4');
    });
  });

  describe('Sizes', () => {
    it('should apply default size styles', () => {
      render(<Button>Default Size</Button>);
      const button = screen.getByRole('button', { name: /default size/i });
      expect(button).toHaveClass('h-10', 'px-4', 'py-2');
    });

    it('should apply sm size styles', () => {
      render(<Button size="sm">Small</Button>);
      const button = screen.getByRole('button', { name: /small/i });
      expect(button).toHaveClass('h-9', 'px-3');
    });

    it('should apply lg size styles', () => {
      render(<Button size="lg">Large</Button>);
      const button = screen.getByRole('button', { name: /large/i });
      expect(button).toHaveClass('h-11', 'px-8');
    });

    it('should apply icon size styles', () => {
      render(<Button size="icon">Icon</Button>);
      const button = screen.getByRole('button', { name: /icon/i });
      expect(button).toHaveClass('h-10', 'w-10');
    });
  });

  describe('States', () => {
    it('should be disabled when disabled prop is true', () => {
      render(<Button disabled>Disabled</Button>);
      const button = screen.getByRole('button', { name: /disabled/i });
      expect(button).toBeDisabled();
    });

    it('should have disabled styles when disabled', () => {
      render(<Button disabled>Disabled</Button>);
      const button = screen.getByRole('button', { name: /disabled/i });
      expect(button).toHaveClass('pointer-events-none', 'opacity-50');
    });

    it('should be enabled by default', () => {
      render(<Button>Enabled</Button>);
      const button = screen.getByRole('button', { name: /enabled/i });
      expect(button).not.toBeDisabled();
    });
  });

  describe('Interactions', () => {
    it('should call onClick when clicked', () => {
      const handleClick = jest.fn();
      render(<Button onClick={handleClick}>Clickable</Button>);
      const button = screen.getByRole('button', { name: /clickable/i });
      
      fireEvent.click(button);
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('should not call onClick when disabled', () => {
      const handleClick = jest.fn();
      render(<Button onClick={handleClick} disabled>Disabled</Button>);
      const button = screen.getByRole('button', { name: /disabled/i });
      
      fireEvent.click(button);
      expect(handleClick).not.toHaveBeenCalled();
    });

    it('should handle keyboard interactions', () => {
      const handleClick = jest.fn();
      render(<Button onClick={handleClick}>Keyboard</Button>);
      const button = screen.getByRole('button', { name: /keyboard/i });
      
      fireEvent.keyDown(button, { key: 'Enter' });
      expect(handleClick).toHaveBeenCalledTimes(1);
      
      fireEvent.keyDown(button, { key: ' ' });
      expect(handleClick).toHaveBeenCalledTimes(2);
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA attributes', () => {
      render(<Button aria-label="Custom label">Content</Button>);
      const button = screen.getByRole('button', { name: /custom label/i });
      expect(button).toBeInTheDocument();
    });

    it('should support ref forwarding', () => {
      const ref = jest.fn();
      render(<Button ref={ref}>Ref Test</Button>);
      expect(ref).toHaveBeenCalled();
    });

    it('should forward additional props', () => {
      render(<Button data-testid="test-button" aria-describedby="description">Props</Button>);
      const button = screen.getByTestId('test-button');
      expect(button).toHaveAttribute('aria-describedby', 'description');
    });
  });

  describe('Edge Cases', () => {
    it('should render without children', () => {
      render(<Button />);
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });

    it('should handle null children', () => {
      render(<Button>{null}</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });

    it('should handle undefined children', () => {
      render(<Button>{undefined}</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });

    it('should handle empty string children', () => {
      render(<Button>{''}</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });
  });
});
