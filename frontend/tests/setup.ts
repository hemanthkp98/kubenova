/**
 * @file Vitest test setup — mock browser APIs not available in jsdom.
 */

import "@testing-library/jest-dom";

// Mock matchMedia (not implemented in jsdom).
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});

// Mock ResizeObserver (used by Monaco Editor and some Radix components).
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock crypto.randomUUID for generateId().
if (!global.crypto.randomUUID) {
  Object.defineProperty(global.crypto, "randomUUID", {
    value: () => "test-uuid-" + Math.random().toString(36).slice(2),
  });
}

// Suppress console.error for known expected test warnings.
const originalError = console.error;
beforeAll(() => {
  console.error = (...args: unknown[]) => {
    const message = String(args[0]);
    if (message.includes("Warning: ReactDOM.render") || message.includes("act(")) return;
    originalError(...args);
  };
});
afterAll(() => {
  console.error = originalError;
});
