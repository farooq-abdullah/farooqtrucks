export const waypointAssets = {
  start: '934c0.svg', pickup: '6ad21.svg', dropoff: '58212.svg',
  fuel: '7fe3d.svg', rest: '4177e.svg', restart: '4177e.svg', break: '6cf2b.svg',
};
const smallAssets = { start: 'df277.svg', pickup: 'fcf74.svg', dropoff: '482be.svg' };
export const waypointSource = (kind, small = false) => kind === 'inspection'
  ? '/assets/inspection.svg'
  : `/assets/figma/${small ? smallAssets[kind] : waypointAssets[kind]}`;
export default function Waypoint({ kind, small = false }) {
  const size = small ? 32 : 40;
  return <img className="waypoint" src={waypointSource(kind, small)} width={size} height={size} alt="" />;
}
