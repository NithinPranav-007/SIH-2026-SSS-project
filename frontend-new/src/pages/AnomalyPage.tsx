import React, { useState, useEffect } from 'react';
import { HelpCircle, AlertTriangle, Search, Filter, Compass, ShieldAlert, Sparkles, RefreshCw } from 'lucide-react';
import { Contact } from '../types/detection';
import { apiService } from '../services/api';

interface AnomalyPageProps {
  onSelectContact?: (contact: Contact) => void;
}

export const AnomalyPage: React.FC<AnomalyPageProps> = ({ onSelectContact }) => {
  const [anomalies, setAnomalies] = useState<Contact[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [minNovelty, setMinNovelty] = useState<number>(40);
  const [searchTerm, setSearchTerm] = useState<string>('');

  const fetchAnomalies = async () => {
    setLoading(true);
    try {
      const data = await apiService.getUnknownAnomalies(minNovelty);
      setAnomalies(data);
    } catch (err) {
      console.error('Failed to load anomalies', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnomalies();
  }, [minNovelty]);

  const filtered = anomalies.filter(a => 
    a.contact_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    a.survey_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6 animate-fade-in font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[var(--color-border)] pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className="p-2 rounded-xl bg-purple-100 text-purple-700">
              <Sparkles className="w-5 h-5" />
            </div>
            <h1 className="text-2xl font-extrabold text-[var(--color-text)] tracking-tight">
              Unknown Acoustic Anomalies
            </h1>
            <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-200">
              Open-Set Discovery
            </span>
          </div>
          <p className="text-sm text-[var(--color-text-muted)]">
            Acoustic contact signatures that deviate significantly from known target archetypes.
          </p>
        </div>

        <button
          onClick={fetchAnomalies}
          className="flex items-center gap-2 px-4 py-2 rounded-xl border border-[var(--color-border)] bg-white text-sm font-semibold hover:bg-[var(--color-surface-2)] transition shadow-sm"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh Registry
        </button>
      </div>

      {/* Scientific Principle Notice */}
      <div className="p-4 rounded-2xl bg-gradient-to-r from-purple-50/70 to-indigo-50/70 border border-purple-200 flex items-start gap-3">
        <HelpCircle className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
        <div className="text-xs text-purple-900 leading-relaxed">
          <strong className="font-semibold">Domain Integrity Rule:</strong> Novelty measures mathematical feature divergence from catalogued training prototypes. 
          <em className="font-medium"> "Unknown" does NOT automatically indicate critical risk</em> — anomalous seabed geology or uncommon marine debris are flagged here for human specialist ground-truthing.
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 rounded-2xl bg-white border border-[var(--color-border)] shadow-sm">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search anomaly by contact or survey ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 text-sm rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-purple-500/20 focus:border-purple-500"
          />
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <span className="text-xs font-semibold text-[var(--color-text-muted)] whitespace-nowrap">
            Min Novelty: <span className="text-purple-700 font-bold">{minNovelty}/100</span>
          </span>
          <input
            type="range"
            min="20"
            max="80"
            step="5"
            value={minNovelty}
            onChange={(e) => setMinNovelty(Number(e.target.value))}
            className="w-36 accent-purple-600 cursor-pointer"
          />
        </div>
      </div>

      {/* Grid of Anomalies */}
      {loading ? (
        <div className="h-64 flex flex-col items-center justify-center gap-3">
          <RefreshCw className="w-8 h-8 text-purple-600 animate-spin" />
          <span className="text-sm font-medium text-[var(--color-text-muted)]">Scanning 37-dimensional embedding space...</span>
        </div>
      ) : filtered.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-white border border-[var(--color-border)]">
          <Sparkles className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-base font-bold text-gray-700">No Uncatalogued Anomalies</h3>
          <p className="text-xs text-gray-400 mt-1">
            All contacts in database conform to known class prototypes above {minNovelty} novelty threshold.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filtered.map((anomaly) => (
            <div
              key={anomaly.contact_id}
              onClick={() => onSelectContact && onSelectContact(anomaly)}
              className="p-5 rounded-2xl bg-white border border-[var(--color-border)] shadow-sm hover:shadow-md hover:border-purple-300 transition cursor-pointer flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="font-mono text-xs font-bold px-2.5 py-1 rounded-lg bg-gray-100 text-gray-800">
                    {anomaly.contact_id}
                  </span>
                  <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-purple-100 text-purple-800 border border-purple-200">
                    Novelty: {anomaly.novelty_score ?? 55}/100
                  </span>
                </div>

                <div className="text-sm font-bold text-gray-900 mb-1 capitalize">
                  {anomaly.class_name.replace(/_/g, ' ')}
                </div>
                <div className="text-xs text-gray-500 mb-4 truncate" title={anomaly.survey_id}>
                  Survey: {anomaly.survey_id}
                </div>

                {/* Metric Badges */}
                <div className="grid grid-cols-2 gap-2 text-xs mb-4">
                  <div className="p-2 rounded-xl bg-gray-50 border border-gray-100">
                    <span className="text-[10px] text-gray-400 block uppercase">Confidence</span>
                    <span className="font-semibold text-gray-800">
                      {((anomaly.calibrated_confidence ?? anomaly.confidence) * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="p-2 rounded-xl bg-gray-50 border border-gray-100">
                    <span className="text-[10px] text-gray-400 block uppercase">Risk Tier</span>
                    <span className={`font-semibold ${
                      anomaly.risk_level === 'CRITICAL' ? 'text-red-600' :
                      anomaly.risk_level === 'HIGH' ? 'text-orange-600' :
                      'text-blue-600'
                    }`}>
                      {anomaly.risk_level ?? 'MEDIUM'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-gray-100 flex items-center justify-between text-xs text-purple-700 font-semibold">
                <span>Inspect Acoustic Signature</span>
                <span>&rarr;</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
