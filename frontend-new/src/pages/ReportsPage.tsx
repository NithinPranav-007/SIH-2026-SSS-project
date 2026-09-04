import React, { useState } from 'react';
import { Contact, SurveyUploadResponse } from '../types/detection';
import { 
  FileText, 
  Download, 
  CheckCircle2, 
  Table, 
  FileSpreadsheet, 
  Globe, 
  FileCheck,
  Sparkles,
  Layers,
  ArrowRight
} from 'lucide-react';

interface ReportsPageProps {
  survey: SurveyUploadResponse | null;
  contacts: Contact[];
}

export const ReportsPage: React.FC<ReportsPageProps> = ({ survey, contacts }) => {
  const [downloadMsg, setDownloadMsg] = useState<string | null>(null);

  const handleExportCSV = () => {
    if (!survey) return;
    window.open(`/api/surveys/${survey.survey_id}/csv`, '_blank');
    setDownloadMsg('Generated detection CSV export successfully.');
  };

  const handleExportGeoJSON = () => {
    if (!survey) return;
    window.open(`/api/surveys/${survey.survey_id}/geojson`, '_blank');
    setDownloadMsg('Generated spatial GeoJSON export successfully.');
  };

  const handleExportSummary = () => {
    if (!survey) return;
    window.open(`/api/surveys/${survey.survey_id}/summary`, '_blank');
    setDownloadMsg('Generated hydrographic executive summary report.');
  };

  return (
    <div className="p-6 lg:p-8 max-w-[1600px] mx-auto space-y-8 font-sans">
      
      {/* 1. Header */}
      <div className="bg-white rounded-[24px] border border-[#e6e6e6] p-6 shadow-soft flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="section-label">Standardized Exports</span>
            <span className="text-[#e6e6e6]">/</span>
            <span className="text-xs font-bold text-[#ff383c] uppercase tracking-wider font-sans">
              Data Products Central
            </span>
          </div>
          <h2 className="text-2xl font-extrabold text-[#1f1f1f] font-display flex items-center gap-2.5">
            <FileText className="w-6 h-6 text-[#ff383c]" />
            Hydrographic Data Products & Export Central
          </h2>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold px-3.5 py-1.5 rounded-full bg-[#fcfcfc] border border-[#e6e6e6] text-[#1f1f1f] shadow-tactile">
            Active Swath: <strong className="font-mono">{survey?.filename || 'Viator-04'}</strong>
          </span>
          <span className="text-xs font-bold px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-100">
            {contacts.length} Records Ready
          </span>
        </div>
      </div>

      {/* Success Download Banner */}
      {downloadMsg && (
        <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold flex items-center justify-between shadow-soft">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>{downloadMsg}</span>
          </div>
          <button 
            onClick={() => setDownloadMsg(null)} 
            className="text-emerald-700 hover:text-emerald-900 font-bold underline cursor-pointer text-[11px]"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* 2. Three Core Hydrographic Data Products */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Product 1: Tabular CSV */}
        <div className="group relative overflow-hidden bg-white rounded-[24px] border border-[#e6e6e6] p-7 shadow-soft hover:shadow-card-hover transition-all duration-300 flex flex-col justify-between space-y-6">
          <div className="absolute -right-8 -bottom-8 w-36 h-36 bg-[#ff383c]/5 rounded-full blur-3xl pointer-events-none transition-all duration-500 group-hover:bg-[#ff383c]/15" />

          <div className="relative z-10 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#fcfcfc] border border-[#e6e6e6] text-[#ff383c] transition-all duration-300 group-hover:bg-[#ff383c] group-hover:text-white group-hover:border-[#ff383c]">
                <FileSpreadsheet className="w-5 h-5" />
              </div>
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-slate-100 text-[#8e8e93]">
                .CSV Spreadsheet
              </span>
            </div>

            <div>
              <h3 className="text-lg font-bold text-[#1f1f1f] font-display">Tabular Detections CSV</h3>
              <p className="text-xs text-[#8e8e93] leading-relaxed mt-1">
                Full spreadsheet export with Candidate IDs, pixel bounds, AI confidences, acoustic evidence scores, and review status logs.
              </p>
            </div>
          </div>

          <button
            onClick={handleExportCSV}
            disabled={!survey}
            className="relative z-10 w-full py-3 rounded-full bg-[#ff383c] hover:bg-[#dc143c] text-white font-semibold text-xs transition-all duration-200 shadow-tactile flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Detections CSV</span>
          </button>
        </div>

        {/* Product 2: Spatial GeoJSON */}
        <div className="group relative overflow-hidden bg-white rounded-[24px] border border-[#e6e6e6] p-7 shadow-soft hover:shadow-card-hover transition-all duration-300 flex flex-col justify-between space-y-6">
          <div className="absolute -right-8 -bottom-8 w-36 h-36 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none transition-all duration-500 group-hover:bg-emerald-500/15" />

          <div className="relative z-10 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#fcfcfc] border border-[#e6e6e6] text-emerald-600 transition-all duration-300 group-hover:bg-emerald-600 group-hover:text-white group-hover:border-emerald-600">
                <Globe className="w-5 h-5" />
              </div>
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700">
                RFC 7946 Standard
              </span>
            </div>

            <div>
              <h3 className="text-lg font-bold text-[#1f1f1f] font-display">Spatial RFC 7946 GeoJSON</h3>
              <p className="text-xs text-[#8e8e93] leading-relaxed mt-1">
                Standardized FeatureCollection of Point geometries ready for immediate drag-and-drop ingestion into QGIS, ArcGIS, or MapStore.
              </p>
            </div>
          </div>

          <button
            onClick={handleExportGeoJSON}
            disabled={!survey}
            className="relative z-10 w-full py-3 rounded-full bg-[#1f1f1f] hover:bg-black text-white font-semibold text-xs transition-all duration-200 shadow-tactile flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Spatial GeoJSON</span>
          </button>
        </div>

        {/* Product 3: Executive Summary */}
        <div className="group relative overflow-hidden bg-white rounded-[24px] border border-[#e6e6e6] p-7 shadow-soft hover:shadow-card-hover transition-all duration-300 flex flex-col justify-between space-y-6">
          <div className="absolute -right-8 -bottom-8 w-36 h-36 bg-[#ffd400]/10 rounded-full blur-3xl pointer-events-none transition-all duration-500 group-hover:bg-[#ffd400]/20" />

          <div className="relative z-10 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#fcfcfc] border border-[#e6e6e6] text-amber-600 transition-all duration-300 group-hover:bg-[#ffd400] group-hover:text-[#1f1f1f] group-hover:border-[#ffd400]">
                <FileCheck className="w-5 h-5" />
              </div>
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-800">
                Audit Summary
              </span>
            </div>

            <div>
              <h3 className="text-lg font-bold text-[#1f1f1f] font-display">Executive Survey Summary</h3>
              <p className="text-xs text-[#8e8e93] leading-relaxed mt-1">
                Structured hydrographic report covering swath coverage, dynamic range, candidate counts, and operator triage resolution rates.
              </p>
            </div>
          </div>

          <button
            onClick={handleExportSummary}
            disabled={!survey}
            className="relative z-10 w-full py-3 rounded-full bg-[#fcfcfc] hover:bg-slate-100 border border-[#e6e6e6] text-[#1f1f1f] font-semibold text-xs transition-all duration-200 shadow-tactile flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5 text-[#8e8e93]" />
            <span>Download Summary JSON</span>
          </button>
        </div>

      </section>

      {/* 3. Live Data Preview Table Card */}
      <section className="bg-white rounded-[24px] border border-[#e6e6e6] p-7 shadow-soft space-y-5">
        <div className="border-b border-[#f2f2f2] pb-3 flex items-center justify-between">
          <div>
            <span className="section-label block">Live Export Preview</span>
            <h3 className="text-base font-bold text-[#1f1f1f] font-display mt-0.5 flex items-center gap-2">
              <Table className="w-4 h-4 text-[#ff383c]" />
              Survey Detections Export Table ({contacts.length} Records)
            </h3>
          </div>
          <span className="text-xs font-semibold text-[#8e8e93]">
            Format: RFC 4180 CSV
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-sans">
            <thead>
              <tr className="border-b border-[#e6e6e6] text-[#8e8e93] text-[10px] uppercase font-bold tracking-wider">
                <th className="pb-3 pl-2">Contact ID</th>
                <th className="pb-3">Priority</th>
                <th className="pb-3">Confidence</th>
                <th className="pb-3">Bounding Box</th>
                <th className="pb-3">Latitude / Longitude</th>
                <th className="pb-3 pr-2">Triage Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#f2f2f2]">
              {contacts.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-xs text-[#8e8e93]">
                    No contacts loaded for preview. Select a benchmark swath from the top header.
                  </td>
                </tr>
              ) : (
                contacts.map((c) => {
                  const isHigh = c.priority === 'HIGH';
                  const isConfirmed = c.review_status === 'CONFIRMED';
                  const isFalseAlarm = c.review_status === 'FALSE_POSITIVE';

                  return (
                    <tr key={c.contact_id} className="hover:bg-[#fcfcfc] transition-colors">
                      <td className="py-3.5 pl-2 font-mono font-bold text-[#1f1f1f]">{c.contact_id}</td>
                      <td className="py-3.5">
                        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold font-sans ${
                          isHigh ? 'bg-[#ff383c]/10 text-[#ff383c]' : 'bg-amber-50 text-amber-700'
                        }`}>
                          {c.priority}
                        </span>
                      </td>
                      <td className="py-3.5 font-bold text-[#1f1f1f] font-mono">{Math.round(c.confidence * 100)}%</td>
                      <td className="py-3.5 text-[#8e8e93] font-mono">[{c.bbox.x1}, {c.bbox.y1}, {c.bbox.x2}, {c.bbox.y2}]</td>
                      <td className="py-3.5 font-mono text-slate-700">
                        {c.latitude && c.longitude ? `${c.latitude.toFixed(5)}°, ${c.longitude.toFixed(5)}°` : 'Awaiting GPS Nav Log'}
                      </td>
                      <td className="py-3.5 pr-2">
                        <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold font-sans ${
                          isConfirmed
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-100'
                            : isFalseAlarm
                            ? 'bg-slate-100 text-slate-700'
                            : 'bg-slate-100 text-[#8e8e93]'
                        }`}>
                          {c.review_status.replace('_', ' ')}
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
