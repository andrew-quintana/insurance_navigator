import { render, screen } from '@testing-library/react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';

describe('Card Components', () => {
  describe('Card', () => {
    it('should render card with default styles', () => {
      render(<Card>Card content</Card>);
      const card = screen.getByText('Card content');
      expect(card).toBeInTheDocument();
      expect(card.parentElement).toHaveClass('rounded-lg', 'border', 'bg-card', 'text-card-foreground');
    });

    it('should render card with custom className', () => {
      render(<Card className="custom-card">Custom Card</Card>);
      const card = screen.getByText('Custom Card');
      expect(card.parentElement).toHaveClass('custom-card');
    });

    it('should forward additional props', () => {
      render(<Card data-testid="test-card">Test Card</Card>);
      const card = screen.getByTestId('test-card');
      expect(card).toBeInTheDocument();
    });
  });

  describe('CardHeader', () => {
    it('should render card header with default styles', () => {
      render(
        <Card>
          <CardHeader>Header content</CardHeader>
        </Card>
      );
      const header = screen.getByText('Header content');
      expect(header.parentElement).toHaveClass('flex', 'flex-col', 'space-y-1.5', 'p-6');
    });

    it('should render card header with custom className', () => {
      render(
        <Card>
          <CardHeader className="custom-header">Custom Header</CardHeader>
        </Card>
      );
      const header = screen.getByText('Custom Header');
      expect(header.parentElement).toHaveClass('custom-header');
    });

    it('should forward additional props', () => {
      render(
        <Card>
          <CardHeader data-testid="test-header">Test Header</CardHeader>
        </Card>
      );
      const header = screen.getByTestId('test-header');
      expect(header).toBeInTheDocument();
    });
  });

  describe('CardTitle', () => {
    it('should render card title with default styles', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Card Title</CardTitle>
          </CardHeader>
        </Card>
      );
      const title = screen.getByText('Card Title');
      expect(title).toHaveClass('text-2xl', 'font-semibold', 'leading-none', 'tracking-tight');
    });

    it('should render card title with custom className', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle className="custom-title">Custom Title</CardTitle>
          </CardHeader>
        </Card>
      );
      const title = screen.getByText('Custom Title');
      expect(title).toHaveClass('custom-title');
    });

    it('should forward additional props', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle data-testid="test-title">Test Title</CardTitle>
          </CardHeader>
        </Card>
      );
      const title = screen.getByTestId('test-title');
      expect(title).toBeInTheDocument();
    });
  });

  describe('CardDescription', () => {
    it('should render card description with default styles', () => {
      render(
        <Card>
          <CardHeader>
            <CardDescription>Card Description</CardDescription>
          </CardHeader>
        </Card>
      );
      const description = screen.getByText('Card Description');
      expect(description).toHaveClass('text-sm', 'text-muted-foreground');
    });

    it('should render card description with custom className', () => {
      render(
        <Card>
          <CardHeader>
            <CardDescription className="custom-description">Custom Description</CardDescription>
          </CardHeader>
        </Card>
      );
      const description = screen.getByText('Custom Description');
      expect(description).toHaveClass('custom-description');
    });

    it('should forward additional props', () => {
      render(
        <Card>
          <CardHeader>
            <CardDescription data-testid="test-description">Test Description</CardDescription>
          </CardHeader>
        </Card>
      );
      const description = screen.getByTestId('test-description');
      expect(description).toBeInTheDocument();
    });
  });

  describe('CardContent', () => {
    it('should render card content with default styles', () => {
      render(
        <Card>
          <CardContent>Card content</CardContent>
        </Card>
      );
      const content = screen.getByText('Card content');
      expect(content.parentElement).toHaveClass('p-6', 'pt-0');
    });

    it('should render card content with custom className', () => {
      render(
        <Card>
          <CardContent className="custom-content">Custom Content</CardContent>
        </Card>
      );
      const content = screen.getByText('Custom Content');
      expect(content.parentElement).toHaveClass('custom-content');
    });

    it('should forward additional props', () => {
      render(
        <Card>
          <CardContent data-testid="test-content">Test Content</CardContent>
        </Card>
      );
      const content = screen.getByTestId('test-content');
      expect(content).toBeInTheDocument();
    });
  });

  describe('CardFooter', () => {
    it('should render card footer with default styles', () => {
      render(
        <Card>
          <CardFooter>Card footer</CardFooter>
        </Card>
      );
      const footer = screen.getByText('Card footer');
      expect(footer.parentElement).toHaveClass('flex', 'items-center', 'p-6', 'pt-0');
    });

    it('should render card footer with custom className', () => {
      render(
        <Card>
          <CardFooter className="custom-footer">Custom Footer</CardFooter>
        </Card>
      );
      const footer = screen.getByText('Custom Footer');
      expect(footer.parentElement).toHaveClass('custom-footer');
    });

    it('should forward additional props', () => {
      render(
        <Card>
          <CardFooter data-testid="test-footer">Test Footer</CardFooter>
        </Card>
      );
      const footer = screen.getByTestId('test-footer');
      expect(footer).toBeInTheDocument();
    });
  });

  describe('Complete Card Structure', () => {
    it('should render complete card with all components', () => {
      render(
        <Card className="test-card">
          <CardHeader>
            <CardTitle>Test Title</CardTitle>
            <CardDescription>Test Description</CardDescription>
          </CardHeader>
          <CardContent>Test Content</CardContent>
          <CardFooter>Test Footer</CardFooter>
        </Card>
      );

      expect(screen.getByText('Test Title')).toBeInTheDocument();
      expect(screen.getByText('Test Description')).toBeInTheDocument();
      expect(screen.getByText('Test Content')).toBeInTheDocument();
      expect(screen.getByText('Test Footer')).toBeInTheDocument();
      
      const card = screen.getByText('Test Title').closest('.test-card');
      expect(card).toBeInTheDocument();
    });

    it('should handle nested content', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Nested Title</CardTitle>
            <CardDescription>Nested Description</CardDescription>
          </CardHeader>
          <CardContent>
            <div data-testid="nested-content">
              <p>Nested paragraph</p>
              <button>Nested button</button>
            </div>
          </CardContent>
        </Card>
      );

      expect(screen.getByTestId('nested-content')).toBeInTheDocument();
      expect(screen.getByText('Nested paragraph')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /nested button/i })).toBeInTheDocument();
    });

    it('should handle empty content gracefully', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle></CardTitle>
            <CardDescription></CardDescription>
          </CardHeader>
          <CardContent></CardContent>
          <CardFooter></CardFooter>
        </Card>
      );

      const card = screen.getByRole('generic');
      expect(card).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should support semantic HTML structure', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Accessible Title</CardTitle>
            <CardDescription>Accessible Description</CardDescription>
          </CardHeader>
          <CardContent>Accessible Content</CardContent>
        </Card>
      );

      // Check that the structure is semantically correct
      const title = screen.getByText('Accessible Title');
      const description = screen.getByText('Accessible Description');
      const content = screen.getByText('Accessible Content');

      expect(title).toBeInTheDocument();
      expect(description).toBeInTheDocument();
      expect(content).toBeInTheDocument();
    });

    it('should forward ARIA attributes', () => {
      render(
        <Card aria-label="Test Card">
          <CardHeader>
            <CardTitle aria-describedby="description">Title</CardTitle>
            <CardDescription id="description">Description</CardDescription>
          </CardHeader>
        </Card>
      );

      const card = screen.getByLabelText('Test Card');
      const title = screen.getByText('Title');
      
      expect(card).toBeInTheDocument();
      expect(title).toHaveAttribute('aria-describedby', 'description');
    });
  });

  describe('Styling and Layout', () => {
    it('should apply correct spacing between components', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Title</CardTitle>
            <CardDescription>Description</CardDescription>
          </CardHeader>
          <CardContent>Content</CardContent>
          <CardFooter>Footer</CardFooter>
        </Card>
      );

      const header = screen.getByText('Title').closest('div');
      const content = screen.getByText('Content').closest('div');
      const footer = screen.getByText('Footer').closest('div');

      expect(header).toHaveClass('p-6');
      expect(content).toHaveClass('p-6', 'pt-0');
      expect(footer).toHaveClass('p-6', 'pt-0');
    });

    it('should handle custom styling overrides', () => {
      render(
        <Card className="border-red-500 bg-blue-100">
          <CardHeader className="bg-yellow-100">
            <CardTitle className="text-red-600">Custom Styled</CardTitle>
          </CardHeader>
        </Card>
      );

      const card = screen.getByText('Custom Styled').closest('.border-red-500');
      const header = screen.getByText('Custom Styled').closest('.bg-yellow-100');
      const title = screen.getByText('Custom Styled');

      expect(card).toHaveClass('border-red-500', 'bg-blue-100');
      expect(header).toHaveClass('bg-yellow-100');
      expect(title).toHaveClass('text-red-600');
    });
  });
});
