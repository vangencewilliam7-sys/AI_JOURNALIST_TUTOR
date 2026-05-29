import React from 'react';
import { AlertCircle, BrainCircuit, GitBranch, Swords, Crosshair } from 'lucide-react';
import type { CourseBlueprint } from '../../types';

interface Props {
  blueprint: CourseBlueprint;
}

export const DeepExtractionGrid: React.FC<Props> = ({ blueprint: r }) => {
  return (
    <div className="report-cards" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginTop: '16px' }}>
      
      {r.friction_points?.length > 0 && (
        <div className="report-card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '15px', color: '#ef4444', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid #334155', paddingBottom: '8px' }}>
            <AlertCircle size={16} /> Friction Points
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {r.friction_points.map((fp, i) => (
              <div key={i}>
                <strong style={{ display: 'block', fontSize: '13px', color: '#fca5a5' }}>{fp.concept}</strong>
                <p style={{ fontSize: '12px', color: '#94a3b8', margin: '4px 0' }}><em>Sticking point:</em> {fp.friction_detail}</p>
                <p style={{ fontSize: '12px', color: '#4ade80' }}><em>Unblock Strategy:</em> {fp.unblock_strategy}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {r.teaching_frameworks?.length > 0 && (
        <div className="report-card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '15px', color: '#818cf8', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid #334155', paddingBottom: '8px' }}>
            <BrainCircuit size={16} /> First Principles Frameworks
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {r.teaching_frameworks.map((tf, i) => (
              <div key={i}>
                <strong style={{ display: 'block', fontSize: '13px', color: '#c084fc' }}>{tf.framework_name} ({tf.topic})</strong>
                <p style={{ fontSize: '12px', color: '#cbd5e1', margin: '4px 0' }}>{tf.explanation}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {r.edge_cases?.length > 0 && (
        <div className="report-card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '15px', color: '#f59e0b', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid #334155', paddingBottom: '8px' }}>
            <GitBranch size={16} /> Real-World Edge Cases
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {r.edge_cases.map((ec, i) => (
              <div key={i}>
                <strong style={{ display: 'block', fontSize: '13px', color: '#fde047' }}>{ec.scenario}</strong>
                <p style={{ fontSize: '12px', color: '#cbd5e1', margin: '4px 0' }}><em>Solution:</em> {ec.solution}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {r.anti_patterns?.length > 0 && (
        <div className="report-card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '15px', color: '#ec4899', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid #334155', paddingBottom: '8px' }}>
            <Swords size={16} /> Beginner Anti-Patterns
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {r.anti_patterns.map((ap, i) => (
              <div key={i}>
                <strong style={{ display: 'block', fontSize: '13px', color: '#fbcfe8' }}>{ap.bad_habit}</strong>
                <p style={{ fontSize: '12px', color: '#cbd5e1', margin: '4px 0' }}><em>How to correct:</em> {ap.correction}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {r.evaluation_methods?.length > 0 && (
        <div className="report-card" style={{ padding: '20px', gridColumn: 'span 2' }}>
          <h3 style={{ fontSize: '15px', color: '#10b981', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid #334155', paddingBottom: '8px' }}>
            <Crosshair size={16} /> Evaluation & Mastery Methods
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            {r.evaluation_methods.map((em, i) => (
              <div key={i} style={{ background: 'rgba(0,0,0,0.15)', padding: '12px', borderRadius: '6px' }}>
                <strong style={{ display: 'block', fontSize: '13px', color: '#a7f3d0', marginBottom: '4px' }}>{em.concept}</strong>
                <p style={{ fontSize: '12px', color: '#cbd5e1' }}><em>Assessment Task:</em> {em.assessment_task}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
