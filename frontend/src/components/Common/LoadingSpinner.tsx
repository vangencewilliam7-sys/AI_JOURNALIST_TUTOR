import React from 'react';
import { Loader2 } from 'lucide-react';

interface Props {
  size?: number;
  text?: string;
  fullscreen?: boolean;
}

export const LoadingSpinner: React.FC<Props> = ({ size = 24, text, fullscreen = false }) => {
  const content = (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px', color: 'var(--text-dim)' }}>
      <Loader2 size={size} className="spin" />
      {text && <span style={{ fontSize: '13px', fontWeight: 600 }}>{text}</span>}
    </div>
  );

  if (fullscreen) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: 'var(--bg)' }}>
        {content}
      </div>
    );
  }

  return content;
};
