import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests', timeout: 120000, workers: 1,
  use: { baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:5180', channel: process.env.PLAYWRIGHT_CHANNEL || 'msedge', headless: true, viewport: { width: 1440, height: 1000 } },
  reporter: [['list']],
});
