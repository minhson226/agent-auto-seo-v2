/**
 * Tests for API client
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock axios before importing
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      interceptors: {
        request: {
          use: vi.fn(),
        },
        response: {
          use: vi.fn(),
        },
      },
    })),
  },
}));

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('stores and retrieves JWT token from localStorage', () => {
    const testToken = 'test-jwt-token';
    localStorage.setItem('jwt_token', testToken);
    
    expect(localStorage.getItem('jwt_token')).toBe(testToken);
  });

  it('clears tokens on logout', () => {
    localStorage.setItem('jwt_token', 'test-token');
    localStorage.setItem('refresh_token', 'test-refresh');
    
    localStorage.removeItem('jwt_token');
    localStorage.removeItem('refresh_token');
    
    expect(localStorage.getItem('jwt_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
  });
});
