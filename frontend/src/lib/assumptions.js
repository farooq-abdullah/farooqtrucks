const BASE_ASSUMPTIONS = [
  'Property-carrying driver; 70-hour/8-day cycle; no adverse-driving exception.',
  'Driver starts after at least 10 consecutive hours off duty, with fresh daily driving clocks.',
  'Prior daily cycle history is unknown: no old hours are recaptured; a 34-hour restart restores capacity.',
  'The 70-hour and 14-hour limits stop driving; loading, unloading and inspections can continue beyond them.',
  "Departure defaults to today at 08:00 in the starting location's time zone.",
  'Full daily rests and cycle restarts assume actual use of a compliant sleeper berth; short driving breaks are off duty.',
  'Solo driver with one carrier and the same truck/trailer throughout; no split sleeper, team driving, personal conveyance, yard moves or special exceptions are used.',
  'One hour each for pickup and drop-off; 30 minutes per fuel stop; a full tank at departure.',
  'Pre-trip and post-trip inspections/TIV are planned as 15 minutes each per driving shift; this is an estimate, not a legal minimum or proof of completion.',
  'At least one fuel stop every 1,000 miles; 30-minute fueling/loading can satisfy the driving-break rule.',
  'Road travel times are estimates without live traffic or truck height/weight restrictions.',
  'Driving mileage is distributed proportionally to elapsed driving time within each route leg.',
  'Stop markers estimate where a break is due; they do not identify verified parking or fuel facilities.',
  'These are planned logs; missing driver, carrier and vehicle details are left unspecified.',
  'Off-duty time before departure and after completion fills the planned day; it is assumed, not supplied historical activity.',
  'Roadside remarks use estimated nearby places and road names where available; actual highway/milepost or service-plaza details must be recorded in the official log.',
];

export function planningAssumptions(plan) {
  const timezone = plan.planning_parameters.time_zone;
  const timezoneAssumption = `The starting location was resolved to ${timezone} and is used as the driver's home-terminal clock, and log sheets start at midnight. This assumes the trip starts at the driver's home terminal and the carrier's 24-hour period starts at midnight. The UTC offset at departure is held constant across these 24-hour planned sheets; a daylight-saving transition during a trip is not modeled.`;

  return [...BASE_ASSUMPTIONS, timezoneAssumption];
}
