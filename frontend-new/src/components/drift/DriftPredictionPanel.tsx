import React, { useState, useEffect } from 'react';
import { Contact } from '../../types/detection';
import { DriftForecastDetail, DriftMilestone } from '../../types/drift';
import { apiService } from '../../services/api';
import { useToast } from '../../hooks/useToast';
import { DriftForecastCard } from './DriftForecastCard';
import { OceanDataStatus } from './OceanDataStatus';
import { DriftModelComparison } from './DriftModelComparison';
import { DriftUncertaintyPanel } from './DriftUncertaintyPanel';
import { DriftTrajectoryChart } from './DriftTrajectoryChart';
import { 
  Waves, 
  Compass, 
  MapPin, 
  Clock, 
  Navigation, 
  Sparkles, 
  Layers, 
  ShieldAlert, 
  ArrowRight, 
  Flame,
  CheckCircle2,
  RefreshCw
} from 'lucide-react';

interface DriftPredictionPanelProps {
  contact: Contact;
  onNavigateToMap?: () => void;
  onForecastGenerated?: (forecast: DriftForecastDetail) => void;
}

export const DriftPredictionPanel: React.FC<DriftPredictionPanelProps> = ({
  contact,
  onNavigateToMap,
  onForecastGenerated,
}) => {
  const { toast } = useToast();
  const [forecast, setForecast] = useState<DriftForecastDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedModel, setSelectedModel] = useState<string>('CHAMPION');
  const [horizonHours, setHorizonHours] = useState<number>(72);

  // Auto-fetch existing forecast for this contact if any exists
  useEffect(() => {
    let isMounted = true;
    const checkExisting = async () => {
      try {
        const existing = await apiService.getContactDriftForecasts(contact.contact_id);
        if (isMounted && existing && existing.length > 0) {
          // Fetch the latest detailed forecast
          const detail = await apiService.getDriftForecast(existing[0].forecast_id);
          setForecast(detail);
          if (onForecastGenerated) {
            onForecastGenerated(detail);
          }
        }
      } catch (err) {
        // No existing forecast found
      }
    };
    checkExisting();
    return () => {
      isMounted = false;
    };
  }, [contact.contact_id]);

  const handlePredict = async () => {
    setLoading(true);
    try {
      const res = await apiService.predictDrift({
        contact_id: contact.contact_id,
        latitude: contact.latitude || undefined,
        longitude: contact.longitude || undefined,
        horizon_hours: horizonHours,
        model_preference: selectedModel,
      });

      setForecast(res);
      if (onForecastGenerated) {
        onForecastGenerated(res);
      }
      toast.success(`72h Drift Trajectory calculated via ${res.model_name}`);
    } catch (err: any) {
      toast.error(err.message || 'Failed to compute drift trajectory.');
    } finally {
      setLoading(false);
    }
  };

  const isGhostNet = contact.class_name?.toLowerCase().includes('net');

  return (
    <div className="bg-white rounded-[24px] border border-slate-200 p-6 shadow-soft space-y-6 font-sans">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="section-label">Debris Intelligence</span>
            <span className="text-slate-300">/</span>
            <span className="text-xs font-bold text-cyan-600 uppercase tracking-wider font-sans">
              Lagrangian Drift Predictor
            </span>
          </div>
          <h3 className="text-xl font-extrabold text-slate-800 font-display flex items-center gap-2">
            <Waves className="w-5 h-5 text-cyan-500" />
            Ghost Net Drift Forecast (24h / 48h / 72h)
          </h3>
        </div>

        {/* Model Selector & Predict Button */}
        <div className="flex items-center gap-2.5">
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="text-xs font-semibold bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-700 cursor-pointer focus:outline-none focus:ring-2 focus:ring-cyan-500/20"
          >
            <option value="CHAMPION">Champion (Physics Baseline)</option>
            <option value="PHYSICS">Physics (Runge-Kutta RK2)</option>
            <option value="PHYSICS_GRU">Physics + GRU Residual</option>
            <option value="PHYSICS_LSTM">Physics + LSTM Residual</option>
          </select>

          <button
            onClick={handlePredict}
            disabled={loading}
            className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white rounded-xl text-xs font-bold shadow-md hover:shadow-lg transition-all flex items-center gap-2 disabled:opacity-50 cursor-pointer"
          >
            {loading ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                Integrating Ocean Currents...
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                Predict Drift
              </>
            )}
          </button>
        </div>
      </div>

      {/* Target Origin Telemetry */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Target Class</div>
          <div className="text-sm font-extrabold text-slate-800 capitalize mt-0.5 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-rose-500" />
            {contact.class_name.replace('_', ' ')}
          </div>
        </div>

        <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Detection Confidence</div>
          <div className="text-sm font-extrabold text-slate-800 font-mono mt-0.5">
            {(contact.confidence * 100).toFixed(1)}%
          </div>
        </div>

        <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Coordinates</div>
          <div className="text-sm font-extrabold text-slate-800 font-mono mt-0.5">
            {contact.latitude ? `${contact.latitude.toFixed(4)}°N` : '15.0000°N'},{' '}
            {contact.longitude ? `${contact.longitude.toFixed(4)}°E` : '70.0000°E'}
          </div>
        </div>

        <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Ocean Layer Mode</div>
          <div className="text-sm font-extrabold text-cyan-700 font-mono mt-0.5">
            SURFACE (0.494m)
          </div>
        </div>
      </div>

      {/* Ocean Environmental Telemetry Component */}
      <OceanDataStatus />

      {/* Forecast Results (Rendered if forecast exists) */}
      {forecast && (
        <div className="space-y-6 pt-4 border-t border-slate-100">
          {/* Hotspot Intelligence Indicator */}
          <div className="p-4 bg-gradient-to-r from-amber-500/10 via-amber-50 to-orange-50 rounded-2xl border border-amber-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-amber-500 text-white flex items-center justify-center font-extrabold text-sm shadow-sm">
                <Flame className="w-5 h-5" />
              </div>
              <div>
                <div className="text-xs font-bold text-amber-900 uppercase tracking-wider">
                  Marine Debris Hotspot & Retention Intelligence
                </div>
                <div className="text-xs text-amber-700 mt-0.5">
                  Retention score: <span className="font-mono font-bold text-amber-900">{forecast.hotspot_score} / 100</span>{' '}
                  ({forecast.hotspot_evidence?.retention_indicator || 'CALCULATED'}). Sub-surface convergence and eddy circulation analysis.
                </div>
              </div>
            </div>

            {onNavigateToMap && (
              <button
                onClick={onNavigateToMap}
                className="px-3 py-1.5 bg-slate-900 hover:bg-black text-white text-xs font-bold rounded-xl flex items-center gap-1.5 transition-all shadow-sm cursor-pointer self-start sm:self-auto"
              >
                <Layers className="w-3.5 h-3.5" />
                View On Nautical GIS
                <ArrowRight className="w-3 h-3" />
              </button>
            )}
          </div>

          {/* Multi-Horizon Milestones (24h, 48h, 72h) */}
          <div className="space-y-2">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Drift Horizon Milestones
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {['24h', '48h', '72h'].map((key) => {
                const ms = forecast.milestones?.[key];
                if (!ms) return null;
                return (
                  <DriftForecastCard
                    key={key}
                    milestoneKey={key}
                    milestone={ms}
                    isChampion={forecast.champion_model === forecast.model_name}
                  />
                );
              })}
            </div>
          </div>

          {/* Trajectory Dispersion & Kinematics Chart */}
          <DriftTrajectoryChart 
            milestones={forecast.milestones} 
            initialCoords={{ lat: forecast.initial_latitude, lon: forecast.initial_longitude }}
          />

          {/* Uncertainty Analysis */}
          <DriftUncertaintyPanel milestones={forecast.milestones} />

          {/* Research Model Comparison */}
          <DriftModelComparison />
        </div>
      )}
    </div>
  );
};
