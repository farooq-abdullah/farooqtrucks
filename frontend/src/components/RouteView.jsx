import { lazy, Suspense, useMemo, useState } from 'react';
import { Accordion, AccordionDetails, AccordionSummary, Alert, Button, ButtonBase, Skeleton } from '@mui/material';
import Icon from './Icon';
import Waypoint from './Waypoint';
import DriverClocks from './DriverClocks';
import PlanningParameters from './PlanningParameters';
import { buildItinerary, cityOnly, clock, hm, longDate, miles, shortDate, shortPlace } from '../lib/plan';
import { planningAssumptions } from '../lib/assumptions';
const RouteMap = lazy(() => import('../RouteMap'));
export default function RouteView({ plan, onHelp, onDownload }) {
  const [focus, setFocus] = useState(null);
  const itinerary = useMemo(() => buildItinerary(plan), [plan]);
  const assumptions = planningAssumptions(plan);
  const stops = itinerary.filter(item => item.type === 'stop');
  const extra = stops.filter(s => ['fuel', 'break', 'rest', 'restart'].includes(s.kind));
  const { summary } = plan;
  return <>
    <div className="page-heading"><h1>{cityOnly(plan.locations[0].label)} to {cityOnly(plan.locations[2].label)}</h1><p>Via {shortPlace(plan.locations[1].label)} · {longDate(summary.departure_time)}</p></div>
    <div className="trip-metrics">{[['Distance', `${miles(summary.distance_miles, 1)} mi`], ['Driving', hm(summary.driving_hours)], ['Elapsed', hm(summary.elapsed_hours)], ['Complete by', clock(summary.completion_time)]].map(([label, value]) =>
      <div key={label}><span className="caption">{label}</span><strong className="mono">{value}</strong>{label === 'Complete by' && <span className="caption">{shortDate(summary.completion_time)} · terminal clock</span>}</div>)}
    </div>
    <div className="desktop-only"><PlanningParameters plan={plan} onHelp={onHelp} /></div>
    <div className="route-clocks"><DriverClocks clocks={plan.clocks} onHelp={onHelp} /></div>
    <div className="route-and-stops">
      <div className="route-map-column"><Suspense fallback={<Skeleton variant="rounded" height={470} />}><RouteMap plan={plan} focus={focus} /></Suspense>
        <p className="caption desktop-only">General road route · check truck restrictions. Stop markers show estimated locations.</p>
      </div>
      <section className="itinerary surface"><div className="section-heading"><h2>Trip itinerary</h2><span className="caption">{stops.length} activities</span></div>
        <ol>{stops.map((stop, index) => <li key={stop.key}><ButtonBase className="itinerary-stop" onClick={() => setFocus(stop)} aria-label={`Show ${stop.title} at ${stop.place} on map`}>
          <Waypoint kind={stop.kind} /><div><span className="caption mono">{String(index + 1).padStart(2, '0')} · {stop.title.toUpperCase()}</span>
            <strong title={stop.fullPlace}>{stop.place}</strong><span className="mono stop-time">{shortDate(stop.start)} · {clock(stop.start)}{stop.hours > 0 && `–${stop.start.slice(0, 10) !== stop.end.slice(0, 10) ? shortDate(stop.end) + ' ' : ''}${clock(stop.end)}`}</span>
            <span className="caption">{stop.kind === 'start' ? (stop.title === 'Depart' ? 'Departure' : 'Planning starts') : `${hm(stop.hours)} ${stop.status === 'on_duty' ? 'on duty' : 'rest'}`}</span>
            {['break', 'rest', 'restart'].includes(stop.kind) && <span className="caption stop-reason">{stop.reason}</span>}
          </div></ButtonBase></li>)}</ol>
        <p className="stop-summary"><Icon name={extra.length ? 'fuel' : 'check'} />{extra.length ? `${summary.fuel_stops} fuel stops · ${extra.length - summary.fuel_stops} rest / break stops` : 'No extra fuel or rest stop due'}</p>
      </section>
    </div>
    <section className="road-legs"><h2>Road legs</h2>{plan.route.legs.map((leg, index) => <Accordion key={index} disableGutters elevation={0} className="road-leg">
      <AccordionSummary expandIcon={<Icon name="chevronDown" />}><Icon name="route" /><div className="leg-title"><strong>{cityOnly(plan.locations[index].label)} → {cityOnly(plan.locations[index + 1].label)}</strong><span className="caption mono">{miles(leg.distance_miles, 1)} mi · {hm(leg.duration_seconds / 3600)}</span></div></AccordionSummary>
      <AccordionDetails><ol className="directions">{leg.instructions.map((step, i) => <li key={i}><span>{step.instruction}</span><span className="caption mono">{miles(step.distance_miles, 1)} mi</span></li>)}</ol>{!leg.instructions.length && <p className="caption">No road movement on this leg.</p>}</AccordionDetails>
    </Accordion>)}</section>
    {plan.warnings.map(w => <Alert key={w} severity="warning">{w}</Alert>)}
    <div className="plan-actions"><span className="caption">Planned trip · {summary.log_days} daily log {summary.log_days === 1 ? 'sheet' : 'sheets'}</span><Button variant="outlined" onClick={onDownload} startIcon={<Icon name="download" />}>Download plan</Button></div>
    <div className="mobile-only"><PlanningParameters plan={plan} onHelp={onHelp} /><p className="caption">General road route · check truck restrictions.</p></div>
    <Accordion className="assumptions" elevation={0}><AccordionSummary expandIcon={<Icon name="chevronDown" />}>Planning assumptions</AccordionSummary><AccordionDetails><ul>{assumptions.map(a => <li key={a}>{a}</li>)}</ul></AccordionDetails></Accordion>
  </>;
}
