import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react() as any],
  test: {
    environment: 'jsdom',
    setupFiles: ['./test/setup.ts'],
    globals: true,
    css: true,
    // Integration Tests Konfiguration
    include: [
      'test/**/*.{test,spec}.{js,ts,jsx,tsx}',
      'test/integration/**/*.{test,spec}.{js,ts,jsx,tsx}'
    ],
    exclude: [
      'node_modules',
      'dist',
      '.next',
      'coverage'
    ],
    // Timeout für Integration Tests
    testTimeout: 30000,
    hookTimeout: 30000,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'test/',
        '**.config.{js,ts}',
        '**/types/**',
        '**.d.ts',
        '**/integration/**' // Integration Tests aus Coverage ausschließen
      ],
      // Coverage-Schwellenwerte
      thresholds: {
        global: {
          branches: 80,
          functions: 80,
          lines: 80,
          statements: 80
        }
      }
    },
    // Parallel Test Execution
    pool: 'threads',
    poolOptions: {
      threads: {
        singleThread: false
      }
    },
    // Retry-Konfiguration für Integration Tests
    retry: 2,
    // Reporter-Konfiguration
    reporter: ['verbose']
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './')
    }
  }
})

