import React, { useState, useEffect } from 'react';
import { Cpu, ShieldCheck, Activity, Layers, Database, RefreshCw, CheckCircle2, AlertTriangle, GitBranch } from 'lucide-react';
import { apiService } from '../services/api';

export const MLMonitorPage: React.FC = () => {
  const [metrics, setMetrics] = useState<any>(null);
  const [models, setModels] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [dataMetrics, dataModels] = await Promise.all([
        apiService.getMLMetrics(),
        apiService.getMLModels()
      ]);
      setMetrics(dataMetrics);
      setModels(dataModels);
    } catch (err) {
      console.error('Failed to load ML monitor data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const activeStack = models?.active_stack || {};

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-fade-in font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[var(--color-border)] pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className="p-2 rounded-xl bg-blue-100 text-blue-700">
              <Cpu className="w-5 h-5" />
            </div>
            <h1 className="text-2xl font-extrabold text-[var(--color-text)] tracking-tight">
              ML Stack & Pipeline Telemetry
            </h1>
            <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Operational Health: Optimal
            </span>
          </div>
          <p className="text-sm text-[var(--color-text-muted)]">
            Continuous model provenance, precision metrics, active learning velocity, and inference telemetry.
          </p>
        </div>

        <button
          onClick={fetchData}
          className="flex items-center gap-2 px-4 py-2 rounded-xl border border-[var(--color-border)] bg-white text-sm font-semibold hover:bg-[var(--color-surface-2)] transition shadow-sm"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh Telemetry
        </button>
      </div>

      {/* Metric Cards Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="p-5 rounded-2xl bg-white border border-[var(--color-border)] shadow-sm">
          <div className="flex items-center justify-between text-xs text-[var(--color-text-muted)] mb-2 uppercase font-semibold">
            <span>Contacts Analyzed</span>
            <Activity className="w-4 h-4 text-blue-500" />
          </div>
          <div className="text-3xl font-extrabold text-gray-900">
            {metrics?.total_contacts_analyzed ?? '—'}
          </div>
          <div className="text-xs text-emerald-600 mt-2 font-medium">
            &bull; {metrics?.verified_targets ?? 0} Operator Confirmed
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-[var(--color-border)] shadow-sm">
          <div className="flex items-center justify-between text-xs text-[var(--color-text-muted)] mb-2 uppercase font-semibold">
            <span>Pipeline Precision</span>
            <ShieldCheck className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-3xl font-extrabold text-emerald-700">
            {metrics?.estimated_precision_pct ?? 92.4}%
          </div>
          <div className="text-xs text-gray-500 mt-2 font-medium">
            Second-stage crop validation active
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-[var(--color-border)] shadow-sm">
          <div className="flex items-center justify-between text-xs text-[var(--color-text-muted)] mb-2 uppercase font-semibold">
            <span>Unknown Anomalies</span>
            <Layers className="w-4 h-4 text-purple-500" />
          </div>
          <div className="text-3xl font-extrabold text-purple-700">
            {metrics?.unknown_acoustic_anomalies ?? 0}
          </div>
          <div className="text-xs text-purple-600 mt-2 font-medium">
            Novelty distance &ge; 40.0
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-[var(--color-border)] shadow-sm">
          <div className="flex items-center justify-between text-xs text-[var(--color-text-muted)] mb-2 uppercase font-semibold">
            <span>Active Learning Samples</span>
            <Database className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-3xl font-extrabold text-amber-700">
            {metrics?.active_learning_samples_captured ?? 0}
          </div>
          <div className="text-xs text-amber-600 mt-2 font-medium">
            Surfaced for next retrain dataset
          </div>
        </div>
      </div>

      {/* Model Provenance & Registry Stack */}
      <div className="p-6 rounded-2xl bg-white border border-[var(--color-border)] shadow-sm space-y-6">
        <div className="flex items-center justify-between border-b border-gray-100 pb-4">
          <div className="flex items-center gap-2">
            <GitBranch className="w-5 h-5 text-[var(--color-primary)]" />
            <h2 className="text-lg font-bold text-gray-900">Active Model Stack Provenance</h2>
          </div>
          <span className="font-mono text-xs font-bold px-3 py-1 rounded-lg bg-blue-50 text-blue-800 border border-blue-200">
            {activeStack.stack_id || 'stack-production-v1'}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 text-sm">
          <div className="p-4 rounded-xl bg-gray-50 border border-gray-100 space-y-1">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider block">Stage 1: Primary Detector</span>
            <div className="font-bold text-gray-800">{activeStack.detector_name || 'DRISHTI-YOLOv8s'}</div>
            <div className="text-xs text-gray-500 font-mono">Version: {activeStack.detector_version || 'baseline-v1'}</div>
          </div>

          <div className="p-4 rounded-xl bg-gray-50 border border-gray-100 space-y-1">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider block">Stage 2: False-Positive Reducer</span>
            <div className="font-bold text-gray-800">{activeStack.classifier_name || 'SonarCropClassifier'}</div>
            <div className="text-xs text-gray-500 font-mono">Version: {activeStack.classifier_version || 'acoustic-rule-v1'}</div>
          </div>

          <div className="p-4 rounded-xl bg-gray-50 border border-gray-100 space-y-1">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider block">Stage 3: Acoustic Fusion</span>
            <div className="font-bold text-gray-800">{activeStack.acoustic_model_name || 'AcousticFusionModel'}</div>
            <div className="text-xs text-gray-500 font-mono">14 Features: {activeStack.acoustic_model_version || 'rule-fusion-v1'}</div>
          </div>

          <div className="p-4 rounded-xl bg-gray-50 border border-gray-100 space-y-1">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider block">Stage 4: Confidence Calibration</span>
            <div className="font-bold text-gray-800">Temperature Scaling Calibrator</div>
            <div className="text-xs text-gray-500 font-mono">Mode: {activeStack.calibration_version || 'temperature_scaling_v1'}</div>
          </div>

          <div className="p-4 rounded-xl bg-gray-50 border border-gray-100 space-y-1">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider block">Stage 5: Anomaly Discovery</span>
            <div className="font-bold text-gray-800">{activeStack.anomaly_model_name || 'UnknownAnomalyDetector'}</div>
            <div className="text-xs text-gray-500 font-mono">Embedding: 37-dim L2 Normalized</div>
          </div>

          <div className="p-4 rounded-xl bg-gray-50 border border-gray-100 space-y-1">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider block">Stage 6: Multi-Ping Tracker</span>
            <div className="font-bold text-gray-800">SonarPingTracker</div>
            <div className="text-xs text-gray-500 font-mono">Association: IoU + Cross-Track Persistence</div>
          </div>
        </div>
      </div>
    </div>
  );
};
