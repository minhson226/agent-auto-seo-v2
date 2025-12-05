/**
 * Tests for SummaryCards component
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import SummaryCards from '../components/analytics/SummaryCards';

describe('SummaryCards', () => {
  it('renders all summary cards with correct values', () => {
    render(
      <SummaryCards
        totalImpressions={10000}
        totalClicks={500}
        avgPosition={5.5}
      />
    );

    expect(screen.getByText('Total Impressions')).toBeInTheDocument();
    expect(screen.getByText('10.0K')).toBeInTheDocument();
    
    expect(screen.getByText('Total Clicks')).toBeInTheDocument();
    expect(screen.getByText('500')).toBeInTheDocument();
    
    expect(screen.getByText('Average Position')).toBeInTheDocument();
    expect(screen.getByText('5.5')).toBeInTheDocument();
    
    expect(screen.getByText('CTR')).toBeInTheDocument();
    expect(screen.getByText('5.00%')).toBeInTheDocument();
  });

  it('formats large numbers correctly', () => {
    render(
      <SummaryCards
        totalImpressions={1500000}
        totalClicks={75000}
        avgPosition={3.2}
      />
    );

    expect(screen.getByText('1.5M')).toBeInTheDocument();
    expect(screen.getByText('75.0K')).toBeInTheDocument();
  });

  it('handles zero values correctly', () => {
    render(
      <SummaryCards
        totalImpressions={0}
        totalClicks={0}
        avgPosition={0}
      />
    );

    // CTR should be 0.00% when there are no impressions
    expect(screen.getByText('0.00%')).toBeInTheDocument();
    expect(screen.getByText('0.0')).toBeInTheDocument();
  });
});
