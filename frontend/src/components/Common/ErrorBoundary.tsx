import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  errorMsg: string;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    errorMsg: ''
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, errorMsg: error.message };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', background: 'var(--bg)', color: 'var(--text)' }}>
          <AlertTriangle size={48} color="var(--red)" style={{ marginBottom: '16px' }} />
          <h2>Something went wrong.</h2>
          <p style={{ color: 'var(--text-dim)', marginTop: '8px' }}>{this.state.errorMsg}</p>
          <button 
            className="btn-primary" 
            style={{ marginTop: '24px' }}
            onClick={() => window.location.href = '/'}
          >
            Return Home
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
