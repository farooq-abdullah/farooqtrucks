import { test, expect } from './helpers/map-test';
import { mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';
test('long road trip shows fuel, rests and a sheet for every day', async ({ page }) => {
  // Marker symbols must survive failed image requests; map tiles are mocked by
  // the shared fixture, while the road route and schedule still use the API.
  const waypointPath = /\/assets\/(?:inspection\.svg|figma\/(?:934c0|6ad21|58212|7fe3d|4177e|6cf2b|df277|fcf74|482be)\.svg)$/;
  await page.route('**/assets/**', route => route.request().resourceType() === 'image' && waypointPath.test(new URL(route.request().url()).pathname)
    ? route.fulfill({status:404,body:'Image request unavailable'}) : route.continue());
  await page.goto('/');
  await page.getByRole('combobox', { name: 'Current location', exact: true }).fill('Los Angeles, CA');
  await page.getByRole('combobox', { name: 'Pickup location', exact: true }).fill('Phoenix, AZ');
  await page.getByRole('combobox', { name: 'Drop-off location', exact: true }).fill('New York, NY');
  await page.getByRole('spinbutton', { name: 'Current cycle used (hrs)', exact: true }).fill('66');
  const responsePromise = page.waitForResponse(r => r.url().includes('/api/trips/plan/') && r.request().method() === 'POST', { timeout: 110000 });
  await page.getByRole('button', { name: 'Plan route & logs →' }).click();
  const response = await responsePromise; expect(response.status()).toBe(200); const plan = await response.json();
  expect(plan.summary.distance_miles).toBeGreaterThan(2000);
  expect(plan.summary.fuel_stops).toBeGreaterThanOrEqual(2);
  expect(plan.summary.cycle_restarts).toBeGreaterThanOrEqual(1);
  expect(plan.events.some(e => e.activity.startsWith('Daily rest'))).toBeTruthy();
  await expect(page.getByRole('button', {name:/30-minute breaks: [1-9]\d* planned/})).toBeVisible();
  await expect(page.locator('.driver-clocks')).not.toContainText('Not due');
  expect(plan.daily_logs.every(log => sum(log.totals_minutes) === 1440)).toBeTruthy();
  const fuel = plan.events.filter(e => e.activity.startsWith('Fueling'));
  let previous = 0;
  for (const stop of fuel) { expect(stop.start_route_miles - previous).toBeLessThanOrEqual(1000 + 1e-6); previous = stop.start_route_miles; }
  expect(plan.summary.distance_miles - previous).toBeLessThanOrEqual(1000 + 1e-6);
  await expect(page.locator('.leaflet-container')).toBeVisible();
  expect(await page.locator('.route-waypoint img').count()).toBeGreaterThan(3);
  await expect.poll(() => page.locator('.route-waypoint img, .itinerary-stop .waypoint').evaluateAll(images =>
    images.filter(image => !image.complete || image.naturalWidth === 0).map(image => image.getAttribute('src'))
  )).toEqual([]);
  await page.getByRole('button', {name:/30-minute breaks: [1-9]\d* planned/}).click();
  await expect(page.locator('.leaflet-popup-content')).toContainText('30-minute break');
  const itineraryCount = await page.locator('.itinerary-stop').count();
  await page.locator('.itinerary-stop').nth(Math.floor(itineraryCount / 2)).scrollIntoViewIfNeeded();
  const map = await page.locator('.route-map-column').boundingBox();
  const header = await page.locator('.workflow-toolbar').boundingBox();
  expect(map.y).toBeGreaterThanOrEqual(header.y + header.height + 8);
  expect(map.y).toBeLessThanOrEqual(header.y + header.height + 32);
  expect(map.y + map.height).toBeLessThanOrEqual(1000);
  await expect(page.locator('.itinerary-stop')).toHaveCount(1 + plan.events.filter(e => e.status !== 'driving').length);
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  await expect.poll(() => page.locator('.itinerary-stop .waypoint').evaluateAll(images =>
    images.filter(image => !image.complete || image.naturalWidth === 0).map(image => image.getAttribute('src'))
  )).toEqual([]);
  await page.getByRole('button', { name: 'Review logs', exact: true }).click();
  await expect(page.locator('.day-choice')).toHaveCount(plan.daily_logs.length);
  await page.locator('.day-choice').last().click();
  await expect(page.locator('.mobile-log .duty-graph')).toBeVisible();
  await page.emulateMedia({ media: 'print' });
  const artifacts = resolve('../artifacts'); await mkdir(artifacts, { recursive: true });
  const pdf = await page.pdf({ path: `${artifacts}/long-trip-logs.pdf`, preferCSSPageSize: true, printBackground: true });
  expect((pdf.toString('latin1').match(/\/Type\s*\/Page\b/g) || []).length).toBe(plan.daily_logs.length);
});
const sum = object => Object.values(object).reduce((a, b) => a + b, 0);
