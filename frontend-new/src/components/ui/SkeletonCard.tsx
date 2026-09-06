import React from 'react';

/** Single-line text skeleton with shimmer animation */
export const SkeletonText: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`skeleton rounded-lg ${className}`} />
);

/** A full stat card skeleton matching the StatCard layout */
export const SkeletonStatCard: React.FC = () => (
  <div className="bg-white rounded-[24px] border border-[#e6e6e6] p-6 shadow-soft space-y-4">
    <div className="flex items-start justify-between gap-4">
      <div className="space-y-2 flex-1">
        <SkeletonText className="h-2.5 w-24" />
        <SkeletonText className="h-8 w-16 mt-1" />
      </div>
      <div className="skeleton h-12 w-12 rounded-2xl shrink-0" />
    </div>
    <div className="pt-3.5 border-t border-[#f2f2f2] flex justify-between">
      <SkeletonText className="h-5 w-20 rounded-full" />
      <SkeletonText className="h-4 w-28" />
    </div>
  </div>
);

/** A skeleton row for table / list items */
export const SkeletonRow: React.FC<{ cols?: number }> = ({ cols = 4 }) => (
  <div className="flex items-center gap-4 py-3.5 border-b border-[#f2f2f2]">
    {Array.from({ length: cols }).map((_, i) => (
      <SkeletonText
        key={i}
        className={`h-3.5 rounded-lg ${i === 0 ? 'w-28' : i === cols - 1 ? 'w-16' : 'w-20'}`}
      />
    ))}
  </div>
);

/** A skeleton for a large card panel */
export const SkeletonCard: React.FC<{ lines?: number; className?: string }> = ({
  lines = 3,
  className = '',
}) => (
  <div className={`bg-white rounded-[24px] border border-[#e6e6e6] p-6 shadow-soft space-y-4 ${className}`}>
    <SkeletonText className="h-4 w-40" />
    {Array.from({ length: lines }).map((_, i) => (
      <SkeletonText key={i} className={`h-3.5 ${i === lines - 1 ? 'w-2/3' : 'w-full'}`} />
    ))}
  </div>
);
