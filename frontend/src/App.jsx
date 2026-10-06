import { lazy, Suspense, useEffect, useRef, useState } from 'react';
import { Alert, Button, Dialog, DialogActions, DialogContent, DialogTitle, Skeleton, Tab, Tabs, TextField } from '@mui/material';
import { planTrip } from './api';
import Brand from './components/Brand';
import TripForm from './components/TripForm';
import CycleSummary from './components/CycleSummary';
import PlanningParameters, { EXPLANATIONS } from './components/PlanningParameters';
import RouteView from './components/RouteView';
import LogsView from './components/LogsView';
import EmptyPlanView from './components/EmptyPlanView';
import LogSheet, { METADATA_FIELDS } from './LogSheet';
import { cycleByDay } from './lib/plan';
const RouteMap = lazy(() => import('./RouteMap'));
const INITIAL = { current_location: 'Chicago, IL', pickup_location: 'Springfield, IL', dropoff_location: 'St. Louis, MO', current_cycle_used: '20' };
const VIEWS = ['plan', 'route', 'logs'];
const viewFromPath = () => {
  const path = window.location.pathname.replace(/\/$/, '').slice(1);
  return VIEWS.includes(path) ? path : 'plan';
};

export default function App() {
  const [inputs, setInputs] = useState(INITIAL), [errors, setErrors] = useState({});
  const [plan, setPlan] = useState(null), [submitted, setSubmitted] = useState(null), [view, setView] = useState(viewFromPath);
  const [loading, setLoading] = useState(false), [error, setError] = useState(''), [help, setHelp] = useState(null);
  const [details, setDetails] = useState(false), [metadata, setMetadata] = useState({}), [draft, setDraft] = useState({});
  const [printing, setPrinting] = useState(false);
  const request = useRef(null), heading = useRef(null);
  const navigate = target => { setView(target); window.history.pushState(null, '', `/${target}`); window.scrollTo({ top: 0, behavior: 'instant' }); requestAnimationFrame(() => heading.current?.focus({ preventScroll: true })); };
  useEffect(() => {
    if (window.location.pathname === '/') window.history.replaceState(null, '', '/plan');
    const onPopState = () => setView(viewFromPath());
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, []);
  useEffect(() => () => request.current?.abort(), []);
  useEffect(() => {
    const handler = event => { if (event.altKey || event.ctrlKey || event.metaKey || /INPUT|TEXTAREA|SELECT/.test(event.target.tagName) || event.target.isContentEditable || help || details) return; if (event.key === '1') navigate('route'); if (event.key === '2') navigate('logs'); };
    window.addEventListener('keydown', handler); return () => window.removeEventListener('keydown', handler);
  });
  useEffect(() => {
    if (!printing) return;
    let cancelled = false;
    const after = () => setPrinting(false); window.addEventListener('afterprint', after);
    document.fonts.ready.then(() => requestAnimationFrame(() => { if (!cancelled) window.print(); }));
    return () => { cancelled = true; window.removeEventListener('afterprint', after); };
  }, [printing]);
  async function submit(event) {
    event.preventDefault(); const nextErrors = {};
    for (const key of ['current_location', 'pickup_location', 'dropoff_location']) if (!inputs[key].trim()) nextErrors[key] = 'Enter a city and state, or a full address.';
    if (inputs.current_cycle_used.trim() === '' || !Number.isFinite(Number(inputs.current_cycle_used)) || Number(inputs.current_cycle_used) < 0 || Number(inputs.current_cycle_used) > 70) nextErrors.current_cycle_used = 'Enter hours between 0 and 70.';
    setErrors(nextErrors); setError('');
    if (Object.keys(nextErrors).length) { document.getElementById(Object.keys(nextErrors)[0])?.focus(); return; }
    setLoading(true); const controller = new AbortController(); request.current = controller;
    const timeout = setTimeout(() => controller.abort('timeout'), 150000);
    try {
      const payload = { ...inputs, current_cycle_used: Number(inputs.current_cycle_used) };
      const result = await planTrip(payload, controller.signal);
      setPlan(result); setSubmitted(payload); setMetadata({}); navigate('route');
    } catch (err) {
      if (controller.signal.reason === 'timeout') setError('Planning took too long. Please try again.');
      else if (err.name !== 'AbortError') {
        setError(err.message === 'Failed to fetch' ? 'Cannot reach the planner. Check your connection and try again.' : err.message);
        if (err.fields) setErrors(err.fields);
      }
    } finally { clearTimeout(timeout); setLoading(false); }
  }
  function download() {
    const url = URL.createObjectURL(new Blob([JSON.stringify({ ...plan, sheet_details: metadata }, null, 2)], { type: 'application/json' }));
    const a = document.createElement('a'); a.href = url; a.download = `farooqtrucks-plan-${plan.daily_logs[0].date}.json`; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  const exactSample = ['current_location', 'pickup_location', 'dropoff_location'].every(key => inputs[key].trim().toLowerCase() === INITIAL[key].toLowerCase());
  const previewPlan = plan && submitted && ['current_location', 'pickup_location', 'dropoff_location'].every(key => inputs[key] === submitted[key]) ? plan : null;
  const dayCycles = plan ? cycleByDay(plan, plan.planning_parameters.initial_cycle_hours) : [];
  return <>
    <a className="skip-link" href="#workspace">Skip to trip planner</a>
    <header className="workflow-toolbar no-print"><div className="toolbar-inner">
      <Brand onClick={event => { event.preventDefault(); navigate('plan'); }} />
      <Tabs className="workflow-tabs" value={view} onChange={(_, target) => navigate(target)} aria-label="Trip workflow" slotProps={{ indicator: { style: { display: 'none' } } }}>
        <Tab value="plan" label="Plan trip" /><Tab value="route" label={<><span className="desktop-only">Route & stops</span><span className="mobile-only">Route</span></>} /><Tab value="logs" label="Daily logs" />
      </Tabs>
      <div className="toolbar-actions">{view === 'route' && plan ? <><Button className="desktop-only" variant="outlined" onClick={() => navigate('plan')}>Edit trip</Button><Button variant="contained" onClick={() => navigate('logs')}><span className="desktop-only">Review log sheets →</span><span className="mobile-only">Review logs</span></Button></> : view === 'logs' && plan ? <Button variant="contained" onClick={() => setPrinting(true)}>Print logs</Button> : <span className="desktop-only toolbar-rule">PROPERTY CARRYING <b className="mono">70h / 8d</b></span>}</div>
    </div></header>
    <main id="workspace" className={`workspace view-${view} no-print`} ref={heading} tabIndex="-1">
      {view === 'plan' && <>
        <div className="page-heading"><h1>Plan your next haul</h1><p>Plan your route, breaks and rests, with pre-filled daily log sheets.</p></div>
        <div className="plan-layout"><TripForm values={inputs} errors={errors} loading={loading} onChange={next => { setInputs(next); setErrors({}); }} onSubmit={submit} onCancel={() => request.current?.abort()} onHelp={setHelp} />
          <div className="locations-preview desktop-only"><div className="section-heading"><span>Locations preview</span><span className="caption">{previewPlan || exactSample ? '3 entered locations' : 'Plan to preview locations'}</span></div>
            <Suspense fallback={<Skeleton variant="rounded" height={466} />}><RouteMap plan={previewPlan} preview showSample={exactSample} /></Suspense><CycleSummary value={inputs.current_cycle_used} onHelp={setHelp} />
          </div>
        </div>
        {error && <Alert severity="error" action={<Button color="inherit" onClick={() => setError('')}>Dismiss</Button>}>{error}</Alert>}
        <PlanningParameters onHelp={setHelp} />
        <p className="caption mobile-only">Pickup and unloading · 1 hour each</p>
        {plan && <Button onClick={() => navigate('route')}>Back to the previous plan →</Button>}
      </>}
      {view === 'route' && plan && <RouteView plan={plan} onHelp={setHelp} onDownload={download} />}
      {view === 'logs' && plan && <LogsView key={plan.summary.departure_time + plan.summary.distance_miles} plan={plan} metadata={metadata} onDetails={() => { setDraft(metadata); setDetails(true); }} onHelp={setHelp} />}
      {view !== 'plan' && !plan && <EmptyPlanView view={view} onPlan={() => navigate('plan')} />}
    </main>
    <Dialog open={Boolean(help)} onClose={() => setHelp(null)} aria-labelledby="help-title"><DialogTitle id="help-title">{EXPLANATIONS[help]?.[0]}</DialogTitle><DialogContent><p>{EXPLANATIONS[help]?.[1]}</p>{help === 'departure' && plan && <p className="caption">This plan: {plan.summary.departure_time.replace('T', ' ')}.</p>}</DialogContent><DialogActions><Button onClick={() => setHelp(null)}>Got it</Button></DialogActions></Dialog>
    <Dialog open={details} onClose={() => setDetails(false)} aria-labelledby="details-title"><DialogTitle id="details-title">Optional sheet details</DialogTitle><DialogContent><p className="caption">These details appear on every printable sheet.</p><div className="metadata-form">{METADATA_FIELDS.map(([key, label]) => <TextField key={key} label={label} fullWidth value={draft[key] || ''} onChange={event => setDraft({ ...draft, [key]: event.target.value })} slotProps={{ htmlInput: { maxLength: 200 } }} />)}</div></DialogContent><DialogActions><Button onClick={() => setDetails(false)}>Cancel</Button><Button variant="contained" onClick={() => { setMetadata(draft); setDetails(false); }}>Save details</Button></DialogActions></Dialog>
    {plan && <div className="print-only" aria-hidden={!printing}>{plan.daily_logs.map((log, index) => <LogSheet key={log.date} printCopy log={log} locations={plan.locations} metadata={metadata} availability={Math.max(0, 70 - (index === 0 ? plan.planning_parameters.initial_cycle_hours : dayCycles[index - 1]))} />)}</div>}
  </>;
}
