import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { useMediaQuery } from '@mui/material';
import { waypointSource } from './components/Waypoint';
import { clock, shortPlace, stopKind } from './lib/plan';

const PREVIEW_LOCATIONS = [
  { label: 'Chicago, IL', coordinates: [-87.6298, 41.8781] },
  { label: 'Springfield, IL', coordinates: [-89.6501, 39.7817] },
  { label: 'St. Louis, MO', coordinates: [-90.1994, 38.627] },
];
function popup(title, detail) {
  const node = document.createElement('div');
  const strong = document.createElement('strong'); strong.textContent = title;
  const body = document.createElement('p'); body.textContent = detail;
  node.append(strong, body); return node;
}
export default function RouteMap({ plan, preview = false, showSample = false, focus }) {
  const container = useRef(null), mapRef = useRef(null);
  const [tileError, setTileError] = useState(false), [tilesReady, setTilesReady] = useState(false);
  const compact = useMediaQuery('(max-width:1000px)');
  useEffect(() => {
    setTileError(false);
    setTilesReady(false);
    const map = L.map(container.current, { scrollWheelZoom: false, zoomControl: false });
    mapRef.current = map;
    L.control.zoom({ position: 'topleft' }).addTo(map);
    const tiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> · OSRM', maxZoom: 19,
    }).addTo(map);
    tiles.on('tileerror', () => { setTileError(true); setTilesReady(true); });
    tiles.on('load', () => setTilesReady(true));
    const locations = plan?.locations || (showSample ? PREVIEW_LOCATIONS : []);
    if (plan && !preview) {
      L.geoJSON(plan.route.geometry, { style: { color: '#fff', weight: 7, opacity: 0.95 } }).addTo(map);
      const line = L.geoJSON(plan.route.geometry, { style: { color: '#244EBA', weight: 4 } }).addTo(map);
      map.fitBounds(line.getBounds(), { padding: [44, 44], maxZoom: 12 });
    } else if (locations.length) map.fitBounds(locations.map(p => [p.coordinates[1], p.coordinates[0]]), { padding: [50, 60], maxZoom: 8 });
    else map.setView([39, -97], 4);
    const marker = (coordinates, kind, title, detail, label, number = null, count = 1) => {
      if (!coordinates) return;
      const [lon, lat] = coordinates;
      const symbol = document.createElement('span');
      if (compact) {
        symbol.className = number ? `map-number map-number-${kind}` : `map-stop-marker map-stop-${kind}${count > 1 ? ' multiple' : ''}`;
        symbol.textContent = number ? String(number) : count > 1 ? String(count) : '';
      } else {
        const image = document.createElement('img'); image.src = waypointSource(kind); image.width = 40; image.height = 40; image.alt = ''; symbol.append(image);
      }
      const size = compact ? number ? 26 : count > 1 ? 22 : 14 : 40;
      const icon = L.divIcon({ className: 'route-waypoint', html: symbol, iconSize: [size, size], iconAnchor: [size / 2, size / 2] });
      const inspections = plan?.events.filter(e => e.activity.includes('inspection / TIV') && e.coordinates?.every((value, index) => Math.abs(value - coordinates[index]) < 1e-6)) || [];
      const inspectionDetail = inspections.map(e => `${stopKind(e.activity).title} · ${e.start.slice(0, 10)} ${clock(e.start)}–${clock(e.end)}`).join('\n');
      const point = L.marker([lat, lon], { icon, title, keyboard: true, zIndexOffset: compact && number ? 300 : 0 }).bindPopup(popup(title, [detail, inspectionDetail].filter(Boolean).join('\n'))).addTo(map);
      if (label) {
        const text = document.createElement('span'); text.textContent = shortPlace(label);
        point.bindTooltip(text, { permanent: !compact, direction: compact ? 'top' : 'right', offset: compact ? [0, -12] : [22, 0], className: 'place-label' });
      }
    };
    locations.forEach((location, index) => marker(location.coordinates, ['start', 'pickup', 'dropoff'][index], ['Start', 'Pickup', 'Drop-off'][index], location.label, location.label, index + 1));
    const groupedStops = new Map();
    if (plan && !preview) plan.events.filter(e => e.status !== 'driving').forEach(event => {
      const { kind, title } = stopKind(event.activity);
      // Inspections happen at an existing departure, arrival or rest stop;
      // include their times in that marker's popup instead of covering it.
      if (['pickup', 'dropoff', 'inspection'].includes(kind)) return;
      if (!event.coordinates) return;
      const key = compact ? event.coordinates.join(',') : `${groupedStops.size}`;
      const group = groupedStops.get(key) || {coordinates:event.coordinates,kind,title,details:[]};
      group.details.push(`${title} · ${event.location} · ${event.start.slice(0, 10)} ${clock(event.start)} to ${event.end.slice(0, 10)} ${clock(event.end)}`);
      groupedStops.set(key, group);
    });
    groupedStops.forEach(group => marker(group.coordinates, group.kind, group.details.length > 1 ? `${group.details.length} planned activities` : group.title, group.details.join('\n'), null, null, group.details.length));
    const observer = new ResizeObserver(() => map.invalidateSize()); observer.observe(container.current);
    return () => { observer.disconnect(); map.remove(); mapRef.current = null; };
  }, [plan, preview, showSample, compact]);
  useEffect(() => {
    if (!focus?.coordinates || !mapRef.current) return;
    const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
    mapRef.current.setView([focus.coordinates[1], focus.coordinates[0]], 10, {animate:!reduced});
    if (compact) {
      container.current.scrollIntoView({behavior:reduced ? 'instant' : 'smooth',block:'center'});
    }
    L.popup().setLatLng([focus.coordinates[1], focus.coordinates[0]]).setContent(popup(focus.title, [focus.place, focus.routeReference, `${clock(focus.start)}–${clock(focus.end)}`].filter(Boolean).join('\n'))).openOn(mapRef.current);
  }, [focus, compact]);
  return <div className={`map-wrap ${preview ? 'preview-map' : ''}`} data-tiles-ready={tilesReady}>
    <div ref={container} className="route-map" role="region" aria-label={preview ? 'Entered locations preview' : 'Road route and planned stops'} />
    {tileError && <p className="map-status" role="status">Background map unavailable. Route and stop data remain visible.</p>}
  </div>;
}
