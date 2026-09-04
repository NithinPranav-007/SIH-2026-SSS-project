import React from 'react';
import { 
  Sparkles, 
  Upload, 
  Play, 
  Activity, 
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

export const Header: React.FC<HeaderProps> = ({
  survey,
  analyzing,
  onRunAnalysis,
  onCustomUploadClick,
  onLoadDemoSample,
  activeScreen,
}) => {
  const demoSamples = [
    { id: 'viator_04', label: 'Viator-04', badge: 'True Wreck', desc: 'Shipwreck True Positive' },
    { id: 'corsican_02', label: 'Corsican-02', badge: 'Verified', desc: 'Held-out Target' },
    { id: 'artificial_reef_02', label: 'Artificial Reef', badge: 'Clutter', desc: 'Geological Clutter' },
    { id: 'survey_001', label: 'Survey-001', badge: 'Nav Track', desc: 'Towfish Nav Track' },
  ];

  return (
    <header className="h-20 bg-white border-b border-[#e6e6e6] px-8 flex items-center justify-between sticky top-0 z-30 shadow-soft shrink-0">
      
      {/* Left: Breadcrumbs & Live Status */}
      <div className="flex items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-bold text-[#8e8e93] uppercase tracking-wider font-sans">
              MISSION INTELLIGENCE
            </span>
            <span className="text-[#e6e6e6]">/</span>
            <span className="text-[11px] font-bold text-[#ff383c] uppercase tracking-wider font-sans">
              {activeScreen.replace('-', ' ')}
            </span>
          </div>
          <h1 className="text-xl font-extrabold text-[#1f1f1f] font-display tracking-tight flex items-center gap-2.5 mt-0.5">
            Operations Overview
            <span className="inline-flex items-center gap-1.5 text-[11px] font-sans font-semibold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-600 border border-emerald-200">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              API Connected
            </span>
          </h1>
        </div>
      </div>

      {/* Right Actions: Benchmarks & CTAs */}
      <div className="flex items-center gap-4">
        
        {/* Curated Demo Swath Benchmark Selector */}
        <div className="hidden xl:flex items-center bg-[#fcfcfc] border border-[#e6e6e6] rounded-full p-1 pl-3.5 shadow-tactile">
          <span className="text-xs font-semibold text-[#8e8e93] mr-2 flex items-center gap-1.5 font-sans">
            <Sparkles className="w-3.5 h-3.5 text-[#ffd400]" />
            Benchmarks:
          </span>
          <div className="flex items-center gap-1.5">
            {demoSamples.map((sample) => {
              const isSelected = survey?.filename.toLowerCase().includes(sample.id.replace('_', ''));
              return (
                <button
                  key={sample.id}
                  onClick={() => onLoadDemoSample(sample.id)}
                  className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all duration-200 cursor-pointer ${
                    isSelected
                      ? 'bg-[#1f1f1f] text-white shadow-sm'
                      : 'text-[#1f1f1f] hover:bg-slate-200/60'
                  }`}
                  title={sample.desc}
                >
                  <span>{sample.label}</span>
                  <span className={`ml-1.5 text-[10px] px-1.5 py-0.2 rounded-full font-bold ${
                    isSelected ? 'bg-white/20 text-white' : 'bg-slate-100 text-[#8e8e93]'
                  }`}>
                    {sample.badge}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Custom Upload CTA */}
        <button
          onClick={onCustomUploadClick}
          className="h-10 px-4 rounded-full bg-white hover:bg-slate-50 text-[#1f1f1f] border border-[#e6e6e6] font-semibold text-xs flex items-center gap-2 transition-all duration-200 shadow-tactile cursor-pointer"
        >
          <Upload className="w-3.5 h-3.5 text-[#8e8e93]" />
          <span>Upload Swath</span>
        </button>

        {/* Primary Action Button: Run Inference */}
        <button
          onClick={onRunAnalysis}
          disabled={!survey || analyzing}
          className={`h-10 px-5 rounded-full font-semibold text-xs flex items-center gap-2 transition-all duration-200 shadow-tactile ${
            analyzing
              ? 'bg-slate-200 text-[#8e8e93] cursor-wait'
              : survey
              ? 'bg-[#ff383c] hover:bg-[#dc143c] text-white hover:scale-[1.02] active:scale-[0.98] cursor-pointer'
              : 'bg-slate-100 text-[#8e8e93] cursor-not-allowed'
          }`}
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          <span>{analyzing ? 'Inference Running...' : 'Run YOLOv8n Triage'}</span>
        </button>
      </div>
    </header>
  );
};
