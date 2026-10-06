import { test as base, expect } from '@playwright/test';

// Public OSM tiles prohibit automated pan/zoom fetching. Rendering tests use a
// neutral local background; the actual route, markers and API remain real.
const background = '<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256"><rect width="256" height="256" fill="#edf2f7"/><path d="M0 128H256M128 0V256" stroke="#e2e8f0"/></svg>';

export const test = base.extend({
  mapTileRequests: [async ({ page }, use) => {
    const requests = [];
    await page.route('https://tile.openstreetmap.org/**', async route => {
      requests.push({ url:route.request().url(), referer:route.request().headers().referer || '' });
      await route.fulfill({status:200,contentType:'image/svg+xml',body:background,headers:{'cache-control':'public, max-age=604800'}});
    });
    await use(requests);
  }, {auto:true}],
});
export { expect };
