import { ButtonBase } from '@mui/material';
import { clock, hm, shortDate } from '../lib/plan';
export default function DriverClocks({ clocks, breaks = [], onBreak, onHelp }) {
  const first = breaks[0];
  const data = [
    ['Driving', hm(clocks.driving_used_hours), `${hm(clocks.driving_remaining_hours)} left / 11h`, clocks.driving_used_hours / 11, 'driving'],
    ['Shift window', hm(clocks.shift_used_hours), `${hm(clocks.shift_remaining_hours)} left / 14h`, clocks.shift_used_hours / 14, 'shift'],
    ['30-minute breaks', first ? `${breaks.length} planned` : 'No extra stop', first ? `First: ${shortDate(first.start)} · ${clock(first.start)}` : 'Other planned stops satisfy the break rule.', null, 'break'],
    ['70-hour cycle', hm(clocks.cycle_used_hours), clocks.cycle_used_hours > 70 ? 'Driving limit reached · work can finish' : `${hm(clocks.cycle_remaining_hours)} left / 70h`, clocks.cycle_used_hours / 70, 'restart'],
  ];
  return <div className="driver-clocks" aria-label="Driver hours and planned breaks">{data.map(([label, value, detail, progress, key]) =>
    <ButtonBase className="driver-clock" key={key} onClick={() => key === 'break' && first ? onBreak?.(first) : onHelp(key)} aria-label={`${label}: ${value}. ${detail}. ${key === 'break' && first ? 'Show first break on map' : 'Explain'}`}>
      <span className="caption">{label}</span><strong className="mono">{value}</strong><span className="caption">{detail}</span>
      {progress !== null && <span className="progress-track"><span style={{ width: `${Math.min(100, progress * 100)}%` }} /></span>}
    </ButtonBase>)}
  </div>;
}
