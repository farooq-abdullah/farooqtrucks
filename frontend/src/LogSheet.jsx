import { useState } from 'react';
import { Button, ClickAwayListener, Tooltip } from '@mui/material';
import Icon from './components/Icon';
import { duty, DUTY_ORDER } from './theme';
import { activityLabel, activityReason, clock, dutyHours, hhmm, hm, hms, logActivities, longDate, miles, minuteTime, remarkPlace, shortDate, shortPlace, timeOfDay, utcLabel } from './lib/plan';

export const METADATA_FIELDS = [
  ['driver', 'Driver'], ['driverId', 'Driver no. (optional)'], ['initials', 'Initials (optional)'],
  ['codriver', 'Co-driver'], ['carrier', 'Carrier name'],
  ['office', 'Main office address'], ['terminal', 'Home terminal'], ['truck', 'Tractor / truck no.'],
  ['trailer', 'Trailer no.'], ['shipping', 'Shipping document no.'], ['commodity', 'Shipper / commodity'],
];
const y = status => 65 + DUTY_ORDER.indexOf(status) * 42;
export function DutyGraph({ log, interactive = true }) {
  const [active, setActive] = useState(null);
  const [pointer, setPointer] = useState('mouse');
  const width = 844, x = minute => 10 + minute / 1440 * (width - 20);
  const activities = logActivities(log);
  const points = [];
  log.segments.forEach((segment, i) => {
    if (i) points.push(`${x(segment.start_minute)},${y(log.segments[i - 1].status)}`);
    points.push(`${x(segment.start_minute)},${y(segment.status)}`, `${x(segment.end_minute)},${y(segment.status)}`);
  });
  return <ClickAwayListener onClickAway={() => setActive(null)}><div className="duty-graph">
    <div className="duty-labels"><div className="graph-heading">DUTY STATUS</div>{DUTY_ORDER.map((key, i) => <div key={key}><b className="status-dot" style={{ background: duty[key].color }} /><span>{i + 1}. {duty[key].label}{key === 'on_duty' && <small>Not driving</small>}</span></div>)}<div className="graph-bottom" /></div>
    <div className="time-scroller" tabIndex="0" role="region" aria-label="24-hour timeline. Scroll horizontally to view all hours.">
      <svg viewBox={`0 0 ${width} 232`} preserveAspectRatio="none" className="log-grid" role="group" aria-label={`Planned duty changes for ${log.date}`}>
        <title>Duty status from midnight to midnight</title><desc>{log.segments.map(s => `${duty[s.status].label} from minute ${s.start_minute.toFixed(1)} to ${s.end_minute.toFixed(1)}`).join('. ')}</desc>
        <rect width={width} height="44" fill="#EDF2F7" />
        {Array.from({ length: 25 }, (_, hour) => <g key={hour}><text x={x(hour * 60)} y="17" textAnchor="middle" fontSize="9">{hour === 0 || hour === 24 ? 'Mid.' : hour === 12 ? 'Noon' : hour % 12}</text><line x1={x(hour * 60)} x2={x(hour * 60)} y1="24" y2="212" stroke="#CBD5E1" /></g>)}
        {DUTY_ORDER.map(key => <g key={key}><line x1="0" x2={width} y1={y(key) + 21} y2={y(key) + 21} stroke="#E2E8F0" />{Array.from({ length: 97 }, (_, tick) => <line key={tick} x1={x(tick * 15)} x2={x(tick * 15)} y1={y(key) + (tick % 4 === 0 ? 4 : tick % 2 === 0 ? 11 : 16)} y2={y(key) + 21} stroke="#788A9B" strokeWidth="0.6" />)}</g>)}
        <polyline points={points.join(' ')} fill="none" stroke="#101F30" strokeWidth="3" strokeLinejoin="round" />
        {interactive && activities.map((activity, index) => {
          const key = `${log.date}-${index}`, hours = (activity.end_minute - activity.start_minute) / 60;
          const label = activityLabel(activity.activity), previous = activities[index - 1];
          const line = `M ${x(activity.start_minute)} ${y(activity.status)} H ${x(activity.end_minute)}`;
          const transition = previous && previous.status !== activity.status ? `M ${x(activity.start_minute)} ${y(previous.status)} V ${y(activity.status)}` : null;
          const fullPeriod = activity.event_start && (activity.event_start.slice(0, 10) !== log.date || activity.event_end.slice(0, 10) !== log.date);
          return <Tooltip key={key} arrow followCursor={pointer === 'mouse'} describeChild disableInteractive disableTouchListener enterDelay={0} leaveDelay={0}
            open={active === key} onOpen={() => setActive(key)} onClose={() => pointer !== 'touch' && setActive(value => value === key ? null : value)}
            slotProps={{ tooltip: { className: 'log-tooltip' }, popper: { className: 'no-print' } }}
            title={<div className="log-tooltip-content"><strong>{label}</strong><span className="mono">{minuteTime(activity.start_minute)}–{minuteTime(activity.end_minute)} · {hms(hours)}</span>
              <span>{duty[activity.status].label}{activity.status === 'on_duty' ? ' · counts as work' : activity.status === 'driving' ? ' · counts as work' : ' · does not count as work'}</span>
              {activity.location && <span className="log-tooltip-place">{remarkPlace(activity)}</span>}
              {fullPeriod && <span className="log-tooltip-place">Full activity: {shortDate(activity.event_start)} {clock(activity.event_start)} → {shortDate(activity.event_end)} {clock(activity.event_end)}</span>}
              <p className="log-tooltip-reason">{activity.reason || activityReason(activity.activity)}</p></div>}>
            <g className={`log-activity ${active === key ? 'active' : ''}`} data-log-activity={activity.activity} tabIndex={0} role="button"
              aria-label={`${label}, ${minuteTime(activity.start_minute)}–${minuteTime(activity.end_minute)}, ${hms(hours)}`}
              onPointerEnter={event => setPointer(event.pointerType === 'touch' ? 'touch' : 'mouse')}
              onFocus={event => { if (event.currentTarget.matches(':focus-visible')) setPointer('keyboard'); }}
              onClick={() => setActive(key)} onKeyDown={event => {
                setPointer('keyboard');
                if (event.key === 'Escape') { setActive(null); event.stopPropagation(); }
                if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); setActive(value => value === key ? null : key); }
              }}>
              <path className="activity-highlight" d={line} fill="none" stroke="#244EBA" strokeWidth="5" pointerEvents="none" />
              {transition && <path d={transition} fill="none" stroke="transparent" strokeWidth="4" pointerEvents="stroke" />}
              <rect className="activity-hit" x={x(activity.start_minute)} y={y(activity.status) - 8} width={Math.max(1, x(activity.end_minute) - x(activity.start_minute))} height="16" fill="transparent" />
            </g>
          </Tooltip>;
        })}
        <text x="10" y="227" fontSize="10">Midnight · 00:00</text><text x={width / 2} y="227" textAnchor="middle" fontSize="10">Noon · 12:00</text><text x={width - 10} y="227" textAnchor="end" fontSize="10">Midnight · 24:00</text>
      </svg>
    </div>
    <div className="duty-totals"><div className="graph-heading">H:M</div>{DUTY_ORDER.map(key => <div key={key} className="mono">{hhmm(log.totals_minutes ? log.totals_minutes[key] / 60 : log.totals_hours[key])}</div>)}<div className="graph-bottom mono">24:00</div></div>
  </div></ClickAwayListener>;
}
export function DayRecap({ log, availability, onHelp }) {
  const driving = log.totals_minutes ? log.totals_minutes.driving / 60 : log.totals_hours.driving;
  const work = log.totals_minutes ? log.totals_minutes.on_duty / 60 : log.totals_hours.on_duty;
  return <section className="day-recap"><h2>70-hour / 8-day recap</h2><div className="recap-values">{[
    ['A · Prior seven days', 'Not supplied'], ['B · Planned budget at day start', hm(availability)],
    ['C · On duty today', hm(dutyHours(log))], ['D · Available tomorrow', 'History needed'],
  ].map(([label, value]) => <div key={label}><span className="caption">{label}</span><strong className="mono">{value}</strong></div>)}</div>
    <p className="caption recap-breakdown no-print">Rounded totals: {hm(driving)} driving + {hm(work)} other work = <strong>{hm(dutyHours(log))} on duty</strong>. Breaks and sleeper time are excluded.</p>
    <Button className="recap-help no-print" onClick={() => onHelp?.('recap')} startIcon={<Icon name="info" />}>Earlier daily hours are needed for an exact rolling recap.</Button>
  </section>;
}
export function PlanNotice() {
  return <p className="plan-notice caption">Planned log · assumed off-duty time outside the trip · estimated mileage and stop locations. Record actual activity in your official log.</p>;
}
export default function LogSheet({ log, locations, metadata, availability, onHelp, printCopy = false }) {
  const offset = log.clock.replace('UTC', '');
  return <article className="log-sheet surface" aria-label={`Daily log ${log.date}`}>
    <div className="sheet-heading"><div><h2>Driver’s daily log</h2><p className="mono">{longDate(log.date)}</p></div><span className="sheet-stamp">PLANNED</span></div>
    <div className="sheet-trip"><div><span>Trip from: {shortPlace(locations[0].log_location || locations[0].label)}</span><span>Trip to: {shortPlace(locations[2].log_location || locations[2].label)}</span></div><div><strong className="mono">{miles(log.distance_miles, 1)} miles driving today</strong><span>Truck mileage: {miles(log.distance_miles, 1)} mi · solo estimate</span><span>00:00–24:00 · fixed {utcLabel(`${log.date}T00:00:00${offset.slice(0, 3)}:${offset.slice(3)}`)}</span></div></div>
    <div className="sheet-details">{METADATA_FIELDS.map(([key, label]) => <div key={key}><span className="caption">{label}</span><span>{metadata[key] || 'Not supplied'}</span></div>)}</div>
    <DutyGraph key={log.date} log={log} interactive={!printCopy} />
    <p className="accounting"><Icon name="check" />24:00 accounted for · totals rounded to minutes</p>
    <section className={`remarks ${log.remarks.length > 8 ? 'remarks-dense' : ''}`}><h2>Duty changes & location remarks</h2><ol>{log.remarks.map((remark, index) => <li key={index}><time className="mono">{timeOfDay(remark.time)}</time><div><strong>{activityLabel(remark.activity)}</strong><span title={remark.location}>{remarkPlace(remark)}</span></div></li>)}</ol></section>
    <DayRecap log={log} availability={availability} onHelp={onHelp} />
    <PlanNotice />
  </article>;
}
