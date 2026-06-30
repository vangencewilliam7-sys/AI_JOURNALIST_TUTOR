import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  BrainCircuit, Database, ChevronRight, Sparkles, Cpu, Activity, BookOpen, Loader2, CloudDownload, User, LogOut
} from 'lucide-react';
import { supabase } from '../supabaseClient';
import AutocompleteInput from '../components/AutocompleteInput';

const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const { session } = useAuth();
  const [view, setView] = useState<'landing' | 'tutor_setup' | 'ingest'>('landing');
  const [selectedDomain, setSelectedDomain] = useState<'Tutor' | 'IT' | 'Healthcare'>('Tutor');
  const [isSubmittingProfile, setIsSubmittingProfile] = useState(false);
  const [tutorProfile, setTutorProfile] = useState({
    current_title: '',
    expertise_streams: '',
    years_of_experience: 0,
    short_bio: '',
    target_audience: '',
  });
  const [activeSession, setActiveSession] = useState<any>(null);
  const [hasPendingInsights, setHasPendingInsights] = useState<boolean>(false);
  const [suggestions, setSuggestions] = useState<Record<string, (string | number)[]>>({
    domain: [], target_audience: [], short_bio: [], years_of_experience: []
  });

  useEffect(() => {
    if (!session?.user?.id) return;
    
    supabase.from('interview_sessions')
      .select('id, status, iteration_number')
      .eq('expert_id', session.user.id)
      .order('created_at', { ascending: false })
      .limit(1)
      .then(res => {
        if (res.data && res.data.length > 0) {
          const latest = res.data[0];
          setActiveSession(latest);
          
          supabase.from('expert_tacit_insights')
            .select('id')
            .eq('session_id', latest.id)
            .eq('status', 'pending')
            .limit(1)
            .then(insRes => {
              if (insRes.data && insRes.data.length > 0) {
                setHasPendingInsights(true);
              }
            });
        }
      });
  }, [session]);

  // Fetch autocomplete suggestions from server on mount
  useEffect(() => {
    if (!session?.access_token) return;
    fetch('http://localhost:9120/field-suggestions', {
      headers: { 'Authorization': `Bearer ${session.access_token}` }
    })
      .then(r => r.json())
      .then(data => { if (data.suggestions) setSuggestions(data.suggestions); })
      .catch(() => {});
  }, [session]);

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    navigate('/login');
  };

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmittingProfile(true);
    try {
      const res = await fetch('http://localhost:9120/intake', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${session?.access_token}` },
        body: JSON.stringify({
          name: session?.user?.user_metadata?.name || session?.user?.email?.split('@')[0],
          domain: tutorProfile.expertise_streams,
          stream_type: selectedDomain === 'Tutor' ? 'tutor' : 'general',
          target_audience: tutorProfile.target_audience,
          years_of_experience: tutorProfile.years_of_experience,
          short_bio: tutorProfile.short_bio
        })
      });
      const data = await res.json();
      
      if (data.status === 'success') {
        localStorage.setItem('expert_id', data.expert_id);
        localStorage.setItem('session_id', data.session_id);
        if (data.icebreaker) {
           localStorage.setItem('icebreaker', JSON.stringify(data.icebreaker));
        }
        navigate('/script');
      } else {
        console.error("Intake failed", data);
        alert("Failed to initialize session. Make sure backend is running.");
      }
    } catch (error) {
      console.error(error);
      alert("Network error. Backend down?");
    } finally {
      setIsSubmittingProfile(false);
    }
  };

  if (view === 'tutor_setup') {
    return (
      <div className="ingest-page">
        <div className="ingest-container" style={{ maxWidth: '800px', width: '100%' }}>
          <button className="back-link" onClick={() => setView('landing')}>
            <ChevronRight size={14} style={{ transform: 'rotate(180deg)' }} /> Back to Home
          </button>
          <h2 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '4px' }}>
            <Database size={20} style={{ verticalAlign: '-3px', marginRight: '8px', color: 'var(--accent)' }} />
            Session Intake — Expert Profile
          </h2>
          <p style={{ color: 'var(--text-dim)', fontSize: '13px', marginBottom: '32px' }}>Configure the expert metadata before launching the AI Journalist session.</p>

          <form onSubmit={handleProfileSubmit} className="setup-form">
            <div className="setup-grid">
              
              <div className="setup-col">
                <div className="setup-col-header">
                  <User size={16} /> Expert Identity
                </div>


                
                <div className="input-group">
                  <label>Current Title</label>
                  <AutocompleteInput
                    required
                    className="input-field"
                    value={tutorProfile.current_title}
                    onChange={val => setTutorProfile({...tutorProfile, current_title: val})}
                    suggestions={suggestions.domain || []}
                    placeholder="e.g. Senior Backend Engineer"
                  />
                </div>

                <div className="input-group">
                  <label>Years of Experience</label>
                  <AutocompleteInput
                    required
                    type="number"
                    className="input-field"
                    value={tutorProfile.years_of_experience}
                    onChange={val => setTutorProfile({...tutorProfile, years_of_experience: parseInt(val) || 0})}
                    suggestions={suggestions.years_of_experience || []}
                    placeholder="e.g. 8"
                  />
                </div>

                <div className="input-group">
                  <label>Core Domain / Specialization</label>
                  <AutocompleteInput
                    required
                    className="input-field"
                    value={tutorProfile.expertise_streams}
                    onChange={val => setTutorProfile({...tutorProfile, expertise_streams: val})}
                    suggestions={suggestions.domain || []}
                    placeholder="e.g. Distributed Systems, Cloud Architecture"
                  />
                </div>
              </div>

              <div className="setup-col">
                <div className="setup-col-header">
                  <Sparkles size={16} /> Session Configuration
                </div>
                
                <div className="input-group">
                  <label>Target Audience</label>
                  <AutocompleteInput
                    required
                    className="input-field"
                    value={tutorProfile.target_audience}
                    onChange={val => setTutorProfile({...tutorProfile, target_audience: val})}
                    suggestions={suggestions.target_audience || []}
                    placeholder="e.g. Junior to Mid-Level Software Engineers"
                  />
                </div>

                <div className="input-group">
                  <label>Expert Bio / Context</label>
                  <AutocompleteInput
                    required
                    isTextarea
                    className="input-field"
                    style={{ minHeight: '120px' }}
                    value={tutorProfile.short_bio}
                    onChange={val => setTutorProfile({...tutorProfile, short_bio: val})}
                    suggestions={suggestions.short_bio || []}
                    placeholder="Brief background about the expert..."
                  />
                </div>

              </div>

            </div>

            <button type="submit" className="btn-primary" disabled={isSubmittingProfile} style={{ marginTop: '24px', width: '100%', justifyContent: 'center' }}>
              {isSubmittingProfile ? <><Loader2 size={16} className="spin" /> Initializing Session...</> : 'Initialize Session & Generate Script'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  if (view === 'ingest') {
    return (
      <div className="ingest-page">
         <div className="ingest-container" style={{ maxWidth: '800px', width: '100%', margin: '0 auto', paddingTop: '60px' }}>
          <button className="back-link" onClick={() => setView('landing')}>
            <ChevronRight size={14} style={{ transform: 'rotate(180deg)' }} /> Back to Home
          </button>
          <h2 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '4px', marginTop: '24px' }}>
            {selectedDomain === 'IT' ? <Cpu size={24} style={{ verticalAlign: '-4px', marginRight: '8px', color: '#38bdf8' }} /> : <Activity size={24} style={{ verticalAlign: '-4px', marginRight: '8px', color: '#fbbf24' }} />}
            {selectedDomain} Knowledge Hub
          </h2>
          <p style={{ color: 'var(--text-dim)', fontSize: '14px', marginBottom: '32px' }}>Upload documents, wikis, or transcripts to give the AI Journalist context before the interview.</p>
          
          <div style={{ border: '2px dashed var(--border)', padding: '60px 40px', textAlign: 'center', borderRadius: 'var(--radius)', background: 'var(--bg-card)', transition: 'all 0.2s' }} onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--accent)'} onMouseLeave={(e) => e.currentTarget.style.borderColor = 'var(--border)'}>
             <CloudDownload size={48} style={{ color: 'var(--accent)', marginBottom: '16px' }} />
             <h3 style={{ margin: '0 0 12px 0', fontSize: '14px', fontFamily: '"Press Start 2P", cursive', textTransform: 'uppercase', color: 'var(--text)' }}>Drag and drop documents</h3>
             <p style={{ color: 'var(--text-dim)', fontSize: '14px', margin: '0 0 24px 0' }}>Supports PDF, TXT, DOCX, and Youtube Links</p>
             <button className="btn-primary" onClick={() => document.getElementById('file-upload')?.click()} style={{ margin: '0 auto' }}>Browse Files</button>
             <input id="file-upload" type="file" style={{ display: 'none' }} multiple onChange={(e) => {
                 if (e.target.files && e.target.files.length > 0) {
                     navigate('/script');
                 }
             }} />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="landing">
      <nav className="landing-nav">
        <div className="landing-logo">
          <div className="landing-logo-icon"><BrainCircuit size={20} /></div>
          AI Journalist
        </div>
        <div className="landing-nav-actions">
          <button className="btn-ghost" onClick={() => navigate('/knowledge')}>Tacit Knowledge Dashboard</button>
          <button className="btn-ghost" onClick={() => navigate('/homework')}>Homework Dashboard</button>
          <button className="btn-ghost" onClick={handleSignOut} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <LogOut size={14} /> Log Out
          </button>
        </div>
      </nav>
      <div className="landing-hero">
        <h1 className="landing-title">Extract Your<br />Unwritten Knowledge.</h1>
        <p className="landing-subtitle">Synthesizing expert tacit knowledge into a structured knowledge blueprint.</p>
        
        {hasPendingInsights && activeSession && (
          <div style={{ 
            background: 'rgba(124,106,255,0.08)', 
            border: '1px solid var(--accent, #7c6aff)', 
            borderRadius: '12px', 
            padding: '16px 24px', 
            margin: '24px auto 0 auto', 
            maxWidth: '650px', 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            textAlign: 'left'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div style={{ background: 'rgba(124,106,255,0.15)', padding: '10px', borderRadius: '50%', color: 'var(--accent, #7c6aff)' }}>
                <BrainCircuit size={24} />
              </div>
              <div>
                <div style={{ fontWeight: 600, fontSize: '15px', color: 'var(--text)' }}>Verify Extracted Insights</div>
                <div style={{ fontSize: '13px', color: 'var(--text-dim)', marginTop: '4px' }}>
                  You have pending tacit insights from Session Iteration {activeSession.iteration_number} to review.
                </div>
              </div>
            </div>
            <button 
              className="btn-primary" 
              onClick={() => navigate(`/verify-insights/${activeSession.id}`)}
              style={{ fontSize: '13px', padding: '10px 20px', whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              Verify Now <ChevronRight size={14} />
            </button>
          </div>
        )}

        <div style={{ display: 'flex', gap: '20px', justifyContent: 'center', marginTop: '40px', flexWrap: 'wrap' }}>
           <div 
             style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '30px', width: '220px', cursor: 'pointer', transition: 'all 0.2s', boxShadow: 'var(--shadow-sm)' }}
             onClick={() => { setSelectedDomain('Tutor'); setView('tutor_setup'); }}
             onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = 'var(--shadow-md)'; e.currentTarget.style.borderColor = 'var(--accent)'; }}
             onMouseLeave={(e) => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.boxShadow = 'var(--shadow-sm)'; e.currentTarget.style.borderColor = 'var(--border)'; }}
           >
              <BookOpen size={32} style={{ color: 'var(--accent)', marginBottom: '16px' }} />
              <h3 style={{ margin: '0 0 12px 0', fontSize: '12px', fontFamily: '"Press Start 2P", cursive', textTransform: 'uppercase', lineHeight: '1.4', color: 'var(--text)' }}>Tutor</h3>
              <p style={{ color: 'var(--text-dim)', fontSize: '13px', margin: 0 }}>Build a course blueprint from your expertise.</p>
           </div>
           
           <div 
             style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '30px', width: '220px', cursor: 'pointer', transition: 'all 0.2s', boxShadow: 'var(--shadow-sm)' }}
             onClick={() => { setSelectedDomain('IT'); setView('ingest'); }}
             onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = 'var(--shadow-md)'; e.currentTarget.style.borderColor = 'var(--accent)'; }}
             onMouseLeave={(e) => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.boxShadow = 'var(--shadow-sm)'; e.currentTarget.style.borderColor = 'var(--border)'; }}
           >
              <Cpu size={32} style={{ color: 'var(--accent)', marginBottom: '16px' }} />
              <h3 style={{ margin: '0 0 12px 0', fontSize: '12px', fontFamily: '"Press Start 2P", cursive', textTransform: 'uppercase', lineHeight: '1.4', color: 'var(--text)' }}>IT Pro</h3>
              <p style={{ color: 'var(--text-dim)', fontSize: '13px', margin: 0 }}>Extract technical playbooks and war stories.</p>
           </div>

           <div 
             style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '30px', width: '220px', cursor: 'pointer', transition: 'all 0.2s', boxShadow: 'var(--shadow-sm)' }}
             onClick={() => { setSelectedDomain('Healthcare'); setView('ingest'); }}
             onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = 'var(--shadow-md)'; e.currentTarget.style.borderColor = 'var(--accent)'; }}
             onMouseLeave={(e) => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.boxShadow = 'var(--shadow-sm)'; e.currentTarget.style.borderColor = 'var(--border)'; }}
           >
              <Activity size={32} style={{ color: 'var(--accent)', marginBottom: '16px' }} />
              <h3 style={{ margin: '0 0 12px 0', fontSize: '12px', fontFamily: '"Press Start 2P", cursive', textTransform: 'uppercase', lineHeight: '1.4', color: 'var(--text)' }}>Health</h3>
              <p style={{ color: 'var(--text-dim)', fontSize: '13px', margin: 0 }}>Extract clinical heuristics and instinct.</p>
           </div>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;
