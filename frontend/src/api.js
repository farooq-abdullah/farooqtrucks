const base = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
export const apiBase = base;
const locationCache = new Map();
const LOCATION_CACHE_MS = 10 * 60 * 1000;

export async function suggestLocations(query, signal) {
  signal?.throwIfAborted();
  const key = query.trim().toLocaleLowerCase();
  const cached = locationCache.get(key);
  if (cached && cached.expires > Date.now()) return cached.suggestions;
  const response = await fetch(`${base}/api/locations/search/?q=${encodeURIComponent(query)}`, { signal });
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(data?.detail || 'Location suggestions are unavailable. You can still enter a full address.');
  if (!Array.isArray(data?.suggestions)) throw new Error('Location search returned an invalid response.');
  signal?.throwIfAborted();
  // Repeated edits and searches in another field reuse exact-query results.
  // Never reuse a prefix result: doing so can hide a matching address or state.
  locationCache.delete(key);
  locationCache.set(key, { suggestions: data.suggestions, expires: Date.now() + (data.suggestions.length ? LOCATION_CACHE_MS : 30000) });
  if (locationCache.size > 100) locationCache.delete(locationCache.keys().next().value);
  return data.suggestions;
}

export async function planTrip(inputs, signal) {
  const response = await fetch(`${base}/api/trips/plan/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(inputs),
    signal,
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const message = data?.detail || (data && Object.entries(data)
      .map(([field, value]) => `${field.replaceAll('_', ' ')}: ${[].concat(value).join(' ')}`).join('\n'));
    const error = new Error(message || `The planner could not respond (HTTP ${response.status}).`);
    if (data && !data.detail) error.fields = Object.fromEntries(Object.entries(data).map(([key, value]) => [key, [].concat(value).join(' ')]));
    throw error;
  }
  return data;
}
