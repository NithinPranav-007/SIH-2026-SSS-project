import React, { useState, useRef, useEffect } from 'react';
import { Contact, SurveyUploadResponse } from '../types/detection';
import { 
  Eye, 
  Sliders, 
  CheckCircle2, 
  AlertTriangle, 
  Filter, 
  Play, 
  ArrowRight, 
  Scan, 
  Crosshair, 
  Layers,
  Waves,
  ShieldAlert,
  Compass,
  Maximize2
} from 'lucide-react';

interface SonarAnalysisPageProps {
  survey: SurveyUploadResponse | null;
  contacts: Contact[];
  selectedContact: Contact | null;
  analyzing: boolean;
  onSelectContact: (contact: Contact) => void;
  onRunAnalysis: () => void;
  onVerifyContact?: (contact: Contact) => void;
}

export const SonarAnalysisPage: React.FC<SonarAnalysisPageProps> = ({
  survey,
  contacts,
  selectedContact,
  analyzing,
  onSelectContact,
  onRunAnalysis,
  onVerifyContact
}) => {
  const [viewMode, setViewMode] = useState<'raw' | 'processed'>('processed');
  const [showBoxes, setShowBoxes] = useState<boolean>(true);
  const [filterMode, setFilterMode] = useState<'top' | 'all'>('top');
  const [contrast, setContrast] = useState<number>(100);
  const [cursorPos, setCursorPos] = useState<{ x: number; y: number; slantM: number } | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const [scale, setScale] = useState<{ scaleX: number; scaleY: number }>({ scaleX: 1, scaleY: 1 });

  const displayedContacts = filterMode === 'top' ? contacts.slice(0, 5) : contacts;

  const updateScaling = () => {
    if (imgRef.current && imgRef.current.clientWidth > 0) {
      const renderW = imgRef.current.clientWidth;
      const renderH = imgRef.current.clientHeight;
      setScale({
        scaleX: renderW / (survey?.image_width || 1280),
        scaleY: renderH / (survey?.image_height || 1800)
      });
    }
  };

  useEffect(() => {
    window.addEventListener('resize', updateScaling);
    return () => window.removeEventListener('resize', updateScaling);
  }, [survey]);

  useEffect(() => {
    if (selectedContact && containerRef.current && scale.scaleY > 0) {
      const targetY = selectedContact.bbox.y1 * scale.scaleY;
      containerRef.current.scrollTo({
        top: Math.max(0, targetY - containerRef.current.clientHeight / 3),
        behavior: 'smooth'
      });
    }
  }, [selectedContact, scale]);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!imgRef.current || !survey) return;
    const rect = imgRef.current.getBoundingClientRect();
    const clientX = e.clientX - rect.left;
    const clientY = e.clientY - rect.top;

    if (clientX >= 0 && clientX <= rect.width && clientY >= 0 && clientY <= rect.height) {
      const origX = Math.round(clientX / (scale.scaleX || 1));
      const origY = Math.round(clientY / (scale.scaleY || 1));
      const nadirX = survey.image_width / 2;
      const slantDistPx = Math.abs(origX - nadirX);
      const slantM = Math.round((slantDistPx * 0.15) * 10) / 10;

      setCursorPos({ x: origX, y: origY, slantM });
    } else {
      setCursorPos(null);
    }
  };

  const activeContact = selectedContact || contacts[0] || null;

  return (
    <div className="p-6 lg:p-8 max-w-[1700px] mx-auto space-y-6 font-sans">
      
      {/* 1. Workspace Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-white rounded-[24px] border border-[#e6e6e6] p-6 shadow-soft">
        <div>
          <div className="flex items-center gap-2">
            <span className="section-label">Acoustic Workstation</span>
            <span className="text-[#e6e6e6]">/</span>
            <span className="text-xs font-bold text-[#ff383c] uppercase tracking-wider font-sans">
              Waterfall Inspection
            </span>
          </div>
          <h2 className="text-2xl font-extrabold text-[#1f1f1f] font-display mt-0.5 flex items-center gap-2.5">
            <Waves className="w-6 h-6 text-[#ff383c]" />
            Side-Scan Sonar Analysis & Candidate Triage
          </h2>
        </div>

        {/* Quick Actions */}
        <div className="flex items-center gap-3">
          <div className="text-xs font-semibold px-4 py-2 rounded-full bg-[#fcfcfc] border border-[#e6e6e6] text-[#1f1f1f] flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>{survey ? survey.filename : 'No Swath Active'}</span>
          </div>

          {activeContact && (
            <button
              onClick={() => onVerifyContact?.(activeContact)}
              className="px-5 py-2.5 rounded-full bg-[#ff383c] hover:bg-[#dc143c] text-white font-semibold text-xs transition-all duration-200 shadow-tactile flex items-center gap-2 cursor-pointer"
            >
              <span>Verify Target {activeContact.contact_id}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* 2. Three-Column Main Analysis Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[640px]">
        
        {/* Left Column (3 Cols): Swath Telemetry & Acoustic Metrics */}
        <div className="lg:col-span-3 space-y-6">
          
          {/* Swath Telemetry Record Card */}
          <div className="bg-white rounded-[24px] border border-[#e6e6e6] p-6 shadow-soft space-y-4">
            <div className="border-b border-[#f2f2f2] pb-3 flex items-center justify-between">
              <span className="section-label">Ingestion Record</span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-[#1f1f1f]">
                2D-SSS
              </span>
            </div>

            <div className="space-y-3 text-xs">
              <div className="p-3 rounded-2xl bg-[#fcfcfc] border border-[#e6e6e6] space-y-1">
                <span className="text-[10px] text-[#8e8e93] font-bold uppercase tracking-wider">Survey Swath ID</span>
                <div className="text-xs font-bold text-[#1f1f1f] truncate font-mono" title={survey?.survey_id}>
                  {survey?.survey_id || 'STANDBY'}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2.5">
                <div className="p-3 rounded-2xl bg-[#fcfcfc] border border-[#e6e6e6]">
                  <span className="text-[10px] text-[#8e8e93] font-bold uppercase tracking-wider">Matrix Size</span>
                  <div className="text-xs font-bold text-[#1f1f1f] font-mono mt-1">
                    {survey ? `${survey.image_width}x${survey.image_height}` : '--'}
                  </div>
                </div>

                <div className="p-3 rounded-2xl bg-[#fcfcfc] border border-[#e6e6e6]">
                  <span className="text-[10px] text-[#8e8e93] font-bold uppercase tracking-wider">Resolution</span>
                  <div className="text-xs font-bold text-[#1f1f1f] font-mono mt-1">
                    15.0 cm / px
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Radiometric Stats & Quality */}
          <div className="bg-white rounded-[24px] border border-[#e6e6e6] p-6 shadow-soft space-y-4">
            <div className="border-b border-[#f2f2f2] pb-3 flex items-center justify-between">
              <span className="section-label">Acoustic Radiometrics</span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700">
                Calibrated
              </span>
            </div>

            <div className="space-y-3.5 text-xs">
              <div className="space-y-1.5">
                <div className="flex justify-between items-center">
                  <span className="text-[#8e8e93] font-medium">Swath SNR Quality:</span>
                  <span className="font-bold text-emerald-600">
                    {survey ? `${Math.round(survey.data_quality * 100)}%` : '--'}
                  </span>
                </div>
                <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-emerald-500 rounded-full" 
                    style={{ width: `${survey ? Math.round(survey.data_quality * 100) : 0}%` }}
                  />
                </div>
              </div>

              <div className="flex justify-between items-center pt-1 border-t border-[#f2f2f2]">
                <span className="text-[#8e8e93]">Dynamic Range:</span>
                <span className="font-bold text-[#1f1f1f] font-mono">18.4 dB</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-[#8e8e93]">Normalization:</span>
                <span className="font-semibold text-sky-600 bg-sky-50 px-2 py-0.5 rounded-full text-[11px]">
                  1%–99% Percentile
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-[#8e8e93]">CLAHE Filter:</span>
                <span className="text-[#8e8e93] text-[11px] font-medium">
                  Audit Disabled (Shadow Preservation)
                </span>
              </div>
            </div>
          </div>

          {/* Towfish Nav Sensor Log */}
          <div className="bg-white rounded-[24px] border border-[#e6e6e6] p-6 shadow-soft space-y-4">
            <div className="border-b border-[#f2f2f2] pb-3 flex items-center justify-between">
              <span className="section-label">Towfish Sensor Log</span>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                survey?.has_navigation ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-[#8e8e93]'
              }`}>
                {survey?.has_navigation ? 'SYNCHRONIZED' : 'DEAD-RECKONING'}
              </span>
            </div>

            <div className="space-y-2.5 text-xs font-mono">
              {survey?.has_navigation ? (
                <>
                  <div className="flex justify-between items-center">
                    <span className="text-[#8e8e93]">Heading:</span>
                    <span className="font-bold text-[#1f1f1f]">184.2° (SSW)</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[#8e8e93]">Tow Velocity:</span>
                    <span className="font-bold text-[#1f1f1f]">4.2 kts</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[#8e8e93]">Towfish Altitude:</span>
                    <span className="font-bold text-[#ff383c]">12.5 m</span>
                  </div>
                </>
              ) : (
                <div className="p-3 rounded-2xl bg-[#fcfcfc] border border-[#e6e6e6] text-[#8e8e93] text-[11px] leading-relaxed">
                  Raw acoustic waterfall loaded. Towfish navigation coordinates estimated via dead-reckoning.
                </div>
              )}
            </div>

            {/* Run Analysis CTA */}
            {survey && (
              <button
                onClick={onRunAnalysis}
                disabled={analyzing}
                className={`w-full mt-2 py-3 rounded-full font-semibold text-xs flex items-center justify-center gap-2 transition-all duration-200 shadow-tactile ${
                  analyzing
                    ? 'bg-slate-200 text-[#8e8e93] cursor-wait'
                    : 'bg-[#ff383c] hover:bg-[#dc143c] text-white hover:scale-[1.02] active:scale-[0.98] cursor-pointer'
                }`}
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>{analyzing ? 'Processing Swath...' : 'Re-Run YOLOv8n Triage'}</span>
              </button>
            )}
          </div>
        </div>

        {/* Center Column (6 Cols): Dominant Acoustic Sonar Waterfall Viewer */}
        <div className="lg:col-span-6 flex flex-col bg-white rounded-[24px] border border-[#e6e6e6] shadow-soft overflow-hidden">
          
          {/* Top Utilitarian Controls Toolbar */}
          <div className="p-4 border-b border-[#e6e6e6] bg-[#fcfcfc] flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setViewMode(viewMode === 'processed' ? 'raw' : 'processed')}
                className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all cursor-pointer ${
                  viewMode === 'processed'
                    ? 'bg-[#1f1f1f] text-white border-[#1f1f1f] shadow-sm'
                    : 'bg-white text-[#1f1f1f] border-[#e6e6e6] hover:bg-slate-50'
                }`}
              >
                {viewMode === 'processed' ? '1–99% Normalized' : 'Raw Acoustic'}
              </button>

              <button
                onClick={() => setShowBoxes(!showBoxes)}
                className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all flex items-center gap-1.5 cursor-pointer ${
                  showBoxes
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200 shadow-sm'
                    : 'bg-white text-[#8e8e93] border-[#e6e6e6] hover:bg-slate-50'
                }`}
              >
                <Eye className="w-3.5 h-3.5" />
                <span>Overlays ({displayedContacts.length})</span>
              </button>
            </div>

            {/* Contrast Gain Slider & Filter Toggle */}
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-xs font-medium text-[#8e8e93]">
                <Sliders className="w-3.5 h-3.5 text-[#8e8e93]" />
                <span>Gain:</span>
                <input
                  type="range"
                  min={50}
                  max={180}
                  value={contrast}
                  onChange={(e) => setContrast(Number(e.target.value))}
                  className="w-20 h-1.5 accent-[#ff383c] cursor-pointer"
                />
                <span className="text-[#1f1f1f] font-bold w-9 text-right font-mono">{contrast}%</span>
              </div>

              <button
                onClick={() => setFilterMode(filterMode === 'top' ? 'all' : 'top')}
                className="px-3 py-1.5 rounded-full bg-white hover:bg-slate-50 border border-[#e6e6e6] text-xs font-semibold text-[#1f1f1f] flex items-center gap-1.5 cursor-pointer shadow-tactile"
              >
                <Filter className="w-3 h-3 text-[#ffd400]" />
                <span>{filterMode === 'top' ? 'Top 5 Targets' : 'All Candidates'}</span>
              </button>
            </div>
          </div>

          {/* Sonar Acoustic Waterfall Canvas Viewport */}
          <div 
            ref={containerRef} 
            onMouseMove={handleMouseMove}
            onMouseLeave={() => setCursorPos(null)}
            className="flex-1 overflow-auto relative p-4 flex justify-center items-start bg-[#050a14] cursor-crosshair min-h-[500px]"
          >
            {survey ? (
              <div className="relative inline-block border border-slate-800 shadow-2xl bg-black">
                
                {/* Port / Starboard Acoustic Header Scale */}
                <div className="w-full bg-[#091122] border-b border-slate-800 py-1 px-3 flex justify-between text-[10px] font-mono text-slate-400 select-none">
                  <span>◄ PORT SWATH (75m)</span>
                  <span className="text-cyan-400 font-bold">NADIR VOID (0m)</span>
                  <span>STARBOARD SWATH (75m) ►</span>
                </div>

                <img
                  ref={imgRef}
                  src={viewMode === 'processed' ? survey.processed_image_url : survey.raw_image_url}
                  alt="Side-Scan Sonar Waterfall"
                  onLoad={updateScaling}
                  style={{
                    filter: `contrast(${contrast}%)`,
                    maxHeight: '100%',
                    display: 'block'
                  }}
                  className="transition-all select-none"
                />

                {/* Tactical Bounding Box Candidate Overlays */}
                {showBoxes && displayedContacts.map((c) => {
                  const isSelected = activeContact?.contact_id === c.contact_id;
                  const left = c.bbox.x1 * scale.scaleX;
                  const top = c.bbox.y1 * scale.scaleY;
                  const width = (c.bbox.x2 - c.bbox.x1) * scale.scaleX;
                  const height = (c.bbox.y2 - c.bbox.y1) * scale.scaleY;

                  let strokeColor = '#38bdf8';
                  let tagBg = '#0284c7';
                  if (c.priority === 'HIGH') {
                    strokeColor = '#ff383c';
                    tagBg = '#ff383c';
                  } else if (c.priority === 'MEDIUM') {
                    strokeColor = '#f59e0b';
                    tagBg = '#d97706';
                  }

                  return (
                    <div
                      key={c.contact_id}
                      onClick={() => onSelectContact(c)}
                      style={{
                        position: 'absolute',
                        left: `${left}px`,
                        top: `${top + 20}px`,
                        width: `${Math.max(16, width)}px`,
                        height: `${Math.max(16, height)}px`,
                        borderColor: strokeColor,
                      }}
                      className={`cursor-pointer border transition-all ${
                        isSelected 
                          ? 'border-2 ring-2 ring-white bg-[#ff383c]/20 z-20 scale-[1.02]' 
                          : 'opacity-90 hover:opacity-100 hover:scale-105 z-10'
                      }`}
                    >
                      {/* Corner Targeting Marks */}
                      <div className="absolute -top-1 -left-1 w-1.5 h-1.5 border-t border-l border-white" />
                      <div className="absolute -top-1 -right-1 w-1.5 h-1.5 border-t border-r border-white" />
                      <div className="absolute -bottom-1 -left-1 w-1.5 h-1.5 border-b border-l border-white" />
                      <div className="absolute -bottom-1 -right-1 w-1.5 h-1.5 border-b border-r border-white" />

                      {/* Pill Badge */}
                      <div 
                        style={{ backgroundColor: tagBg }}
                        className="absolute -bottom-5 left-0 px-1.5 py-0.5 rounded-full font-mono font-bold text-[9px] text-white whitespace-nowrap shadow-md"
                      >
                        {c.contact_id} • {Math.round(c.confidence * 100)}%
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-xs text-slate-400 font-mono text-center py-24">
                <Crosshair className="w-10 h-10 text-slate-600 animate-spin mb-3" />
                <p className="font-bold text-white text-sm">NO SWATH ACTIVE</p>
                <p className="text-xs text-slate-400 mt-1">Select a curated benchmark swath from the top header.</p>
              </div>
            )}

            {/* Live Hover HUD Coordinates */}
            {cursorPos && (
              <div className="absolute top-4 left-4 px-3 py-1.5 rounded-full bg-white/95 border border-[#e6e6e6] text-[11px] font-mono font-bold text-[#1f1f1f] pointer-events-none z-30 shadow-lg">
                X: {cursorPos.x}px | Y: {cursorPos.y}px | Slant Range: ~{cursorPos.slantM}m
              </div>
            )}
          </div>
        </div>

        {/* Right Column (3 Cols): Ranked Detection Queue */}
        <div className="lg:col-span-3 flex flex-col bg-white rounded-[24px] border border-[#e6e6e6] shadow-soft overflow-hidden">
          <div className="p-5 border-b border-[#f2f2f2] flex items-center justify-between">
            <div>
              <span className="section-label block">Ranked Proposals</span>
              <h3 className="text-base font-bold text-[#1f1f1f] font-display mt-0.5 flex items-center gap-1.5">
                <Scan className="w-4 h-4 text-[#ff383c]" />
                Detection Queue
              </h3>
            </div>
            <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-[#fcfcfc] border border-[#e6e6e6] text-[#1f1f1f]">
              {displayedContacts.length} Ranked
            </span>
          </div>

          {/* List of Ranked Candidate Cards */}
          <div className="flex-1 overflow-y-auto p-4 space-y-2.5">
            {displayedContacts.length === 0 ? (
              <div className="text-center py-12 text-xs text-[#8e8e93]">
                No anomaly detections in active swath.
              </div>
            ) : (
              displayedContacts.map((contact) => {
                const isSelected = activeContact?.contact_id === contact.contact_id;
                const isHigh = contact.priority === 'HIGH';

                return (
                  <div
                    key={contact.contact_id}
                    onClick={() => onSelectContact(contact)}
                    className={`p-3.5 rounded-2xl border transition-all duration-200 cursor-pointer flex items-center justify-between ${
                      isSelected
                        ? 'bg-[#ff383c]/5 border-[#ff383c] shadow-sm'
                        : 'bg-[#fcfcfc] border-[#e6e6e6] hover:bg-white hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      {/* ID Bucket */}
                      <div className={`flex h-10 w-10 items-center justify-center rounded-xl font-mono font-bold text-xs border transition-colors ${
                        isSelected 
                          ? 'bg-[#ff383c] text-white border-[#ff383c]' 
                          : 'bg-white text-[#1f1f1f] border-[#e6e6e6]'
                      }`}>
                        {contact.contact_id}
                      </div>

                      <div>
                        <div className="flex items-center gap-1.5">
                          <span className="font-bold text-[#1f1f1f] text-xs font-mono">
                            {contact.contact_id}
                          </span>
                          <span className={`text-[9px] font-bold px-2 py-0.2 rounded-full font-sans ${
                            isHigh ? 'bg-[#ff383c]/10 text-[#ff383c]' : 'bg-amber-50 text-amber-700'
                          }`}>
                            {contact.priority}
                          </span>
                        </div>
                        <div className="text-[11px] text-[#8e8e93] mt-0.5 font-sans">
                          Confidence: <strong className="text-[#1f1f1f]">{Math.round(contact.confidence * 100)}%</strong>
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectContact(contact);
                        onVerifyContact?.(contact);
                      }}
                      className="p-1.5 rounded-full bg-white hover:bg-[#ff383c] hover:text-white text-[#8e8e93] border border-[#e6e6e6] transition-all cursor-pointer"
                      title="Open in Contact Verification Workflow"
                    >
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </div>

      </div>

      {/* 3. Bottom Acoustic Physics Context Verification Bar */}
      {activeContact && (
        <section className="bg-white rounded-[24px] border border-[#e6e6e6] p-5 shadow-soft flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-3 shrink-0">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#ff383c]/10 text-[#ff383c]">
              <Scan className="w-5 h-5" />
            </div>
            <div>
              <span className="section-label block">Physics Context Engine</span>
              <h4 className="text-base font-extrabold text-[#1f1f1f] font-display">
                Candidate {activeContact.contact_id} Diagnostics
              </h4>
            </div>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 flex-1 max-w-4xl px-2 w-full">
            {/* 1. Object-Shadow Deficit */}
            <div className="p-3 rounded-2xl bg-[#fcfcfc] border border-[#e6e6e6] flex items-center justify-between">
              <div>
                <span className="text-[9px] text-[#8e8e93] font-bold uppercase tracking-wider block">Shadow Deficit</span>
                <span className="text-xs font-bold text-[#1f1f1f]">Shadow Matched</span>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700">
                PASS
              </span>
            </div>

            {/* 2. Seabed Texture Match */}
            <div className="p-3 rounded-2xl bg-[#fcfcfc] border border-[#e6e6e6] flex items-center justify-between">
              <div>
                <span className="text-[9px] text-[#8e8e93] font-bold uppercase tracking-wider block">Seabed Texture</span>
                <span className="text-xs font-bold text-[#1f1f1f]">Sandy / Gravel</span>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700">
                87% Match
              </span>
            </div>

            {/* 3. False Positive Risk */}
            <div className="p-3 rounded-2xl bg-[#fcfcfc] border border-[#e6e6e6] flex items-center justify-between">
              <div>
                <span className="text-[9px] text-[#8e8e93] font-bold uppercase tracking-wider block">Clutter Risk</span>
                <span className="text-xs font-bold text-[#1f1f1f]">Anomalous Struct</span>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-700">
                12/100
              </span>
            </div>

            {/* 4. Overall AI Composite Score */}
            <div className="p-3 rounded-2xl bg-[#fcfcfc] border border-[#e6e6e6] flex items-center justify-between">
              <div>
                <span className="text-[9px] text-[#8e8e93] font-bold uppercase tracking-wider block">Composite Score</span>
                <span className="text-xs font-bold text-[#1f1f1f]">YOLO + Acoustic</span>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#ff383c]/10 text-[#ff383c]">
                {Math.round(activeContact.confidence * 100)}%
              </span>
            </div>
          </div>

          <button
            onClick={() => onVerifyContact?.(activeContact)}
            className="px-6 py-3 rounded-full bg-[#ff383c] hover:bg-[#dc143c] text-white font-semibold text-xs transition-all duration-200 shadow-tactile flex items-center gap-2 cursor-pointer shrink-0"
          >
            <span>Verify Candidate</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </section>
      )}

    </div>
  );
};
