import React from 'react';
import { Clock } from 'lucide-react';
import type { ScriptQuestion } from '../../types';

interface Props {
  q: ScriptQuestion;
}

export const QuestionCard: React.FC<Props> = ({ q }) => {
  return (
    <div className="question-card">
      <div className="question-id">{q.question_id}</div>
      <div className="question-content">
        <p>{q.question_text}</p>
        <div className="question-meta">
          <span><Clock size={12} /> ~{q.estimated_minutes} min</span>
          <span style={{ color: '#818cf8' }}>Related to T{q.theme_id}</span>
        </div>
      </div>
    </div>
  );
};
