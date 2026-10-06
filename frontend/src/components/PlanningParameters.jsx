import { Button } from '@mui/material';
import Icon from './Icon';
export const EXPLANATIONS = {
  departure: ['Departure and terminal clock', 'The plan uses the time zone inferred from your starting location and assumes that location is your home terminal. FMCSA logs use the driver’s home-terminal time standard and the carrier’s specified 24-hour start time; this plan assumes midnight. To keep each planned sheet at 24 hours, the UTC offset at departure stays fixed for the trip, so daylight-saving transitions during the trip are not modeled.'],
  rest: ['Prior daily rest', 'The driver is assumed to have completed at least 10 consecutive hours off duty before starting. Daily clocks start fresh; the entered cycle hours still count. Planned 10-hour and 34-hour rests assume the driver is physically in a compliant sleeper berth. Other off-duty rest also qualifies under the normal rule; split sleeper and team driving are not modeled.'],
  cycle: ['70 hours over eight days', 'Driving and on-duty work, including inspections, loading, unloading and fueling, count toward the 70-hour cycle. At the limit, further driving must stop; non-driving work can continue. Midnight does not reset the cycle. The four inputs do not include earlier daily hours.'],
  restart: ['Available cycle hours', 'Available driving capacity is at least zero, or 70 minus Current Cycle Used. Without earlier daily history, we cannot tell when old hours fall out of the eight-day total. This plan uses a 34-hour rest before further driving when capacity is needed. Non-driving work can finish beyond 70 hours. A restart is optional under the actual rule; this approach can schedule more rest than necessary.'],
  driving: ['Daily driving clock', 'A driver may drive up to 11 hours after a full 10-hour daily rest. This display shows hours used in the final shift and hours remaining at trip completion, including the post-trip inspection.'],
  shift: ['14-hour shift window', 'Driving must stop within 14 elapsed hours after coming on duty. Loading, fueling and short breaks use that window. Non-driving work can continue after hour 14. A full daily rest starts a new driving window.'],
  break: ['Eight-hour driving break', 'After eight accumulated driving hours, at least 30 consecutive minutes without driving are required before more driving. Loading, unloading and fueling can qualify. This clock is shown at trip completion.'],
  recap: ['Daily recap', 'On-duty time for this planned day is known. The previous seven days and tomorrow’s exact rolling availability are unknown without daily history. No earlier entries are invented.'],
  inspections: ['Pre-trip, post-trip and TIV', 'TIV means Trailer Integrity Verification. The plan includes a pre-trip inspection before driving in each shift and a post-trip inspection before a full rest or trip completion. Each is estimated at 15 minutes and counts as on duty, not driving. This duration is a planning assumption; record the actual time and findings in your official records.'],
};
export default function PlanningParameters({ onHelp }) {
  const start = '08:00 · start location zone';
  return <div className="planning-parameters">
    {[[start, 'departure'], ['10h prior rest', 'rest'], ['70h / 8 days', 'cycle'], ['Restart method', 'restart']].map(([label, key]) =>
      <Button key={key} className={`parameter ${key === 'restart' ? 'mobile-only' : ''}`} onClick={() => onHelp(key)} endIcon={<Icon name="info" />}>{label}</Button>)}
  </div>;
}
