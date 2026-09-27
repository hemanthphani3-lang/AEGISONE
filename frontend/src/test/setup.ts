import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock fetch globally for tests if needed
if (!globalThis.fetch) {
  globalThis.fetch = vi.fn();
}
