import React from 'react';
import { 
  LayoutDashboard, 
  Waves, 
  CheckCircle2, 
  Compass, 
  Cpu, 
  FileText, 
  Radio, 
  ChevronRight,
  Sparkles,
  Activity,
  Database,
  Search
} from 'lucide-react';
import { ActiveScreen } from './MainLayout';

interface SidebarProps {
  activeScreen: ActiveScreen;
  onSelectScreen: (screen: ActiveScreen) => void;
  surveyFilename?: string;
  totalContactsCount?: number;
  highPriorityCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeScreen,
  onSelectScreen,
  surveyFilename,
  totalContactsCount = 0,
  highPriorityCount = 0
}) => {
  const navItems = [
    { 
      id: 'dashboard' as ActiveScreen, 
      label: 'Dashboard Overview', 
      icon: LayoutDashboard,
      badge: 'Live'
    },
    { 
      id: 'sonar-analysis' as ActiveScreen, 
      label: 'Sonar Waterfall', 
      icon: Waves,
      badge: totalContactsCount > 0 ? `${totalContactsCount}` : undefined
    },
    { 
      id: 'contact-verification' as ActiveScreen, 
      label: 'Contact Triage', 
      icon: CheckCircle2,
      badge: highPriorityCount > 0 ? `${highPriorityCount} High` : undefined,
      badgeAlert: highPriorityCount > 0
    },
    { 
      id: 'anomalies' as ActiveScreen, 
      label: 'Unknown Anomalies', 
      icon: Sparkles 
    },
    { 
      id: 'analyst' as ActiveScreen, 
      label: 'AI Sonar Analyst', 
      icon: Search 
    },
    { 
      id: 'ml-monitor' as ActiveScreen, 
      label: 'ML Telemetry', 
      icon: Activity 
    },
    { 
      id: 'active-learning' as ActiveScreen, 
      label: 'Active Learning', 
      icon: Database 
    },
    { 
      id: 'gis-mapping' as ActiveScreen, 
      label: 'GIS Mapping & Spatial', 
      icon: Compass 
    },
    { 
      id: 'ai-pipeline' as ActiveScreen, 
      label: 'Pipeline Monitor', 
      icon: Cpu 
    },
    { 
      id: 'reports' as ActiveScreen, 
      label: 'Reports & Export', 
      icon: FileText 
    },
  ];

  return (
    // CSS-only hover: w-20 → group-hover:w-[260px], no JS onMouseEnter/Leave
    <aside 
      className="group fixed left-0 top-0 bottom-0 z-50 w-20 hover:w-[260px] bg-[var(--color-surface)] border-r border-[var(--color-border)] shadow-soft hover:shadow-2xl flex flex-col justify-between transition-all duration-300 ease-[cubic-bezier(0.2,0.8,0.2,1)] overflow-hidden"
    >
      {/* Top Branding Header */}
      <div>
        <div className="h-20 flex items-center px-4 border-b border-[var(--color-border)]">
          {/* Logo Mark Bucket */}
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-[var(--color-primary)] text-white shadow-md shadow-[var(--color-primary)]/25 transition-transform group-hover:scale-105">
            <Radio className="w-6 h-6 animate-pulse" />
          </div>

          {/* Expanded Brand Name & Tag */}
          <div className="ml-3.5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 whitespace-nowrap overflow-hidden">
            <div className="flex items-center gap-1.5">
              <span className="font-display text-base font-extrabold tracking-tight text-[var(--color-text)]">
                SONAR-INTEL
              </span>
              <span className="text-[10px] font-bold px-1.5 py-[1px] rounded-full bg-[var(--color-accent)] text-[#1f1f1f]">
                v2.0
              </span>
            </div>
            <p className="text-[11px] font-medium text-[var(--color-text-muted)]">
              Hydrographic Anomaly Triage
            </p>
          </div>
        </div>

        {/* Section Label */}
        <div className="px-5 pt-5 pb-2">
          <span className="text-[10px] font-bold tracking-wider text-[var(--color-text-muted)] uppercase opacity-0 group-hover:opacity-100 transition-opacity duration-200 block whitespace-nowrap font-sans">
            Workspaces
          </span>
        </div>

        {/* Navigation Items */}
        <nav className="px-2 space-y-1.5" aria-label="Main navigation">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeScreen === item.id;

            return (
              <button
                key={item.id}
                id={`nav-${item.id}`}
                onClick={() => onSelectScreen(item.id)}
                aria-label={item.label}
                aria-current={isActive ? 'page' : undefined}
                className={`relative w-full h-12 rounded-2xl flex items-center transition-all duration-200 font-sans cursor-pointer ${
                  isActive
                    ? 'bg-[var(--color-primary-dim)] text-[var(--color-primary)] font-semibold'
                    : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-2)] font-medium'
                }`}
                title={item.label}
              >
                {/* Active Left-Aligned Vertical Indicator Bar */}
                {isActive && (
                  <span className="absolute left-0 top-3 bottom-3 w-1.5 rounded-r-full bg-[var(--color-primary)]" />
                )}

                {/* Centered Icon Container (Fixed 76px width for 80px bar) */}
                <div className="w-[76px] shrink-0 flex items-center justify-center">
                  <Icon className={`w-5 h-5 transition-colors ${isActive ? 'text-[var(--color-primary)]' : 'text-current'}`} />
                </div>

                {/* Expanded Label & Badges */}
                <div className="flex-1 flex items-center justify-between pr-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300 whitespace-nowrap overflow-hidden">
                  <span className="text-sm tracking-tight text-left">{item.label}</span>

                  {item.badge && (
                    <span 
                      className={`text-[10px] font-bold px-2 py-[1px] rounded-full font-sans ml-2 ${
                        (item as any).badgeAlert
                          ? 'bg-[var(--color-primary)] text-white'
                          : isActive
                          ? 'bg-[var(--color-primary-dim)] text-[var(--color-primary)]'
                          : 'bg-[var(--color-surface-2)] text-[var(--color-text-muted)]'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </div>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom Area: Active Swath Context & Operator Profile */}
      <div className="p-3 border-t border-[var(--color-border)] space-y-3">
        {/* Active Swath Badge (Visible only on expansion) */}
        {surveyFilename && (
          <div className="hidden group-hover:block p-3 rounded-2xl bg-[var(--color-surface-2)] border border-[var(--color-border)] transition-all">
            <div className="flex items-center justify-between text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">
              <span className="flex items-center gap-1 text-[var(--color-primary)]">
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-primary)] animate-ping" />
                Active Swath
              </span>
              <span className="text-[10px] text-emerald-600 bg-emerald-50 px-1.5 py-[1px] rounded-full font-semibold">
                READY
              </span>
            </div>
            <div className="text-xs font-semibold text-[var(--color-text)] truncate font-sans" title={surveyFilename}>
              {surveyFilename}
            </div>
          </div>
        )}

        {/* User Profile Avatar Card */}
        <div className="flex items-center h-12 px-1 rounded-2xl hover:bg-[var(--color-surface-2)] transition-colors cursor-pointer">
          {/* Avatar with live status indicator (Centered in 76px) */}
          <div className="w-[74px] shrink-0 flex items-center justify-center">
            <div className="relative flex h-10 w-10 items-center justify-center rounded-full bg-[var(--color-surface-2)] border border-[var(--color-border)] text-[var(--color-text)] font-bold text-xs">
              CV
              <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-emerald-500 border-2 border-[var(--color-surface)]" />
            </div>
          </div>

          {/* User Details (Expanded) */}
          <div className="ml-1 opacity-0 group-hover:opacity-100 transition-opacity duration-300 whitespace-nowrap overflow-hidden flex-1">
            <div className="text-xs font-bold text-[var(--color-text)] leading-tight">Dr. C. Vance</div>
            <div className="text-[11px] text-[var(--color-text-muted)]">Lead Hydrographer</div>
          </div>

          <ChevronRight className="w-4 h-4 text-[var(--color-text-muted)] opacity-0 group-hover:opacity-100 transition-opacity duration-300 pr-2" />
        </div>
      </div>
    </aside>
  );
};
