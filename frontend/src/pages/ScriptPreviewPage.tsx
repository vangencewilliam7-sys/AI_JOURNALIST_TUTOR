import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useInterviewContext } from '../context/InterviewContext';
import { ArrowLeft, BookOpen, Loader2 } from 'lucide-react';
import { PhaseBlock } from '../components/ScriptPreview/PhaseBlock';
import { ThemeCard } from '../components/ScriptPreview/ThemeCard';
import { api } from '../services/api';

export const ScriptPreviewPage: React.FC = () => {
  const { script, sessionId } = useInterviewContext();
  const navigate = useNavigate();

  if (!script) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <h2>No Active Script Found</h2>
        <button className="btn-primary" onClick={() => navigate('/setup')} style={{ marginTop: '16px' }}>Go to Setup</button>
      </div>
    );
  }

  const arc = script.interview_arc;

  const handleStartInterview = async () => {
    // Navigate directly to the interview room since the session is already active
    navigate('/interview');
  };

  return (
    <div className="layout-container script-page">
      <header className="script-header">
        <div className="script-header-left">
          <button className="btn-ghost" onClick={() => navigate('/setup')} style={{ padding: '8px', border: 'none' }}>
            <ArrowLeft size={18} />
          </button>
          <div>
            <h1>AI-Generated Extraction Script</h1>
            <small>Review the blueprint before beginning the interview</small>
          </div>
        </div>
        <button className="btn-go-live" onClick={handleStartInterview}>
          Start Live Interview
        </button>
      </header>

      <div className="script-body">
        <div className="script-layout">
          <div className="script-main">
            <div className="section-label">
              <div className="section-label-dot" /> Interview Phases
            </div>
            
            <PhaseBlock number={1} title="Genesis & Audience" phase={arc.phase_1_genesis_audience} />
            <PhaseBlock number={2} title="Module Breakdown" phase={arc.phase_2_module_breakdown} />
            <PhaseBlock number={3} title="Deep Dives & Scenarios" phase={arc.phase_3_deep_dives} />
          </div>

          <aside className="script-sidebar">
            <div className="section-label">
              <div className="section-label-dot" style={{ background: '#10b981' }} /> Discovered Themes
            </div>
            
            {script.metadata?.themes ? (
              script.metadata.themes.map((t: any, i: number) => (
                <ThemeCard key={i} theme={t} />
              ))
            ) : (
              <p style={{ fontSize: '13px', color: 'var(--text-dim)' }}>No specific themes extracted.</p>
            )}

            <div className="info-box">
              <div className="info-box-header">
                <BookOpen size={16} /> Note
              </div>
              <p>The AI will use these generated questions as a baseline, but will dynamically ask follow-ups based on your live answers to dig deeper.</p>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
};
