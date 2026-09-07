import React from 'react';
import { ShieldAlert, Info, Circle } from 'lucide-react';
import { DriftMilestone } from '../../types/drift';

interface DriftUncertaintyPanelProps {
  milestones?: Record<string, DriftMilestone>;
}

export const DriftUncertaintyPanel: React.FC<DriftUncertaintyPanelProps> = ({ milestones = {} }) => {
  const m24 = milestones['24h'];
  const m48 = milestones['48h'];
  const m72 = milestones['72h'];

  return (
    <div className="p-4 bg-white rounded-2xl border border-slate-200 shadow-soft space-y-3 font-sans">
      <div className="flex items-center gap-2">
        <ShieldAlert className="w-4 h-4 text-amber-500" />
        <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
          Spatial Uncertainty & Debris Search Area
        </span>
      </div>

      <p className="text-xs text-slate-500 leading-relaxed">
        Ocean debris dispersion expands non-linearly over time due to turbulent sub-mesoscale eddies and shear.
        Search cones are computed using calibrated Lagrangian dispersion formulas:
      </p>

      <div className="grid grid-cols-3 gap-2.5 pt-1">
        <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-100 text-center">
          <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">24h Radius</div>
          <div className="text-base font-extrabold text-slate-800 font-mono mt-0.5">
            ±{m24 ? m24.uncertainty_radius_km.toFixed(1) : '5.0'} km
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">
            Area: ~{m24 ? Math.round(Math.PI * m24.uncertainty_radius_km ** 2) : 78} km²
          </div>
        </div>

        <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-100 text-center">
          <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">48h Radius</div>
          <div className="text-base font-extrabold text-slate-800 font-mono mt-0.5">
            ±{m48 ? m48.uncertainty_radius_km.toFixed(1) : '8.2'} km
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">
            Area: ~{m48 ? Math.round(Math.PI * m48.uncertainty_radius_km ** 2) : 211} km²
          </div>
        </div>

        <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-100 text-center">
          <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">72h Radius</div>
          <div className="text-base font-extrabold text-slate-800 font-mono mt-0.5">
            ±{m72 ? m72.uncertainty_radius_km.toFixed(1) : '11.2'} km
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">
            Area: ~{m72 ? Math.round(Math.PI * m72.uncertainty_radius_km ** 2) : 394} km²
          </div>
        </div>
      </div>
    </div>
  );
};
