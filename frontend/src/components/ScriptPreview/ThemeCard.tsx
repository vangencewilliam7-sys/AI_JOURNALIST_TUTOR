import React from 'react';
import { Target, Lightbulb, Link as LinkIcon } from 'lucide-react';

interface Props {
  theme: any;
}

export const ThemeCard: React.FC<Props> = ({ theme }) => {
  return (
    <div className="theme-card">
      <div className="theme-card-header">
        <h4>{theme.pillar_title}</h4>
        <span className="theme-card-id">T{theme.pillar_id}</span>
      </div>
      <p style={{ marginBottom: '8px' }}>
        <Target size={10} style={{ display: 'inline', marginRight: '4px' }} />
        {theme.learning_objective}
      </p>
      
      {theme.missing_piece && (
        <p style={{ color: '#fbbf24' }}>
          <Lightbulb size={10} style={{ display: 'inline', marginRight: '4px' }} />
          {theme.missing_piece}
        </p>
      )}
      
      {theme.source_evidence && theme.source_evidence.length > 0 && (
        <div className="theme-card-anchor">
          <LinkIcon size={10} /> Grounded in {theme.source_evidence[0].source_title}
        </div>
      )}
    </div>
  );
};
