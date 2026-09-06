import React from 'react';
import { CheckCircle2, AlertCircle, Info, AlertTriangle, X } from 'lucide-react';
import { useToast, Toast, ToastType } from '../../hooks/useToast';

const ICONS: Record<ToastType, React.FC<{ className?: string }>> = {
  success: CheckCircle2,
  error:   AlertCircle,
  info:    Info,
  warning: AlertTriangle,
};

const STYLES: Record<ToastType, { bar: string; icon: string; text: string; bg: string; border: string }> = {
  success: {
    bar:    'bg-emerald-500',
    icon:   'text-emerald-600',
    text:   'text-emerald-900',
    bg:     'bg-emerald-50',
    border: 'border-emerald-200',
  },
  error: {
    bar:    'bg-[#ff383c]',
    icon:   'text-[#ff383c]',
    text:   'text-red-900',
    bg:     'bg-red-50',
    border: 'border-red-200',
  },
  warning: {
    bar:    'bg-amber-500',
    icon:   'text-amber-600',
    text:   'text-amber-900',
    bg:     'bg-amber-50',
    border: 'border-amber-200',
  },
  info: {
    bar:    'bg-blue-500',
    icon:   'text-blue-600',
    text:   'text-blue-900',
    bg:     'bg-blue-50',
    border: 'border-blue-200',
  },
};

const ToastItem: React.FC<{ toast: Toast }> = ({ toast }) => {
  const { removeToast } = useToast();
  const Icon = ICONS[toast.type];
  const s = STYLES[toast.type];

  return (
    <div
      role="alert"
      aria-live="polite"
      className={`
        relative flex items-start gap-3 w-80 max-w-full rounded-2xl border px-4 py-3.5
        shadow-lg font-sans overflow-hidden
        ${s.bg} ${s.border}
        ${toast.dismissing ? 'toast-exit' : 'toast-enter'}
      `}
    >
      {/* Accent left bar */}
      <span className={`absolute left-0 top-0 bottom-0 w-1 rounded-l-2xl ${s.bar}`} />

      <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${s.icon}`} />

      <span className={`flex-1 text-xs font-semibold leading-snug ${s.text}`}>
        {toast.message}
      </span>

      <button
        onClick={() => removeToast(toast.id)}
        aria-label="Dismiss notification"
        className={`shrink-0 p-0.5 rounded-full hover:bg-black/10 transition-colors cursor-pointer ${s.icon}`}
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
};

export const ToastContainer: React.FC = () => {
  const { toasts } = useToast();

  if (toasts.length === 0) return null;

  return (
    <div
      aria-label="Notifications"
      className="fixed bottom-6 right-6 z-[9999] flex flex-col gap-2.5 items-end pointer-events-none"
    >
      {toasts.map(toast => (
        <div key={toast.id} className="pointer-events-auto">
          <ToastItem toast={toast} />
        </div>
      ))}
    </div>
  );
};
