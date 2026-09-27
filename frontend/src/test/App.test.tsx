import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';

describe('Frontend UI Core Components', () => {
  it('renders Button component with variant and text', () => {
    render(<Button variant="primary">Click Me</Button>);
    const button = screen.getByRole('button', { name: /click me/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveClass('bg-indigo-600');
  });

  it('renders Badge component with correct text', () => {
    render(<Badge variant="success">Active</Badge>);
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('renders EmptyState component with title and description', () => {
    render(<EmptyState title="No Items" description="Collection is currently empty" />);
    expect(screen.getByText('No Items')).toBeInTheDocument();
    expect(screen.getByText('Collection is currently empty')).toBeInTheDocument();
  });

  it('renders ErrorState component with retry action', () => {
    const handleRetry = vi.fn();
    render(<ErrorState title="Load Failed" message="Connection error" onRetry={handleRetry} />);
    expect(screen.getByText('Load Failed')).toBeInTheDocument();
    expect(screen.getByText('Connection error')).toBeInTheDocument();
    
    const retryBtn = screen.getByRole('button', { name: /retry/i });
    retryBtn.click();
    expect(handleRetry).toHaveBeenCalledTimes(1);
  });
});
