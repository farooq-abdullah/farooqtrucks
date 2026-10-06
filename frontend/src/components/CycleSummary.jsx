import { IconButton } from '@mui/material';
import Icon from './Icon';
import { hm } from '../lib/plan';
export default function CycleSummary({ value, onHelp }) {
  const used = value !== '' && Number.isFinite(Number(value)) && Number(value) >= 0 && Number(value) <= 70 ? Number(value) : null;
  return <div className="cycle-summary">
    <div><span className="caption">Used · 70h limit</span><strong className="mono">{used === null ? '—' : hm(used)}</strong></div>
    <div><span className="caption">Available to plan</span><strong className="mono blue">{used === null ? '—' : hm(70 - used)}</strong></div>
    <IconButton aria-label="Explain cycle hours" onClick={() => onHelp('restart')}><Icon name="info" /></IconButton>
  </div>;
}
