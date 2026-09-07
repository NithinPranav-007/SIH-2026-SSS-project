import React, { useEffect, useState } from 'react';
import { apiService } from '../../services/api';
import { OceanDataStatus as OceanDataStatusType } from '../../types/drift';
import { Waves, Database, AlertTriangle, CheckCircle2, XCircle, Info, RefreshCw } from 'lucide-react';

export const OceanDataStatus: React.FC = () => {
  const [dataStatus, setDataStatus] = useState<OceanDataStatusType | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiService.getDriftDataStatus();
      setDataStatus(res);
    } catch (err: any) {
      setError(err.message || 'Failed to query ocean intelligence catalogs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  if (loading && !dataStatus) {
    return (
      <div className="p-4 bg-[#f8fafc] rounded-2xl border border-slate-200 flex items-center gap-3 text-slate-500 animate-pulse text-sm">
        <RefreshCw className="w-4 h-4 animate-spin text-cyan-500" />
        Synchronizing Copernicus and INCOIS data status...
      </div>
    );
  }

  if (error || !dataStatus) {
    return (
      <div className="p-4 bg-amber-50 rounded-2xl border border-amber-200 flex items-center justify-between text-xs text-amber-800">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
          <span>Ocean Intelligence Service: {error || 'Data status unavailable'}</span>
        </div>
        <button
          onClick={fetchStatus}
          className="px-2 py-1 bg-white border border-amber-300 rounded-lg hover:bg-amber-100 font-medium"
        >
          Retry
        </button>
      </div>
    );
  }

  const { copernicus, incois, summary } = dataStatus;

  return (
    <div className="space-y-3 font-sans">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Waves className="w-4 h-4 text-cyan-500" />
          <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Ocean Environmental Telemetry & Data Sources
          </span>
        </div>
        <button
          onClick={fetchStatus}
          title="Refresh Data Status"
          className="p-1 text-slate-400 hover:text-slate-600 rounded transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {/* Copernicus Card */}
        <div className="p-3.5 bg-white rounded-xl border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-blue-600" />
              <span className="text-xs font-bold text-slate-800">Copernicus Marine</span>
            </div>
            {copernicus.available ? (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                <CheckCircle2 className="w-3 h-3" />
                Active ({copernicus.drift_mode})
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-600 bg-rose-50 px-2 py-0.5 rounded-full border border-rose-200">
                <XCircle className="w-3 h-3" />
                Unavailable
              </span>
            )}
          </div>

          <p className="text-[11px] text-slate-500 truncate">
            {copernicus.dataset_product_id || 'GLOBAL_MULTIYEAR_PHY_001_030'} (GLORYS12V1)
          </p>

          <div className="flex flex-wrap gap-1 text-[10px]">
            {copernicus.variables_available.slice(0, 6).map((v) => (
              <span key={v} className="bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded font-mono font-medium">
                {v}
              </span>
            ))}
            {copernicus.variables_available.length > 6 && (
              <span className="text-slate-400 self-center">
                +{copernicus.variables_available.length - 6} more
              </span>
            )}
          </div>
        </div>

        {/* INCOIS LAS Card */}
        <div className="p-3.5 bg-white rounded-xl border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-amber-600" />
              <span className="text-xs font-bold text-slate-800">INCOIS LAS Catalog</span>
            </div>
            {incois.available ? (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                <CheckCircle2 className="w-3 h-3" />
                Available ({incois.source_mode})
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
                <AlertTriangle className="w-3 h-3" />
                INCOIS Source Unavailable
              </span>
            )}
          </div>

          <p className="text-[11px] text-slate-500 truncate">
            {incois.product_family || 'Argo Value Added Products (D26)'}
          </p>

          <div className="flex flex-wrap gap-1 text-[10px]">
            {incois.variables && incois.variables.length > 0 ? (
              incois.variables.map((col) => (
                <span key={col} className="bg-amber-50 text-amber-700 px-1.5 py-0.5 rounded font-mono font-medium border border-amber-100">
                  {col}
                </span>
              ))
            ) : (
              <span className="text-slate-400 italic">No variables discovered</span>
            )}
          </div>
        </div>
      </div>

      {/* Scientific Integrity Disclosure: Excluded Variables */}
      <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-200 flex items-start gap-2 text-[11px] text-slate-600">
        <Info className="w-3.5 h-3.5 text-slate-400 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-700">Scientific Integrity Notice: </span>
          Variables not present in source datasets (
          <span className="font-mono text-slate-700">wind_u, wind_v, wave_height, wave_period</span>
          ) are strictly excluded from model features rather than fabricated. Predictions operate in{' '}
          <span className="font-semibold text-cyan-700">{summary.drift_mode}</span>.
        </div>
      </div>
    </div>
  );
};
