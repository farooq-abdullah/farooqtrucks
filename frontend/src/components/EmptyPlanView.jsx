import { Button } from '@mui/material';
import Icon from './Icon';

export default function EmptyPlanView({ view, onPlan }) {
  const logs = view === 'logs';
  return <>
    <div className="page-heading"><h1>{logs ? 'Daily logs' : 'Route & stops'}</h1></div>
    <section className="empty-plan surface">
      <span className="empty-plan-icon" aria-hidden="true"><Icon name={logs ? 'file' : 'route'} /></span>
      <h2>{logs ? 'Plan a trip to generate your log sheets' : 'Plan a trip to see your route and stops'}</h2>
      <p>{logs
        ? 'Your planned duty changes, daily totals and printable sheets will appear here.'
        : 'Enter your current location, pickup, drop-off and cycle hours to calculate the road route, fuel stops and rests.'}</p>
      <Button variant="contained" onClick={onPlan}>Enter trip details →</Button>
    </section>
  </>;
}
