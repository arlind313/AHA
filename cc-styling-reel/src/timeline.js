// ─────────────────────────────────────────────────────────────
//  CC STYLING — "Three Locations. One Vision."  Master timeline
//  All times in seconds. Edit here to retime the whole reel.
// ─────────────────────────────────────────────────────────────
export const FPS = 30;
export const DURATION = 20;
export const WIDTH = 1080;
export const HEIGHT = 1920;

export const BRAND_RED = '#E30613';

// Real-world coordinates (lat, lon)
export const LOCATIONS = {
  ireland:  { name: 'IRELAND',  sub: 'WHERE IT ALL BEGAN', lat: 53.35, lon: -6.26 },  // Dublin
  marbella: { name: 'MARBELLA', sub: 'THE EXPANSION',      lat: 36.51, lon: -4.88 },
  dubai:    { name: 'DUBAI',    sub: 'THE NEXT CHAPTER',   lat: 25.20, lon: 55.27 },
};

export const T = {
  // Act 1 — Ireland
  irelandPin: 0.95,
  irelandTitleIn: 1.15, irelandTitleOut: 2.85,
  planeAppear: 1.2,        // aircraft fades in above Ireland
  lightsOn: 1.75,          // nav lights / strobes / engine glow
  takeoff: 2.55,           // aircraft starts rolling
  // Act 2 — Marbella
  marbellaPin: 5.95,
  marbellaTitleIn: 6.15, marbellaTitleOut: 7.85,
  orbitStart: 6.2, orbitEnd: 8.0,
  // Act 3 — Dubai
  dubaiPin: 12.35,
  dubaiTitleIn: 12.55, dubaiTitleOut: 14.05,
  burjIn: 12.6, burjOut: 14.2,
  arriveDubai: 13.9,
  // Act 4 — Final reveal
  pullBack: 14.0,
  flybyStart: 14.35, flybyEnd: 16.15,
  mapLabels: 14.9,
  line1: 15.55,            // THREE LOCATIONS.
  line2: 16.3,             // ONE VISION.
  logo: 17.25,
  locationsLine: 17.7,
};
