import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Header } from './Header';
import { BrowserRouter } from 'react-router-dom';

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('Header', () => {
  it('renders application title', () => {
    renderWithRouter(<Header />);
    
    expect(screen.getByText(/MAPS/i)).toBeInTheDocument();
    expect(screen.getByText(/medical imaging processing suite/i)).toBeInTheDocument();
  });

  it('displays navigation links', () => {
    renderWithRouter(<Header />);
    
    expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
    expect(screen.getByText(/upload/i)).toBeInTheDocument();
    expect(screen.getByText(/history/i)).toBeInTheDocument();
  });

  it('highlights active navigation item', () => {
    renderWithRouter(<Header />);
    
    const dashboardLink = screen.getByRole('link', { name: /dashboard/i });
    expect(dashboardLink).toHaveClass('active'); // or whatever class indicates active state
  });

  it('shows user menu when clicked', async () => {
    renderWithRouter(<Header />);
    
    const userButton = screen.getByRole('button', { name: /user|profile|menu/i });
    fireEvent.click(userButton);
    
    await waitFor(() => {
      expect(screen.getByText(/settings/i)).toBeInTheDocument();
    });
  });

  it('responds to window resize', () => {
    renderWithRouter(<Header />);
    
    // simulate mobile view
    global.innerWidth = 500;
    global.dispatchEvent(new Event('resize'));
    
    // mobile menu button should appear
    const mobileMenuButton = screen.queryByRole('button', { name: /menu/i });
    expect(mobileMenuButton).toBeInTheDocument();
  });
});
