import React, { useState } from 'react';
import { Activity } from 'lucide-react';
import type { DecisionLog as DecisionLogType, RagChunk } from '../../types';

interface Props {
  decision?: DecisionLogType;
  chunks?: RagChunk[];
}

export const DecisionLog: React.FC<Props> = ({ decision, chunks }) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!decision) return null;

  return (
    <div className="decision-section">
      <button className="decision-toggle" onClick={() => setIsOpen(!isOpen)}>
        <Activity size={12} /> Decision Log
      </button>
      
      {isOpen && (
        <div style={{ padding: '16px', background: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', marginTop: '8px', fontSize: '12px' }}>
          <p style={{ color: '#818cf8', fontWeight: 700, marginBottom: '8px' }}>Internal Monologue:</p>
          <p style={{ color: '#cbd5e1', fontStyle: 'italic', marginBottom: '12px' }}>"{decision.internal_monologue}"</p>
          
          {chunks && chunks.length > 0 && (
            <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid #1e293b' }}>
              <p style={{ color: '#10b981', fontWeight: 700, marginBottom: '4px' }}>Source Context:</p>
              <p style={{ color: '#64748b' }}>{chunks[0].source_title}: {chunks[0].content}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
