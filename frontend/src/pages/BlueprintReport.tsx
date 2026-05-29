import React from 'react';
import { BookOpen, Users, Rocket, Crosshair, ArrowLeft } from 'lucide-react';
import { useInterviewContext } from '../context/InterviewContext';
import { ModuleCard } from '../components/Report/ModuleCard';
import { DeepExtractionGrid } from '../components/Report/DeepExtractionGrid';
import { Link, useNavigate } from 'react-router-dom';

export const BlueprintReport: React.FC = () => {
  const { blueprint, resetInterviewState } = useInterviewContext();
  const navigate = useNavigate();

  if (!blueprint) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <h2>No Blueprint Available</h2>
        <button className="btn-primary" onClick={() => navigate('/')} style={{ marginTop: '16px' }}>Go Home</button>
      </div>
    );
  }

  const handleStartOver = () => {
    resetInterviewState();
    navigate('/setup');
  };

  return (
    <div className="layout-container">
      <nav style={{ marginBottom: '40px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Link to="/" className="btn-ghost" style={{ padding: '0' }}><ArrowLeft size={16} /> Back to Dashboard</Link>
        <button className="btn-primary" onClick={handleStartOver}>Start New Course Extract</button>
      </nav>

      <div style={{ maxWidth: '900px', margin: '0 auto' }}>
        <header style={{ marginBottom: '40px', borderBottom: '1px solid #334155', paddingBottom: '32px' }}>
          <div style={{ display: 'inline-block', padding: '4px 12px', background: 'rgba(99,102,241,0.1)', color: '#818cf8', borderRadius: '100px', fontSize: '11px', fontWeight: 800, letterSpacing: '0.5px', marginBottom: '16px' }}>
            FINAL SYNTHESIS
          </div>
          <h1 style={{ fontSize: '36px', fontWeight: 900, marginBottom: '16px', lineHeight: 1.2 }}>{blueprint.course_title}</h1>
          <p style={{ fontSize: '16px', color: '#94a3b8', lineHeight: 1.6 }}>{blueprint.summary}</p>
        </header>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '48px' }}>
          <div className="report-card">
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', color: '#cbd5e1', marginBottom: '8px' }}>
              <Users size={16} style={{ color: '#fbbf24' }} /> Target Audience
            </h3>
            <p style={{ fontSize: '14px' }}>{blueprint.target_audience}</p>
          </div>
          <div className="report-card">
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', color: '#cbd5e1', marginBottom: '8px' }}>
              <Rocket size={16} style={{ color: '#34d399' }} /> North Star Outcome
            </h3>
            <p style={{ fontSize: '14px' }}>{blueprint.north_star_outcome}</p>
          </div>
        </div>

        <div style={{ marginBottom: '48px' }}>
          <h2 style={{ fontSize: '24px', fontWeight: 800, marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '12px' }}>
            <BookOpen style={{ color: '#818cf8' }} /> Module Breakdown ({blueprint.total_modules})
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {blueprint.course_modules?.map((mod, i) => (
              <ModuleCard key={i} mod={mod} />
            ))}
          </div>
        </div>

        <div style={{ marginBottom: '48px' }}>
          <h2 style={{ fontSize: '24px', fontWeight: 800, marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Crosshair style={{ color: '#f43f5e' }} /> Deep Extraction Matrix
          </h2>
          <p style={{ color: '#94a3b8', marginBottom: '20px' }}>Tacit knowledge mapped from your interview answers.</p>
          <DeepExtractionGrid blueprint={blueprint} />
        </div>

        {blueprint.marketing_hooks?.length > 0 && (
          <div>
            <h2 style={{ fontSize: '24px', fontWeight: 800, marginBottom: '24px' }}>Marketing Hooks</h2>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              {blueprint.marketing_hooks.map((hook, i) => (
                <div key={i} className="report-card" style={{ padding: '20px', borderLeft: '4px solid #818cf8' }}>
                  <p style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>"{hook.hook}"</p>
                  <p style={{ fontSize: '12px', color: '#94a3b8' }}><em>Why it works:</em> {hook.why_it_works}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
