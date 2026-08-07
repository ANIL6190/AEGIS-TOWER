import * as satellite from 'satellite.js';

// Satellite dataset with TLEs updated to August 2026
export const TLE_DATA = [
  {
    id: "25544",
    name: "ISS (ZARYA)",
    type: "satellite",
    tle1: "1 25544U 98067A   26218.25000000  .00016717  00000-0  30276-3 0  9018",
    tle2: "2 25544  51.6428  21.2062 0001469  78.2714 281.8216 15.49280727260254"
  },
  {
    id: "20580",
    name: "HST (HUBBLE)",
    type: "satellite",
    tle1: "1 20580U 90037B   26218.25000000  .00000351  00000-0  18193-4 0  9997",
    tle2: "2 20580  28.4690 145.2341 0002871 310.1287 180.2319 14.99285741193181"
  },
  {
    id: "44713",
    name: "STARLINK-1012",
    type: "satellite",
    tle1: "1 44713U 19074A   26218.25000000  .00001150  00000-0  85292-4 0  9993",
    tle2: "2 44713  53.0543  89.1023 0001356  90.2345 270.1290 15.05432109312301"
  },
  {
    id: "33591",
    name: "NOAA 19",
    type: "satellite",
    tle1: "1 33591U 09005A   26218.25000000  .00000120  00000-0  65123-4 0  9995",
    tle2: "2 33591  98.7042 120.4532 0012354 110.1235 250.3245 14.12345678901234"
  },
  {
    id: "27386",
    name: "ENVISAT DEBRIS",
    type: "debris",
    tle1: "1 27386U 02009A   26218.25000000  .00000045  00000-0  34123-4 0  9991",
    tle2: "2 27386  98.5432 230.1245 0001234  80.4532 280.1234 14.32109876543210"
  },
  {
    id: "29812",
    name: "FENGYUN 1C DEBRIS",
    type: "debris",
    tle1: "1 29812U 07001A   26218.25000000  .00004523  00000-0  12345-3 0  9992",
    tle2: "2 29812  98.8523 345.1234 0021345 270.3421  90.2341 14.85234123214567"
  },
  {
    id: "36123",
    name: "COSMOS 2251 DEBRIS",
    type: "debris",
    tle1: "1 36123U 93036A   26218.25000000  .00001234  00000-0  54321-3 0  9993",
    tle2: "2 36123  74.0321  15.1234 0012453 180.1234 180.3241 14.23451234567890"
  },
  {
    id: "39634",
    name: "SENTINEL-1A",
    type: "satellite",
    tle1: "1 39634U 14016A   26218.25000000  .00000012  00000-0  12345-4 0  9994",
    tle2: "2 39634  98.1823  45.3421 0001234  90.2345 270.1234 14.59231023456789"
  },
  {
    id: "40697",
    name: "SENTINEL-2A",
    type: "satellite",
    tle1: "1 40697U 15028A   26218.25000000  .00000023  00000-0  23456-4 0  9995",
    tle2: "2 40697  98.5623 185.3214 0001123  45.1234 315.2341 14.39234102345678"
  },
  {
    id: "48274",
    name: "TIANGONG STATION",
    type: "satellite",
    tle1: "1 48274U 21035A   26218.25000000  .00012341  00000-0  21345-3 0  9996",
    tle2: "2 48274  41.5823 234.1234 0001423 120.3421 240.2341 15.62134512345678"
  },
  {
    id: "34124",
    name: "IRIDIUM 33 DEBRIS",
    type: "debris",
    tle1: "1 34124U 97051C   26218.25000000  .00002134  00000-0  87654-4 0  9997",
    tle2: "2 34124  86.4231 150.3214 0001234  60.2341 300.1234 14.32145678901234"
  },
  {
    id: "51023",
    name: "STARLINK-2104",
    type: "satellite",
    tle1: "1 51023U 22002A   26218.25000000  .00001543  00000-0  10234-3 0  9998",
    tle2: "2 51023  53.2134 310.2341 0001245 150.3241 210.1234 15.08234123456789"
  },
  {
    id: "58214",
    name: "SENTINEL-DEMO-SAT-1",
    type: "satellite",
    tle1: "1 58214U 23050A   26218.25000000  .00001021  00000-0  45213-4 0  9999",
    tle2: "2 58214  51.6442  45.1234 0001421  90.1234 270.3241 15.12453678912345"
  },
  {
    id: "49271",
    name: "DEBRIS FRAGMENT-B",
    type: "debris",
    tle1: "1 49271U 21085C   26218.25000000  .00003412  00000-0  12345-3 0  9990",
    tle2: "2 49271  51.6450  45.1240 0001430  90.1245 270.3220 15.12461234567890"
  },
  {
    id: "35421",
    name: "AEROSAT-9",
    type: "satellite",
    tle1: "1 35421U 08042A   26218.25000000  .00000156  00000-0  21345-4 0  9991",
    tle2: "2 35421  74.0456 220.1234 0002345  45.1234 315.1234 14.89123456789012"
  },
  {
    id: "35422",
    name: "DEBRIS-C (METEOR)",
    type: "debris",
    tle1: "1 35422U 08042B   26218.25000000  .00000543  00000-0  54321-4 0  9992",
    tle2: "2 35422  74.0460 220.1250 0002350  45.1220 315.1210 14.89134512345678"
  }
];

// Returns position of a satellite in ECI (Earth-Centered Inertial) coordinates (km)
export function getSatellitePosition(tle1, tle2, date) {
  try {
    const satrec = satellite.twoline2satrec(tle1, tle2);
    const posAndVel = satellite.propagate(satrec, date);
    const positionEci = posAndVel.position;
    if (positionEci && typeof positionEci.x === 'number') {
      return {
        x: positionEci.x,
        y: positionEci.y,
        z: positionEci.z
      };
    }
  } catch (err) {
    console.error("Propagation error:", err);
  }
  return null;
}

// Generate coordinate points for a full orbit trajectory loop
export function getOrbitPoints(tle1, tle2, startDate, pointsCount = 100) {
  const points = [];
  try {
    const satrec = satellite.twoline2satrec(tle1, tle2);
    // satrec.no is Mean Motion in radians/minute. Period (min) = 2*pi / no
    const periodMinutes = (2 * Math.PI) / satrec.no;
    
    for (let i = 0; i <= pointsCount; i++) {
      const offsetMinutes = (periodMinutes * i) / pointsCount;
      const date = new Date(startDate.getTime() + offsetMinutes * 60 * 1000);
      const posAndVel = satellite.propagate(satrec, date);
      const pos = posAndVel.position;
      if (pos && typeof pos.x === 'number') {
        points.push([pos.x, pos.y, pos.z]);
      }
    }
  } catch (err) {
    console.error("Orbit path generation error:", err);
  }
  return points;
}
