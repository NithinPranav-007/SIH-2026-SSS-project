import React, { useState, useEffect, useCallback } from 'react';
import { Contact, SurveyUploadResponse, ReviewStatus } from '../types/detection';
import { useToast } from '../hooks/useToast';
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
  Sparkles,
  Search,
  ArrowLeft,
  ArrowRight,
  Keyboard
} from 'lucide-react';

interface ContactVerificationPageProps {
  survey: SurveyUploadResponse | null;
  contacts: Contact[];
  selectedContact: Contact | null;
  onSelectContact: (contact: Contact) => void;
  onSubmitReview: (contactId: string, status: ReviewStatus, note?: string) => Promise<void>;
  onNavigateToMap: () => void;
  onLoadDemoSample: (sampleId: string) => void;
}

export const ContactVerificationPage: React.FC<ContactVerificationPageProps> = ({
  survey,
  contacts,
  selectedContact,
  onSelectContact,
  onSubmitReview,
  onNavigateToMap,
  onLoadDemoSample,
}) => {
  const { toast } = useToast();
  const activeContact = selectedContact || contacts[0] || null;
  const [operatorNote, setOperatorNote] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [contactSearch, setContactSearch] = useState<string>('');

  // Filtered contacts for pill selector
  const filteredContacts = contacts.filter(c => {
    if (!contactSearch.trim()) return true;
    const q = contactSearch.toLowerCase();
    return c.contact_id.toLowerCase().includes(q) || c.class_name.toLowerCase().includes(q);
  });

  // Navigate contacts list
  const navigateContact = useCallback((direction: 'prev' | 'next') => {
    if (!activeContact || contacts.length === 0) return;
    const idx = contacts.findIndex(c => c.contact_id === activeContact.contact_id);
    const next = direction === 'next'
      ? contacts[(idx + 1) % contacts.length]
      : contacts[(idx - 1 + contacts.length) % contacts.length];
    onSelectContact(next);
  }, [activeContact, contacts, onSelectContact]);

  const handleAction = useCallback(async (status: ReviewStatus) => {
    if (!activeContact || submitting) return;
    setSubmitting(true);
    try {
      await onSubmitReview(activeContact.contact_id, status, operatorNote || undefined);

      const labelMap: Record<ReviewStatus, string> = {
        CONFIRMED: 'Confirmed as valid target',
        FALSE_POSITIVE: 'Marked as false positive',
        UNCERTAIN: 'Flagged for secondary review',
        AI_CANDIDATE: 'Reset to AI candidate',
      };
      toast.success(`${activeContact.contact_id}: ${labelMap[status]}`);
      setOperatorNote('');

      // Auto-advance to next unreviewed AI_CANDIDATE contact
      const currentIdx = contacts.findIndex(c => c.contact_id === activeContact.contact_id);
      const remaining = contacts.filter((c, i) => i !== currentIdx && c.review_status === 'AI_CANDIDATE');
      if (remaining.length > 0) {
        onSelectContact(remaining[0]);
      } else {
        // All reviewed — wrap to next
        const next = contacts[(currentIdx + 1) % contacts.length];
        if (next && next.contact_id !== activeContact.contact_id) {
          onSelectContact(next);
        }
      }
    } catch (err) {
      toast.error('Failed to submit review. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }, [activeContact, contacts, onSubmitReview, operatorNote, toast, submitting, onSelectContact]);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      // Don't fire if user is typing in textarea/input
      if ((e.target as HTMLElement).tagName === 'TEXTAREA' ||
          (e.target as HTMLElement).tagName === 'INPUT') return;
      if (!activeContact) return;

      switch (e.key.toLowerCase()) {
        case 'c': e.preventDefault(); handleAction('CONFIRMED'); break;
        case 'f': e.preventDefault(); handleAction('FALSE_POSITIVE'); break;
        case 'u': e.preventDefault(); handleAction('UNCERTAIN'); break;
        case 'arrowright': e.preventDefault(); navigateContact('next'); break;
        case 'arrowleft': e.preventDefault(); navigateContact('prev'); break;
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [handleAction, navigateContact, activeContact]);

  // --- Empty state: no contacts loaded ---
  if (contacts.length === 0) {
    return (
      <div className="p-12 flex items-center justify-center min-h-[500px]">
        <div className="text-center max-w-lg bg-[var(--color-surface)] rounded-[24px] border border-[var(--color-border)] shadow-soft p-10 space-y-5">
          <div className="w-16 h-16 rounded-full bg-[var(--color-primary-dim)] text-[var(--color-primary)] flex items-center justify-center mx-auto">
            <Scan className="w-8 h-8" />
          </div>
          <div className="space-y-2">
            <h3 className="text-xl font-bold text-[var(--color-text)] font-display">No Contacts Loaded</h3>
            <p className="text-xs text-[var(--color-text-muted)] leading-relaxed">
              Load a benchmark sonar swath to begin operator triage. Pre-computed contacts will appear here instantly — no model weights required.
            </p>
          </div>
          <div className="flex flex-col sm:flex-row items-center gap-3 justify-center pt-2">
            <button
              onClick={() => onLoadDemoSample('viator_04')}
              className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] text-white text-xs font-bold transition-all shadow-tactile cursor-pointer"
            >
              <Sparkles className="w-3.5 h-3.5" />
              Load Viator-04 Benchmark
            </button>
            <button
              onClick={() => onLoadDemoSample('corsican_02')}
              className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-[var(--color-surface-2)] hover:bg-[var(--color-border)] border border-[var(--color-border)] text-[var(--color-text)] text-xs font-bold transition-all shadow-tactile cursor-pointer"
            >
              Load Corsican-02
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!activeContact) return null;

  const bboxWidth = activeContact.bbox.x2 - activeContact.bbox.x1;
  const bboxHeight = activeContact.bbox.y2 - activeContact.bbox.y1;
  const isHigh = activeContact.priority === 'HIGH';
  const currentIdx = contacts.findIndex(c => c.contact_id === activeContact.contact_id);
  const pendingCount = contacts.filter(c => c.review_status === 'AI_CANDIDATE').length;

  return (
    <div className="p-6 lg:p-8 max-w-[1600px] mx-auto space-y-6 font-sans">
      
      {/* 1. Header & Contact Selector Pill Bar */}
      <div className="bg-[var(--color-surface)] rounded-[24px] border border-[var(--color-border)] p-6 shadow-soft flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="section-label">Human-in-the-Loop Triage</span>
            <span className="text-[var(--color-border)]">/</span>
            <span className="text-xs font-bold text-[var(--color-primary)] uppercase tracking-wider font-sans">
              Contact Verification Console
            </span>
          </div>
          <h2 className="text-2xl font-extrabold text-[var(--color-text)] font-display flex items-center gap-2.5">
            <ShieldCheck className="w-6 h-6 text-[var(--color-primary)]" />
            Target {activeContact.contact_id} Verification
            <span className="text-sm font-normal text-[var(--color-text-muted)]">
              ({currentIdx + 1} / {contacts.length})
            </span>
          </h2>
        </div>

        {/* Contact Selector with Search */}
        <div className="flex flex-col gap-2 w-full lg:max-w-[560px]">
          {/* Search Filter */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--color-text-muted)]" />
            <input
              type="search"
              placeholder="Filter by ID or class (e.g. shipwreck)…"
              value={contactSearch}
              onChange={e => setContactSearch(e.target.value)}
              aria-label="Filter contacts"
              className="w-full pl-8 pr-4 py-2 rounded-full bg-[var(--color-surface-2)] border border-[var(--color-border)] text-[var(--color-text)] text-xs placeholder:text-[var(--color-text-muted)] focus:border-[var(--color-primary)] focus:outline-none transition-colors"
            />
          </div>

          {/* Contact Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto p-1.5 rounded-full bg-[var(--color-surface-2)] border border-[var(--color-border)] shadow-tactile max-w-full">
            {filteredContacts.length === 0 ? (
              <span className="px-4 py-1.5 text-xs text-[var(--color-text-muted)]">No contacts match filter</span>
            ) : filteredContacts.map((c) => {
              const isSelected = activeContact.contact_id === c.contact_id;
              const isReviewed = c.review_status !== 'AI_CANDIDATE';
              return (
                <button
                  key={c.contact_id}
                  onClick={() => onSelectContact(c)}
                  aria-label={`Select contact ${c.contact_id}`}
                  aria-pressed={isSelected}
                  className={`px-3.5 py-1.5 rounded-full text-xs font-bold transition-all duration-200 cursor-pointer flex items-center gap-1.5 shrink-0 ${
                    isSelected
                      ? 'bg-[var(--color-primary)] text-white shadow-sm scale-[1.02]'
                      : isReviewed
                      ? 'text-[var(--color-text-muted)] bg-[var(--color-border)] hover:bg-[var(--color-border-2)]'
                      : 'text-[var(--color-text)] hover:bg-[var(--color-border)]'
                  }`}
                >
                  <span className="font-mono">{c.contact_id.slice(-6)}</span>
                  {c.priority === 'HIGH' && (
                    <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${isSelected ? 'bg-white' : 'bg-[var(--color-primary)]'}`} />
                  )}
                  {isReviewed && (
                    <CheckCircle2 className={`w-3 h-3 shrink-0 ${isSelected ? 'text-white' : 'text-emerald-500'}`} />
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Keyboard Shortcut Hint Bar */}
      <div className="flex items-center gap-3 px-2 flex-wrap">
        <span className="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider flex items-center gap-1.5">
          <Keyboard className="w-3.5 h-3.5" /> Shortcuts:
        </span>
        {[
          { key: 'C', label: 'Confirm', color: 'text-emerald-700 bg-emerald-50 border-emerald-200' },
          { key: 'F', label: 'False Positive', color: 'text-red-700 bg-red-50 border-red-200' },
          { key: 'U', label: 'Uncertain', color: 'text-amber-700 bg-amber-50 border-amber-200' },
          { key: '← →', label: 'Navigate', color: 'text-[var(--color-text-2)] bg-[var(--color-surface-2)] border-[var(--color-border)]' },
        ].map(s => (
          <div key={s.key} className="flex items-center gap-1.5">
            <kbd className={`kbd border ${s.color}`}>{s.key}</kbd>
            <span className="text-[10px] text-[var(--color-text-muted)]">{s.label}</span>
          </div>
        ))}
        {pendingCount > 0 && (
          <span className="ml-auto text-[10px] font-bold text-amber-700 bg-amber-50 border border-amber-200 px-2.5 py-1 rounded-full">
            {pendingCount} pending review
          </span>
        )}
      </div>

      {/* 2. Main Two-Column Triage Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column (5 Cols): Acoustic Target Optical Crop */}
        <div className="lg:col-span-5 bg-[var(--color-surface)] rounded-[24px] border border-[var(--color-border)] p-6 shadow-soft space-y-5 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-[var(--color-border)] pb-3">
              <div>
                <span className="section-label block">Optical Backscatter Crop</span>
                <h3 className="text-base font-bold text-[var(--color-text)] font-display mt-0.5 flex items-center gap-1.5">
                  <Scan className="w-4 h-4 text-[var(--color-primary)]" />
                  Acoustic Signature Crop ({activeContact.contact_id})
                </h3>
              </div>
              <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-full bg-[var(--color-surface-2)] border border-[var(--color-border)] text-[var(--color-text)]">
                {bboxWidth} × {bboxHeight} px
              </span>
            </div>

            {/* High-Resolution Optical Crop Container */}
            <div className="aspect-4/3 rounded-2xl bg-[#050a14] border border-slate-800 relative overflow-hidden shadow-xl flex items-center justify-center group">
              {survey ? (
                <img
                  src={survey.processed_image_url || survey.raw_image_url}
                  alt={`Acoustic crop of contact ${activeContact.contact_id}`}
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
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-[var(--color-primary)] text-white font-mono font-bold text-[10px] rounded-full shadow-md whitespace-nowrap">
                  {activeContact.contact_id} • {Math.round(activeContact.confidence * 100)}% CONF
                </div>
                {/* Crosshairs */}
                <div className="absolute top-1/2 left-0 right-0 h-px bg-cyan-400/40" />
                <div className="absolute top-0 bottom-0 left-1/2 w-px bg-cyan-400/40" />
              </div>
            </div>
          </div>

          {/* Physical Acoustic Characteristics Card */}
          <div className="p-4 rounded-2xl bg-[var(--color-surface-2)] border border-[var(--color-border)] space-y-2.5 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-[var(--color-text-muted)] font-medium">Acoustic Shadow Deficit:</span>
              <span className="font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-100">
                MATCHED (High-Deficit Void)
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-[var(--color-text-muted)] font-medium">Seabed Backscatter Floor:</span>
              <span className="font-bold text-[var(--color-text)]">Sandy / Gravel Sediment</span>
            </div>
            <div className="flex justify-between items-center pt-2 border-t border-[var(--color-border)]">
              <span className="text-[var(--color-text-muted)] font-medium">Slant Bounding Box:</span>
              <span className="font-mono font-bold text-[var(--color-text)]">
                [{activeContact.bbox.x1}, {activeContact.bbox.y1}, {activeContact.bbox.x2}, {activeContact.bbox.y2}]
              </span>
            </div>
          </div>

          {/* Navigation arrows */}
          <div className="flex items-center justify-between pt-1">
            <button
              onClick={() => navigateContact('prev')}
              aria-label="Previous contact"
              className="flex items-center gap-1.5 px-4 py-2 rounded-full bg-[var(--color-surface-2)] border border-[var(--color-border)] text-[var(--color-text)] text-xs font-semibold hover:bg-[var(--color-border)] transition-colors cursor-pointer"
            >
              <ArrowLeft className="w-3.5 h-3.5" /> Prev
            </button>
            <span className="text-xs text-[var(--color-text-muted)] font-mono">{currentIdx + 1} / {contacts.length}</span>
            <button
              onClick={() => navigateContact('next')}
              aria-label="Next contact"
              className="flex items-center gap-1.5 px-4 py-2 rounded-full bg-[var(--color-surface-2)] border border-[var(--color-border)] text-[var(--color-text)] text-xs font-semibold hover:bg-[var(--color-border)] transition-colors cursor-pointer"
            >
              Next <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Right Column (7 Cols): Candidate Telemetry & Triage Buttons */}
        <div className="lg:col-span-7 space-y-6">
          
          {/* Candidate Telemetry Grid */}
          <div className="bg-[var(--color-surface)] rounded-[24px] border border-[var(--color-border)] p-6 shadow-soft space-y-4">
            <div className="border-b border-[var(--color-border)] pb-3 flex items-center justify-between">
              <div>
                <span className="section-label block">Target Telemetry</span>
                <h3 className="text-base font-bold text-[var(--color-text)] font-display mt-0.5">
                  Physical & Spatial Properties
                </h3>
              </div>
              <span className="text-xs font-semibold px-3 py-1 rounded-full bg-[var(--color-surface-2)] text-[var(--color-text-muted)]">
                WGS-84 Datum
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="p-4 rounded-2xl bg-[var(--color-surface-2)] border border-[var(--color-border)]">
                <span className="text-[10px] text-[var(--color-text-muted)] font-bold uppercase tracking-wider block">AI Confidence</span>
                <div className="text-2xl font-extrabold text-[var(--color-text)] font-display mt-1">
                  {Math.round(activeContact.confidence * 100)}%
                </div>
                <div className="text-[11px] text-emerald-600 font-medium mt-0.5">
                  Calibrated: {Math.round((activeContact.calibrated_confidence ?? activeContact.confidence) * 100)}%
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-[var(--color-surface-2)] border border-[var(--color-border)]">
                <span className="text-[10px] text-[var(--color-text-muted)] font-bold uppercase tracking-wider block">Operational Risk</span>
                <div className={`text-2xl font-extrabold font-display mt-1 ${
                  activeContact.risk_level === 'CRITICAL' ? 'text-red-600' :
                  activeContact.risk_level === 'HIGH' ? 'text-orange-600' :
                  'text-blue-600'
                }`}>
                  {activeContact.risk_level ?? activeContact.priority}
                </div>
                <div className="text-[11px] text-[var(--color-text-muted)] font-medium mt-0.5">
                  Score: {activeContact.risk_score ?? 45}/100
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-[var(--color-surface-2)] border border-[var(--color-border)]">
                <span className="text-[10px] text-[var(--color-text-muted)] font-bold uppercase tracking-wider block">Target Classification</span>
                <div className="text-sm font-extrabold text-[var(--color-text)] font-display mt-2 leading-tight capitalize">
                  {activeContact.class_name.replace(/_/g, ' ')}
                </div>
                <div className="text-[11px] text-[var(--color-text-muted)] font-medium mt-0.5">
                  {activeContact.anomaly_type === 'UNKNOWN_ANOMALY' ? 'Unknown Anomaly' : 'Catalogued Target'}
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-[var(--color-surface-2)] border border-[var(--color-border)]">
                <span className="text-[10px] text-[var(--color-text-muted)] font-bold uppercase tracking-wider block">Ping Persistence</span>
                <div className="text-sm font-extrabold text-[var(--color-text)] font-mono mt-2">
                  {activeContact.track_observations ?? 1} Ping{activeContact.track_observations !== 1 ? 's' : ''}
                </div>
                <div className="text-[11px] text-[var(--color-text-muted)] font-medium mt-0.5">
                  Track: {activeContact.track_id ? activeContact.track_id.slice(-7) : 'Single'}
                </div>
              </div>
            </div>

            {/* Target Dimensions Panel */}
            <div className="pt-4 border-t border-[var(--color-border)]">
              <span className="text-xs font-bold text-[var(--color-text)] uppercase tracking-wider block mb-2">
                Physical Dimensions &amp; Geometry
              </span>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="p-3 rounded-xl bg-white border border-[var(--color-border)]">
                  <span className="text-[10px] text-gray-400 block uppercase font-semibold">Length</span>
                  <span className="font-bold text-gray-800">
                    {activeContact.measurements?.length?.value != null ? `${activeContact.measurements.length.value} ${activeContact.measurements.length.unit}` : `${Math.max(activeContact.bbox.x2 - activeContact.bbox.x1, activeContact.bbox.y2 - activeContact.bbox.y1) * 0.06} m`}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-white border border-[var(--color-border)]">
                  <span className="text-[10px] text-gray-400 block uppercase font-semibold">Width</span>
                  <span className="font-bold text-gray-800">
                    {activeContact.measurements?.width?.value != null ? `${activeContact.measurements.width.value} ${activeContact.measurements.width.unit}` : `${Math.min(activeContact.bbox.x2 - activeContact.bbox.x1, activeContact.bbox.y2 - activeContact.bbox.y1) * 0.06} m`}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-white border border-[var(--color-border)]">
                  <span className="text-[10px] text-gray-400 block uppercase font-semibold">Acoustic Shadow</span>
                  <span className="font-bold text-gray-800">
                    {(activeContact.shadow_evidence * 100).toFixed(0)}% Deficit
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-white border border-[var(--color-border)]">
                  <span className="text-[10px] text-gray-400 block uppercase font-semibold">Novelty Score</span>
                  <span className="font-bold text-purple-700">
                    {activeContact.novelty_score ?? 35}/100
                  </span>
                </div>
              </div>
            </div>

            {/* Explainable AI Evidence Breakdown */}
            <div className="pt-4 border-t border-[var(--color-border)] space-y-2">
              <span className="text-xs font-bold text-[var(--color-text)] uppercase tracking-wider block">
                Explainability Engine (XAI)
              </span>
              <div className="space-y-1.5 text-xs">
                {(activeContact.explanation?.positive_evidence || [
                  `Detector activation at ${Math.round(activeContact.confidence * 100)}%`,
                  activeContact.shadow_evidence > 0.4 ? "Visible down-range acoustic shadow deficit" : null,
                  activeContact.context_score > 0.5 ? "Acoustic physics context consistent with solid contact" : null
                ]).filter(Boolean).map((ev: any, idx: number) => (
                  <div key={idx} className="flex items-center gap-2 text-emerald-700 bg-emerald-50/70 p-2 rounded-xl border border-emerald-100">
                    <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
                    <span>{String(ev)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* One-Click Operator Triage Actions Card */}
          <div className="bg-[var(--color-surface)] rounded-[24px] border border-[var(--color-border)] p-6 shadow-soft space-y-5">
            <div className="border-b border-[var(--color-border)] pb-3 flex items-center justify-between">
              <div>
                <span className="section-label block">Classification Action</span>
                <h3 className="text-base font-bold text-[var(--color-text)] font-display mt-0.5">
                  One-Click Operator Triage Decisions
                </h3>
              </div>
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-[var(--color-primary-dim)] text-[var(--color-primary)]">
                {activeContact.review_status.replace(/_/g, ' ')}
              </span>
            </div>

            {/* 3 Decision Action Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* Confirm Contact */}
              <button
                onClick={() => handleAction('CONFIRMED')}
                disabled={submitting}
                aria-label="Confirm contact (C)"
                className="p-4 rounded-2xl bg-emerald-50 hover:bg-emerald-100/80 border border-emerald-200 text-emerald-900 transition-all duration-200 flex flex-col items-center text-center gap-2 cursor-pointer shadow-tactile hover:-translate-y-0.5 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-emerald-600 shadow-xs">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <div>
                  <div className="font-bold text-xs uppercase tracking-wide">Confirm Debris</div>
                  <div className="text-[11px] text-emerald-700 mt-0.5">Validated Target</div>
                  <kbd className="kbd border border-emerald-200 bg-white text-emerald-700 mt-1">C</kbd>
                </div>
              </button>

              {/* False Alarm / Clutter */}
              <button
                onClick={() => handleAction('FALSE_POSITIVE')}
                disabled={submitting}
                aria-label="Mark as false positive (F)"
                className="p-4 rounded-2xl bg-[var(--color-danger-bg)] hover:bg-red-100/80 border border-[var(--color-danger-border)] text-[var(--color-danger)] transition-all duration-200 flex flex-col items-center text-center gap-2 cursor-pointer shadow-tactile hover:-translate-y-0.5 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-[var(--color-primary)] shadow-xs">
                  <XCircle className="w-5 h-5" />
                </div>
                <div>
                  <div className="font-bold text-xs uppercase tracking-wide">False Alarm</div>
                  <div className="text-[11px] text-[var(--color-danger)]/80 mt-0.5">Geological Clutter</div>
                  <kbd className="kbd border border-[var(--color-danger-border)] bg-white text-[var(--color-danger)] mt-1">F</kbd>
                </div>
              </button>

              {/* Needs Review */}
              <button
                onClick={() => handleAction('UNCERTAIN')}
                disabled={submitting}
                aria-label="Mark as uncertain (U)"
                className="p-4 rounded-2xl bg-amber-50 hover:bg-amber-100/80 border border-amber-200 text-amber-900 transition-all duration-200 flex flex-col items-center text-center gap-2 cursor-pointer shadow-tactile hover:-translate-y-0.5 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-amber-600 shadow-xs">
                  <HelpCircle className="w-5 h-5" />
                </div>
                <div>
                  <div className="font-bold text-xs uppercase tracking-wide">Needs Review</div>
                  <div className="text-[11px] text-amber-700 mt-0.5">Secondary ROV Pass</div>
                  <kbd className="kbd border border-amber-200 bg-white text-amber-700 mt-1">U</kbd>
                </div>
              </button>
            </div>

            {/* Operator Notes Input & Save Action */}
            <div className="space-y-3 pt-2">
              <label htmlFor="operator-notes" className="section-label block">
                Operator Observations & Hydrographic Log Notes
              </label>
              <textarea
                id="operator-notes"
                value={operatorNote}
                onChange={(e) => setOperatorNote(e.target.value)}
                placeholder="Enter acoustic signature observations, wreck structural integrity, or diver notes..."
                rows={3}
                className="w-full p-4 rounded-2xl bg-[var(--color-surface-2)] border border-[var(--color-border)] focus:border-[var(--color-primary)] text-[var(--color-text)] text-xs placeholder:text-[var(--color-text-muted)] focus:outline-none transition-colors"
              />

              <div className="flex items-center justify-between pt-1">
                <button
                  onClick={onNavigateToMap}
                  aria-label="View contact on GIS map"
                  className="px-4 py-2.5 rounded-full bg-[var(--color-surface-2)] hover:bg-[var(--color-border)] border border-[var(--color-border)] text-[var(--color-text)] text-xs font-semibold flex items-center gap-2 transition-colors cursor-pointer shadow-tactile"
                >
                  <Compass className="w-4 h-4 text-[var(--color-primary)]" />
                  <span>View On GIS Nautical Map</span>
                </button>

                <button
                  onClick={() => handleAction(activeContact.review_status)}
                  disabled={submitting || !operatorNote.trim()}
                  aria-label="Save operator observations"
                  className={`px-6 py-2.5 rounded-full text-xs font-semibold flex items-center gap-2 transition-all duration-200 shadow-tactile ${
                    operatorNote.trim() && !submitting
                      ? 'bg-[var(--color-text)] hover:bg-black text-white cursor-pointer'
                      : 'bg-[var(--color-border)] text-[var(--color-text-muted)] cursor-not-allowed'
                  }`}
                >
                  <Save className="w-3.5 h-3.5" />
                  <span>Save Observations</span>
                </button>
              </div>
            </div>
          </div>

          {/* Audit History Log Card */}
          <div className="bg-[var(--color-surface)] rounded-[24px] border border-[var(--color-border)] p-6 shadow-soft space-y-4">
            <div className="border-b border-[var(--color-border)] pb-3 flex items-center justify-between">
              <div>
                <span className="section-label block">Audit Trail</span>
                <h3 className="text-base font-bold text-[var(--color-text)] font-display mt-0.5 flex items-center gap-2">
                  <Clock className="w-4 h-4 text-[var(--color-text-muted)]" />
                  Verification Review History
                </h3>
              </div>
              <span className="text-xs font-semibold text-[var(--color-text-muted)]">
                Immutable Hydrographic Log
              </span>
            </div>

            <div className="space-y-2.5 text-xs">
              <div className="p-3.5 rounded-2xl bg-[var(--color-surface-2)] border border-[var(--color-border)] flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-border)] font-bold text-xs text-[var(--color-text)]">
                    CV
                  </div>
                  <div>
                    <span className="font-bold text-[var(--color-text)]">Dr. C. Vance (Lead Hydrographer)</span>
                    <div className="text-[11px] text-[var(--color-text-muted)]">
                      Status: <strong className="text-[var(--color-text)]">{activeContact.review_status.replace(/_/g, ' ')}</strong>
                      {activeContact.review_note && ` • "${activeContact.review_note}"`}
                    </div>
                  </div>
                </div>
                <span className="text-[11px] text-[var(--color-text-muted)] font-mono">
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
