import { render, screen, fireEvent } from '@testing-library/react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';

// Mock the useDialog hook if it exists
jest.mock('@/components/ui/dialog', () => {
  const originalModule = jest.requireActual('@/components/ui/dialog');
  return {
    ...originalModule,
    useDialog: jest.fn(() => ({
      open: false,
      onOpenChange: jest.fn(),
    })),
  };
});

describe('Dialog Components', () => {
  describe('Dialog', () => {
    it('should render dialog with default props', () => {
      render(
        <Dialog>
          <DialogTrigger>Open Dialog</DialogTrigger>
          <DialogContent>Dialog content</DialogContent>
        </Dialog>
      );
      
      const trigger = screen.getByText('Open Dialog');
      expect(trigger).toBeInTheDocument();
    });

    it('should render dialog with custom className', () => {
      render(
        <Dialog className="custom-dialog">
          <DialogTrigger>Custom Dialog</DialogTrigger>
          <DialogContent>Content</DialogContent>
        </Dialog>
      );
      
      const trigger = screen.getByText('Custom Dialog');
      expect(trigger).toBeInTheDocument();
    });

    it('should forward additional props', () => {
      render(
        <Dialog data-testid="test-dialog">
          <DialogTrigger>Test Dialog</DialogTrigger>
          <DialogContent>Content</DialogContent>
        </Dialog>
      );
      
      const dialog = screen.getByTestId('test-dialog');
      expect(dialog).toBeInTheDocument();
    });
  });

  describe('DialogTrigger', () => {
    it('should render trigger button', () => {
      render(
        <Dialog>
          <DialogTrigger>Click to open</DialogTrigger>
          <DialogContent>Content</DialogContent>
        </Dialog>
      );
      
      const trigger = screen.getByRole('button', { name: /click to open/i });
      expect(trigger).toBeInTheDocument();
    });

    it('should render trigger with custom className', () => {
      render(
        <Dialog>
          <DialogTrigger className="custom-trigger">Custom Trigger</DialogTrigger>
          <DialogContent>Content</DialogContent>
        </Dialog>
      );
      
      const trigger = screen.getByRole('button', { name: /custom trigger/i });
      expect(trigger).toHaveClass('custom-trigger');
    });

    it('should forward additional props', () => {
      render(
        <Dialog>
          <DialogTrigger data-testid="test-trigger" aria-label="Open dialog">
            Trigger
          </DialogTrigger>
          <DialogContent>Content</DialogContent>
        </Dialog>
      );
      
      const trigger = screen.getByTestId('test-trigger');
      expect(trigger).toHaveAttribute('aria-label', 'Open dialog');
    });

    it('should handle click events', () => {
      const handleClick = jest.fn();
      render(
        <Dialog>
          <DialogTrigger onClick={handleClick}>Clickable Trigger</DialogTrigger>
          <DialogContent>Content</DialogContent>
        </Dialog>
      );
      
      const trigger = screen.getByRole('button', { name: /clickable trigger/i });
      fireEvent.click(trigger);
      expect(handleClick).toHaveBeenCalledTimes(1);
    });
  });

  describe('DialogContent', () => {
    it('should render content with default styles', () => {
      render(
        <Dialog>
          <DialogTrigger>Open</DialogTrigger>
          <DialogContent>Dialog content</DialogContent>
        </Dialog>
      );
      
      const content = screen.getByText('Dialog content');
      expect(content).toBeInTheDocument();
    });

    it('should render content with custom className', () => {
      render(
        <Dialog>
          <DialogTrigger>Open</DialogTrigger>
          <DialogContent className="custom-content">Custom Content</DialogContent>
        </Dialog>
      );
      
      const content = screen.getByText('Custom Content');
      expect(content.parentElement).toHaveClass('custom-content');
    });

    it('should forward additional props', () => {
      render(
        <Dialog>
          <DialogTrigger>Open</DialogTrigger>
          <DialogContent data-testid="test-content">Content</DialogContent>
        </Dialog>
      );
      
      const content = screen.getByTestId('test-content');
      expect(content).toBeInTheDocument();
    });

    it('should handle children content', () => {
      render(
        <Dialog>
          <DialogTrigger>Open</DialogTrigger>
          <DialogContent>
            <div data-testid="nested-content">Nested content</div>
            <p>Paragraph content</p>
          </DialogContent>
        </Dialog>
      );
      
      expect(screen.getByTestId('nested-content')).toBeInTheDocument();
      expect(screen.getByText('Paragraph content')).toBeInTheDocument();
    });
  });

  describe('DialogHeader', () => {
    it('should render header with default styles', () => {
      render(
        <Dialog>
          <DialogTrigger>Open</DialogTrigger>
          <DialogContent>
            <DialogHeader>Header content</DialogHeader>
          </DialogContent>
        </Dialog>
      );
      
      const header = screen.getByText('Header content');
      expect(header.parentElement).toHaveClass('flex', 'flex-col', 'space-y-1.5', 'text-center', 'sm:text-left');
    });

    it('should render header with custom className', () => {
      render(
        <Dialog>
          <DialogTrigger>Open</DialogTrigger>
          <DialogContent>
            <DialogHeader className="custom-header">Custom Header</DialogHeader>
          </DialogContent>
        </Dialog>
      );
      
      const header = screen.getByText('Custom Header');
      expect(header.parentElement).toHaveClass('custom-header');
    });

    it('should forward additional props', () => {
      render(
        <Dialog>
          <DialogTrigger>Open</DialogTrigger>
          <DialogContent>
            <DialogHeader data-testid="test-header">Test Header</DialogHeader>
          </DialogContent>
        </Dialog>
      );
      
      const header = screen.getByTestId('test-header');
      expect(header).toBeInTheDocument();
    });
  });

  describe('DialogTitle', () => {
    it('should render title with default styles', () => {
      render(
        <Dialog>
          <DialogTrigger>Open</DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Dialog Title</DialogTitle>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );
      
      const title = screen.getByText('Dialog Title');
      expect(title).toHaveClass('text-lg', 'font-semibold', 'leading-none', 'tracking-tight');
    });

    it('should render title with custom className', () => {
      render(
        <Dialog>
          <DialogTrigger>Open</DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="custom-title">Custom Title</DialogTitle>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );
      
      const title = screen.getByText('Custom Title');
      expect(title).toHaveClass('custom-title');
    });

    it('should forward additional props', () => {
      render(
        <Dialog>
          <DialogTrigger>Open</DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle data-testid="test-title">Test Title</DialogTitle>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );
      
      const title = screen.getByTestId('test-title');
      expect(title).toBeInTheDocument();
    });
  });

  describe('DialogDescription', () => {
    it('should render description with default styles', () => {
      render(
        <Dialog>
          <DialogTrigger>Open</DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogDescription>Dialog Description</DialogDescription>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );
      
      const description = screen.getByText('Dialog Description');
      expect(description).toHaveClass('text-sm', 'text-muted-foreground');
    });

    it('should render description with custom className', () => {
      render(
        <Dialog>
          <DialogTrigger>Open</DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogDescription className="custom-description">Custom Description</DialogDescription>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );
      
      const description = screen.getByText('Custom Description');
      expect(description).toHaveClass('custom-description');
    });

    it('should forward additional props', () => {
      render(
        <Dialog>
          <DialogTrigger>Open</DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogDescription data-testid="test-description">Test Description</DialogDescription>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );
      
      const description = screen.getByTestId('test-description');
      expect(description).toBeInTheDocument();
    });
  });

  describe('DialogFooter', () => {
    it('should render footer with default styles', () => {
      render(
        <Dialog>
          <DialogTrigger>Open</DialogTrigger>
          <DialogContent>
            <DialogFooter>Footer content</DialogFooter>
          </DialogContent>
        </Dialog>
      );
      
      const footer = screen.getByText('Footer content');
      expect(footer.parentElement).toHaveClass('flex', 'flex-col-reverse', 'sm:flex-row', 'sm:justify-end', 'sm:space-x-2');
    });

    it('should render footer with custom className', () => {
      render(
        <Dialog>
          <DialogTrigger>Open</DialogTrigger>
          <DialogContent>
            <DialogFooter className="custom-footer">Custom Footer</DialogFooter>
          </DialogContent>
        </Dialog>
      );
      
      const footer = screen.getByText('Custom Footer');
      expect(footer.parentElement).toHaveClass('custom-footer');
    });

    it('should forward additional props', () => {
      render(
        <Dialog>
          <DialogTrigger>Open</DialogTrigger>
          <DialogContent>
            <DialogFooter data-testid="test-footer">Test Footer</DialogFooter>
          </DialogContent>
        </Dialog>
      );
      
      const footer = screen.getByTestId('test-footer');
      expect(footer).toBeInTheDocument();
    });

    it('should handle multiple children', () => {
      render(
        <Dialog>
          <DialogTrigger>Open</DialogTrigger>
          <DialogContent>
            <DialogFooter>
              <button>Cancel</button>
              <button>Confirm</button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      );
      
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /confirm/i })).toBeInTheDocument();
    });
  });

  describe('Complete Dialog Structure', () => {
    it('should render complete dialog with all components', () => {
      render(
        <Dialog>
          <DialogTrigger>Open Complete Dialog</DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Complete Dialog</DialogTitle>
              <DialogDescription>This is a complete dialog example</DialogDescription>
            </DialogHeader>
            <div>Main content goes here</div>
            <DialogFooter>
              <button>Cancel</button>
              <button>Save</button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      );

      expect(screen.getByText('Open Complete Dialog')).toBeInTheDocument();
      expect(screen.getByText('Complete Dialog')).toBeInTheDocument();
      expect(screen.getByText('This is a complete dialog example')).toBeInTheDocument();
      expect(screen.getByText('Main content goes here')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
    });

    it('should handle nested content structures', () => {
      render(
        <Dialog>
          <DialogTrigger>Open Nested</DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Nested Dialog</DialogTitle>
              <DialogDescription>With nested content</DialogDescription>
            </DialogHeader>
            <div>
              <section>
                <h3>Section 1</h3>
                <p>Content 1</p>
              </section>
              <section>
                <h3>Section 2</h3>
                <p>Content 2</p>
              </section>
            </div>
            <DialogFooter>
              <div className="flex gap-2">
                <button>Back</button>
                <button>Next</button>
              </div>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      );

      expect(screen.getByText('Section 1')).toBeInTheDocument();
      expect(screen.getByText('Content 1')).toBeInTheDocument();
      expect(screen.getByText('Section 2')).toBeInTheDocument();
      expect(screen.getByText('Content 2')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /back/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should support ARIA attributes', () => {
      render(
        <Dialog>
          <DialogTrigger aria-label="Open dialog">Open</DialogTrigger>
          <DialogContent aria-labelledby="dialog-title" aria-describedby="dialog-description">
            <DialogHeader>
              <DialogTitle id="dialog-title">Accessible Dialog</DialogTitle>
              <DialogDescription id="dialog-description">Description for accessibility</DialogDescription>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );

      const trigger = screen.getByLabelText('Open dialog');
      const content = screen.getByText('Accessible Dialog').closest('[aria-labelledby]');
      
      expect(trigger).toBeInTheDocument();
      expect(content).toHaveAttribute('aria-labelledby', 'dialog-title');
      expect(content).toHaveAttribute('aria-describedby', 'dialog-description');
    });

    it('should support role attributes', () => {
      render(
        <Dialog>
          <DialogTrigger role="button">Open</DialogTrigger>
          <DialogContent role="dialog">Content</DialogContent>
        </Dialog>
      );

      const trigger = screen.getByRole('button');
      const content = screen.getByRole('dialog');
      
      expect(trigger).toBeInTheDocument();
      expect(content).toBeInTheDocument();
    });
  });

  describe('Styling and Layout', () => {
    it('should apply correct spacing and layout classes', () => {
      render(
        <Dialog>
          <DialogTrigger>Open</DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Title</DialogTitle>
              <DialogDescription>Description</DialogDescription>
            </DialogHeader>
            <div>Content</div>
            <DialogFooter>
              <button>Action</button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      );

      const header = screen.getByText('Title').closest('div');
      const content = screen.getByText('Content').closest('div');
      const footer = screen.getByText('Action').closest('div');

      expect(header).toHaveClass('flex', 'flex-col', 'space-y-1.5');
      expect(content).toBeInTheDocument();
      expect(footer).toHaveClass('flex', 'flex-col-reverse', 'sm:flex-row');
    });

    it('should handle custom styling overrides', () => {
      render(
        <Dialog>
          <DialogTrigger className="bg-blue-500 text-white">Blue Trigger</DialogTrigger>
          <DialogContent className="border-red-500">
            <DialogHeader className="bg-yellow-100">
              <DialogTitle className="text-red-600">Custom Styled</DialogTitle>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );

      const trigger = screen.getByRole('button', { name: /blue trigger/i });
      const content = screen.getByText('Custom Styled').closest('.border-red-500');
      const header = screen.getByText('Custom Styled').closest('.bg-yellow-100');
      const title = screen.getByText('Custom Styled');

      expect(trigger).toHaveClass('bg-blue-500', 'text-white');
      expect(content).toHaveClass('border-red-500');
      expect(header).toHaveClass('bg-yellow-100');
      expect(title).toHaveClass('text-red-600');
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty content gracefully', () => {
      render(
        <Dialog>
          <DialogTrigger></DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle></DialogTitle>
              <DialogDescription></DialogDescription>
            </DialogHeader>
            <DialogFooter></DialogFooter>
          </DialogContent>
        </Dialog>
      );

      const dialog = screen.getByRole('generic');
      expect(dialog).toBeInTheDocument();
    });

    it('should handle null and undefined children', () => {
      render(
        <Dialog>
          <DialogTrigger>{null}</DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{undefined}</DialogTitle>
              <DialogDescription>{null}</DialogDescription>
            </DialogHeader>
            <DialogFooter>{undefined}</DialogFooter>
          </DialogContent>
        </Dialog>
      );

      const dialog = screen.getByRole('generic');
      expect(dialog).toBeInTheDocument();
    });

    it('should handle very long content', () => {
      const longText = 'a'.repeat(1000);
      render(
        <Dialog>
          <DialogTrigger>Open</DialogTrigger>
          <DialogContent>
            <DialogTitle>{longText}</DialogTitle>
            <DialogDescription>{longText}</DialogDescription>
          </DialogContent>
        </Dialog>
      );

      expect(screen.getByText(longText)).toBeInTheDocument();
    });
  });

  describe('Ref Forwarding', () => {
    it('should forward refs correctly', () => {
      const ref = jest.fn();
      render(
        <Dialog ref={ref}>
          <DialogTrigger>Open</DialogTrigger>
          <DialogContent>Content</DialogContent>
        </Dialog>
      );
      expect(ref).toHaveBeenCalled();
    });

    it('should support imperative handle', () => {
      const ref = jest.fn();
      render(
        <Dialog ref={ref}>
          <DialogTrigger>Open</DialogTrigger>
          <DialogContent>Content</DialogContent>
        </Dialog>
      );
      
      if (ref.mock.calls[0][0]) {
        ref.mock.calls[0][0].focus();
      }
    });
  });
});
