import React, { useState } from 'react';
import { DriftMilestone } from '../../types/drift';
import { 
  TrendingUp, 
  Compass, 
  Activity, 
  ShieldAlert, 
  Navigation,
  Clock,
  Layers,
  Info
} from 'lucide-react';

interface DriftTrajectoryChartProps {
  milestones: Record<string, DriftMilestone>;
  initialCoords?: { lat: number; lon: number };
}

export const DriftTrajectoryChart: React.FC<DriftTrajectoryChartProps> = ({
  milestones,
  initialCoords
}) => {
  const [activeTab, setActiveTab] = useState<'distance' | 'speed' | 'uncertainty'>('distance');
  const [hoveredPoint, setHoveredPoint] = useState<number | null>(null);

  // Normalize milestone points sorted by horizon
  const points: {
    label: string;
    hours: number;
    distance_km: number;
    speed_ms: number;
    heading_deg: number;
    uncertainty_km: number;
    lat: number;
    lon: number;
  }[] = [
    {
      label: '0h (T0)',
      hours: 0,
      distance_km: 0,
      speed_ms: milestones['24h'] ? Math.max(0.05, milestones['24h'].speed_ms * 0.9) : 0.15,
      heading_deg: milestones['24h'] ? milestones['24h'].heading_deg : 0,
      uncertainty_km: 0.5,
      lat: initialCoords?.lat || 15.0,
      lon: initialCoords?.lon || 70.0,
    }
  ];

  ['24h', '48h', '72h'].forEach((key) => {
    const ms = milestones[key];
    if (ms) {
      points.push({
        label: `${ms.horizon_hours}h`,
        hours: ms.horizon_hours,
        distance_km: ms.distance_km,
        speed_ms: ms.speed_ms,
        heading_deg: ms.heading_deg,
        uncertainty_km: ms.uncertainty_radius_km,
        lat: ms.latitude,
        lon: ms.longitude,
      });
    }
  });

  // Chart dimensions & scaling
  const width = 560;
  const height = 180;
  const padding = { top: 20, right: 30, bottom: 30, left: 45 };
  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;

  // Max values
  const maxDistance = Math.max(10, ...points.map((p) => p.distance_km * 1.2));
  const maxSpeed = Math.max(0.5, ...points.map((p) => p.speed_ms * 1.3));
  const maxUncertainty = Math.max(10, ...points.map((p) => p.uncertainty_km * 1.2));

  // Coordinate mappers
  const getX = (index: number) => padding.left + (index / (points.length - 1)) * innerWidth;
  
  const getYDistance = (d: number) => 
    padding.top + innerHeight - (d / maxDistance) * innerHeight;
    
  const getYSpeed = (s: number) => 
    padding.top + innerHeight - (s / maxSpeed) * innerHeight;
    
  const getYUncertainty = (u: number) => 
    padding.top + innerHeight - (u / maxUncertainty) * innerHeight;

  // Path generators
  const distancePath = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getYDistance(p.distance_km)}`)
    .join(' ');

  const distanceArea = `${distancePath} L ${getX(points.length - 1)} ${height - padding.bottom} L ${getX(0)} ${height - padding.bottom} Z`;

  const speedPath = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getYSpeed(p.speed_ms)}`)
    .join(' ');

  const uncertaintyUpperPath = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getYDistance(p.distance_km + p.uncertainty_km)}`)
    .join(' ');
  const uncertaintyLowerPath = [...points]
    .reverse()
    .map((p, i) => {
      const idx = points.length - 1 - i;
      return `L ${getX(idx)} ${getYDistance(Math.max(0, p.distance_km - p.uncertainty_km))}`;
    })
    .join(' ');
  const uncertaintyArea = `${uncertaintyUpperPath} ${uncertaintyLowerPath} Z`;

  const activePoint = hoveredPoint !== null ? points[hoveredPoint] : points[points.length - 1];

  return (
    <div className="bg-slate-900 text-slate-100 rounded-2xl p-5 border border-slate-800 shadow-lg space-y-4">
      {/* Chart Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/20 text-cyan-400 flex items-center justify-center">
            <TrendingUp className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-white tracking-wide">
              Lagrangian Drift Dispersion Profile
            </h4>
            <p className="text-[11px] text-slate-400">
              Displacement, hydrodynamics & uncertainty propagation (0h - 72h)
            </p>
          </div>
        </div>

        {/* Metric Switcher Tabs */}
        <div className="flex items-center gap-1 bg-slate-800/80 p-1 rounded-xl border border-slate-700/60">
          <button
            onClick={() => setActiveTab('distance')}
            className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'distance'
                ? 'bg-cyan-500 text-slate-950 font-bold shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Distance (km)
          </button>
          <button
            onClick={() => setActiveTab('speed')}
            className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'speed'
                ? 'bg-cyan-500 text-slate-950 font-bold shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Speed (m/s)
          </button>
          <button
            onClick={() => setActiveTab('uncertainty')}
            className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'uncertainty'
                ? 'bg-cyan-500 text-slate-950 font-bold shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Cone (±km)
          </button>
        </div>
      </div>

      {/* SVG Chart Canvas */}
      <div className="relative">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-44 overflow-visible font-mono text-[10px]"
        >
          <defs>
            <linearGradient id="distanceGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.0" />
            </linearGradient>
            <linearGradient id="speedGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.0" />
            </linearGradient>
            <linearGradient id="coneGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#f59e0b" stopOpacity="0.05" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio, idx) => {
            const y = padding.top + innerHeight * (1 - ratio);
            const valLabel =
              activeTab === 'distance'
                ? `${(maxDistance * ratio).toFixed(0)} km`
                : activeTab === 'speed'
                ? `${(maxSpeed * ratio).toFixed(2)} m/s`
                : `${(maxUncertainty * ratio).toFixed(0)} km`;

            return (
              <g key={idx}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={width - padding.right}
                  y2={y}
                  stroke="#334155"
                  strokeDasharray="3 3"
                  strokeWidth="0.8"
                />
                <text
                  x={padding.left - 8}
                  y={y + 3}
                  fill="#64748b"
                  textAnchor="end"
                >
                  {valLabel}
                </text>
              </g>
            );
          })}

          {/* Uncertainty Cone Area if active or distance */}
          {activeTab === 'distance' && (
            <path
              d={uncertaintyArea}
              fill="url(#coneGradient)"
              stroke="#f59e0b"
              strokeWidth="1"
              strokeDasharray="2 2"
              opacity="0.7"
            />
          )}

          {/* Main Area & Line */}
          {activeTab === 'distance' && (
            <>
              <path d={distanceArea} fill="url(#distanceGradient)" />
              <path
                d={distancePath}
                fill="none"
                stroke="#06b6d4"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
            </>
          )}

          {activeTab === 'speed' && (
            <>
              <path
                d={`${speedPath} L ${getX(points.length - 1)} ${height - padding.bottom} L ${getX(0)} ${height - padding.bottom} Z`}
                fill="url(#speedGradient)"
              />
              <path
                d={speedPath}
                fill="none"
                stroke="#3b82f6"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
            </>
          )}

          {activeTab === 'uncertainty' && (
            <>
              <path
                d={points
                  .map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getYUncertainty(p.uncertainty_km)}`)
                  .join(' ')}
                fill="none"
                stroke="#f59e0b"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
            </>
          )}

          {/* Data Points */}
          {points.map((p, i) => {
            const cx = getX(i);
            const cy =
              activeTab === 'distance'
                ? getYDistance(p.distance_km)
                : activeTab === 'speed'
                ? getYSpeed(p.speed_ms)
                : getYUncertainty(p.uncertainty_km);

            const isSelected = hoveredPoint === i;

            return (
              <g
                key={i}
                className="cursor-pointer transition-transform"
                onMouseEnter={() => setHoveredPoint(i)}
                onMouseLeave={() => setHoveredPoint(null)}
              >
                {/* Vertical guidelines */}
                <line
                  x1={cx}
                  y1={padding.top}
                  x2={cx}
                  y2={height - padding.bottom}
                  stroke={isSelected ? '#06b6d4' : '#1e293b'}
                  strokeWidth={isSelected ? '1.5' : '1'}
                />

                {/* Outer halo */}
                <circle
                  cx={cx}
                  cy={cy}
                  r={isSelected ? 7 : 4}
                  fill={activeTab === 'speed' ? '#3b82f6' : activeTab === 'uncertainty' ? '#f59e0b' : '#06b6d4'}
                  opacity={isSelected ? 0.4 : 0.2}
                />

                {/* Center dot */}
                <circle
                  cx={cx}
                  cy={cy}
                  r={isSelected ? 4 : 2.5}
                  fill="#ffffff"
                  stroke={activeTab === 'speed' ? '#3b82f6' : activeTab === 'uncertainty' ? '#f59e0b' : '#06b6d4'}
                  strokeWidth="2"
                />

                {/* X axis labels */}
                <text
                  x={cx}
                  y={height - padding.bottom + 16}
                  fill={isSelected ? '#38bdf8' : '#94a3b8'}
                  textAnchor="middle"
                  fontWeight={isSelected ? 'bold' : 'normal'}
                >
                  {p.label}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Telemetry Summary Strip for Active/Hovered Point */}
      {activePoint && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-slate-800 text-xs">
          <div className="bg-slate-800/60 p-2.5 rounded-xl border border-slate-700/50">
            <span className="text-[10px] text-slate-400 uppercase font-semibold flex items-center gap-1">
              <Clock className="w-3 h-3 text-cyan-400" /> Horizon
            </span>
            <div className="text-white font-mono font-bold mt-0.5">
              +{activePoint.hours}h ({activePoint.label})
            </div>
          </div>

          <div className="bg-slate-800/60 p-2.5 rounded-xl border border-slate-700/50">
            <span className="text-[10px] text-slate-400 uppercase font-semibold flex items-center gap-1">
              <TrendingUp className="w-3 h-3 text-emerald-400" /> Displacement
            </span>
            <div className="text-white font-mono font-bold mt-0.5">
              {activePoint.distance_km.toFixed(1)} km
            </div>
          </div>

          <div className="bg-slate-800/60 p-2.5 rounded-xl border border-slate-700/50">
            <span className="text-[10px] text-slate-400 uppercase font-semibold flex items-center gap-1">
              <Compass className="w-3 h-3 text-blue-400" /> Current / Bearing
            </span>
            <div className="text-white font-mono font-bold mt-0.5">
              {activePoint.speed_ms.toFixed(2)} m/s @ {activePoint.heading_deg.toFixed(0)}°
            </div>
          </div>

          <div className="bg-slate-800/60 p-2.5 rounded-xl border border-slate-700/50">
            <span className="text-[10px] text-slate-400 uppercase font-semibold flex items-center gap-1">
              <ShieldAlert className="w-3 h-3 text-amber-400" /> Uncertainty Radius
            </span>
            <div className="text-amber-300 font-mono font-bold mt-0.5">
              ±{activePoint.uncertainty_km.toFixed(1)} km (95% CI)
            </div>
          </div>
        </div>
      )}

      {/* Scientific Footnote */}
      <div className="flex items-center gap-1.5 text-[10px] text-slate-500 pt-1">
        <Info className="w-3 h-3 text-slate-400 shrink-0" />
        <span>
          Drift trajectory propagated via 4th-order Runge-Kutta advection on Copernicus GLORYS12V1 surface velocities with empirical diffusion sigma_t ~ sqrt(2 * D * t).
        </span>
      </div>
    </div>
  );
};
