import { defineConfig } from '@playwright/test';
const browserName = process.env.PLAYWRIGHT_BROWSER || 'chromium';
export default defineConfig({
  testDir: './tests', timeout: 120000, workers: 1,
  use: { baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:5180', browserName, channel: browserName === 'chromium' ? process.env.PLAYWRIGHT_CHANNEL || 'msedge' : undefined, isMobile: browserName === 'webkit', hasTouch: browserName === 'webkit', headless: true, viewport: { width: 1440, height: 1000 } },
  reporter: [['list']],
});
