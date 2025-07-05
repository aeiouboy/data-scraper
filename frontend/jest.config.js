module.exports = {
  preset: 'react-scripts',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  moduleNameMapper: {
    // Remove axios mapping since we're mocking it globally in setupTests.ts
  },
  transformIgnorePatterns: [
    'node_modules/(?!(axios)/)',
  ],
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.{js,jsx,ts,tsx}',
    '<rootDir>/src/**/*.{spec,test}.{js,jsx,ts,tsx}',
  ],
  testPathIgnorePatterns: [
    '/node_modules/',
    '/build/',
  ],
  coveragePathIgnorePatterns: [
    '/node_modules/',
    '/src/test-utils.tsx',
    '/src/setupTests.ts',
  ],
};