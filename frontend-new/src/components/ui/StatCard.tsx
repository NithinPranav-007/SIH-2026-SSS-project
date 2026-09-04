import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  icon: LucideIcon;
  trend?: {
    value: string;
    isUp?: boolean;
    isNeutral?: boolean;
  };
  onClick?: () => void;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  subtext,
  icon: Icon,
  trend,
  onClick,
}) => {
  return (
    <div
      onClick={onClick}
      className={`group relative overflow-hidden bg-white rounded-[24px] border border-[#e6e6e6] p-6 shadow-soft hover:shadow-card-hover transition-all duration-300 ${
        onClick ? 'cursor-pointer hover:-translate-y-1' : ''
      }`}
    >
      {/* Absolute Decorative Glow Gradient */}
      <div 
        className="absolute -right-8 -bottom-8 w-36 h-36 bg-[#ff383c]/5 rounded-full blur-3xl pointer-events-none transition-all duration-500 group-hover:bg-[#ff383c]/15 group-hover:scale-125" 
      />

      {/* Top Header: Label & Icon Bucket */}
      <div className="relative z-10 flex items-start justify-between gap-4">
        <div className="space-y-1 min-w-0">
          <span className="section-label block truncate">
            {label}
          </span>
          <div className="text-3xl font-extrabold tracking-tight text-[#1f1f1f] font-display">
            {value}
          </div>
        </div>

        {/* Interactive Icon Bucket (Placely Spec) */}
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-[#fcfcfc] border border-[#e6e6e6] text-[#ff383c] transition-all duration-300 group-hover:bg-[#ff383c] group-hover:text-white group-hover:border-[#ff383c] group-hover:shadow-md group-hover:shadow-[#ff383c]/20">
          <Icon className="w-5 h-5 transition-transform duration-300 group-hover:scale-110" />
        </div>
      </div>

      {/* Footer / Trend Tracker */}
      <div className="relative z-10 mt-5 flex items-center justify-between pt-3.5 border-t border-[#f2f2f2] text-xs">
        {trend ? (
          <span
            className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold transition-colors ${
              trend.isNeutral
                ? 'bg-slate-100 text-slate-700'
                : trend.isUp
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-100'
                : 'bg-[#ff383c]/10 text-[#ff383c] border border-[#ff383c]/20'
            }`}
          >
            {trend.value}
          </span>
        ) : (
          <span className="text-xs text-[#8e8e93] font-medium">Calibrated</span>
        )}

        {subtext && (
          <span className="text-xs font-medium text-[#8e8e93] truncate max-w-[180px]" title={subtext}>
            {subtext}
          </span>
        )}
      </div>
    </div>
  );
};
