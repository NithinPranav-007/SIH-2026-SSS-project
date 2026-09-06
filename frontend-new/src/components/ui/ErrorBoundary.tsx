import React from 'react';
import { AlertTriangle, RotateCcw } from 'lucide-react';

interface ErrorBoundaryProps {
  children: React.ReactNode;
  pageName?: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error(`[ErrorBoundary] Page crashed — ${this.props.pageName ?? 'unknown'}:`, error, info);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[400px] p-10 gap-5 font-sans">
          <div className="w-16 h-16 rounded-full bg-[#ff383c]/10 flex items-center justify-center">
            <AlertTriangle className="w-8 h-8 text-[#ff383c]" />
          </div>
          <div className="text-center space-y-2 max-w-md">
            <h3 className="text-lg font-extrabold text-[#1f1f1f] font-display">
              {this.props.pageName ? `${this.props.pageName} Crashed` : 'Page Error'}
            </h3>
            <p className="text-xs text-[#8e8e93] leading-relaxed">
              An unexpected error occurred in this view. The rest of the application is unaffected.
            </p>
            {this.state.error && (
              <pre className="mt-2 text-[10px] text-left text-[#ff383c] bg-[#ff383c]/5 border border-[#ff383c]/20 rounded-xl px-4 py-3 font-mono overflow-x-auto max-w-full">
                {this.state.error.message}
              </pre>
            )}
          </div>
          <button
            onClick={this.handleReset}
            className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-[#1f1f1f] text-white text-xs font-semibold hover:bg-black transition-colors shadow-tactile cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset This View</span>
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
