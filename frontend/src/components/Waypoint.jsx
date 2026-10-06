import startSvg from '/assets/figma/934c0.svg?raw';
import pickupSvg from '/assets/figma/6ad21.svg?raw';
import dropoffSvg from '/assets/figma/58212.svg?raw';
import fuelSvg from '/assets/figma/7fe3d.svg?raw';
import restSvg from '/assets/figma/4177e.svg?raw';
import breakSvg from '/assets/figma/6cf2b.svg?raw';
import smallStartSvg from '/assets/figma/df277.svg?raw';
import smallPickupSvg from '/assets/figma/fcf74.svg?raw';
import smallDropoffSvg from '/assets/figma/482be.svg?raw';
import inspectionSvg from '/assets/inspection.svg?raw';

// Bundle the original artwork so markers and itinerary symbols never require
// separate image requests after the app loads.
const source = svg => `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
export const waypointAssets = {
  start: source(startSvg), pickup: source(pickupSvg), dropoff: source(dropoffSvg),
  fuel: source(fuelSvg), rest: source(restSvg), restart: source(restSvg), break: source(breakSvg),
  inspection: source(inspectionSvg),
  other: source('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><circle cx="20" cy="20" r="18" fill="#475867"/><circle cx="20" cy="20" r="4" fill="white"/></svg>'),
};
const smallAssets = { start: source(smallStartSvg), pickup: source(smallPickupSvg), dropoff: source(smallDropoffSvg) };
export const waypointSource = (kind, small = false) => (small && smallAssets[kind]) || waypointAssets[kind] || waypointAssets.other;
export default function Waypoint({ kind, small = false }) {
  const size = small ? 32 : 40;
  return <img className="waypoint" src={waypointSource(kind, small)} width={size} height={size} alt="" />;
}
