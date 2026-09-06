import React, { useState, useEffect } from 'react';
import { Database, Download, RefreshCw, CheckCircle2, XCircle, AlertCircle, ShieldAlert } from 'lucide-react';
import { apiService } from '../services/api';

export const ActiveLearningPage: React.FC = () => {
  const [samples, setSamples] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [exporting, setExporting] = useState<boolean>(false);
  const [exportSuccess, setExportSuccess] = useState<string | null>(null);

  const fetchSamples = async () => {
    setLoading(true);
    try {
      const data = await apiService.getCuratedSamples('MEDIUM');
      setSamples(data.samples || []);
    } catch (err) {
      console.error('Failed to load active learning samples', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSamples();
  }, []);

  const handleExport = async () => {
    setExporting(true);
    setExportSuccess(null);
    try {
      const data = await apiService.exportActiveLearningDataset();
      setExportSuccess(`Successfully exported ${data.exported_contacts} training annotations to ${data.output_directory}`);
    } catch (err) {
      console.error('Export failed', err);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6 animate-fade-in font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[var(--color-border)] pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className="p-2 rounded-xl bg-amber-100 text-amber-700">
              <Database className="w-5 h-5" />
            </div>
            <h1 className="text-2xl font-extrabold text-[var(--color-text)] tracking-tight">
              Active Learning Dataset Curation
            </h1>
            <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200">
              Human-in-the-Loop Feedback Loop
            </span>
          </div>
          <p className="text-sm text-[var(--color-text-muted)]">
            High-value sonar contacts captured during operator triage for continuous model retraining.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchSamples}
            className="flex items-center gap-2 px-4 py-2 rounded-xl border border-[var(--color-border)] bg-white text-sm font-semibold hover:bg-[var(--color-surface-2)] transition shadow-sm"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>

          <button
            onClick={handleExport}
            disabled={exporting}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[var(--color-primary)] text-white text-sm font-semibold hover:opacity-90 transition shadow-sm disabled:opacity-50"
          >
            <Download className="w-4 h-4" />
            {exporting ? 'Exporting...' : 'Export YOLO Annotations'}
          </button>
        </div>
      </div>

      {/* Safety Notice */}
      <div className="p-4 rounded-2xl bg-amber-50/70 border border-amber-200 flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
        <div className="text-xs text-amber-900 leading-relaxed">
          <strong className="font-semibold">Model Governance Rule:</strong> Curated samples inform future model iteration datasets but 
          <em className="font-medium"> never automatically overwrite or deploy to the production stack</em> without independent validation and human approval.
        </div>
      </div>

      {exportSuccess && (
        <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-xs font-semibold text-emerald-800 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          {exportSuccess}
        </div>
      )}

      {/* Samples Table */}
      <div className="rounded-2xl bg-white border border-[var(--color-border)] shadow-sm overflow-hidden">
        <div className="p-4 border-b border-gray-100 flex items-center justify-between">
          <span className="text-sm font-bold text-gray-800">
            Surfaced High-Value Training Samples ({samples.length})
          </span>
          <span className="text-xs text-gray-400">
            Ranked by epistemic uncertainty &amp; operator corrections
          </span>
        </div>

        {loading ? (
          <div className="p-12 text-center text-sm text-gray-400">Loading active learning repository...</div>
        ) : samples.length === 0 ? (
          <div className="p-12 text-center text-sm text-gray-400">
            No active learning samples captured yet. Review contacts in Contact Triage to populate this dataset.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-gray-50 text-gray-500 font-semibold border-b border-gray-100 uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Contact ID</th>
                  <th className="py-3 px-4">Survey</th>
                  <th className="py-3 px-4">Operator Decision</th>
                  <th className="py-3 px-4">Uncertainty</th>
                  <th className="py-3 px-4">Sample Priority</th>
                  <th className="py-3 px-4">Notes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {samples.map((s) => (
                  <tr key={s.sample_id} className="hover:bg-gray-50/80 transition">
                    <td className="py-3 px-4 font-mono font-bold text-gray-800">{s.contact_id}</td>
                    <td className="py-3 px-4 text-gray-600 truncate max-w-xs">{s.survey_id}</td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center gap-1 font-semibold px-2 py-0.5 rounded-full ${
                        s.review_decision === 'CONFIRMED' ? 'bg-emerald-100 text-emerald-800' :
                        s.review_decision === 'FALSE_POSITIVE' ? 'bg-red-100 text-red-800' :
                        'bg-amber-100 text-amber-800'
                      }`}>
                        {s.review_decision === 'CONFIRMED' ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                        {s.review_decision}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono">
                      {((s.uncertainty_score ?? 0) * 100).toFixed(0)}%
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded font-bold text-[10px] ${
                        s.sample_priority === 'HIGH' ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-amber-50 text-amber-700 border border-amber-200'
                      }`}>
                        {s.sample_priority}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-gray-500 italic max-w-xs truncate">
                      {s.review_note || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
