import React from 'react';
import { ArrowRight, BrainCircuit, Database, Zap } from 'lucide-react';
import { Link } from 'react-router-dom';

export const HeroSection: React.FC = () => {
  return (
    <>
      <nav className="landing-nav">
        <div className="landing-logo">
          <div className="landing-logo-icon"><BrainCircuit size={20} /></div>
          <span>Course Architect AI</span>
        </div>
        <div className="landing-nav-actions">
          <Link to="/setup" className="btn-primary" style={{ padding: '8px 20px', fontSize: '13px' }}>Start Session</Link>
        </div>
      </nav>

      <main className="landing-hero">
        <div className="landing-badge">
          <Zap size={12} /> AI Tacit Knowledge Extraction Pipeline
        </div>
        
        <h1 className="landing-title">Turn Your Messy Expertise<br/>Into A Course Blueprint.</h1>
        <p className="landing-subtitle">
          Feed the AI your raw notes, youtube videos, and scattered thoughts. 
          Then, jump into a live interview where the AI plays the role of your day-one student.
        </p>

        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <Link to="/ingest" className="btn-ghost">
            <Database size={16} /> Knowledge Hub
          </Link>
          <Link to="/setup" className="btn-primary">
            Start Extraction Interview <ArrowRight size={18} />
          </Link>
        </div>
      </main>

      <footer className="landing-stats">
        <div className="stat-item">
          <label>Phase 1</label>
          <span>Data Ingestion & RAG</span>
        </div>
        <div className="stat-item">
          <label>Phase 2</label>
          <span>Dynamic Script Crafting</span>
        </div>
        <div className="stat-item">
          <label>Phase 3</label>
          <span>Live Audio Interview</span>
        </div>
        <div className="stat-item">
          <label>Phase 4</label>
          <span>Course Blueprint Synthesis</span>
        </div>
      </footer>
    </>
  );
};
