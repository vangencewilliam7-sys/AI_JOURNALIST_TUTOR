import React from 'react';
import type { ScriptPhase } from '../../types';
import { QuestionCard } from './QuestionCard';

interface Props {
  number: number;
  title: string;
  phase: ScriptPhase;
}

export const PhaseBlock: React.FC<Props> = ({ number, title, phase }) => {
  if (!phase || !phase.questions) return null;

  return (
    <div className="phase-block">
      <div className="phase-header">
        <div className="phase-number">{number}</div>
        <div>
          <h4>{title}</h4>
          <p style={{ fontSize: '12px', color: 'var(--text-dim)', marginTop: '2px' }}>{phase.phase_goal}</p>
        </div>
        <div className="phase-count">{phase.questions.length} Questions</div>
      </div>
      
      <div className="phase-questions">
        {phase.questions.map((q, idx) => (
          <QuestionCard key={idx} q={q} />
        ))}
      </div>
    </div>
  );
};
