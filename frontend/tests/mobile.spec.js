import { test, expect } from './helpers/map-test';
import { readFile, mkdir } from 'node:fs/promises';

// Actual hosted API output, kept deterministic so layout regressions do not
// depend on provider latency. The other browser specs exercise live routing.
const plan = JSON.parse(await readFile(new URL('./fixtures/recorded-short-plan.json', import.meta.url), 'utf8'));

test('phone inputs stay readable without Safari focus zoom', async ({ page }) => {
  for (const width of [320, 390, 430]) {
    await page.setViewportSize({ width, height: 844 });
    await page.goto('/plan');
    const inputs = page.getByRole('combobox');
    for (const input of await inputs.all()) {
      expect(await input.evaluate(node => parseFloat(getComputedStyle(node).fontSize))).toBeGreaterThanOrEqual(16);
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
    const header = await page.locator('.workflow-toolbar').boundingBox();
    expect(header.height).toBeLessThanOrEqual(72);
    const cycle = page.getByRole('spinbutton', { name: 'Current cycle used (hrs)', exact: true });
    await cycle.fill('71');
    await expect(page.getByText('Enter hours between 0 and 70.')).toBeVisible();
    await expect(cycle).toHaveAttribute('aria-invalid', 'true');
    await cycle.fill('20');
    await expect(page.getByText('Enter hours between 0 and 70.')).toBeHidden();
    const nav = await page.getByRole('tablist', { name: 'Trip workflow' }).boundingBox();
    expect(nav.y + nav.height).toBeGreaterThanOrEqual(820);
    for (const tab of await page.getByRole('tab').all()) {
      expect((await tab.boundingBox()).height).toBeGreaterThanOrEqual(44);
    }
  }
});

test('phone log shows midnight through 24:00 without horizontal scrolling', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.route('**/api/trips/plan/', route => route.fulfill({json:plan}));
  await page.goto('/plan');
  await page.getByRole('button', {name:'Plan route & logs →'}).click();
  await page.getByRole('tab', {name:'Daily logs',exact:true}).click();
  const graph = page.locator('.mobile-log .duty-graph');
  await expect(graph).toBeVisible();
  const scroller = graph.locator('.time-scroller');
  expect(await scroller.evaluate(node => node.scrollWidth <= node.clientWidth)).toBeTruthy();
  const grid = await graph.locator('svg').boundingBox();
  expect(grid.x).toBeGreaterThanOrEqual(0);
  expect(grid.x + grid.width).toBeLessThanOrEqual(390);
  await expect(graph).toContainText('24:00');
  await expect(graph).toContainText('Off duty');
  await expect(graph).toContainText('Sleeper berth');
  const picker = page.getByLabel('Activity details', {exact:true});
  expect((await picker.boundingBox()).height).toBeGreaterThanOrEqual(44);
  await picker.selectOption({label:'08:00 · Pre-trip inspection / TIV (15 minutes)'});
  await expect(page.locator('.compact-activity-details')).toContainText('Pre-trip inspection');
  await expect(page.locator('.compact-activity-details')).toContainText('08:00–08:15 · 15m');
  await graph.locator('[data-log-activity^="Pickup"] .activity-hit').click();
  await expect(page.getByRole('tooltip')).toContainText('Pickup');
  await expect(page.getByRole('tooltip')).toContainText('1h');
  await graph.locator('[data-log-activity^="Pickup"]').press('Escape');
  await page.getByRole('button', {name:'Events',exact:true}).click();
  await expect(page.locator('.log-events')).toContainText('12:06:48');
  await page.getByRole('tab', {name:'Route',exact:true}).click();
  await expect(page.locator('.route-waypoint').first()).toBeVisible();
  for (const marker of await page.locator('.route-waypoint').all()) {
    const box = await marker.boundingBox();
    expect(box.width).toBeLessThanOrEqual(28);
  }
  await mkdir('../artifacts/mobile-redesign', {recursive:true});
  await page.screenshot({path:'../artifacts/mobile-redesign/route-390.png',fullPage:true});
});
