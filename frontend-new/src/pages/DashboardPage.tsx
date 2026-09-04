import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';
import { Contact, SurveyUploadResponse } from '../types/detection';
import { StatCard } from '../components/ui/StatCard';
import { 
  Layers, 
  Scan, 
  CheckCircle2, 
  AlertTriangle, 
  ShieldCheck, 
  Database,
  ArrowRight, 
  TrendingUp, 
  Compass, 
  Clock, 
  Waves,
  BarChart3,
  Anchor,
  ChevronRight,
  Upload
} from 'lucide-react';

interface DashboardPageProps {
  survey: SurveyUploadResponse | null;
  contacts: Contact[];
  onSelectScreen: (screen: 'dashboard' | 'sonar-analysis' | 'contact-verification' | 'gis-mapping' | 'ai-pipeline' | 'reports') => void;
  onSelectContact: (contact: Contact) => void;
  onCustomUploadClick?: () => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  survey,
  contacts,
  onSelectScreen,
  onSelectContact,
  onCustomUploadClick
}) => {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeHoverBar, setActiveHoverBar] = useState<number | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await apiService.getDashboardStats();
        setStats(res);
      } catch (err) {
        console.warn('Dashboard stats error:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, [contacts, survey]);

  const totalDetections = stats?.total_detections ?? contacts.length;
  const confirmedCount = stats?.confirmed_contacts ?? contacts.filter(c => c.review_status === 'CONFIRMED').length;
  const falsePositives = stats?.false_positives ?? contacts.filter(c => c.review_status === 'FALSE_POSITIVE').length;
  const highPriority = stats?.priority_distribution?.high ?? contacts.filter(c => c.priority === 'HIGH').length;
  const totalSurveys = stats?.total_surveys ?? (survey ? 1 : 0);

  const swathDensityData = [
    { code: 'L01', label: 'L01 (Bay)', count: 4, height: 35 },
    { code: 'L02', label: 'L02 (Reef)', count: 9, height: 75 },
    { code: 'L03', label: 'L03 (Channel)', count: 3, height: 25 },
    { code: 'L04', label: 'L04 (Wreck)', count: 11, height: 95, isPeak: true },
    { code: 'L05', label: 'L05 (Slope)', count: 6, height: 50 },
    { code: 'L06', label: 'L06 (Deep)', count: 2, height: 18 },
    { code: 'L07', label: 'L07 (Shoal)', count: 5, height: 42 },
  ];

  return (
    <div className="p-8 lg:p-10 max-w-[1500px] mx-auto space-y-8 font-sans">
      
      {/* 1. Hero / Operational Mission Banner */}
      <section className="relative overflow-hidden bg-white rounded-[24px] border border-[#e6e6e6] p-8 lg:p-10 shadow-soft">
        <div className="absolute -right-16 -top-16 w-80 h-80 bg-[#ffd400]/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute right-1/4 -bottom-20 w-96 h-96 bg-[#ff383c]/5 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-8">
          <div className="space-y-3 max-w-3xl">
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full bg-[#ff383c]/10 text-[#ff383c] text-xs font-bold font-sans">
                <span className="w-2 h-2 rounded-full bg-[#ff383c] animate-pulse" />
                MISSION PHASE 2: HUMAN-IN-THE-LOOP TRIAGE
              </span>
              <span className="px-3 py-1 rounded-full bg-slate-100 text-[#8e8e93] text-xs font-semibold">
                DATUM: WGS-84 / EPSG:4326
              </span>
            </div>

            <h2 className="text-3xl lg:text-4xl font-extrabold tracking-tight text-[#1f1f1f] font-display">
              Side-Scan Sonar Acoustic Triage Command
            </h2>
            <p className="text-sm lg:text-base text-[#8e8e93] leading-relaxed">
              AI-assisted highlight-shadow anomaly proposal generator with hydrographic surveyor validation. 
              Reviewing swath telemetry, verified candidate densities, and geospatial wreck contacts.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3 shrink-0">
            {onCustomUploadClick && (
              <button
                onClick={onCustomUploadClick}
                className="px-5 py-3.5 rounded-full bg-white hover:bg-slate-50 text-[#1f1f1f] border border-[#e6e6e6] font-semibold text-xs transition-all duration-200 shadow-tactile flex items-center gap-2 cursor-pointer"
              >
                <Upload className="w-4 h-4 text-[#8e8e93]" />
                <span>Upload Swath</span>
              </button>
            )}

            <button
              onClick={() => onSelectScreen('sonar-analysis')}
              className="px-6 py-3.5 rounded-full bg-[#ff383c] hover:bg-[#dc143c] text-white font-semibold text-xs transition-all duration-200 shadow-tactile hover:scale-[1.02] active:scale-[0.98] flex items-center gap-2 cursor-pointer"
            >
              <Waves className="w-4 h-4" />
              <span>Open Sonar Workstation</span>
            </button>

            <button
              onClick={() => onSelectScreen('contact-verification')}
              className="px-5 py-3.5 rounded-full bg-white hover:bg-slate-50 text-[#1f1f1f] border border-[#e6e6e6] font-semibold text-xs transition-all duration-200 shadow-tactile flex items-center gap-2 cursor-pointer"
            >
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Triage Queue ({contacts.length})</span>
            </button>
          </div>
        </div>
      </section>

      {/* 2. Key Telemetry Stat Cards: Spacious 3-Column Layout */}
      <section className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        <StatCard
          label="AI Proposals"
          value={totalDetections}
          subtext="yolov8n-baseline"
          icon={Scan}
          trend={{ value: '18.7ms Latency', isNeutral: true }}
          onClick={() => onSelectScreen('ai-pipeline')}
        />

        <StatCard
          label="Confirmed Debris"
          value={confirmedCount}
          subtext="Operator Approved"
          icon={CheckCircle2}
          trend={{ value: 'Verified 100%', isUp: true }}
          onClick={() => onSelectScreen('contact-verification')}
        />

        <StatCard
          label="High Priority Targets"
          value={highPriority}
          subtext="Acoustic Shadow Deficits"
          icon={AlertTriangle}
          trend={{ value: `${highPriority} Critical ROV`, isUp: false }}
          onClick={() => onSelectScreen('contact-verification')}
        />

        <StatCard
          label="Total Swath Surveys"
          value={totalSurveys}
          subtext="Lines L01–L07 Active"
          icon={Layers}
          trend={{ value: '+2 Ingested', isUp: true }}
          onClick={() => onSelectScreen('gis-mapping')}
        />

        <StatCard
          label="False Alarms Filtered"
          value={falsePositives}
          subtext="Geological Reefs & Clutter"
          icon={ShieldCheck}
          trend={{ value: 'Clutter Rejected', isNeutral: true }}
        />

        <StatCard
          label="Spatial Database"
          value="PostGIS 15"
          subtext="EPSG:4326 Synced"
          icon={Database}
          trend={{ value: 'Online Sync', isUp: true }}
          onClick={() => onSelectScreen('gis-mapping')}
        />
      </section>

      {/* 3. Multi-Column Analytics: Swath Density & Operator Audit Log */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Column (7 Cols): Swath Anomaly Density Chart & Contact Stream */}
        <div className="lg:col-span-7 space-y-8">
          
          {/* Swath Anomaly Density Chart Card */}
          <div className="bg-white rounded-[24px] border border-[#e6e6e6] p-7 shadow-soft space-y-6">
            <div className="flex items-center justify-between border-b border-[#f2f2f2] pb-4">
              <div>
                <span className="section-label block">
                  Acoustic Distribution
                </span>
                <h3 className="text-lg font-bold text-[#1f1f1f] font-display mt-0.5 flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-[#ff383c]" />
                  Swath Anomaly Density & AI Hit Rate
                </h3>
              </div>

              <span className="text-xs font-semibold px-3 py-1 rounded-full bg-[#fcfcfc] border border-[#e6e6e6] text-[#8e8e93]">
                Survey Lines L01–L07
              </span>
            </div>

            {/* Interactive Density Bars */}
            <div className="h-60 flex items-end justify-between gap-4 pt-4 px-2">
              {swathDensityData.map((bar, idx) => {
                const isHovered = activeHoverBar === idx;
                return (
                  <div 
                    key={idx} 
                    onMouseEnter={() => setActiveHoverBar(idx)}
                    onMouseLeave={() => setActiveHoverBar(null)}
                    className="flex-1 flex flex-col items-center gap-2.5 h-full justify-end cursor-pointer group"
                  >
                    {/* Hover Count Badge */}
                    <span 
                      className={`text-xs font-bold transition-all duration-200 ${
                        isHovered || bar.isPeak
                          ? 'opacity-100 text-[#ff383c] scale-110'
                          : 'opacity-0 text-[#8e8e93]'
                      }`}
                    >
                      {bar.count}
                    </span>

                    {/* Bar Pillar */}
                    <div className="w-full bg-slate-100 rounded-2xl h-full flex items-end overflow-hidden p-1 transition-all group-hover:bg-slate-200">
                      <div
                        className={`w-full rounded-xl transition-all duration-500 ${
                          bar.isPeak
                            ? 'bg-[#ff383c] shadow-md shadow-[#ff383c]/30'
                            : isHovered
                            ? 'bg-[#dc143c]'
                            : 'bg-[#1f1f1f]'
                        }`}
                        style={{ height: `${bar.height}%` }}
                      />
                    </div>

                    {/* Bottom Label */}
                    <span className={`text-xs font-semibold text-center truncate max-w-full font-sans transition-colors ${
                      bar.isPeak ? 'text-[#ff383c] font-bold' : 'text-[#8e8e93] group-hover:text-[#1f1f1f]'
                    }`}>
                      {bar.code}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Benchmark Peak Footer Banner */}
            <div className="p-4 rounded-2xl bg-[#fcfcfc] border border-[#e6e6e6] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-2 text-[#1f1f1f]">
                <span className="w-2.5 h-2.5 rounded-full bg-[#ff383c]" />
                <span className="font-semibold font-sans">
                  Benchmark Maximum: <strong className="text-[#ff383c]">L04 (Viator-04 Shipwreck)</strong> with 11 acoustic candidate proposals.
                </span>
              </div>
              <span className="px-3 py-1 rounded-full bg-[#ffd400]/20 text-[#1f1f1f] font-bold text-xs tracking-wide font-sans">
                52.3 FPS GPU INFERENCE
              </span>
            </div>
          </div>

          {/* Recent Ingestion & Operator Triage Audit Stream */}
          <div className="bg-white rounded-[24px] border border-[#e6e6e6] p-7 shadow-soft space-y-5">
            <div className="flex items-center justify-between border-b border-[#f2f2f2] pb-4">
              <div>
                <span className="section-label block">
                  Operator Triage Audit Log
                </span>
                <h3 className="text-lg font-bold text-[#1f1f1f] font-display mt-0.5 flex items-center gap-2">
                  <Clock className="w-5 h-5 text-[#ff383c]" />
                  Recent Ingestion & Contact Classification Stream
                </h3>
              </div>

              <span className="text-xs font-semibold text-[#8e8e93]">
                {contacts.length} Total Candidates Loaded
              </span>
            </div>

            {/* List of Contacts */}
            <div className="space-y-3">
              {contacts.length === 0 ? (
                <div className="text-center py-10 text-sm text-[#8e8e93]">
                  No candidates currently loaded. Select a benchmark swath from the top header.
                </div>
              ) : (
                contacts.slice(0, 5).map((contact) => {
                  const isHigh = contact.priority === 'HIGH';
                  const isConfirmed = contact.review_status === 'CONFIRMED';
                  const isFalseAlarm = contact.review_status === 'FALSE_POSITIVE';

                  return (
                    <div
                      key={contact.contact_id}
                      onClick={() => {
                        onSelectContact(contact);
                        onSelectScreen('sonar-analysis');
                      }}
                      className="group p-4.5 rounded-2xl bg-[#fcfcfc] hover:bg-white border border-[#e6e6e6] hover:border-[#ff383c]/40 hover:shadow-md transition-all duration-200 flex items-center justify-between cursor-pointer"
                    >
                      <div className="flex items-center gap-4">
                        {/* ID Badge Bucket */}
                        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white border border-[#e6e6e6] text-[#1f1f1f] font-mono font-bold text-xs group-hover:border-[#ff383c] group-hover:text-[#ff383c] transition-colors">
                          {contact.contact_id}
                        </div>

                        {/* Details */}
                        <div>
                          <div className="flex items-center gap-2.5">
                            <span className="font-bold text-[#1f1f1f] text-sm">
                              {contact.contact_id}
                            </span>
                            <span
                              className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full font-sans ${
                                isHigh
                                  ? 'bg-[#ff383c]/10 text-[#ff383c]'
                                  : 'bg-amber-50 text-amber-700'
                              }`}
                            >
                              {contact.priority} PRIORITY
                            </span>
                            <span className="text-xs text-[#8e8e93]">
                              Confidence: <strong className="text-[#1f1f1f]">{Math.round(contact.confidence * 100)}%</strong>
                            </span>
                          </div>

                          <p className="text-xs text-[#8e8e93] mt-1 font-sans">
                            Survey Swath: <span className="font-medium text-[#1f1f1f]">{contact.survey_id}</span> • Slant BBox: [{contact.bbox.x1}, {contact.bbox.y1}, {contact.bbox.x2}, {contact.bbox.y2}]
                          </p>
                        </div>
                      </div>

                      {/* Right Review Status & Arrow */}
                      <div className="flex items-center gap-3">
                        <span
                          className={`text-xs font-semibold px-3 py-1 rounded-full font-sans ${
                            isConfirmed
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              : isFalseAlarm
                              ? 'bg-slate-100 text-slate-700'
                              : 'bg-slate-100 text-[#8e8e93]'
                          }`}
                        >
                          {contact.review_status.replace('_', ' ')}
                        </span>

                        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white border border-[#e6e6e6] text-[#8e8e93] group-hover:text-[#ff383c] group-hover:border-[#ff383c] transition-all">
                          <ChevronRight className="w-4 h-4" />
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Right Column (5 Cols): Priority Triage Breakdown & Swath Telemetry */}
        <div className="lg:col-span-5 space-y-8">
          
          {/* Priority Triage Classification Card */}
          <div className="bg-white rounded-[24px] border border-[#e6e6e6] p-7 shadow-soft space-y-6">
            <div className="border-b border-[#f2f2f2] pb-4">
              <span className="section-label block">
                Anomaly Categorization
              </span>
              <h3 className="text-lg font-bold text-[#1f1f1f] font-display mt-0.5 flex items-center gap-2">
                <Compass className="w-5 h-5 text-[#ffd400]" />
                Priority Triage Classification
              </h3>
            </div>

            {/* Distribution Bars */}
            <div className="space-y-4">
              {/* High Priority */}
              <div className="space-y-2">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-[#ff383c] flex items-center gap-1.5 font-sans">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#ff383c]" />
                    High Priority (Deficit Shadow)
                  </span>
                  <span className="font-bold text-[#1f1f1f]">{highPriority} Candidates</span>
                </div>
                <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-[#ff383c] rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(100, (highPriority / Math.max(1, totalDetections)) * 100)}%` }}
                  />
                </div>
              </div>

              {/* Medium Priority */}
              <div className="space-y-2">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-amber-700 flex items-center gap-1.5 font-sans">
                    <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                    Medium Priority (Acoustic Proposals)
                  </span>
                  <span className="font-bold text-[#1f1f1f]">{totalDetections - highPriority} Candidates</span>
                </div>
                <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-amber-500 rounded-full transition-all duration-500"
                    style={{ width: `${Math.max(15, ((totalDetections - highPriority) / Math.max(1, totalDetections)) * 100)}%` }}
                  />
                </div>
              </div>

              {/* Low / Ambient */}
              <div className="space-y-2">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-slate-500 flex items-center gap-1.5 font-sans">
                    <span className="w-2.5 h-2.5 rounded-full bg-slate-400" />
                    Low / Ambient Backscatter
                  </span>
                  <span className="font-bold text-[#1f1f1f]">0 Excluded</span>
                </div>
                <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-slate-300 rounded-full w-[8%]" />
                </div>
              </div>
            </div>

            {/* GIS Map Navigation CTA */}
            <button
              onClick={() => onSelectScreen('gis-mapping')}
              className="w-full py-3.5 rounded-full bg-[#fcfcfc] hover:bg-slate-100 border border-[#e6e6e6] text-[#1f1f1f] font-semibold text-xs transition-all duration-200 flex items-center justify-center gap-2 shadow-tactile cursor-pointer"
            >
              <Compass className="w-4 h-4 text-[#ff383c]" />
              <span>Inspect Geospatial Map Markers</span>
            </button>
          </div>

          {/* Active Survey Provenance Card */}
          <div className="bg-white rounded-[24px] border border-[#e6e6e6] p-7 shadow-soft space-y-4">
            <div className="border-b border-[#f2f2f2] pb-4">
              <span className="section-label block">
                Swath Telemetry
              </span>
              <h3 className="text-lg font-bold text-[#1f1f1f] font-display mt-0.5 flex items-center gap-2">
                <Anchor className="w-5 h-5 text-[#ff383c]" />
                Active Acoustic Survey
              </h3>
            </div>

            {survey ? (
              <div className="space-y-3.5">
                <div className="p-4 rounded-2xl bg-[#fcfcfc] border border-[#e6e6e6] space-y-1">
                  <div className="text-[10px] text-[#8e8e93] font-bold uppercase tracking-wider">Filename</div>
                  <div className="text-xs font-bold text-[#1f1f1f] truncate font-mono">
                    {survey.filename}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3.5">
                  <div className="p-4 rounded-2xl bg-[#fcfcfc] border border-[#e6e6e6]">
                    <div className="text-[10px] text-[#8e8e93] font-bold uppercase tracking-wider">Data Quality</div>
                    <div className="text-lg font-bold text-emerald-600 mt-1">
                      {Math.round(survey.data_quality * 100)}%
                    </div>
                  </div>

                  <div className="p-4 rounded-2xl bg-[#fcfcfc] border border-[#e6e6e6]">
                    <div className="text-[10px] text-[#8e8e93] font-bold uppercase tracking-wider">Dimensions</div>
                    <div className="text-lg font-bold text-[#1f1f1f] font-mono mt-1">
                      {survey.image_width}x{survey.image_height}
                    </div>
                  </div>
                </div>

                <div className="p-4 rounded-2xl bg-[#fcfcfc] border border-[#e6e6e6] flex items-center justify-between text-xs">
                  <span className="text-[#8e8e93] font-medium">Navigation Track:</span>
                  <span className={`font-semibold px-2.5 py-0.5 rounded-full ${
                    survey.has_navigation ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-[#8e8e93]'
                  }`}>
                    {survey.has_navigation ? 'Synchronized' : 'Dead-Reckoning'}
                  </span>
                </div>
              </div>
            ) : (
              <div className="p-6 text-center text-xs text-[#8e8e93]">
                No survey swath loaded. Select one from the top bar.
              </div>
            )}

            <button
              onClick={() => onSelectScreen('ai-pipeline')}
              className="w-full py-3.5 rounded-full bg-[#1f1f1f] hover:bg-black text-white font-semibold text-xs transition-all duration-200 flex items-center justify-center gap-2 shadow-tactile cursor-pointer"
            >
              <BarChart3 className="w-4 h-4 text-[#ffd400]" />
              <span>View YOLOv8n Pipeline Metrics</span>
            </button>
          </div>

        </div>
      </section>

    </div>
  );
};
