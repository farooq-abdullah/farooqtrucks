import { Button, CircularProgress, TextField } from '@mui/material';
import Waypoint from './Waypoint';
import CycleSummary from './CycleSummary';
import Icon from './Icon';
import LocationField from './LocationField';
const FIELDS = [
  ['current_location', 'Current location', 'start'],
  ['pickup_location', 'Pickup location', 'pickup'],
  ['dropoff_location', 'Drop-off location', 'dropoff'],
];
export default function TripForm({ values, errors, loading, onChange, onSubmit, onCancel, onHelp }) {
  const change = name => event => onChange({ ...values, [name]: event.target.value });
  return <form className="trip-form" onSubmit={onSubmit} noValidate>
    <h2 className="desktop-only">Trip details</h2>
    {FIELDS.map(([name, label, kind]) => <div className="stop-field" key={name}>
      <span className="stop-field-symbol"><Waypoint kind={kind} small /></span>
      <div className="field-group"><label htmlFor={name}>{label}</label>
        <LocationField name={name} label={label} value={values[name]} disabled={loading} error={errors[name]}
          onChange={next => onChange({ ...values, [name]: next })} />
      </div>
    </div>)}
    <div className="stop-field">
      <span className="stop-field-symbol cycle-field-icon"><Icon name="clock" size={20} /></span>
      <div className="field-group"><label htmlFor="current_cycle_used">Current cycle used (hrs)</label>
      <TextField id="current_cycle_used" name="current_cycle_used" fullWidth required type="number" value={values.current_cycle_used}
        disabled={loading} onChange={change('current_cycle_used')} error={Boolean(errors.current_cycle_used)}
        helperText={errors.current_cycle_used || <span className="desktop-only">On-duty hours already used in your 70-hour cycle.</span>}
        slotProps={{ htmlInput: { min: 0, max: 70, step: 'any', inputMode: 'decimal', 'aria-label': 'Current cycle used (hrs)' } }} />
      </div>
    </div>
    <div className="mobile-only"><CycleSummary value={values.current_cycle_used} onHelp={onHelp} /></div>
    <Button type="submit" variant="contained" fullWidth disabled={loading}>
      {loading ? <><CircularProgress size={18} color="inherit" sx={{ mr: 1 }} />Planning trip…</> : 'Plan route & logs →'}
    </Button>
    {loading && <div className="loading-note" role="status">Resolving the road route and planned stops. <Button size="small" onClick={onCancel}>Cancel</Button></div>}
    <p className="caption desktop-only">Pickup and unloading · 1 hour each</p>
    <Button size="small" className="inspection-note" onClick={() => onHelp('inspections')} endIcon={<Icon name="info" />}>Pre & post-trip / TIV · 15 min each (estimate)</Button>
    <p className="location-attribution">Location search: <a href="https://github.com/komoot/photon" target="_blank" rel="noreferrer">Photon</a> · <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">© OpenStreetMap contributors</a></p>
  </form>;
}
