import React, { useEffect, useState } from 'react';
import { apiService } from '../../services/api';
import { Trophy, CheckCircle, Clock, AlertCircle } from 'lucide-react';

export const DriftModelComparison: React.FC = () => {
  const [metricsData, setMetricsData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const data = await apiService.getDriftMetrics();
        setMetricsData(data);
      } catch (err) {
        console.warn('Failed to load drift metrics:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchMetrics();
  }, []);

  if (loading) {
    return <div className="p-4 text-xs text-slate-400">Loading model comparison matrix...</div>;
  }

  const championModel = metricsData?.champion_model || 'PHYSICS';
  const models = metricsData?.models || [];

  return (
    <div className="space-y-3 font-sans">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Trophy className="w-4 h-4 text-amber-500" />
          <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Model Evaluation & Research Benchmarks
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-xs">
          <span className="text-slate-400">Current Champion:</span>
          <span className="font-extrabold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
            {championModel}
          </span>
        </div>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-200">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-600 uppercase tracking-wider">
              <th className="py-2.5 px-3">Model Architecture</th>
              <th className="py-2.5 px-3">Status</th>
              <th className="py-2.5 px-3">24h RMSE</th>
              <th className="py-2.5 px-3">48h RMSE</th>
              <th className="py-2.5 px-3">72h RMSE</th>
              <th className="py-2.5 px-3">Champion?</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {/* Persistence Baseline */}
            <tr>
              <td className="py-2.5 px-3 font-medium text-slate-800">A. Persistence Baseline</td>
              <td className="py-2.5 px-3 text-slate-500">Benchmark</td>
              <td className="py-2.5 px-3 font-mono text-slate-400">Zero Displacement</td>
              <td className="py-2.5 px-3 font-mono text-slate-400">Zero Displacement</td>
              <td className="py-2.5 px-3 font-mono text-slate-400">Zero Displacement</td>
              <td className="py-2.5 px-3 text-slate-400">—</td>
            </tr>

            {/* Models from Registry */}
            {models.map((m: any) => {
              const isChamp = m.model_name === championModel;
              const hasMetrics = m.metrics?.status === 'VALIDATED';

              return (
                <tr
                  key={m.model_name}
                  className={isChamp ? 'bg-amber-50/30 font-medium' : 'hover:bg-slate-50/50'}
                >
                  <td className="py-2.5 px-3 text-slate-800">
                    <div className="font-bold">{m.model_name}</div>
                    <div className="text-[10px] text-slate-400">{m.version}</div>
                  </td>
                  <td className="py-2.5 px-3">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                        isChamp
                          ? 'bg-amber-100 text-amber-800'
                          : m.status === 'candidate'
                          ? 'bg-blue-50 text-blue-700'
                          : 'bg-slate-100 text-slate-600'
                      }`}
                    >
                      {m.status}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 font-mono text-slate-700">
                    {hasMetrics && m.metrics['24h']?.rmse_km
                      ? `${m.metrics['24h'].rmse_km} km`
                      : 'Pending Field Data'}
                  </td>
                  <td className="py-2.5 px-3 font-mono text-slate-700">
                    {hasMetrics && m.metrics['48h']?.rmse_km
                      ? `${m.metrics['48h'].rmse_km} km`
                      : 'Pending Field Data'}
                  </td>
                  <td className="py-2.5 px-3 font-mono text-slate-700">
                    {hasMetrics && m.metrics['72h']?.rmse_km
                      ? `${m.metrics['72h'].rmse_km} km`
                      : 'Pending Field Data'}
                  </td>
                  <td className="py-2.5 px-3">
                    {isChamp ? (
                      <span className="inline-flex items-center gap-1 text-amber-600 font-bold">
                        <CheckCircle className="w-3.5 h-3.5" />
                        Champion
                      </span>
                    ) : (
                      <span className="text-slate-300">—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-200 flex items-start gap-2 text-[11px] text-slate-600">
        <AlertCircle className="w-3.5 h-3.5 text-slate-400 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-700">Research Policy: </span>
          Per scientific integrity guidelines, ML residual correction models (GRU/LSTM) are evaluated on real drifter trajectories.
          Until empirical trajectory validation benchmarks are recorded, the deterministic{' '}
          <span className="font-bold text-slate-800">Physics Baseline (GLORYS12V1)</span> is retained as the active champion.
        </div>
      </div>
    </div>
  );
};
