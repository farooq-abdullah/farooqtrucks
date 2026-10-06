import { test, expect } from './helpers/map-test';

const chicago = { label: 'Chicago, Illinois, United States', primary: 'Chicago', secondary: 'Illinois, United States', supported: true };
const denver = { label: 'Denver, Colorado, United States', primary: 'Denver', secondary: 'Colorado, United States', supported: true };

test('location suggestions: debounce, country labels, selection, unsupported places and mobile', async ({ page }) => {
  const errors = []; page.on('pageerror', error => errors.push(error.message));
  const queries = [];
  await page.route('**/api/locations/search/?*', route => {
    const query = new URL(route.request().url()).searchParams.get('q'); queries.push(query);
    const suggestions = query.toLowerCase().startsWith('tok') ? [
      { label: 'Tokyo, Japan', primary: 'Tokyo', secondary: 'Japan', supported: false },
      { label: 'Tokio, North Dakota, United States', primary: 'Tokio', secondary: 'North Dakota, United States', supported: true },
    ] : [chicago];
    return route.fulfill({ contentType: 'application/json', body: JSON.stringify({ suggestions }) });
  });
  await page.goto('/plan');
  const current = page.getByRole('combobox', { name: 'Current location', exact: true });
  await current.fill('C'); await page.waitForTimeout(650); expect(queries).toEqual([]);
  await current.fill('Chi'); await current.fill('Chic');
  await expect(page.getByRole('option', { name: /Chicago/ })).toBeVisible();
  expect(queries).toEqual(['Chic']);
  await current.press('ArrowDown'); await current.press('Enter');
  await expect(current).toHaveValue(chicago.label);
  await expect(page.getByRole('listbox')).toBeHidden();
  const request = page.waitForRequest(r => r.url().includes('/api/trips/plan/') && r.method() === 'POST');
  await page.route('**/api/trips/plan/', route => route.fulfill({ status: 502, contentType: 'application/json', body: JSON.stringify({ detail: 'Test planner response' }) }));
  await page.getByRole('button', { name: 'Plan route & logs →' }).click();
  expect((await request).postDataJSON().current_location).toBe(chicago.label);
  await expect(page.getByRole('button', { name: 'Plan route & logs →' })).toBeEnabled();
  const pickup = page.getByRole('combobox', { name: 'Pickup location', exact: true });
  await pickup.fill('Tokio');
  await expect(page.getByRole('option', { name: /Tokyo/ })).toHaveAttribute('aria-disabled', 'true');
  await expect(page.getByRole('option', { name: /Tokio/ })).toContainText('North Dakota, United States');
  await page.screenshot({ path: '../artifacts/location-suggestions-desktop.png', fullPage: true });
  await pickup.press('Escape');
  await page.setViewportSize({ width: 390, height: 844 });
  const dropoff = page.getByRole('combobox', { name: 'Drop-off location', exact: true });
  await dropoff.fill('Chi'); await expect(page.getByRole('option', { name: /Chicago/ })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  await page.screenshot({ path: '../artifacts/location-suggestions-mobile.png', fullPage: true });
  await page.getByRole('option', { name: /Chicago/ }).click(); await expect(dropoff).toHaveValue(chicago.label);
  expect(errors).toEqual([]);
});

test('location search discards stale responses and recovers from errors', async ({ page }) => {
  await page.route('**/api/locations/search/?*', async route => {
    const query = new URL(route.request().url()).searchParams.get('q');
    if (query === 'Chic') {
      await new Promise(resolve => setTimeout(resolve, 1200));
      return route.fulfill({ contentType: 'application/json', body: JSON.stringify({ suggestions: [chicago] }) }).catch(() => {});
    }
    if (query === 'error') return route.fulfill({ status: 502, contentType: 'application/json', body: '{}' });
    return route.fulfill({ contentType: 'application/json', body: JSON.stringify({ suggestions: [denver] }) });
  });
  await page.goto('/plan');
  const current = page.getByRole('combobox', { name: 'Current location', exact: true });
  const oldRequest = page.waitForRequest('**/api/locations/search/?q=Chic');
  await current.fill('Chic'); await oldRequest;
  await current.fill('Denv'); await expect(page.getByRole('option', { name: /Denver/ })).toBeVisible();
  await page.waitForTimeout(1300); await expect(page.getByRole('option', { name: /Chicago/ })).toHaveCount(0);
  await current.fill('error'); await expect(page.getByText('Location suggestions are unavailable. You can still enter a full address.').first()).toBeVisible();
  await current.fill('Denv'); await expect(page.getByRole('option', { name: /Denver/ })).toBeVisible();
});


test('two-letter city aliases display explicit places and cache across fields', async ({ page }) => {
  const queries = [];
  const ny = { label: 'New York, New York, United States', primary: 'New York', secondary: 'New York, United States', supported: true };
  const la = { label: 'Los Angeles, California, United States', primary: 'Los Angeles', secondary: 'California, United States', supported: true };
  await page.route('**/api/locations/search/?*', route => {
    const query = new URL(route.request().url()).searchParams.get('q'); queries.push(query);
    return route.fulfill({ contentType: 'application/json', body: JSON.stringify({ suggestions: [query.toLowerCase() === 'ny' ? ny : la] }) });
  });
  await page.goto('/plan');
  const current = page.getByRole('combobox', { name: 'Current location', exact: true });
  await current.fill('NY');
  await expect(page.getByRole('option', { name: /New York.*United States/ })).toBeVisible();
  await current.press('ArrowDown'); await current.press('Enter');
  await expect(current).toHaveValue(ny.label);
  const pickup = page.getByRole('combobox', { name: 'Pickup location', exact: true });
  await pickup.fill('LA');
  await expect(page.getByRole('option', { name: /Los Angeles.*California/ })).toBeVisible();
  await page.getByRole('option', { name: /Los Angeles/ }).click();
  await expect(pickup).toHaveValue(la.label);
  const dropoff = page.getByRole('combobox', { name: 'Drop-off location', exact: true });
  await dropoff.fill('ny');
  await expect(page.getByRole('option', { name: /New York/ })).toBeVisible();
  expect(queries).toEqual(['NY', 'LA']);
});

test('location search stops an unresponsive provider and clearing input clears loading', async ({ page }) => {
  await page.route('**/api/locations/search/?*', () => {});
  await page.goto('/plan');
  const current = page.getByRole('combobox', { name: 'Current location', exact: true });
  await current.fill('Unknown address');
  await expect(page.getByLabel('Searching places', { exact: true })).toBeVisible();
  await expect(page.getByText('Location search took too long. Try again or enter a full address.').first()).toBeVisible({ timeout: 12000 });
  await expect(page.getByLabel('Searching places', { exact: true })).toBeHidden();
  await current.fill('New search');
  await expect(page.getByLabel('Searching places', { exact: true })).toBeVisible();
  await current.fill('');
  await expect(page.getByLabel('Searching places', { exact: true })).toBeHidden();
});
