import { test, expect } from '@playwright/test';
import { clock, dutyHours, hms, hm, minuteTime, timeOfDay } from '../src/lib/plan.js';

test('activity boundaries preserve seconds while the day recap uses displayed minute totals', () => {
  // A 16:15:43 completion must not look like 16:15 alongside an 8h16m recap.
  expect(clock('2026-10-06T16:15:43-05:00')).toBe('16:15:43');
  expect(timeOfDay('16:15:43')).toBe('16:15:43');
  expect(minuteTime(16 * 60 + 15 + 43 / 60)).toBe('16:15:43');
  expect(hms((5 * 3600 + 45 * 60 + 43) / 3600)).toBe('5h 45m 43s');
  expect(hms(15 / 60)).toBe('15m');
  expect(minuteTime(1440)).toBe('24:00');
  expect(minuteTime(1439 + 59 / 60)).toBe('23:59:59');
  expect(clock('2026-10-06T08:00:00-05:00')).toBe('08:00');

  const log = { totals_minutes: { driving: 346, on_duty: 150 }, totals_hours: { driving: 5.762, on_duty: 2.5 } };
  expect(hm(dutyHours(log))).toBe('8h 16m');
});
