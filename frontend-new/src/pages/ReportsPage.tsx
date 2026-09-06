import React from 'react';
import { Contact, SurveyUploadResponse } from '../types/detection';
import { useToast } from '../hooks/useToast';
import { 
  FileText, 
  Download, 
  Table, 
  FileSpreadsheet, 
  Globe, 
  FileCheck,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  Clock
} from 'lucide-react';

interface ReportsPageProps {
  survey: SurveyUploadResponse | null;
  contacts: Contact[];
}

export const ReportsPage: React.FC<ReportsPageProps> = ({ survey, contacts }) => {
  const { toast } = useToast();

  const hasData = !!survey && contacts.length > 0;
  const disabledReason = !survey
    ? 'Load a benchmark swath first'
    : contacts.length === 0
    ? 'No detections yet — run analysis or load a demo'
    : '';

  const handleExportCSV = () => {
    if (!hasData) return;
    window.open(`/api/surveys/${survey!.survey_id}/csv`, '_blank');
    toast.success('Detection CSV export initiated successfully.');
  };

  const handleExportGeoJSON = () => {
    if (!hasData) return;
    window.open(`/api/surveys/${survey!.survey_id}/geojson`, '_blank');
    toast.success('Spatial RFC 7946 GeoJSON export initiated.');
  };

  const handleExportSummary = () => {
    if (!hasData) return;
    window.open(`/api/surveys/${survey!.survey_id}/summary`, '_blank');
    toast.success('Hydrographic executive summary export initiated.');
  };

  // Triage progress counts
  const confirmedCount = contacts.filter(c => c.review_status === 'CONFIRMED').length;
  const falsePositiveCount = contacts.filter(c => c.review_status === 'FALSE_POSITIVE').length;
  const pendingCount = contacts.filter(c => c.review_status === 'AI_CANDIDATE').length;
  const reviewedCount = confirmedCount + falsePositiveCount + contacts.filter(c => c.review_status === 'UNCERTAIN').length;

  return (
    <div className="p-6 lg:p-8 max-w-[1600px] mx-auto space-y-8 font-sans">
      
      {/* 1. Header */}
      <div className="bg-[var(--color-surface)] rounded-[24px] border border-[var(--color-border)] p-6 shadow-soft flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="section-label">Standardized Exports</span>
            <span className="text-[var(--color-border)]">/</span>
            <span className="text-xs font-bold text-[var(--color-primary)] uppercase tracking-wider font-sans">
              Data Products Central
            </span>
          </div>
          <h2 className="text-2xl font-extrabold text-[var(--color-text)] font-display flex items-center gap-2.5">
            <FileText className="w-6 h-6 text-[var(--color-primary)]" />
            Hydrographic Data Products & Export Central
          </h2>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <span className="text-xs font-semibold px-3.5 py-1.5 rounded-full bg-[var(--color-surface-2)] border border-[var(--color-border)] text-[var(--color-text)] shadow-tactile">
            Active Swath: <strong className="font-mono">{survey?.filename || '—'}</strong>
          </span>
          <span className={`text-xs font-bold px-3 py-1 rounded-full border ${
            hasData ? 'bg-emerald-50 text-emerald-700 border-emerald-100' : 'bg-[var(--color-border)] text-[var(--color-text-muted)] border-[var(--color-border)]'
          }`}>
            {contacts.length} Records
          </span>
        </div>
      </div>

      {/* No data empty state */}
      {!hasData && (
        <div className="p-8 rounded-[24px] bg-[var(--color-warning-bg)] border border-[var(--color-warning-border)] flex items-center gap-4 shadow-soft">
          <div className="w-10 h-10 rounded-xl bg-white flex items-center justify-center shrink-0">
            <AlertTriangle className="w-5 h-5 text-[var(--color-warning)]" />
          </div>
          <div>
            <p className="text-sm font-bold text-[var(--color-text)]">No Data Available for Export</p>
            <p className="text-xs text-[var(--color-text-muted)] mt-0.5">{disabledReason}. Download buttons will be enabled once contacts are loaded.</p>
          </div>
        </div>
      )}

      {/* Triage Progress Summary */}
      {contacts.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Total Contacts', value: contacts.length, color: 'text-[var(--color-text)]' },
            { label: 'Confirmed', value: confirmedCount, color: 'text-emerald-700' },
            { label: 'Reviewed', value: reviewedCount, color: 'text-blue-700' },
            { label: 'Pending', value: pendingCount, color: 'text-amber-700' },
          ].map(s => (
            <div key={s.label} className="bg-[var(--color-surface)] rounded-[20px] border border-[var(--color-border)] p-4 shadow-soft text-center">
              <div className={`text-2xl font-extrabold font-display ${s.color}`}>{s.value}</div>
              <div className="text-[10px] text-[var(--color-text-muted)] font-bold uppercase tracking-wider mt-1">{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* 2. Three Core Hydrographic Data Products */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Product 1: Tabular CSV */}
        <div className="group relative overflow-hidden bg-[var(--color-surface)] rounded-[24px] border border-[var(--color-border)] p-7 shadow-soft hover:shadow-card-hover transition-all duration-300 flex flex-col justify-between space-y-6">
          <div className="absolute -right-8 -bottom-8 w-36 h-36 bg-[var(--color-primary-dim)] rounded-full blur-3xl pointer-events-none transition-all duration-500 group-hover:scale-150" />

          <div className="relative z-10 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--color-surface-2)] border border-[var(--color-border)] text-[var(--color-primary)] transition-all duration-300 group-hover:bg-[var(--color-primary)] group-hover:text-white group-hover:border-[var(--color-primary)]">
                <FileSpreadsheet className="w-5 h-5" />
              </div>
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-[var(--color-surface-2)] text-[var(--color-text-muted)]">
                .CSV Spreadsheet
              </span>
            </div>

            <div>
              <h3 className="text-lg font-bold text-[var(--color-text)] font-display">Tabular Detections CSV</h3>
              <p className="text-xs text-[var(--color-text-muted)] leading-relaxed mt-1">
                Full spreadsheet export with Candidate IDs, pixel bounds, AI confidences, acoustic evidence scores, and review status logs.
              </p>
            </div>
          </div>

          <button
            id="export-csv-btn"
            onClick={handleExportCSV}
            disabled={!hasData}
            title={disabledReason}
            className="relative z-10 w-full py-3 rounded-full bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] text-white font-semibold text-xs transition-all duration-200 shadow-tactile flex items-center justify-center gap-2 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Detections CSV</span>
          </button>
        </div>

        {/* Product 2: Spatial GeoJSON */}
        <div className="group relative overflow-hidden bg-[var(--color-surface)] rounded-[24px] border border-[var(--color-border)] p-7 shadow-soft hover:shadow-card-hover transition-all duration-300 flex flex-col justify-between space-y-6">
          <div className="absolute -right-8 -bottom-8 w-36 h-36 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none transition-all duration-500 group-hover:bg-emerald-500/15" />

          <div className="relative z-10 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--color-surface-2)] border border-[var(--color-border)] text-emerald-600 transition-all duration-300 group-hover:bg-emerald-600 group-hover:text-white group-hover:border-emerald-600">
                <Globe className="w-5 h-5" />
              </div>
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700">
                RFC 7946 Standard
              </span>
            </div>

            <div>
              <h3 className="text-lg font-bold text-[var(--color-text)] font-display">Spatial RFC 7946 GeoJSON</h3>
              <p className="text-xs text-[var(--color-text-muted)] leading-relaxed mt-1">
                Standardized FeatureCollection of Point geometries ready for immediate drag-and-drop ingestion into QGIS, ArcGIS, or MapStore.
              </p>
            </div>
          </div>

          <button
            id="export-geojson-btn"
            onClick={handleExportGeoJSON}
            disabled={!hasData}
            title={disabledReason}
            className="relative z-10 w-full py-3 rounded-full bg-[var(--color-text)] hover:bg-black text-white font-semibold text-xs transition-all duration-200 shadow-tactile flex items-center justify-center gap-2 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Spatial GeoJSON</span>
          </button>
        </div>

        {/* Product 3: Executive Summary */}
        <div className="group relative overflow-hidden bg-[var(--color-surface)] rounded-[24px] border border-[var(--color-border)] p-7 shadow-soft hover:shadow-card-hover transition-all duration-300 flex flex-col justify-between space-y-6">
          <div className="absolute -right-8 -bottom-8 w-36 h-36 bg-[var(--color-accent)]/10 rounded-full blur-3xl pointer-events-none transition-all duration-500 group-hover:bg-[var(--color-accent)]/20" />

          <div className="relative z-10 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--color-surface-2)] border border-[var(--color-border)] text-amber-600 transition-all duration-300 group-hover:bg-[var(--color-accent)] group-hover:text-[#1f1f1f] group-hover:border-[var(--color-accent)]">
                <FileCheck className="w-5 h-5" />
              </div>
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-800">
                Audit Summary
              </span>
            </div>

            <div>
              <h3 className="text-lg font-bold text-[var(--color-text)] font-display">Executive Survey Summary</h3>
              <p className="text-xs text-[var(--color-text-muted)] leading-relaxed mt-1">
                Structured hydrographic report covering swath coverage, dynamic range, candidate counts, and operator triage resolution rates.
              </p>
            </div>
          </div>

          <button
            id="export-summary-btn"
            onClick={handleExportSummary}
            disabled={!hasData}
            title={disabledReason}
            className="relative z-10 w-full py-3 rounded-full bg-[var(--color-surface-2)] hover:bg-[var(--color-border)] border border-[var(--color-border)] text-[var(--color-text)] font-semibold text-xs transition-all duration-200 shadow-tactile flex items-center justify-center gap-2 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Download className="w-3.5 h-3.5 text-[var(--color-text-muted)]" />
            <span>Download Summary JSON</span>
          </button>
        </div>

      </section>

      {/* 3. Live Data Preview Table Card */}
      <section className="bg-[var(--color-surface)] rounded-[24px] border border-[var(--color-border)] p-7 shadow-soft space-y-5">
        <div className="border-b border-[var(--color-border)] pb-3 flex items-center justify-between">
          <div>
            <span className="section-label block">Live Export Preview</span>
            <h3 className="text-base font-bold text-[var(--color-text)] font-display mt-0.5 flex items-center gap-2">
              <Table className="w-4 h-4 text-[var(--color-primary)]" />
              Survey Detections Export Table ({contacts.length} Records)
            </h3>
          </div>
          <span className="text-xs font-semibold text-[var(--color-text-muted)]">
            Format: RFC 4180 CSV
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-sans">
            <thead>
              <tr className="border-b border-[var(--color-border)] text-[var(--color-text-muted)] text-[10px] uppercase font-bold tracking-wider">
                <th className="pb-3 pl-2">Contact ID</th>
                <th className="pb-3">Class</th>
                <th className="pb-3">Priority</th>
                <th className="pb-3">Confidence</th>
                <th className="pb-3">Latitude / Longitude</th>
                <th className="pb-3 pr-2">Triage Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-border)]">
              {contacts.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-xs text-[var(--color-text-muted)]">
                    No contacts loaded. Select a benchmark swath from the top header.
                  </td>
                </tr>
              ) : (
                contacts.map((c) => {
                  const isHigh = c.priority === 'HIGH';
                  const isConfirmed = c.review_status === 'CONFIRMED';
                  const isFalseAlarm = c.review_status === 'FALSE_POSITIVE';
                  const isPending = c.review_status === 'AI_CANDIDATE';

                  return (
                    <tr key={c.contact_id} className="hover:bg-[var(--color-surface-2)] transition-colors">
                      <td className="py-3.5 pl-2 font-mono font-bold text-[var(--color-text)]">{c.contact_id}</td>
                      <td className="py-3.5 font-mono text-[var(--color-text-2)] text-[10px]">{c.class_name.replace(/_/g, ' ')}</td>
                      <td className="py-3.5">
                        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold font-sans ${
                          isHigh ? 'bg-[var(--color-danger-bg)] text-[var(--color-danger)]' : 'bg-amber-50 text-amber-700'
                        }`}>
                          {c.priority}
                        </span>
                      </td>
                      <td className="py-3.5 font-bold text-[var(--color-text)] font-mono">{Math.round(c.confidence * 100)}%</td>
                      <td className="py-3.5 font-mono text-[var(--color-text-2)]">
                        {c.latitude && c.longitude ? `${c.latitude.toFixed(5)}°, ${c.longitude.toFixed(5)}°` : 'Awaiting GPS Nav Log'}
                      </td>
                      <td className="py-3.5 pr-2">
                        <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold font-sans ${
                          isConfirmed
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-100'
                            : isFalseAlarm
                            ? 'bg-[var(--color-border)] text-[var(--color-text-muted)]'
                            : isPending
                            ? 'bg-amber-50 text-amber-700 border border-amber-100'
                            : 'bg-[var(--color-border)] text-[var(--color-text-muted)]'
                        }`}>
                          {c.review_status.replace(/_/g, ' ')}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </section>

    </div>
  );
};
