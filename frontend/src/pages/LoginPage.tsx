import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../supabaseClient';
import { BrainCircuit, Lock, Mail, ChevronRight, Loader2, User } from 'lucide-react';
import '../index.css';
import './LoginPage.css';

export const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const navigate = useNavigate();

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (isLogin) {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
        navigate('/landing');
      } else {
        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            data: {
              name: name || email.split('@')[0],
              domain: 'General',
              stream_type: 'general'
            }
          }
        });
        if (error) throw error;
        navigate('/landing');
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-left">
        <div className="login-pattern"></div>
        <div className="login-glow"></div>
        
        <div className="login-brand">
          <div className="login-logo">
            <div className="login-logo-icon">
              <BrainCircuit size={24} />
            </div>
            AI Journalist
          </div>
          
          <h2 className="login-title">Distill your tacit knowledge.</h2>
          <p className="login-subtitle">
            A secure, private space for domain experts to unpack their mental models, war stories, and deeply held frameworks through conversational AI.
          </p>
          
          <div className="login-secure-badge">
            <Lock size={16} />
            End-to-end secure authentication via Supabase
          </div>
        </div>
      </div>

      <div className="login-right">
        <div className="login-form-container">
          <div className="login-form-header">
            <h3>{isLogin ? 'Welcome back' : 'Create your vault'}</h3>
            <p>{isLogin ? 'Enter your credentials to access your session history.' : 'Sign up to start your first intake interview.'}</p>
          </div>

          <form onSubmit={handleAuth} className="login-form">
            {!isLogin && (
              <div className="input-group">
                <label>Full Name</label>
                <div className="input-wrapper">
                  <User size={18} className="input-icon" />
                  <input
                    type="text"
                    required={!isLogin}
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="input-field"
                    style={{ paddingLeft: '40px' }}
                    placeholder="Jane Doe"
                  />
                </div>
              </div>
            )}
            
            <div className="input-group">
              <label>Email address</label>
              <div className="input-wrapper">
                <Mail size={18} className="input-icon" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input-field"
                  style={{ paddingLeft: '40px' }}
                  placeholder="expert@domain.com"
                />
              </div>
            </div>

            <div className="input-group">
              <label>Password</label>
              <div className="input-wrapper">
                <Lock size={18} className="input-icon" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-field"
                  style={{ paddingLeft: '40px' }}
                  placeholder="••••••••"
                />
              </div>
            </div>

            {error && (
              <div className="login-error">
                {error}
              </div>
            )}

            <button type="submit" disabled={loading} className="btn-primary" style={{ width: '100%', justifyContent: 'center', marginTop: '12px' }}>
              {loading ? (
                <Loader2 size={16} className="spin" />
              ) : (
                <>
                  {isLogin ? 'Sign In' : 'Create Account'}
                  <ChevronRight size={16} />
                </>
              )}
            </button>
          </form>

          <div className="login-footer">
            <button onClick={() => { setIsLogin(!isLogin); setError(null); }} className="login-toggle-btn">
              {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
