import React, { useState } from 'react';
import { Contact, NavWaypoint, SurveyUploadResponse } from '../types/detection';
import { MapView } from '../components/map/MapView';
import { 
  Compass, 
  MapPin, 
  Filter, 
  FileDown, 
  Layers, 
  ArrowRight, 
  Waves, 
  Scan,
  ShieldCheck,
  ExternalLink
} from 'lucide-react';

interface GisMappingPageProps {
  survey: SurveyUploadResponse | null;
  contacts: Contact[];
  selectedContact: Contact | null;
  navTrack: NavWaypoint[];
  onSelectContact: (contact: Contact) => void;
  onNavigateToAnalysis: () => void;
  onNavigateToVerify: () => void;
  onExportGeoJSON: () => void;
}

export const GisMappingPage: React.FC<GisMappingPageProps> = ({
  survey,
  contacts,
  selectedContact,
  navTrack,
  onSelectContact,
  onNavigateToAnalysis,
  onNavigateToVerify,
  onExportGeoJSON
}) => {
  const [filterMode, setFilterMode] = useState<'all' | 'high' | 'confirmed'>('all');

  const filteredContacts = contacts.filter(c => {
    if (filterMode === 'high') return c.priority === 'HIGH';
    if (filterMode === 'confirmed') return c.review_status === 'CONFIRMED';
    return true;
  });

  const activeContact = selectedContact || filteredContacts[0] || null;

  return (
    <div className="p-6 lg:p-8 max-w-[1700px] mx-auto space-y-6 font-sans">
      
      {/* 1. Header Toolbar */}
      <div className="bg-white rounded-[24px] border border-[#e6e6e6] p-6 shadow-soft flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="section-label">Geospatial Command</span>
            <span className="text-[#e6e6e6]">/</span>
            <span className="text-xs font-bold text-[#ff383c] uppercase tracking-wider font-sans">
              Nautical Vector GIS
            </span>
          </div>
          <h2 className="text-2xl font-extrabold text-[#1f1f1f] font-display flex items-center gap-2.5">
            <Compass className="w-6 h-6 text-[#ff383c]" />
            Spatial Mapping & Target Cleanup Planning
          </h2>
        </div>

        {/* Spatial Filter Buttons & GeoJSON Export */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 p-1 rounded-full bg-[#fcfcfc] border border-[#e6e6e6] shadow-tactile">
            <button
              onClick={() => setFilterMode('all')}
              className={`px-3.5 py-1.5 rounded-full text-xs font-bold transition-all cursor-pointer ${
                filterMode === 'all'
                  ? 'bg-[#1f1f1f] text-white shadow-sm'
                  : 'text-[#8e8e93] hover:text-[#1f1f1f]'
              }`}
            >
              All Areas ({contacts.length})
            </button>

            <button
              onClick={() => setFilterMode('high')}
              className={`px-3.5 py-1.5 rounded-full text-xs font-bold transition-all cursor-pointer ${
                filterMode === 'high'
                  ? 'bg-[#ff383c] text-white shadow-sm'
                  : 'text-[#8e8e93] hover:text-[#1f1f1f]'
              }`}
            >
              High Priority
            </button>

            <button
              onClick={() => setFilterMode('confirmed')}
              className={`px-3.5 py-1.5 rounded-full text-xs font-bold transition-all cursor-pointer ${
                filterMode === 'confirmed'
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'text-[#8e8e93] hover:text-[#1f1f1f]'
              }`}
            >
              Confirmed Only
            </button>
          </div>

          <button
            onClick={onExportGeoJSON}
            disabled={contacts.length === 0}
            className="px-5 py-2.5 rounded-full bg-[#ff383c] hover:bg-[#dc143c] text-white font-semibold text-xs transition-all duration-200 shadow-tactile flex items-center gap-2 cursor-pointer"
          >
            <FileDown className="w-4 h-4" />
            <span>Export RFC 7946 GeoJSON</span>
          </button>
        </div>
      </div>

      {/* 2. Main Map Canvas + Telemetry Drawer Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[640px]">
        
        {/* Vector Nautical Map Canvas (8 Cols) */}
        <div className="lg:col-span-8 bg-white rounded-[24px] border border-[#e6e6e6] shadow-soft overflow-hidden flex flex-col">
          <div className="p-4 border-b border-[#e6e6e6] bg-[#fcfcfc] flex items-center justify-between text-xs font-sans">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="font-bold text-[#1f1f1f]">MapLibre GL Nautical GIS</span>
              <span className="text-[#8e8e93]">• Bathymetric Ocean Contours & PostGIS Trajectory</span>
            </div>
            <span className="text-xs font-bold px-3 py-1 rounded-full bg-white border border-[#e6e6e6] text-[#8e8e93]">
              Datum: WGS-84 (EPSG:4326)
            </span>
          </div>

          <div className="flex-1 w-full min-h-[550px] relative bg-[#050a14]">
            <MapView
              contacts={filteredContacts}
              selectedContact={activeContact}
              navTrack={navTrack}
              onSelectContact={onSelectContact}
            />
          </div>
        </div>

        {/* Spatial Target Telemetry Drawer (4 Cols) */}
        <div className="lg:col-span-4 bg-white rounded-[24px] border border-[#e6e6e6] p-6 shadow-soft space-y-5 flex flex-col justify-between">
          {activeContact ? (
            <div className="space-y-5">
              <div className="border-b border-[#f2f2f2] pb-3 flex items-center justify-between">
                <div>
                  <span className="section-label block">Target Spatial Pin</span>
                  <h3 className="text-base font-bold text-[#1f1f1f] font-display mt-0.5 flex items-center gap-1.5">
                    <MapPin className="w-4 h-4 text-[#ff383c]" />
                    Candidate {activeContact.contact_id}
                  </h3>
                </div>
                <span className={`text-xs font-bold px-3 py-1 rounded-full ${
                  activeContact.priority === 'HIGH' ? 'bg-[#ff383c]/10 text-[#ff383c]' : 'bg-amber-50 text-amber-700'
                }`}>
                  {activeContact.priority} PRIORITY
                </span>
              </div>

              {/* Geographic Coordinates Card */}
              <div className="p-4 rounded-2xl bg-[#fcfcfc] border border-[#e6e6e6] space-y-2">
                <span className="section-label block">WGS-84 Geodetic Fix</span>
                {activeContact.latitude && activeContact.longitude ? (
                  <div className="space-y-1 font-mono text-xs font-bold text-emerald-700">
                    <div>LAT: {activeContact.latitude.toFixed(6)}° N</div>
                    <div>LON: {activeContact.longitude.toFixed(6)}° E</div>
                  </div>
                ) : (
                  <div className="text-xs text-amber-700 font-medium italic">
                    Coordinates unavailable (Awaiting towfish navigation log)
                  </div>
                )}
                <div className="text-[11px] text-[#8e8e93] pt-2 border-t border-[#e6e6e6] flex justify-between">
                  <span>Provenance:</span>
                  <span className="font-bold text-[#1f1f1f]">{activeContact.localization_status}</span>
                </div>
              </div>

              {/* Physical Characteristics Card */}
              <div className="p-4 rounded-2xl bg-[#fcfcfc] border border-[#e6e6e6] space-y-2.5 text-xs">
                <span className="section-label block">Target Diagnostics</span>
                <div className="flex justify-between items-center">
                  <span className="text-[#8e8e93]">Class:</span>
                  <span className="font-bold text-[#1f1f1f] font-mono">{activeContact.class_name}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[#8e8e93]">AI Confidence:</span>
                  <span className="font-bold text-[#1f1f1f] font-mono">{Math.round(activeContact.confidence * 100)}%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[#8e8e93]">Triage Status:</span>
                  <span className="font-bold text-[#ff383c] font-mono">{activeContact.review_status}</span>
                </div>
              </div>

              {/* Navigation Action Buttons */}
              <div className="space-y-2.5 pt-2 border-t border-[#f2f2f2]">
                <button
                  onClick={onNavigateToAnalysis}
                  className="w-full py-3 rounded-full bg-[#fcfcfc] hover:bg-slate-100 border border-[#e6e6e6] text-[#1f1f1f] font-semibold text-xs transition-colors flex items-center justify-center gap-2 shadow-tactile cursor-pointer"
                >
                  <Waves className="w-4 h-4 text-[#ff383c]" />
                  <span>Inspect in Sonar Waterfall</span>
                </button>

                <button
                  onClick={onNavigateToVerify}
                  className="w-full py-3 rounded-full bg-[#ff383c] hover:bg-[#dc143c] text-white font-semibold text-xs transition-colors flex items-center justify-center gap-2 shadow-tactile cursor-pointer"
                >
                  <span>Verify & Classify Target</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          ) : (
            <div className="text-center py-16 space-y-3">
              <MapPin className="w-8 h-8 text-[#8e8e93] mx-auto" />
              <div className="text-sm font-bold text-[#1f1f1f]">No Spatial Target Selected</div>
              <p className="text-xs text-[#8e8e93]">Click any spatial pin on the nautical map to view telemetry.</p>
            </div>
          )}
        </div>

      </div>

    </div>
  );
};
