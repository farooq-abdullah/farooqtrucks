export default function Brand({ onClick }) {
  return <a className="brand" href="/plan" onClick={onClick} aria-label="farooqtrucks — plan a trip">
    <img className="brand-desktop" src="/assets/figma/c2813.svg" width="44" height="40" alt="" />
    <img className="brand-mobile" src="/assets/figma/1110f.svg" width="36" height="33" alt="" />
    <span>farooqtrucks</span>
  </a>;
}
