import { useState } from 'react';
import { Button, ButtonBase, ToggleButton, ToggleButtonGroup } from '@mui/material';
import LogSheet, { DayRecap, DutyGraph, PlanNotice } from '../LogSheet';
import Icon from './Icon';
import { activityLabel, activityReason, cycleByDay, dutyHours, hm, hms, logActivities, miles, minuteTime, remarkPlace, shortDate, shortPlace, timeOfDay, utcLabel } from '../lib/plan';
export default function LogsView({ plan, metadata, onDetails, onHelp }) {
  const [day, setDay] = useState(0), [mode, setMode] = useState('timeline');
  const cycles = cycleByDay(plan, plan.planning_parameters.initial_cycle_hours);
  const log = plan.daily_logs[day];
  const availability = Math.max(0, 70 - (day === 0 ? plan.planning_parameters.initial_cycle_hours : cycles[day - 1]));
  return <>
    <div className="page-heading"><h1>Planned daily logs</h1><p>{plan.locations.map(p => shortPlace(p.log_location || p.label)).join(' → ')} · {plan.daily_logs.length} planned {plan.daily_logs.length === 1 ? 'day' : 'days'}</p></div>
    <p className="sheet-notice desktop-only"><Icon name="info" />These sheets show the suggested trip plan. Record what actually happens in your official log.</p>
    <div className="logs-layout"><aside className="day-picker" aria-label="Choose a log day"><span className="caption desktop-only">LOG DAYS</span><div>{plan.daily_logs.map((item, index) => <ButtonBase className={`day-choice ${day === index ? 'selected' : ''}`} key={item.date} onClick={() => setDay(index)} aria-pressed={day === index}>
      <strong>{shortDate(item.date)}</strong><span className="caption">{miles(item.distance_miles, 1)} mi · {hm(dutyHours(item))} on duty</span>
    </ButtonBase>)}</div><Button variant="outlined" onClick={onDetails}>Sheet details</Button></aside>
      <div className="desktop-only log-desktop"><LogSheet log={log} locations={plan.locations} metadata={metadata} availability={availability} onHelp={onHelp} /></div>
      <div className="mobile-only mobile-log">
        <div className="surface day-summary"><strong className="mono">{miles(log.distance_miles, 1)} mi · {hm(dutyHours(log))} on duty</strong><p className="caption">00:00–24:00 · {plan.planning_parameters.time_zone} · fixed {utcLabel(plan.summary.departure_time)}</p></div>
        <ToggleButtonGroup value={mode} exclusive fullWidth onChange={(_, value) => value && setMode(value)} aria-label="Log reading mode"><ToggleButton value="timeline">Timeline</ToggleButton><ToggleButton value="events">Events</ToggleButton></ToggleButtonGroup>
        {mode === 'timeline' ? <><p className="caption">Scroll the time grid to see all 24 hours.</p><DutyGraph key={log.date} log={log} /><p className="accounting"><Icon name="check" />24:00 accounted for · totals rounded to minutes</p></> : <ol className="log-events">{logActivities(log).map((activity, index) => <li key={index}><span className="mono">{minuteTime(activity.start_minute)}–{minuteTime(activity.end_minute)} · {hms((activity.end_minute - activity.start_minute) / 60)}</span><strong>{activityLabel(activity.activity)}</strong><span className="caption">{remarkPlace(activity)}</span><span className="caption">{activity.reason || activityReason(activity.activity)}</span></li>)}</ol>}
        <section className="mobile-remarks"><h2>Remarks & locations</h2><ol>{log.remarks.map((remark, index) => <li key={index}><time className="mono">{timeOfDay(remark.time)}</time><div><strong>{activityLabel(remark.activity)}</strong><span className="caption">{remarkPlace(remark)}</span></div></li>)}</ol></section>
        <DayRecap log={log} availability={availability} onHelp={onHelp} />
        <PlanNotice />
      </div>
    </div>
  </>;
}
