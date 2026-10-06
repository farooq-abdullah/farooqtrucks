import { ButtonBase } from '@mui/material';
import { hm } from '../lib/plan';
export default function DriverClocks({ clocks, onHelp }) {
  const data = [
    ['Driving', hm(clocks.driving_used_hours), `${hm(clocks.driving_remaining_hours)} left / 11h`, clocks.driving_used_hours / 11, 'driving'],
    ['Shift window', hm(clocks.shift_used_hours), `${hm(clocks.shift_remaining_hours)} left / 14h`, clocks.shift_used_hours / 14, 'shift'],
    ['8-hour break', clocks.break_driving_hours === 0 ? 'Not due' : `${hm(clocks.break_remaining_hours)} left`, clocks.break_driving_hours === 0 ? 'Pickup & unload qualify' : `${hm(clocks.break_driving_hours)} driven since break`, clocks.break_driving_hours / 8, 'break'],
    ['70-hour cycle', hm(clocks.cycle_used_hours), clocks.cycle_used_hours > 70 ? 'Driving limit reached · work can finish' : `${hm(clocks.cycle_remaining_hours)} left / 70h`, clocks.cycle_used_hours / 70, 'restart'],
  ];
  return <div className="driver-clocks" aria-label="Driver clocks at trip completion">{data.map(([label, value, detail, progress, key]) =>
    <ButtonBase className="driver-clock" key={key} onClick={() => onHelp(key)} aria-label={`${label}: ${value}. ${detail}. Explain`}>
      <span className="caption">{label}</span><strong className="mono">{value}</strong><span className="caption">{detail}</span>
      <span className="progress-track"><span style={{ width: `${Math.min(100, progress * 100)}%` }} /></span>
    </ButtonBase>)}
  </div>;
}
