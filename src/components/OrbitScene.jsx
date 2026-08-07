import React, { useRef, useMemo, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Stars, Html, Line } from '@react-three/drei';
import * as THREE from 'three';
import { getSatellitePosition, getOrbitPoints } from '../data/satellites';

// Scale factor: Earth radius is 6371 km. We want Earth radius to be 2.0 in the scene.
const EARTH_RADIUS_3D = 2.0;
const SCALE_KM_TO_3D = EARTH_RADIUS_3D / 6371.0;

// Helper to convert ECI coordinates (km) to 3D Scene coordinates (x, y, z)
// ECI Z is Polar Axis (Y in three.js)
// ECI X, Y is Equatorial Plane (X, Z in three.js)
function eciTo3D(eciPos) {
  if (!eciPos) return [0, 0, 0];
  return [
    eciPos.x * SCALE_KM_TO_3D,
    eciPos.z * SCALE_KM_TO_3D,
    -eciPos.y * SCALE_KM_TO_3D
  ];
}

// Sub-component: Procedural Tactical Earth Sphere
function EarthModel() {
  const earthRef = useRef();

  // Create high-fidelity procedural tactical earth map
  const earthTexture = useMemo(() => {
    const canvas = document.createElement('canvas');
    canvas.width = 1024;
    canvas.height = 512;
    const ctx = canvas.getContext('2d');

    // Deep space navy oceans
    ctx.fillStyle = '#060d1b';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw continents (tactical muted green-grey)
    ctx.fillStyle = '#1c2d3d';

    // Simple polygons for global landmasses
    const drawLand = (pts) => {
      ctx.beginPath();
      ctx.moveTo(pts[0][0], pts[0][1]);
      for (let i = 1; i < pts.length; i++) {
        ctx.lineTo(pts[i][0], pts[i][1]);
      }
      ctx.closePath();
      ctx.fill();
    };

    // North America
    drawLand([[100, 80], [240, 100], [300, 160], [280, 240], [230, 240], [200, 280], [160, 260], [140, 200]]);
    // South America
    drawLand([[240, 250], [290, 290], [320, 350], [280, 480], [240, 420], [220, 310]]);
    // Eurasia / Africa
    drawLand([[420, 60], [800, 80], [850, 180], [750, 260], [600, 230], [530, 240], [450, 210], [420, 140]]);
    // Africa detail
    drawLand([[450, 210], [530, 240], [550, 310], [490, 420], [440, 360], [410, 280]]);
    // Australia
    drawLand([[750, 330], [840, 340], [850, 400], [770, 390]]);
    // Antarctica
    drawLand([[100, 480], [900, 480], [800, 510], [200, 510]]);

    // Draw coordinate grids (Tactical sensor scan lines)
    ctx.strokeStyle = 'rgba(0, 229, 255, 0.09)';
    ctx.lineWidth = 1.0;
    for (let x = 0; x < canvas.width; x += 32) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
    }
    for (let y = 0; y < canvas.height; y += 32) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }

    // Add glowing night lights (cities) using bounding boxes of continents (no heavy getImageData calls)
    ctx.fillStyle = '#ffb300';
    const landBoxes = [
      { minX: 110, maxX: 260, minY: 90, maxY: 230 }, // North America
      { minX: 230, maxX: 300, minY: 260, maxY: 420 }, // South America
      { minX: 430, maxX: 820, minY: 70, maxY: 220 }, // Eurasia
      { minX: 430, maxX: 540, minY: 220, maxY: 380 }, // Africa
      { minX: 760, maxX: 830, minY: 340, maxY: 395 }  // Australia
    ];
    landBoxes.forEach(box => {
      for (let i = 0; i < 60; i++) {
        const x = box.minX + Math.random() * (box.maxX - box.minX);
        const y = box.minY + Math.random() * (box.maxY - box.minY);
        ctx.beginPath();
        ctx.arc(x, y, 1.0, 0, 2 * Math.PI);
        ctx.fill();
      }
    });

    const tex = new THREE.CanvasTexture(canvas);
    tex.needsUpdate = true;
    return tex;
  }, []);

  // Earth rotates slowly on its axis
  useFrame((state, delta) => {
    if (earthRef.current) {
      earthRef.current.rotation.y += delta * 0.04;
    }
  });

  return (
    <group ref={earthRef}>
      {/* Base Earth Sphere */}
      <mesh>
        <sphereGeometry args={[EARTH_RADIUS_3D, 64, 64]} />
        <meshStandardMaterial 
          map={earthTexture}
          roughness={0.8}
          metalness={0.2}
          bumpScale={0.05}
        />
      </mesh>

      {/* Grid Overlay on top of Earth */}
      <mesh>
        <sphereGeometry args={[EARTH_RADIUS_3D + 0.005, 32, 32]} />
        <meshBasicMaterial 
          color="#00e5ff"
          wireframe
          transparent
          opacity={0.03}
        />
      </mesh>
    </group>
  );
}

// Sub-component: Atmospheric Halo Glow
function AtmosphereHalo() {
  return (
    <mesh>
      <sphereGeometry args={[EARTH_RADIUS_3D * 1.04, 32, 32]} />
      <meshBasicMaterial 
        color="#00d8f6"
        transparent
        opacity={0.07}
        blending={THREE.AdditiveBlending}
        side={THREE.BackSide}
      />
    </mesh>
  );
}

// Sub-component: Individual Satellite Marker (handles high-performance scale pulsing without React state updates)
function SatelliteMarker({
  sat,
  pos,
  risk,
  color,
  isSelected,
  isHovered,
  onSelectSat,
  setHoveredSatId
}) {
  const markerRef = useRef();

  useFrame((state) => {
    if (markerRef.current && risk === 'HIGH') {
      const s = 1 + Math.sin(state.clock.getElapsedTime() * 7) * 0.22;
      markerRef.current.scale.set(s, s, s);
    } else if (markerRef.current) {
      markerRef.current.scale.set(1.0, 1.0, 1.0);
    }
  });

  const radius = sat.type === 'debris' ? 0.03 : 0.045;

  return (
    <group 
      ref={markerRef} 
      position={pos}
      onClick={(e) => {
        e.stopPropagation();
        onSelectSat(sat.id);
      }}
      onPointerOver={(e) => {
        e.stopPropagation();
        setHoveredSatId(sat.id);
      }}
      onPointerOut={(e) => {
        e.stopPropagation();
        setHoveredSatId(null);
      }}
    >
      {/* Pulsing Outer Range Glow Ring for selection or high-risk */}
      {(isSelected || risk === 'HIGH') && (
        <mesh>
          <ringGeometry args={[radius * 1.5, radius * 2.0, 16]} />
          <meshBasicMaterial color={color} side={THREE.DoubleSide} transparent opacity={0.5} />
        </mesh>
      )}

      {/* Core Satellite Body */}
      <mesh>
        {sat.type === 'debris' ? (
          <octahedronGeometry args={[radius]} />
        ) : (
          <boxGeometry args={[radius * 1.5, radius * 0.8, radius * 0.8]} />
        )}
        <meshBasicMaterial color={isHovered ? '#ffffff' : color} />
      </mesh>

      {/* Float HUD Label when hovered or selected */}
      {(isHovered || isSelected) && (
        <Html position={[0, 0.2, 0]} zIndexRange={[100, 110]}>
          <div className={`tactical-label-3d ${risk.toLowerCase()}`}>
            <span className="lbl-type">{sat.type.toUpperCase()}</span>
            <span className="lbl-name">{sat.name}</span>
          </div>
        </Html>
      )}
    </group>
  );
}

// Sub-component: Satellites, Orbits, and Conjunction Lines
function OrbitsGroup({
  satellitesData,
  simTime,
  conjunctionEvents,
  selectedSatId,
  onSelectSat,
  hoveredSatId,
  setHoveredSatId
}) {
  // Pre-calculate orbit lines (static)
  const orbitPaths = useMemo(() => {
    return satellitesData.map((sat) => {
      const pts = getOrbitPoints(sat.tle1, sat.tle2, simTime, 100);
      const points3d = pts.map((pt) => eciTo3D({ x: pt[0], y: pt[1], z: pt[2] }));
      // Loop point back to start for full ring
      if (points3d.length > 0) {
        points3d.push(points3d[0]);
      }
      return { id: sat.id, points: points3d };
    });
  }, [satellitesData]);

  // Compute satellite positions dynamically
  const satellitePositions = useMemo(() => {
    const positions = {};
    satellitesData.forEach((sat) => {
      const eciPos = getSatellitePosition(sat.tle1, sat.tle2, simTime);
      positions[sat.id] = eciTo3D(eciPos);
    });
    return positions;
  }, [satellitesData, simTime]);

  // Find risk categories and active conjunction lines
  const satRisks = useMemo(() => {
    const risks = {};
    satellitesData.forEach(s => { risks[s.id] = 'NOMINAL'; });
    
    conjunctionEvents.forEach(evt => {
      const risk = evt.riskClassification;
      // Escalate if higher risk found
      const weight = { NOMINAL: 0, LOW: 1, MEDIUM: 2, HIGH: 3 };
      
      const updateRisk = (id) => {
        if (!risks[id] || weight[risk] > weight[risks[id]]) {
          risks[id] = risk;
        }
      };
      
      updateRisk(evt.primaryObject.id);
      updateRisk(evt.secondaryObject.id);
    });

    return risks;
  }, [satellitesData, conjunctionEvents]);

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'HIGH': return '#ff1744';
      case 'MEDIUM': return '#ffc107';
      case 'LOW':
      default:
        return '#00e5ff';
    }
  };

  return (
    <group>
      {/* 1. Orbit Paths */}
      {orbitPaths.map((path) => {
        const risk = satRisks[path.id];
        const isSelectedOrHovered = selectedSatId === path.id || hoveredSatId === path.id;
        const color = getRiskColor(risk);

        return (
          <Line
            key={path.id}
            points={path.points}
            color={color}
            lineWidth={isSelectedOrHovered ? 1.6 : 0.8}
            opacity={isSelectedOrHovered ? 0.6 : 0.15}
            transparent
          />
        );
      })}

      {/* 2. Interactive Markers */}
      {satellitesData.map((sat) => {
        const pos = satellitePositions[sat.id] || [0,0,0];
        const risk = satRisks[sat.id];
        const color = getRiskColor(risk);
        const isSelected = selectedSatId === sat.id;
        const isHovered = hoveredSatId === sat.id;

        return (
          <SatelliteMarker
            key={sat.id}
            sat={sat}
            pos={pos}
            risk={risk}
            color={color}
            isSelected={isSelected}
            isHovered={isHovered}
            onSelectSat={onSelectSat}
            setHoveredSatId={setHoveredSatId}
          />
        );
      })}

      {/* 3. Conjunction Lines connecting close approaches */}
      {conjunctionEvents.map((evt) => {
        const p1 = satellitePositions[evt.primaryObject.id];
        const p2 = satellitePositions[evt.secondaryObject.id];

        if (!p1 || !p2) return null;

        const color = getRiskColor(evt.riskClassification);

        return (
          <group key={evt.id}>
            {/* Draw dynamic laser line between the two objects */}
            <Line
              points={[p1, p2]}
              color={color}
              lineWidth={evt.riskClassification === 'HIGH' ? 2.5 : 1.5}
              dashed={true}
              dashSize={0.1}
              gapSize={0.05}
              opacity={0.8}
            />

            {/* Hazard alert symbol midpoint */}
            <mesh position={[(p1[0] + p2[0])/2, (p1[1] + p2[1])/2, (p1[2] + p2[2])/2]}>
              <sphereGeometry args={[0.04, 8, 8]} />
              <meshBasicMaterial color={color} transparent opacity={0.9} />
              <Html zIndexRange={[120, 130]}>
                <div className={`tactical-hazard-alert ${evt.riskClassification.toLowerCase()}`}>
                  <span>⚠ CA-{evt.id.slice(-4)}</span>
                </div>
              </Html>
            </mesh>
          </group>
        );
      })}
    </group>
  );
}

const CAMERA_CONFIG = { position: [0, 0, 5.0], fov: 45 };

// Core OrbitScene Component exported for Dashboard use
export default function OrbitScene({
  satellites,
  simTime,
  conjunctionEvents,
  selectedSatId,
  onSelectSat
}) {
  const [hoveredSatId, setHoveredSatId] = useState(null);

  // Set orbit path evaluation date statically at sim initialization
  const baseTime = useMemo(() => new Date(2026, 7, 6, 12, 0, 0), []);

  return (
    <div className="isometric-container viewport-3d">
      {/* 3D Hologram Overlay Tech Text */}
      <div className="telemetry-hud-overlay left">
        <div>SYS_PROPAGATION: SGP4</div>
        <div>ORBIT_MODEL: KEPLERIAN_ECI</div>
        <div>TIME_EXP: {simTime.toLocaleTimeString()}</div>
      </div>

      <div className="telemetry-hud-overlay right">
        <div>CAMERA: LOCKED_CENTRAL</div>
        <div>SENSOR_NET: ACTIVE</div>
        <div>TRACT_OBJS: {satellites.length}</div>
      </div>

      {/* Visual Color Legend for 3D display */}
      <div className="tactical-3d-legend">
        <div className="legend-item"><span className="dot high"></span> HIGH RISK</div>
        <div className="legend-item"><span className="dot med"></span> MONITOR</div>
        <div className="legend-item"><span className="dot nominal"></span> NOMINAL</div>
      </div>

      <Canvas
        camera={CAMERA_CONFIG}
        style={{ width: '100%', height: '100%' }}
      >
        <ambientLight intensity={0.9} />
        <directionalLight position={[5, 3, 5]} intensity={1.8} />
        <pointLight position={[-5, -3, -5]} intensity={0.6} />

        {/* Tactical Stars backdrop */}
        <Stars radius={120} depth={40} count={1200} factor={3.5} saturation={0.5} fade speed={1} />

        {/* Realistic Earth */}
        <EarthModel />

        {/* Atmosphere rim */}
        <AtmosphereHalo />

        {/* Orbit Lines, Satellites, and conjunction lasers */}
        <OrbitsGroup
          satellitesData={satellites}
          simTime={simTime}
          conjunctionEvents={conjunctionEvents}
          selectedSatId={selectedSatId}
          onSelectSat={onSelectSat}
          hoveredSatId={hoveredSatId}
          setHoveredSatId={setHoveredSatId}
        />

        {/* Pivot camera around Earth center without translation drift, like Google Earth */}
        <OrbitControls
          enablePan={false}
          enableZoom={true}
          enableDamping={true}
          dampingFactor={0.05}
          minDistance={2.3}
          maxDistance={8.0}
        />
      </Canvas>
    </div>
  );
}
