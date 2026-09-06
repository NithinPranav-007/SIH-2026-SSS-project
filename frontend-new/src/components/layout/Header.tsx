import React, { useEffect, useState } from 'react';
import { 
  Sparkles, 
  Upload, 
  Play, 
  Moon,
  Sun,
  Waves
} from 'lucide-react';
import { SurveyUploadResponse } from '../../types/detection';

interface HeaderProps {
  survey: SurveyUploadResponse | null;
  analyzing: boolean;
  onRunAnalysis: () => void;
  onCustomUploadClick: () => void;
  onLoadDemoSample: (sampleId: string) => void;
  activeScreen: string;
}

/** Human-readable labels for each screen */
const PAGE_TITLES: Record<string, string> = {
  'dashboard':            'Operations Overview',
  'sonar-analysis':       'Sonar Waterfall Workspace',
  'contact-verification': 'Contact Triage & Verification',
  'gis-mapping':          'GIS Spatial Mapping',
  'ai-pipeline':          'AI Pipeline Monitor',
  'reports':              'Data Products & Export',
};

export const Header: React.FC<HeaderProps> = ({
  survey,
  analyzing,
  onRunAnalysis,
  onCustomUploadClick,
  onLoadDemoSample,
  activeScreen,
}) => {
  const [darkMode, setDarkMode] = useState<boolean>(() => {
    return localStorage.getItem('sonar-theme') === 'dark';
  });

  useEffect(() => {
    document.documentElement.dataset.theme = darkMode ? 'dark' : '';
    localStorage.setItem('sonar-theme', darkMode ? 'dark' : 'light');
  }, [darkMode]);

  const demoSamples = [
    { id: 'viator_04',        label: 'Viator-04',      badge: 'True Wreck', desc: 'Shipwreck True Positive' },
    { id: 'corsican_02',      label: 'Corsican-02',    badge: 'Verified',   desc: 'Held-out Target' },
    { id: 'artificial_reef_02', label: 'Reef-02',      badge: 'Clutter',    desc: 'Geological Clutter' },
    { id: 'survey_001',       label: 'Survey-001',     badge: 'Nav Track',  desc: 'Towfish Nav Track' },
  ];

  const pageTitle = PAGE_TITLES[activeScreen] ?? 'Operations Overview';

  return (
    <header className="h-20 bg-[var(--color-surface)] border-b border-[var(--color-border)] px-8 flex items-center justify-between sticky top-0 z-30 shadow-soft shrink-0">
      
      {/* Left: Breadcrumbs & Live Status */}
      <div className="flex items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider font-sans">
              MISSION INTELLIGENCE
            </span>
            <span className="text-[var(--color-border)]">/</span>
            <span className="text-[11px] font-bold text-[var(--color-primary)] uppercase tracking-wider font-sans">
              {activeScreen.replace(/-/g, ' ')}
            </span>
          </div>
          <h1 className="text-xl font-extrabold text-[var(--color-text)] font-display tracking-tight flex items-center gap-2.5 mt-0.5">
            {pageTitle}
            <span className="inline-flex items-center gap-1.5 text-[11px] font-sans font-semibold px-2.5 py-[1px] rounded-full bg-emerald-50 text-emerald-600 border border-emerald-200">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              API Connected
            </span>
          </h1>
        </div>
      </div>

      {/* Right Actions: Benchmarks & CTAs */}
      <div className="flex items-center gap-3">
        
        {/* Curated Demo Swath Benchmark Selector */}
        <div className="hidden xl:flex items-center bg-[var(--color-surface-2)] border border-[var(--color-border)] rounded-full p-1 pl-3.5 shadow-tactile">
          <span className="text-xs font-semibold text-[var(--color-text-muted)] mr-2 flex items-center gap-1.5 font-sans">
            <Sparkles className="w-3.5 h-3.5 text-[var(--color-accent)]" />
            Benchmarks:
          </span>
          <div className="flex items-center gap-1.5">
            {demoSamples.map((sample) => {
              const isSelected = survey?.filename.toLowerCase().includes(sample.id.replace(/_/g, ''));
              return (
                <button
                  key={sample.id}
                  id={`demo-btn-${sample.id}`}
                  onClick={() => onLoadDemoSample(sample.id)}
                  className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all duration-200 cursor-pointer ${
                    isSelected
                      ? 'bg-[var(--color-text)] text-white shadow-sm'
                      : 'text-[var(--color-text)] hover:bg-[var(--color-surface-2)]'
                  }`}
                  title={sample.desc}
                >
                  <span>{sample.label}</span>
                  <span className={`ml-1.5 text-[10px] px-1.5 py-[1px] rounded-full font-bold ${
                    isSelected ? 'bg-white/20 text-white' : 'bg-[var(--color-border)] text-[var(--color-text-muted)]'
                  }`}>
                    {sample.badge}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Dark Mode Toggle */}
        <button
          id="dark-mode-toggle"
          onClick={() => setDarkMode(d => !d)}
          aria-label={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          className="h-10 w-10 rounded-full bg-[var(--color-surface)] hover:bg-[var(--color-surface-2)] border border-[var(--color-border)] text-[var(--color-text-2)] flex items-center justify-center transition-all duration-200 shadow-tactile cursor-pointer"
        >
          {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>

        {/* Custom Upload CTA */}
        <button
          id="upload-swath-btn"
          onClick={onCustomUploadClick}
          className="h-10 px-4 rounded-full bg-[var(--color-surface)] hover:bg-[var(--color-surface-2)] text-[var(--color-text)] border border-[var(--color-border)] font-semibold text-xs flex items-center gap-2 transition-all duration-200 shadow-tactile cursor-pointer"
        >
          <Upload className="w-3.5 h-3.5 text-[var(--color-text-muted)]" />
          <span>Upload Swath</span>
        </button>

        {/* Primary Action Button: Run Inference */}
        <button
          id="run-analysis-btn"
          onClick={onRunAnalysis}
          disabled={!survey || analyzing}
          aria-label={analyzing ? 'Inference running' : 'Run YOLOv8n triage analysis'}
          className={`h-10 px-5 rounded-full font-semibold text-xs flex items-center gap-2 transition-all duration-200 shadow-tactile ${
            analyzing
              ? 'bg-slate-200 text-[#8e8e93] cursor-wait'
              : survey
              ? 'bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] text-white hover:scale-[1.02] active:scale-[0.98] cursor-pointer'
              : 'bg-[var(--color-border)] text-[var(--color-text-muted)] cursor-not-allowed'
          }`}
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          <span>{analyzing ? 'Inference Running...' : 'Run YOLOv8n Triage'}</span>
        </button>
      </div>
    </header>
  );
};
