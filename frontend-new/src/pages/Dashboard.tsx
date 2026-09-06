import React, { useState, useEffect, useRef } from 'react';
import { MainLayout, ActiveScreen } from '../components/layout/MainLayout';
import { useSurvey } from '../hooks/useSurvey';
import { ToastProvider } from '../hooks/useToast';
import { ToastContainer } from '../components/ui/ToastContainer';
import { ErrorBoundary } from '../components/ui/ErrorBoundary';
import { Contact } from '../types/detection';
import { DashboardPage } from './DashboardPage';
import { SonarAnalysisPage } from './SonarAnalysisPage';
import { ContactVerificationPage } from './ContactVerificationPage';
import { GisMappingPage } from './GisMappingPage';
import { AiPipelinePage } from './AiPipelinePage';
import { ReportsPage } from './ReportsPage';
import { AnomalyPage } from './AnomalyPage';
import { MLMonitorPage } from './MLMonitorPage';
import { ActiveLearningPage } from './ActiveLearningPage';
import { AnalystPage } from './AnalystPage';
import { Upload, AlertCircle, X, CheckCircle2, Play, Navigation, RefreshCw } from 'lucide-react';

export const Dashboard: React.FC = () => {
  const [activeScreen, setActiveScreen] = useState<ActiveScreen>('dashboard');
  const [showUploadModal, setShowUploadModal] = useState<boolean>(false);
  const [selectedSonarFile, setSelectedSonarFile] = useState<File | null>(null);
  const [selectedNavFile, setSelectedNavFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [isDragging, setIsDragging] = useState<boolean>(false);

  const sonarInputRef = useRef<HTMLInputElement>(null);
  const navInputRef = useRef<HTMLInputElement>(null);
  const errorDismissTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const {
    survey,
    contacts,
    selectedContact,
    navTrack,
    summary,
    loading,
    analyzing,
    error,
    setSelectedContact,
    loadSurvey,
    uploadSurvey,
    runAnalysis,
    submitReview,
    loadCuratedSample,
    setError
  } = useSurvey();

  // Auto-load Viator-04 preview on first mount (safe — no model weights needed)
  useEffect(() => {
    if (!survey && !loading) {
      loadCuratedSample('viator_04');
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-dismiss non-critical errors after 5 seconds
  useEffect(() => {
    if (error) {
      if (errorDismissTimer.current) clearTimeout(errorDismissTimer.current);
      errorDismissTimer.current = setTimeout(() => setError(null), 5000);
    }
    return () => {
      if (errorDismissTimer.current) clearTimeout(errorDismissTimer.current);
    };
  }, [error, setError]);

  const handleExportGeoJSON = () => {
    if (!survey) return;
    window.open(`/api/surveys/${survey.survey_id}/geojson`, '_blank');
  };

  const handleVerifyContact = (contact: Contact) => {
    setSelectedContact(contact);
    setActiveScreen('contact-verification');
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.name.match(/\.(png|jpg|jpeg|tif|tiff)$/i)) {
        setSelectedSonarFile(file);
      } else if (file.name.match(/\.(csv|txt|nav)$/i)) {
        setSelectedNavFile(file);
      }
    }
  };

  const handlePerformUpload = async () => {
    if (!selectedSonarFile) return;
    setIsUploading(true);
    try {
      await uploadSurvey(selectedSonarFile, selectedNavFile || undefined);
      setShowUploadModal(false);
      setSelectedSonarFile(null);
      setSelectedNavFile(null);
      setActiveScreen('sonar-analysis');
    } catch (err) {
      // Error handled by useSurvey hook
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <ToastProvider>
      <MainLayout
        activeScreen={activeScreen}
        onSelectScreen={setActiveScreen}
        survey={survey}
        summary={summary}
        contacts={contacts}
        analyzing={analyzing}
        onLoadDemoSample={loadCuratedSample}
        onCustomUploadClick={() => setShowUploadModal(true)}
        onRunAnalysis={() => runAnalysis(0.20)}
      >
        {/* System Error Banner — auto-dismisses after 5s */}
        {error && (
          <div
            role="alert"
            className="mx-8 mt-4 p-4 rounded-2xl bg-[var(--color-danger-bg)] border border-[var(--color-danger-border)] text-[var(--color-danger)] flex items-center justify-between shadow-soft"
          >
            <div className="flex items-center gap-2.5 text-xs font-semibold">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>[System Notice] {error}</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => { setError(null); loadCuratedSample('viator_04'); }}
                className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[var(--color-danger)]/10 hover:bg-[var(--color-danger)]/20 transition-colors cursor-pointer"
                aria-label="Retry loading demo sample"
              >
                <RefreshCw className="w-3 h-3" />
                Retry Demo
              </button>
              <button 
                onClick={() => setError(null)} 
                className="p-1 rounded-full hover:bg-[var(--color-danger)]/20 transition-colors cursor-pointer"
                aria-label="Dismiss error"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* Screen 1: Dashboard Overview */}
        {activeScreen === 'dashboard' && (
          <ErrorBoundary pageName="Dashboard">
            <DashboardPage
              survey={survey}
              contacts={contacts}
              onSelectScreen={setActiveScreen}
              onSelectContact={(c) => {
                setSelectedContact(c);
                setActiveScreen('sonar-analysis');
              }}
              onCustomUploadClick={() => setShowUploadModal(true)}
            />
          </ErrorBoundary>
        )}

        {/* Screen 2: Sonar Analysis Workspace */}
        {activeScreen === 'sonar-analysis' && (
          <ErrorBoundary pageName="Sonar Analysis">
            <SonarAnalysisPage
              survey={survey}
              contacts={contacts}
              selectedContact={selectedContact}
              analyzing={analyzing}
              onSelectContact={setSelectedContact}
              onRunAnalysis={() => runAnalysis(0.20)}
              onVerifyContact={handleVerifyContact}
            />
          </ErrorBoundary>
        )}

        {/* Screen 3: Contact Verification Workflow */}
        {activeScreen === 'contact-verification' && (
          <ErrorBoundary pageName="Contact Verification">
            <ContactVerificationPage
              survey={survey}
              contacts={contacts}
              selectedContact={selectedContact}
              onSelectContact={setSelectedContact}
              onSubmitReview={submitReview}
              onNavigateToMap={() => setActiveScreen('gis-mapping')}
              onLoadDemoSample={loadCuratedSample}
            />
          </ErrorBoundary>
        )}

        {/* Screen 4: GIS Spatial Mapping */}
        {activeScreen === 'gis-mapping' && (
          <ErrorBoundary pageName="GIS Mapping">
            <GisMappingPage
              survey={survey}
              contacts={contacts}
              selectedContact={selectedContact}
              navTrack={navTrack}
              onSelectContact={setSelectedContact}
              onNavigateToAnalysis={() => setActiveScreen('sonar-analysis')}
              onNavigateToVerify={() => setActiveScreen('contact-verification')}
              onExportGeoJSON={handleExportGeoJSON}
            />
          </ErrorBoundary>
        )}

        {/* Screen 5: AI Deep Learning Pipeline Monitor */}
        {activeScreen === 'ai-pipeline' && (
          <ErrorBoundary pageName="AI Pipeline">
            <AiPipelinePage />
          </ErrorBoundary>
        )}

        {/* Screen 6: Reports & Export Central */}
        {activeScreen === 'reports' && (
          <ErrorBoundary pageName="Reports">
            <ReportsPage
              survey={survey}
              contacts={contacts}
            />
          </ErrorBoundary>
        )}

        {/* Screen 7: Unknown Acoustic Anomalies */}
        {activeScreen === 'anomalies' && (
          <ErrorBoundary pageName="Unknown Anomalies">
            <AnomalyPage onSelectContact={handleVerifyContact} />
          </ErrorBoundary>
        )}

        {/* Screen 8: AI Sonar Analyst Query Engine */}
        {activeScreen === 'analyst' && (
          <ErrorBoundary pageName="AI Analyst">
            <AnalystPage onSelectContact={handleVerifyContact} />
          </ErrorBoundary>
        )}

        {/* Screen 9: ML Stack & Telemetry Monitor */}
        {activeScreen === 'ml-monitor' && (
          <ErrorBoundary pageName="ML Monitor">
            <MLMonitorPage />
          </ErrorBoundary>
        )}

        {/* Screen 10: Active Learning Curation */}
        {activeScreen === 'active-learning' && (
          <ErrorBoundary pageName="Active Learning">
            <ActiveLearningPage />
          </ErrorBoundary>
        )}

        {/* Interactive Upload Swath Modal */}
        {showUploadModal && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-[var(--color-surface)] rounded-[28px] border border-[var(--color-border)] max-w-xl w-full p-7 space-y-5 shadow-2xl font-sans">
              
              <div className="flex items-center justify-between border-b border-[var(--color-border)] pb-3">
                <div>
                  <h4 className="text-lg font-extrabold text-[var(--color-text)] font-display">
                    Ingest Side-Scan Sonar Swath
                  </h4>
                  <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                    Upload raw SSS imagery and optional towfish navigation log for PostGIS georeferencing.
                  </p>
                </div>
                <button 
                  onClick={() => setShowUploadModal(false)}
                  aria-label="Close upload modal"
                  className="p-2 rounded-full hover:bg-[var(--color-surface-2)] text-[var(--color-text-muted)] transition-colors cursor-pointer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Hidden file inputs */}
              <input 
                ref={sonarInputRef} 
                type="file" 
                accept=".png,.jpg,.jpeg,.tif,.tiff" 
                className="hidden" 
                onChange={(e) => { if (e.target.files?.[0]) setSelectedSonarFile(e.target.files[0]); }} 
              />
              <input 
                ref={navInputRef} 
                type="file" 
                accept=".csv,.txt,.nav" 
                className="hidden" 
                onChange={(e) => { if (e.target.files?.[0]) setSelectedNavFile(e.target.files[0]); }} 
              />

              {/* Primary Sonar Drag & Drop Zone */}
              <div
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleDrop}
                onClick={() => sonarInputRef.current?.click()}
                className={`border-2 border-dashed rounded-2xl p-6 text-center space-y-2 transition-all cursor-pointer ${
                  isDragging 
                    ? 'border-[var(--color-primary)] bg-[var(--color-primary-dim)]' 
                    : selectedSonarFile 
                    ? 'border-emerald-400 bg-emerald-50/40' 
                    : 'border-[var(--color-border)] hover:border-[var(--color-primary)]/50 bg-[var(--color-surface-2)]'
                }`}
              >
                {selectedSonarFile ? (
                  <div className="flex items-center justify-center gap-3">
                    <CheckCircle2 className="w-8 h-8 text-emerald-500 shrink-0" />
                    <div className="text-left">
                      <div className="text-sm font-bold text-[var(--color-text)] truncate max-w-xs">{selectedSonarFile.name}</div>
                      <div className="text-xs text-[var(--color-text-muted)]">
                        {(selectedSonarFile.size / (1024 * 1024)).toFixed(2)} MB • Ready for AI Preprocessing
                      </div>
                    </div>
                  </div>
                ) : (
                  <>
                    <Upload className="w-8 h-8 text-[var(--color-primary)] mx-auto" />
                    <div className="text-sm font-bold text-[var(--color-text)]">Click to select or drag Sonar Waterfall Swath</div>
                    <div className="text-xs text-[var(--color-text-muted)]">Supports standard SSS GeoTIFF, PNG, JPG</div>
                  </>
                )}
              </div>

              {/* Optional Navigation Track File Section */}
              <div 
                onClick={() => navInputRef.current?.click()}
                className={`p-4 rounded-xl border border-dashed transition-all cursor-pointer flex items-center justify-between ${
                  selectedNavFile 
                    ? 'border-emerald-300 bg-emerald-50/30' 
                    : 'border-[var(--color-border)] bg-[var(--color-surface-2)] hover:border-slate-300'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Navigation className={`w-5 h-5 ${selectedNavFile ? 'text-emerald-500' : 'text-[var(--color-text-muted)]'}`} />
                  <div>
                    <div className="text-xs font-bold text-[var(--color-text)]">
                      {selectedNavFile ? selectedNavFile.name : 'Attach Towfish Navigation Log (Optional)'}
                    </div>
                    <div className="text-[11px] text-[var(--color-text-muted)]">
                      {selectedNavFile ? `${(selectedNavFile.size / 1024).toFixed(1)} KB • Coordinates linked` : 'CSV containing ping_id, latitude, longitude, heading'}
                    </div>
                  </div>
                </div>
                <button type="button" className="text-xs font-bold text-[var(--color-primary)] hover:underline cursor-pointer">
                  {selectedNavFile ? 'Change' : 'Browse'}
                </button>
              </div>

              {/* Actions */}
              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => { setShowUploadModal(false); setSelectedSonarFile(null); setSelectedNavFile(null); }}
                  disabled={isUploading}
                  className="px-5 py-2.5 rounded-full border border-[var(--color-border)] text-[var(--color-text)] text-xs font-semibold hover:bg-[var(--color-surface-2)] transition-colors cursor-pointer"
                >
                  Cancel
                </button>

                <button
                  type="button"
                  onClick={handlePerformUpload}
                  disabled={!selectedSonarFile || isUploading}
                  className={`px-6 py-2.5 rounded-full text-xs font-bold flex items-center gap-2 transition-all shadow-tactile ${
                    !selectedSonarFile || isUploading
                      ? 'bg-slate-200 text-[#8e8e93] cursor-not-allowed'
                      : 'bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] text-white hover:scale-[1.02] active:scale-[0.98] cursor-pointer'
                  }`}
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>{isUploading ? 'Ingesting & Analyzing...' : 'Ingest & Run Pipeline'}</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Global Toast Notification Layer */}
        <ToastContainer />
      </MainLayout>
    </ToastProvider>
  );
};
