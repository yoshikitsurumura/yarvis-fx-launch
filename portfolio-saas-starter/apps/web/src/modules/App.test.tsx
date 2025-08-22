import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { App } from './App.js';

describe('App', () => {
  it('renders heading', () => {
    // mock fetch
    vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify([]), { status: 200 })) as any);
    render(<App />);
    expect(screen.getByText('Portfolio SaaS Starter')).toBeInTheDocument();
  });
});

