import React, { useState } from 'react';
import { Search, Sparkles, ShieldAlert, ArrowRight, CheckCircle2, AlertCircle, Compass } from 'lucide-react';
import { Contact } from '../types/detection';

interface AnalystPageProps {
  onSelectContact?: (contact: Contact) => void;
}

export const AnalystPage: React.FC<AnalystPageProps> = ({ onSelectContact }) => {
  const [query, setQuery] = useState<string>('show critical and high risk contacts');
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<any>(null);

  const quickPrompts = [
    'Show all critical risk contacts',
    'Ghost nets confirmed by surveyor',
    'Unknown acoustic anomalies with high novelty',
    'High priority shipwreck candidates',
    'Low confidence candidates for review'
  ];

  const handleSearch = async (queryText?: string) => {
    const q = queryText || query;
    if (!q.trim()) return;
    setLoading(true);
    try {
      const res = await fetch('/api/analyst/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q, limit: 30 })
      });
      if (res.ok) {
        const data = await res.json();
        setResult(data);
      }
    } catch (err) {
      console.error('Analyst query failed', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6 animate-fade-in font-sans">
      {/* Header */}
      <div className="border-b border-[var(--color-border)] pb-6">
        <div className="flex items-center gap-2 mb-1">
          <div className="p-2 rounded-xl bg-indigo-100 text-indigo-700">
            <Sparkles className="w-5 h-5" />
          </div>
          <h1 className="text-2xl font-extrabold text-[var(--color-text)] tracking-tight">
            AI Sonar Analyst
          </h1>
          <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200">
            Deterministic &bull; Zero Hallucination
          </span>
        </div>
        <p className="text-sm text-[var(--color-text-muted)]">
          Conversational query engine mapping operator questions directly to acoustic telemetry and database records.
        </p>
      </div>

      {/* Query Bar */}
      <div className="p-5 rounded-2xl bg-white border border-[var(--color-border)] shadow-sm space-y-3">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="w-5 h-5 text-gray-400 absolute left-4 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Ask the analyst (e.g., 'Find all high risk ghost nets', 'Uncertain contacts in survey 1')..."
              className="w-full pl-12 pr-4 py-3.5 text-sm rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 font-medium"
            />
          </div>
          <button
            onClick={() => handleSearch()}
            disabled={loading}
            className="px-6 py-3.5 rounded-xl bg-[var(--color-primary)] text-white text-sm font-semibold hover:opacity-90 transition disabled:opacity-50 flex items-center gap-2 shadow-sm"
          >
            {loading ? 'Analyzing...' : 'Execute Query'}
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        {/* Quick Prompts */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-xs text-gray-400 font-medium">Quick Prompts:</span>
          {quickPrompts.map((p, idx) => (
            <button
              key={idx}
              onClick={() => {
                setQuery(p);
                handleSearch(p);
              }}
              className="text-xs font-medium px-3 py-1 rounded-full bg-gray-100 text-gray-700 hover:bg-indigo-50 hover:text-indigo-700 transition"
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Results Section */}
      {result && (
        <div className="space-y-6">
          {/* Interpreted Query Card */}
          <div className="p-5 rounded-2xl bg-indigo-50/70 border border-indigo-200 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-indigo-900 uppercase tracking-wider">
                Interpreted Intent
              </span>
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-white text-indigo-800 border border-indigo-200">
                {result.total_matches} Matching Contacts
              </span>
            </div>
            <div className="text-sm font-semibold text-indigo-950">
              {result.summary_text}
            </div>
            <div className="flex flex-wrap gap-2 pt-1">
              {Object.entries(result.filters_applied || {}).map(([key, val]) => (
                <span key={key} className="text-xs font-mono px-2 py-0.5 rounded bg-white/80 text-indigo-800 border border-indigo-200">
                  {key}: {String(val)}
                </span>
              ))}
            </div>
          </div>

          {/* Contact Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {result.contacts.map((c: Contact) => (
              <div
                key={c.contact_id}
                onClick={() => onSelectContact && onSelectContact(c)}
                className="p-5 rounded-2xl bg-white border border-[var(--color-border)] shadow-sm hover:shadow-md transition cursor-pointer flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-xs font-bold text-gray-800 px-2 py-0.5 rounded bg-gray-100">
                      {c.contact_id}
                    </span>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                      c.risk_level === 'CRITICAL' ? 'bg-red-100 text-red-800' :
                      c.risk_level === 'HIGH' ? 'bg-orange-100 text-orange-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {c.risk_level ?? 'MEDIUM'} RISK
                    </span>
                  </div>

                  <div className="text-sm font-bold text-gray-900 capitalize mb-1">
                    {c.class_name.replace(/_/g, ' ')}
                  </div>
                  <div className="text-xs text-gray-400 truncate mb-3">
                    {c.survey_id}
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                    <div className="p-2 rounded-lg bg-gray-50">
                      <span className="text-[10px] text-gray-400 block">CONFIDENCE</span>
                      <span className="font-bold text-gray-800">{((c.calibrated_confidence ?? c.confidence) * 100).toFixed(0)}%</span>
                    </div>
                    <div className="p-2 rounded-lg bg-gray-50">
                      <span className="text-[10px] text-gray-400 block">REVIEW STATUS</span>
                      <span className="font-semibold text-gray-700">{c.review_status}</span>
                    </div>
                  </div>
                </div>

                <div className="pt-3 border-t border-gray-100 text-xs font-semibold text-indigo-600 flex items-center justify-between">
                  <span>Open in Triage View</span>
                  <span>&rarr;</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
