import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { useInterviewContext } from '../context/InterviewContext';

export const InterviewSetup: React.FC = () => {
  const navigate = useNavigate();
  const { setSessionId, setCourseMetadata, setScript, setScriptProgress, addMessage } = useInterviewContext();
  const [loading, setLoading] = useState(false);
  
  const [formData, setFormData] = useState({
    course_title: '',
    tutor_name: '',
    tutor_role: '',
    tutor_experience: '',
    target_audience: '',
    prerequisites: '',
    completion_time: '',
    north_star_outcome: '',
    topic: 'Course Planning'
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleStart = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const sessionId = 'session_' + Date.now();
      setSessionId(sessionId);
      setCourseMetadata(formData);
      
      const payload = {
        user_session_id: sessionId,
        ...formData
      };
      
      const res = await api.post('/prepare-interview', payload);
      setScript(res.data.script);
      setScriptProgress(`0/${res.data.total_questions}`);
      
      addMessage({
        id: Date.now().toString(),
        role: 'ai',
        text: res.data.first_question
      });
      
      navigate('/preview');
    } catch (err) {
      console.error(err);
      alert('Failed to generate script. Check logs.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="layout-container setup-container">
      <nav style={{ marginBottom: '32px' }}>
        <Link to="/" className="btn-ghost" style={{ padding: '8px 16px', display: 'inline-flex', alignItems: 'center', gap: '8px', fontSize: '13px' }}>
          <ArrowLeft size={16} /> Back to Dashboard
        </Link>
      </nav>
      
      <div className="setup-header">
        <h1 className="setup-title">Course Blueprint Context</h1>
        <p className="setup-subtitle">Provide the high-level goals. The AI will generate a dynamic, tailored interview script to extract your tacit knowledge.</p>
      </div>
      
      <form onSubmit={handleStart} className="setup-form-container">
        
        {/* Section 1: The Basics */}
        <div className="setup-form-section">
          <div className="setup-section-header">
            <h3>1. The Basics</h3>
            <p>Who is teaching and what is the course?</p>
          </div>
          
          <div className="setup-grid">
            <div className="input-group">
              <label className="input-label">Course Title</label>
              <input name="course_title" className="input-field" placeholder="e.g. Advanced Microservices in Go" value={formData.course_title} onChange={handleChange} required />
            </div>
            <div className="input-group">
              <label className="input-label">Expected Completion Time</label>
              <input name="completion_time" className="input-field" placeholder="e.g. 6 weeks, 2 hours/week" value={formData.completion_time} onChange={handleChange} required />
            </div>
          </div>
        </div>

        {/* Section 2: The Instructor */}
        <div className="setup-form-section">
          <div className="setup-section-header">
            <h3>2. The Instructor</h3>
            <p>Establish your authority and persona.</p>
          </div>

          <div className="setup-grid">
            <div className="input-group">
              <label className="input-label">Tutor Name</label>
              <input name="tutor_name" className="input-field" placeholder="e.g. Sarah Jenkins" value={formData.tutor_name} onChange={handleChange} required />
            </div>
            <div className="input-group">
              <label className="input-label">Tutor Role</label>
              <input name="tutor_role" className="input-field" placeholder="e.g. Staff Engineer @ Stripe" value={formData.tutor_role} onChange={handleChange} required />
            </div>
            <div className="input-group" style={{ gridColumn: '1 / -1' }}>
              <label className="input-label">Tutor Experience</label>
              <textarea name="tutor_experience" className="input-field" placeholder="e.g. 10 years designing distributed systems that handle millions of requests..." rows={2} value={formData.tutor_experience} onChange={handleChange} required />
            </div>
          </div>
        </div>

        {/* Section 3: The Audience & Goals */}
        <div className="setup-form-section">
          <div className="setup-section-header">
            <h3>3. Audience & Transformation</h3>
            <p>Who are they now, and who will they become?</p>
          </div>

          <div className="setup-grid">
            <div className="input-group" style={{ gridColumn: '1 / -1' }}>
              <label className="input-label">Target Audience</label>
              <textarea name="target_audience" className="input-field" placeholder="e.g. Mid-level backend engineers wanting to master scalable architecture" rows={2} value={formData.target_audience} onChange={handleChange} required />
            </div>
            <div className="input-group" style={{ gridColumn: '1 / -1' }}>
              <label className="input-label">Prerequisites</label>
              <textarea name="prerequisites" className="input-field" placeholder="e.g. Basic understanding of Go syntax and Docker" rows={2} value={formData.prerequisites} onChange={handleChange} required />
            </div>
            <div className="input-group" style={{ gridColumn: '1 / -1' }}>
              <label className="input-label">North Star Outcome</label>
              <textarea name="north_star_outcome" className="input-field" placeholder="e.g. Build and deploy a fully scalable, fault-tolerant microservice ecosystem" rows={2} value={formData.north_star_outcome} onChange={handleChange} required />
            </div>
          </div>
        </div>

        <div className="setup-submit-zone">
          <button type="submit" className="btn-primary btn-glow" disabled={loading}>
            {loading ? <><Loader2 className="spin" size={18} /> Crafting AI Script...</> : 'Generate Script'}
          </button>
        </div>
      </form>
    </div>
  );
};
