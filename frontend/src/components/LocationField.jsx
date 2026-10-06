import { useEffect, useState } from 'react';
import { Autocomplete, CircularProgress, TextField } from '@mui/material';
import { suggestLocations } from '../api';

export default function LocationField({ name, label, value, error, disabled, onChange }) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState(null);
  const [options, setOptions] = useState([]);
  const [searching, setSearching] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (!open || disabled || !query || query.trim().length < 2) return;
    const controller = new AbortController();
    let active = true;
    let timeout;
    const delay = setTimeout(async () => {
      setSearching(true);
      timeout = setTimeout(() => controller.abort(), 9000);
      try {
        const results = await suggestLocations(query.trim(), controller.signal);
        if (!active) return;
        setOptions(results);
        setMessage(results.length ? '' : 'No matching places. Try adding a state or a full address.');
      } catch (err) {
        if (active) {
          setOptions([]);
          setMessage(err.name === 'AbortError'
            ? 'Location search took too long. Try again or enter a full address.'
            : 'Location suggestions are unavailable. You can still enter a full address.');
        }
      } finally {
        clearTimeout(timeout);
        if (active) setSearching(false);
      }
    }, 350);
    return () => { active = false; clearTimeout(delay); clearTimeout(timeout); controller.abort(); };
  }, [query, open, disabled]);

  return <Autocomplete className="location-input" id={name} freeSolo fullWidth
    value={null} inputValue={value} options={options} open={open && !disabled}
    disabled={disabled} loading={searching} loadingText="Searching places…"
    noOptionsText={message || (query?.trim().length >= 2 ? 'No matching places.' : 'Type a city, address, or abbreviation such as NY or LA.')}
    slotProps={{ paper: { className: 'location-suggestions' } }}
    filterOptions={items => items}
    getOptionLabel={option => typeof option === 'string' ? option : option.label}
    getOptionDisabled={option => !option.supported}
    onOpen={() => setOpen(true)} onClose={() => { setOpen(false); setSearching(false); }}
    onInputChange={(_, next, reason) => {
      if (reason !== 'input' && reason !== 'clear') return;
      setOptions([]); setMessage(''); setSearching(next.trim().length >= 2); setQuery(next); onChange(next);
    }}
    onChange={(_, option) => {
      setQuery(null); setOptions([]); setMessage(''); setSearching(false);
      onChange(typeof option === 'string' ? option : option?.label || '');
    }}
    renderOption={(props, option) => {
      const { key, ...rest } = props;
      return <li key={key} {...rest}><div className="location-option">
        <span className="location-option-primary">{option.primary}</span>
        <span className="location-option-secondary">{option.secondary}</span>
        {!option.supported && <span className="location-option-unavailable">Outside supported US area</span>}
      </div></li>;
    }}
    renderInput={params => <TextField {...params} required placeholder="City and state, or full address"
      error={Boolean(error)} helperText={error || message}
      slotProps={{
        ...params.slotProps,
        htmlInput: { ...params.slotProps.htmlInput, name, maxLength: 200, 'aria-label': label, autoComplete: 'off' },
        input: { ...params.slotProps.input, endAdornment: <>
          {searching && <CircularProgress size={18} aria-label="Searching places" />}
          {params.slotProps.input.endAdornment}
        </> },
        formHelperText: { 'aria-live': 'polite' },
      }} />}
  />;
}
