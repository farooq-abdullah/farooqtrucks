// Pure helpers that turn the API response into display-ready values.
// Times are shown exactly as written by the API (terminal planning clock),
// so no browser timezone conversion happens anywhere in the UI.

const STATES = {
  Alabama: 'AL', Arizona: 'AZ', Arkansas: 'AR', California: 'CA', Colorado: 'CO', Connecticut: 'CT',
  Delaware: 'DE', 'District of Columbia': 'DC', Florida: 'FL', Georgia: 'GA', Idaho: 'ID', Illinois: 'IL',
  Indiana: 'IN', Iowa: 'IA', Kansas: 'KS', Kentucky: 'KY', Louisiana: 'LA', Maine: 'ME', Maryland: 'MD',
  Massachusetts: 'MA', Michigan: 'MI', Minnesota: 'MN', Mississippi: 'MS', Missouri: 'MO', Montana: 'MT',
  Nebraska: 'NE', Nevada: 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM',
  'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', Ohio: 'OH', Oklahoma: 'OK', Oregon: 'OR',
  Pennsylvania: 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC', 'South Dakota': 'SD', Tennessee: 'TN',
  Texas: 'TX', Utah: 'UT', Vermont: 'VT', Virginia: 'VA', Washington: 'WA', 'West Virginia': 'WV',
  Wisconsin: 'WI', Wyoming: 'WY', Alaska: 'AK', Hawaii: 'HI',
};

/** "Springfield, Sangamon County, Illinois, United States" -> "Springfield, IL". */
export function shortPlace(label = '') {
  const parts = label.split(',').map((part) => part.trim()).filter(Boolean)
    .filter((part) => part !== 'United States' && !/^\d{5}(-\d{4})?$/.test(part));
  if (parts.length < 2) return label;
  const stateIndex = parts.findIndex((part, index) => index > 0 && STATES[part]);
  if (stateIndex === -1) return label; // already short, e.g. "Near Chicago, IL"
  return `${parts[0]}, ${STATES[parts[stateIndex]]}`;
}

/** Bare city name for compact titles: "Saint Louis, MO" -> "Saint Louis". */
export const cityOnly = (label) => shortPlace(label).replace(/^Near /, '').split(',')[0];
export function remarkPlace(remark) {
  const place = shortPlace(remark.location);
  const context = remark.route_reference || (remark.road && /^(Near |About |Along route|In transit)/.test(remark.location) ? remark.road : '');
  return `${place}${context && !place.includes(context) ? ` · ${context}` : ''}`;
}
export function activityLabel(activity) {
  const drive = activity.match(/^((?:Continue )?[Dd]rive to )(.+)$/);
  return drive ? `${drive[1]}${shortPlace(drive[2])}` : activity;
}

export function activityReason(activity = '') {
  const name = activity.replace(/^Continue /, '').toLowerCase();
  if (name.startsWith('driving break')) return 'After 8 accumulated driving hours, take 30 minutes without driving before continuing. Coffee is optional; loading or fueling can also satisfy this interruption.';
  if (name.startsWith('daily rest')) return 'A full 10-hour rest starts fresh daily clocks after the 11-hour driving limit or 14-hour window is reached.';
  if (name.startsWith('cycle restart')) return 'The plan uses 34 hours of rest to restore cycle capacity because earlier daily hours for recapture were not supplied.';
  if (name.startsWith('pickup') || name.startsWith('drop-off')) return 'One hour of on-duty loading or unloading, as specified by the assessment.';
  if (name.startsWith('fueling')) return 'A planned 30-minute fuel stop at or before 1,000 miles since the last fill; a full tank is assumed at departure.';
  if (name.includes('inspection')) return 'Vehicle and trailer inspection; 15 minutes is a planning estimate and counts as work.';
  if (name.startsWith('drive to')) return 'Estimated driving time from the road route.';
  return 'Assumed off-duty time outside the trip. Record actual activity in your official log.';
}

export function minuteTime(minutes) {
  const seconds = Math.round(minutes * 60);
  const hours = Math.floor(seconds / 3600);
  const minute = Math.floor(seconds % 3600 / 60);
  const second = seconds % 60;
  return `${String(hours).padStart(2, '0')}:${String(minute).padStart(2, '0')}${second ? `:${String(second).padStart(2, '0')}` : ''}`;
}

/** Keep second-level schedule boundaries visible instead of flooring them. */
export const timeOfDay = time => time.slice(6, 8) === '00' ? time.slice(0, 5) : time.slice(0, 8);

/** Individual activities remain selectable even when adjacent statuses form one line. */
export function logActivities(log) {
  if (log.activities) return log.activities;
  // Already-open plans from the previous API version can still be inspected.
  const remarks = log.remarks.map(remark => ({ ...remark, minute: remark.time.split(':').reduce((sum, value, index) => sum + Number(value) * [60, 1, 1 / 60][index], 0) }));
  return log.segments.flatMap(segment => {
    const boundaries = [segment.start_minute, ...remarks.filter(r => r.minute > segment.start_minute && r.minute < segment.end_minute).map(r => r.minute), segment.end_minute];
    return boundaries.slice(0, -1).map((start, index) => {
      const remark = remarks.findLast(r => r.minute <= start + 1e-8);
      return { ...segment, ...remark, activity: remark?.activity || segment.status.replace('_', ' '), start_minute: start, end_minute: boundaries[index + 1] };
    });
  });
}

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function dateParts(iso) {
  const [y, m, d] = iso.slice(0, 10).split('-').map(Number);
  return { y, m, d, weekday: WEEKDAYS[new Date(Date.UTC(y, m - 1, d)).getUTCDay()] };
}

export const clock = iso => timeOfDay(iso.slice(11, 19));
export function shortDate(iso) {
  const { m, d, weekday } = dateParts(iso);
  return `${weekday} ${d} ${MONTHS[m - 1]}`;
}
export function longDate(iso) {
  const { y, m, d, weekday } = dateParts(iso);
  return `${weekday} ${d} ${MONTHS[m - 1]} ${y}`;
}
/** "-06:00" from an ISO timestamp, displayed as "UTC−06:00". */
export const utcLabel = (iso) => `UTC${iso.slice(19).replace('-', '−') || '+00:00'}`;

/** 7.76 -> "7h 46m"; 0.5 -> "30m"; 34 -> "34h". */
export function hm(hours) {
  const total = Math.round(hours * 60);
  const h = Math.floor(total / 60);
  const m = total % 60;
  if (!h) return `${m}m`;
  return m ? `${h}h ${String(m).padStart(2, '0')}m` : `${h}h`;
}
/** Exact activity duration, so a tooltip agrees with its start/end boundaries. */
export function hms(hours) {
  const seconds = Math.round(hours * 3600);
  const wholeMinutes = Math.floor(seconds / 60);
  const second = seconds % 60;
  return [wholeMinutes ? hm(wholeMinutes / 60) : '', second ? `${second}s` : ''].filter(Boolean).join(' ') || '0m';
}
/** Log-sheet style hours: 16.233 -> "16:14". */
export function hhmm(hours) {
  const total = Math.round(hours * 60);
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, '0')}`;
}
export const miles = (value, digits = 0) => value.toLocaleString('en-US', {
  minimumFractionDigits: digits, maximumFractionDigits: digits,
});

const KINDS = [
  ['Pre-trip inspection', 'inspection', 'Pre-trip / TIV'],
  ['Post-trip inspection', 'inspection', 'Post-trip / TIV'],
  ['Pickup', 'pickup', 'Pickup'],
  ['Drop-off', 'dropoff', 'Drop-off'],
  ['Fueling', 'fuel', 'Fuel stop'],
  ['Driving break', 'break', '30-minute break'],
  ['Daily rest', 'rest', '10-hour rest'],
  ['Cycle restart', 'restart', '34-hour restart'],
];
export function stopKind(activity = '') {
  const match = KINDS.find(([prefix]) => activity.startsWith(prefix));
  return match ? { kind: match[1], title: match[2] } : { kind: 'other', title: activity };
}

/**
 * Collapse the event list into an itinerary: stops (start, every non-driving
 * activity) separated by aggregated driving stretches.
 */
export function buildItinerary(plan) {
  const items = [];
  const first = plan.events[0];
  items.push({
    type: 'stop', key: 'start', kind: 'start', number: 1, title: first.status === 'driving' ? 'Depart' : 'Start plan',
    place: shortPlace(plan.locations[0].label), fullPlace: plan.locations[0].label,
    start: first.start, end: first.start, hours: 0, status: 'driving',
    coordinates: plan.locations[0].coordinates,
  });
  let drive = null;
  plan.events.forEach((event, index) => {
    if (event.status === 'driving') {
      if (!drive) {
        drive = { type: 'drive', key: `drive-${index}`, start: event.start, end: event.end, hours: 0, miles: 0 };
        items.push(drive);
      }
      drive.end = event.end;
      drive.hours += event.duration_seconds / 3600;
      drive.miles += event.distance_miles;
      return;
    }
    drive = null;
    const { kind, title } = stopKind(event.activity);
    const number = kind === 'pickup' ? 2 : kind === 'dropoff' ? 3 : null;
    const location = number ? plan.locations[number - 1] : null;
    items.push({
      type: 'stop', key: `stop-${index}`, kind, number, title, status: event.status,
      place: shortPlace(location?.label || event.location), fullPlace: location?.label || event.location,
      start: event.start, end: event.end, hours: event.duration_seconds / 3600,
      coordinates: location?.coordinates || event.coordinates,
      routeReference: event.route_reference,
      reason: event.reason || activityReason(event.activity),
    });
  });
  return items;
}

/** On-duty (driving + on duty) hours per log day, for the day strip. */
export const dutyHours = (log) => log.totals_minutes
  ? (log.totals_minutes.driving + log.totals_minutes.on_duty) / 60
  : log.totals_hours.driving + log.totals_hours.on_duty;

/**
 * Cycle hours used at the end of each log day. Driving and on-duty time add
 * to the cycle; a 34-hour restart resets it to zero once the restart ends.
 */
export function cycleByDay(plan, startingCycle) {
  const offset = plan.events[0].start.slice(19) || 'Z';
  return plan.daily_logs.map((log) => {
    const [y, m, d] = log.date.split('-').map(Number);
    const next = new Date(Date.UTC(y, m - 1, d + 1)).toISOString().slice(0, 10);
    const dayEnd = Date.parse(`${next}T00:00:00${offset}`);
    let cycle = startingCycle;
    for (const event of plan.events) {
      const start = Date.parse(event.start);
      const end = Date.parse(event.end);
      if (start >= dayEnd) break;
      if (event.status === 'driving' || event.status === 'on_duty') {
        cycle += (Math.min(end, dayEnd) - start) / 3600000;
      } else if (event.activity.startsWith('Cycle restart') && end <= dayEnd) {
        cycle = 0;
      }
    }
    return cycle;
  });
}

/** Total hours that count toward the cycle across the whole trip. */
export const tripDutyHours = (plan) => plan.events
  .filter((event) => event.status === 'driving' || event.status === 'on_duty')
  .reduce((sum, event) => sum + event.duration_seconds / 3600, 0);
