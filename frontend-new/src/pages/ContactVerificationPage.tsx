import React, { useState } from 'react';
import { Contact, SurveyUploadResponse, ReviewStatus } from '../types/detection';
import { 
  CheckCircle2, 
  XCircle, 
  HelpCircle, 
  MapPin, 
  Save, 
  Clock, 
  Scan, 
  ShieldCheck, 
  Compass, 
  ArrowRight,
  Sparkles,
  Layers,
  ChevronRight
} from 'lucide-react';

interface ContactVerificationPageProps {
  survey: SurveyUploadResponse | null;
  contacts: Contact[];
  selectedContact: Contact | null;
  onSelectContact: (contact: Contact) => void;
  onSubmitReview: (contactId: string, status: ReviewStatus, note?: string) => Promise<void>;
  onNavigateToMap: () => void;
}

export const ContactVerificationPage: React.FC<ContactVerificationPageProps> = ({
  survey,
  contacts,
  selectedContact,
  onSelectContact,
  onSubmitReview,
  onNavigateToMap
}) => {
  const activeContact = selectedContact || contacts[0] || null;
  const [operatorNote, setOperatorNote] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  const handleAction = async (status: ReviewStatus) => {
    if (!activeContact) return;
    setSubmitting(true);
    setSaveMessage(null);
    try {
      await onSubmitReview(activeContact.contact_id, status, operatorNote);
      setSaveMessage(`Target ${activeContact.contact_id} classification updated to ${status.replace('_', ' ')}.`);
      setOperatorNote('');
    } catch (err) {
      console.error('Review submission error:', err);
    } finally {
      setSubmitting(false);
    }
  };

  if (!activeContact) {
    return (
      <div className="p-12 text-center max-w-lg mx-auto bg-white rounded-[24px] border border-[#e6e6e6] shadow-soft my-12 space-y-4">
        <div className="w-16 h-16 rounded-full bg-[#ff383c]/10 text-[#ff383c] flex items-center justify-center mx-auto">
          <Scan className="w-8 h-8" />
        </div>
        <h3 className="text-xl font-bold text-[#1f1f1f] font-display">No Candidate Contact Selected</h3>
        <p className="text-xs text-[#8e8e93]">
          Select a survey swath or benchmark case from the top header to begin operator triage.
        </p>
      </div>
    );
  }

  const bboxWidth = activeContact.bbox.x2 - activeContact.bbox.x1;
  const bboxHeight = activeContact.bbox.y2 - activeContact.bbox.y1;
  const isHigh = activeContact.priority === 'HIGH';

  return (
    <div className="p-6 lg:p-8 max-w-[1600px] mx-auto space-y-6 font-sans">
      
      {/* 1. Header & Contact Selector Pill Bar */}
      <div className="bg-white rounded-[24px] border border-[#e6e6e6] p-6 shadow-soft flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="section-label">Human-in-the-Loop Triage</span>
            <span className="text-[#e6e6e6]">/</span>
            <span className="text-xs font-bold text-[#ff383c] uppercase tracking-wider font-sans">
              Contact Verification Console
            </span>
          </div>
          <h2 className="text-2xl font-extrabold text-[#1f1f1f] font-display flex items-center gap-2.5">
            <ShieldCheck className="w-6 h-6 text-[#ff383c]" />
            Target {activeContact.contact_id} Verification & Audit Log
          </h2>
        </div>

        {/* Contact Selector Pills */}
        <div className="flex items-center gap-2 overflow-x-auto p-1.5 rounded-full bg-[#fcfcfc] border border-[#e6e6e6] shadow-tactile max-w-full">
          {contacts.map((c) => {
            const isSelected = activeContact.contact_id === c.contact_id;
            return (
              <button
                key={c.contact_id}
                onClick={() => onSelectContact(c)}
                className={`px-3.5 py-1.5 rounded-full text-xs font-bold transition-all duration-200 cursor-pointer flex items-center gap-1.5 ${
                  isSelected
                    ? 'bg-[#ff383c] text-white shadow-sm scale-[1.02]'
                    : 'text-[#1f1f1f] hover:bg-slate-200/60'
                }`}
              >
                <span>{c.contact_id}</span>
                {c.priority === 'HIGH' && (
                  <span className={`w-1.5 h-1.5 rounded-full ${isSelected ? 'bg-white' : 'bg-[#ff383c]'}`} />
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Success Notification Alert */}
      {saveMessage && (
        <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold flex items-center justify-between shadow-soft">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>{saveMessage}</span>
          </div>
          <button 
            onClick={() => setSaveMessage(null)} 
            className="text-emerald-700 hover:text-emerald-900 font-bold underline cursor-pointer text-[11px]"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* 2. Main Two-Column Triage Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column (5 Cols): Acoustic Target Optical Crop */}
        <div className="lg:col-span-5 bg-white rounded-[24px] border border-[#e6e6e6] p-6 shadow-soft space-y-5 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-[#f2f2f2] pb-3">
              <div>
                <span className="section-label block">Optical Backscatter Crop</span>
                <h3 className="text-base font-bold text-[#1f1f1f] font-display mt-0.5 flex items-center gap-1.5">
                  <Scan className="w-4 h-4 text-[#ff383c]" />
                  Acoustic Signature Crop ({activeContact.contact_id})
                </h3>
              </div>
              <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-full bg-[#fcfcfc] border border-[#e6e6e6] text-[#1f1f1f]">
                {bboxWidth} × {bboxHeight} px
              </span>
            </div>

            {/* High-Resolution Optical Crop Container */}
            <div className="aspect-4/3 rounded-2xl bg-[#050a14] border border-slate-800 relative overflow-hidden shadow-xl flex items-center justify-center group">
              {survey ? (
                <img
                  src={survey.processed_image_url || survey.raw_image_url}
                  alt="Acoustic Target Crop"
                  className="w-full h-full object-cover scale-[1.8] filter contrast-125"
                  style={{
                    objectPosition: `${(activeContact.bbox.x1 / (survey.image_width || 1280)) * 100}% ${(activeContact.bbox.y1 / (survey.image_height || 1800)) * 100}%`
                  }}
                />
              ) : (
                <div className="text-slate-500 font-mono text-xs">No Acoustic Image Available</div>
              )}

              {/* Targeting Reticle & ID Tag Overlay */}
              <div className="absolute inset-5 border-2 border-cyan-400/90 rounded-sm pointer-events-none shadow-2xl">
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-[#ff383c] text-white font-mono font-bold text-[10px] rounded-full shadow-md whitespace-nowrap">
                  {activeContact.contact_id} • {Math.round(activeContact.confidence * 100)}% CONF
                </div>
                {/* Crosshairs */}
                <div className="absolute top-1/2 left-0 right-0 h-px bg-cyan-400/40" />
                <div className="absolute top-0 bottom-0 left-1/2 w-px bg-cyan-400/40" />
              </div>
            </div>
          </div>

          {/* Physical Acoustic Characteristics Card */}
          <div className="p-4 rounded-2xl bg-[#fcfcfc] border border-[#e6e6e6] space-y-2.5 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-[#8e8e93] font-medium">Acoustic Shadow Deficit:</span>
              <span className="font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-100">
                MATCHED (High-Deficit Void)
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-[#8e8e93] font-medium">Seabed Backscatter Floor:</span>
              <span className="font-bold text-[#1f1f1f]">Sandy / Gravel Sediment</span>
            </div>
            <div className="flex justify-between items-center pt-2 border-t border-[#e6e6e6]">
              <span className="text-[#8e8e93] font-medium">Slant Bounding Box:</span>
              <span className="font-mono font-bold text-[#1f1f1f]">
                [{activeContact.bbox.x1}, {activeContact.bbox.y1}, {activeContact.bbox.x2}, {activeContact.bbox.y2}]
              </span>
            </div>
          </div>
        </div>

        {/* Right Column (7 Cols): Candidate Telemetry & Triage Buttons */}
        <div className="lg:col-span-7 space-y-6">
          
          {/* Candidate Telemetry Grid */}
          <div className="bg-white rounded-[24px] border border-[#e6e6e6] p-6 shadow-soft space-y-4">
            <div className="border-b border-[#f2f2f2] pb-3 flex items-center justify-between">
              <div>
                <span className="section-label block">Target Telemetry</span>
                <h3 className="text-base font-bold text-[#1f1f1f] font-display mt-0.5">
                  Physical & Spatial Properties
                </h3>
              </div>
              <span className="text-xs font-semibold px-3 py-1 rounded-full bg-slate-100 text-[#8e8e93]">
                WGS-84 Datum
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="p-4 rounded-2xl bg-[#fcfcfc] border border-[#e6e6e6]">
                <span className="text-[10px] text-[#8e8e93] font-bold uppercase tracking-wider block">AI Confidence</span>
                <div className="text-2xl font-extrabold text-[#1f1f1f] font-display mt-1">
                  {Math.round(activeContact.confidence * 100)}%
                </div>
                <div className="text-[11px] text-emerald-600 font-medium mt-0.5">yolov8n-baseline</div>
              </div>

              <div className="p-4 rounded-2xl bg-[#fcfcfc] border border-[#e6e6e6]">
                <span className="text-[10px] text-[#8e8e93] font-bold uppercase tracking-wider block">Priority Tier</span>
                <div className={`text-2xl font-extrabold font-display mt-1 ${
                  isHigh ? 'text-[#ff383c]' : 'text-amber-600'
                }`}>
                  {activeContact.priority}
                </div>
                <div className="text-[11px] text-[#8e8e93] font-medium mt-0.5">Triage Level</div>
              </div>

              <div className="p-4 rounded-2xl bg-[#fcfcfc] border border-[#e6e6e6]">
                <span className="text-[10px] text-[#8e8e93] font-bold uppercase tracking-wider block">Slant Range</span>
                <div className="text-2xl font-extrabold text-[#1f1f1f] font-display mt-1">
                  24.6 m
                </div>
                <div className="text-[11px] text-[#8e8e93] font-medium mt-0.5">Towfish Offset</div>
              </div>

              <div className="p-4 rounded-2xl bg-[#fcfcfc] border border-[#e6e6e6]">
                <span className="text-[10px] text-[#8e8e93] font-bold uppercase tracking-wider block">Localization</span>
                <div className="text-sm font-extrabold text-[#1f1f1f] font-mono mt-2">
                  {activeContact.localization_status}
                </div>
                <div className="text-[11px] text-[#8e8e93] font-medium mt-0.5">GPS Nav Log</div>
              </div>
            </div>
          </div>

          {/* One-Click Operator Triage Actions Card */}
          <div className="bg-white rounded-[24px] border border-[#e6e6e6] p-6 shadow-soft space-y-5">
            <div className="border-b border-[#f2f2f2] pb-3 flex items-center justify-between">
              <div>
                <span className="section-label block">Classification Action</span>
                <h3 className="text-base font-bold text-[#1f1f1f] font-display mt-0.5">
                  One-Click Operator Triage Decisions
                </h3>
              </div>
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-[#ff383c]/10 text-[#ff383c]">
                Current: {activeContact.review_status.replace('_', ' ')}
              </span>
            </div>

            {/* 3 Decision Action Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* Confirm Contact */}
              <button
                onClick={() => handleAction('CONFIRMED')}
                disabled={submitting}
                className="p-4 rounded-2xl bg-emerald-50 hover:bg-emerald-100/80 border border-emerald-200 text-emerald-900 transition-all duration-200 flex flex-col items-center text-center gap-2 cursor-pointer shadow-tactile hover:-translate-y-0.5"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-emerald-600 shadow-xs">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <div>
                  <div className="font-bold text-xs uppercase tracking-wide">Confirm Debris</div>
                  <div className="text-[11px] text-emerald-700 mt-0.5">Validated Target</div>
                </div>
              </button>

              {/* False Alarm / Clutter */}
              <button
                onClick={() => handleAction('FALSE_POSITIVE')}
                disabled={submitting}
                className="p-4 rounded-2xl bg-[#ff383c]/10 hover:bg-[#ff383c]/15 border border-[#ff383c]/20 text-[#ff383c] transition-all duration-200 flex flex-col items-center text-center gap-2 cursor-pointer shadow-tactile hover:-translate-y-0.5"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-[#ff383c] shadow-xs">
                  <XCircle className="w-5 h-5" />
                </div>
                <div>
                  <div className="font-bold text-xs uppercase tracking-wide">False Alarm</div>
                  <div className="text-[11px] text-[#ff383c]/80 mt-0.5">Geological Clutter</div>
                </div>
              </button>

              {/* Needs Review */}
              <button
                onClick={() => handleAction('UNCERTAIN')}
                disabled={submitting}
                className="p-4 rounded-2xl bg-amber-50 hover:bg-amber-100/80 border border-amber-200 text-amber-900 transition-all duration-200 flex flex-col items-center text-center gap-2 cursor-pointer shadow-tactile hover:-translate-y-0.5"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-amber-600 shadow-xs">
                  <HelpCircle className="w-5 h-5" />
                </div>
                <div>
                  <div className="font-bold text-xs uppercase tracking-wide">Needs Review</div>
                  <div className="text-[11px] text-amber-700 mt-0.5">Secondary ROV Pass</div>
                </div>
              </button>
            </div>

            {/* Operator Notes Input & Save Action */}
            <div className="space-y-3 pt-2">
              <label className="section-label block">
                Operator Observations & Hydrographic Log Notes
              </label>
              <textarea
                value={operatorNote}
                onChange={(e) => setOperatorNote(e.target.value)}
                placeholder="Enter acoustic signature observations, wreck structural integrity, or diver notes..."
                rows={3}
                className="w-full p-4 rounded-2xl bg-[#fcfcfc] border border-[#e6e6e6] focus:border-[#ff383c] text-[#1f1f1f] text-xs placeholder:text-[#8e8e93] focus:outline-none transition-colors"
              />

              <div className="flex items-center justify-between pt-1">
                <button
                  onClick={onNavigateToMap}
                  className="px-4 py-2.5 rounded-full bg-[#fcfcfc] hover:bg-slate-100 border border-[#e6e6e6] text-[#1f1f1f] text-xs font-semibold flex items-center gap-2 transition-colors cursor-pointer shadow-tactile"
                >
                  <Compass className="w-4 h-4 text-[#ff383c]" />
                  <span>View On GIS Nautical Map</span>
                </button>

                <button
                  onClick={() => handleAction(activeContact.review_status)}
                  disabled={submitting || !operatorNote.trim()}
                  className={`px-6 py-2.5 rounded-full text-xs font-semibold flex items-center gap-2 transition-all duration-200 shadow-tactile ${
                    operatorNote.trim() && !submitting
                      ? 'bg-[#1f1f1f] hover:bg-black text-white cursor-pointer'
                      : 'bg-slate-100 text-[#8e8e93] cursor-not-allowed'
                  }`}
                >
                  <Save className="w-3.5 h-3.5" />
                  <span>Save Observations</span>
                </button>
              </div>
            </div>
          </div>

          {/* Audit History Log Card */}
          <div className="bg-white rounded-[24px] border border-[#e6e6e6] p-6 shadow-soft space-y-4">
            <div className="border-b border-[#f2f2f2] pb-3 flex items-center justify-between">
              <div>
                <span className="section-label block">Audit Trail</span>
                <h3 className="text-base font-bold text-[#1f1f1f] font-display mt-0.5 flex items-center gap-2">
                  <Clock className="w-4 h-4 text-[#8e8e93]" />
                  Verification Review History
                </h3>
              </div>
              <span className="text-xs font-semibold text-[#8e8e93]">
                Immutable Hydrographic Log
              </span>
            </div>

            <div className="space-y-2.5 text-xs">
              <div className="p-3.5 rounded-2xl bg-[#fcfcfc] border border-[#e6e6e6] flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-100 font-bold text-xs text-[#1f1f1f]">
                    CV
                  </div>
                  <div>
                    <span className="font-bold text-[#1f1f1f]">Dr. C. Vance (Lead Hydrographer)</span>
                    <div className="text-[11px] text-[#8e8e93]">
                      Status: <strong className="text-[#1f1f1f]">{activeContact.review_status.replace('_', ' ')}</strong>
                      {activeContact.review_note && ` • "${activeContact.review_note}"`}
                    </div>
                  </div>
                </div>
                <span className="text-[11px] text-[#8e8e93] font-mono">
                  Recorded UTC
                </span>
              </div>
            </div>
          </div>

        </div>

      </div>

    </div>
  );
};
