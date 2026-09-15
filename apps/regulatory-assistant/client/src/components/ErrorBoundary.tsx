/**
 * ErrorBoundary.tsx
 * React error boundary for the Regulatory Assistant.
 * Catches render errors and displays a branded fallback instead of crashing.
 * Lakelink Fiber brand: #FF3621 primary, #1B3139 secondary, #F9F7F4 surface.
 */
import { Component, type ReactNode, type ErrorInfo } from 'react';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[ErrorBoundary] Caught error:', error, info.componentStack);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            padding: '32px 24px',
            textAlign: 'center',
            backgroundColor: '#F9F7F4',
            borderRadius: '8px',
            border: '1px solid #E5E2DD',
            margin: '24px',
          }}
        >
          <div
            style={{
              width: 48,
              height: 48,
              borderRadius: '50%',
              backgroundColor: 'rgba(255,54,33,0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px',
              fontSize: '1.5rem',
            }}
          >
            \u26A0\uFE0F
          </div>
          <h3
            style={{
              color: '#1B3139',
              fontSize: '1rem',
              fontWeight: 600,
              marginBottom: 8,
              fontFamily: 'Inter, system-ui, sans-serif',
            }}
          >
            {this.props.fallbackTitle || 'Something went wrong'}
          </h3>
          <p
            style={{
              color: '#6E8898',
              fontSize: '0.85rem',
              marginBottom: 16,
              fontFamily: 'Inter, system-ui, sans-serif',
            }}
          >
            {this.state.error?.message || 'An unexpected error occurred.'}
          </p>
          <button
            onClick={this.handleRetry}
            style={{
              backgroundColor: '#FF3621',
              color: '#FFFFFF',
              border: 'none',
              borderRadius: '6px',
              padding: '8px 20px',
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: 'pointer',
              fontFamily: 'Inter, system-ui, sans-serif',
            }}
          >
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
