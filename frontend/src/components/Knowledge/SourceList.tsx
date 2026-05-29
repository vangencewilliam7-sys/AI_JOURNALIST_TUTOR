import React from 'react';
import { Trash2, Database, Loader2 } from 'lucide-react';
import type { KnowledgeSource } from '../../types';

interface Props {
  sources: KnowledgeSource[];
  onDelete: (id: string) => void;
  loading: boolean;
}

export const SourceList: React.FC<Props> = ({ sources, onDelete, loading }) => {
  return (
    <div style={{ background: 'var(--bg-card)', borderRadius: '16px', border: '1px solid var(--border)', padding: '32px' }}>
      <h2 style={{ fontSize: '16px', fontWeight: 800, marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Database size={18} style={{ color: 'var(--accent)' }} /> 
        Active Knowledge Sources ({sources.length})
      </h2>
      
      {loading ? (
        <div style={{ textAlign: 'center', padding: '20px', color: '#64748b' }}>
          <Loader2 size={18} className="spin" />
        </div>
      ) : sources.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '32px', color: '#475569', fontSize: '13px', border: '1px dashed #1e293b', borderRadius: '12px' }}>
          No sources ingested yet. Upload documents above to get started.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {sources.map(s => (
            <div key={s.id} style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '16px', background: 'rgba(255,255,255,0.02)', borderRadius: '12px', border: '1px solid var(--border)' }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 500, fontSize: '13px' }}>{s.title}</div>
                <div style={{ color: '#64748b', fontSize: '11px', marginTop: '2px' }}>
                  {s.source_type} · {s.chunk_count} chunks · {new Date(s.created_at).toLocaleDateString()}
                </div>
              </div>
              <button
                style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', padding: '8px', opacity: 0.7, transition: 'opacity 0.2s' }}
                onClick={() => onDelete(s.id)}
                title="Delete source"
                onMouseEnter={e => e.currentTarget.style.opacity = '1'}
                onMouseLeave={e => e.currentTarget.style.opacity = '0.7'}
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
