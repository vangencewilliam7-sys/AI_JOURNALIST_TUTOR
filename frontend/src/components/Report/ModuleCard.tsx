import React from 'react';
import { Crosshair } from 'lucide-react';
import type { CourseModule } from '../../types';

interface Props {
  mod: CourseModule;
}

export const ModuleCard: React.FC<Props> = ({ mod }) => {
  return (
    <div className="report-card playbook-card">
      <h3 className="playbook-title">Module {mod.module_number}: {mod.module_title}</h3>
      <p className="card-context">{mod.description}</p>
      
      <div style={{ marginTop: '16px' }}>
        <h4 style={{ fontSize: '13px', color: '#cbd5e1', marginBottom: '8px' }}>Lessons:</h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {mod.lessons?.map((lesson, i) => (
            <div key={i} style={{ background: 'rgba(0,0,0,0.2)', padding: '12px', borderRadius: '6px' }}>
              <strong style={{ display: 'block', color: '#818cf8', fontSize: '13px', marginBottom: '4px' }}>{lesson.lesson_title}</strong>
              <p style={{ fontSize: '12px', color: '#94a3b8' }}>{lesson.details}</p>
            </div>
          ))}
        </div>
      </div>

      {mod.assignments_or_exercises?.length > 0 && (
        <div style={{ marginTop: '16px', borderTop: '1px solid #334155', paddingTop: '12px' }}>
          <h4 style={{ fontSize: '13px', color: '#cbd5e1', marginBottom: '8px' }}>
            <Crosshair size={12} style={{ display: 'inline', marginRight: '4px' }} /> Exercises:
          </h4>
          <ul className="playbook-steps">
            {mod.assignments_or_exercises.map((ex, i) => (
              <li key={i} style={{ fontSize: '12px' }}>{ex}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
