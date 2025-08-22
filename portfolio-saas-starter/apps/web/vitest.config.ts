import { defineConfig } from 'vitest/config';
import { fileURLToPath } from 'node:url';

export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    css: true,
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  define: {
    'import.meta.env.MODE': JSON.stringify('test'),
    'import.meta.env.BASE_URL': JSON.stringify('/'),
    'import.meta.env.PROD': 'false',
    'import.meta.env.DEV': 'true',
  },
});

