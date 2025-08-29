import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '@/components/theme-provider';

describe('ThemeProvider Component', () => {
  it('should render children with theme context', () => {
    render(
      <ThemeProvider>
        <div data-testid="child">Theme Provider Child</div>
      </ThemeProvider>
    );
    
    const child = screen.getByTestId('child');
    expect(child).toBeInTheDocument();
    expect(child).toHaveTextContent('Theme Provider Child');
  });

  it('should render multiple children', () => {
    render(
      <ThemeProvider>
        <div data-testid="child1">Child 1</div>
        <div data-testid="child2">Child 2</div>
        <div data-testid="child3">Child 3</div>
      </ThemeProvider>
    );
    
    expect(screen.getByTestId('child1')).toBeInTheDocument();
    expect(screen.getByTestId('child2')).toBeInTheDocument();
    expect(screen.getByTestId('child3')).toBeInTheDocument();
  });

  it('should render without children', () => {
    render(<ThemeProvider />);
    // Should render without errors
    expect(document.body).toBeInTheDocument();
  });

  it('should forward additional props', () => {
    render(
      <ThemeProvider data-testid="theme-provider" className="custom-theme">
        <div>Content</div>
      </ThemeProvider>
    );
    
    const provider = screen.getByTestId('theme-provider');
    expect(provider).toBeInTheDocument();
    expect(provider).toHaveClass('custom-theme');
  });
});
