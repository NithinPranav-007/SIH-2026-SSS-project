import React from 'react';
import { DriftMilestone } from '../../types/drift';
import { Navigation, Compass, Gauge, ShieldAlert } from 'lucide-react';

interface DriftForecastCardProps {
  milestoneKey: string;
  milestone: DriftMilestone;
  isChampion?: boolean;
}

export const DriftForecastCard: React.FC<DriftForecastCardProps> = ({
  milestoneKey,
  milestone,
  isChampion = false,
}) => {
  return (
    <div
      className={`p-4 rounded-2xl border transition-all ${
        isChampion
          ? 'bg-gradient-to-br from-white to-amber-50/40 border-amber-300 shadow-sm'
          : 'bg-white border-slate-200'
      }`}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 bg-slate-900 text-white font-bold rounded-lg text-xs font-mono">
            {milestoneKey.toUpperCase()}
          </span>
          <span className="text-xs font-semibold text-slate-500">
            +{milestone.horizon_hours} Hours Forecast
          </span>
        </div>
        {isChampion && (
          <span className="text-[10px] font-extrabold uppercase tracking-wider text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full">
            Champion
          </span>
        )}
      </div>

      {/* Primary Metrics Grid */}
      <div className="grid grid-cols-2 gap-3 mb-3">
        <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-100">
          <div className="flex items-center gap-1.5 text-slate-400 text-[11px] mb-1">
            <Navigation className="w-3.5 h-3.5 text-cyan-600" />
            <span>Cumulative Drift</span>
          </div>
          <div className="text-lg font-extrabold text-slate-800 font-mono">
            {milestone.distance_km.toFixed(2)}{' '}
            <span className="text-xs font-normal text-slate-500">km</span>
          </div>
        </div>

        <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-100">
          <div className="flex items-center gap-1.5 text-slate-400 text-[11px] mb-1">
            <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
            <span>Search Uncertainty</span>
          </div>
          <div className="text-lg font-extrabold text-slate-800 font-mono">
            ±{milestone.uncertainty_radius_km.toFixed(1)}{' '}
            <span className="text-xs font-normal text-slate-500">km</span>
          </div>
        </div>
      </div>

      {/* Kinematics & Coordinates */}
      <div className="space-y-1.5 pt-2 border-t border-slate-100 text-xs text-slate-600 font-sans">
        <div className="flex justify-between items-center">
          <span className="text-slate-400">Predicted Location:</span>
          <span className="font-mono font-medium text-slate-700">
            {milestone.latitude.toFixed(4)}°N, {milestone.longitude.toFixed(4)}°E
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-slate-400 flex items-center gap-1">
            <Gauge className="w-3 h-3 text-slate-400" /> Drift Speed:
          </span>
          <span className="font-mono font-medium text-slate-700">
            {milestone.speed_ms.toFixed(2)} m/s ({(milestone.speed_ms * 1.94384).toFixed(1)} kn)
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-slate-400 flex items-center gap-1">
            <Compass className="w-3 h-3 text-slate-400" /> Heading:
          </span>
          <span className="font-mono font-medium text-slate-700">
            {milestone.heading_deg.toFixed(0)}° ({getCardinalDirection(milestone.heading_deg)})
          </span>
        </div>
      </div>
    </div>
  );
};

function getCardinalDirection(angleDeg: number): string {
  const directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
  const index = Math.round(((angleDeg %= 360) < 0 ? angleDeg + 360 : angleDeg) / 22.5) % 16;
  return directions[index];
}
