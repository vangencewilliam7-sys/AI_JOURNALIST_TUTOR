import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { supabase } from '../supabaseClient';
import { Mic, MicOff, Send, PauseCircle, Loader2, BrainCircuit, Eye, Target, Zap, FileText, ArrowRight } from 'lucide-react';

interface Message {
  id: string;
  role: 'expert' | 'ai';
  text: string;
  timestamp: number;
  decision?: {
    intent_classification: string;
    internal_reasoning: string;
    action: string;
  };
}

// Helper to parse transcript strings into Message objects
const parseTranscriptToMessages = (transcript: string, reentryStatement?: string): Message[] => {
  const parsedMessages: Message[] = [];
  const lines = transcript.split('\n');
  let currentRole: 'ai' | 'expert' = 'ai';
  let currentText = '';
  for (const line of lines) {
    if (line.startsWith('[AI JOURNALIST]: ')) {
      if (currentText) parsedMessages.push({ id: Math.random().toString(), role: currentRole, text: currentText.trim(), timestamp: Date.now() });
      currentRole = 'ai';
      currentText = line.substring(17) + '\n';
    } else if (line.startsWith('[EXPERT]: ')) {
      if (currentText) parsedMessages.push({ id: Math.random().toString(), role: currentRole, text: currentText.trim(), timestamp: Date.now() });
      currentRole = 'expert';
      currentText = line.substring(10) + '\n';
    } else if (line.startsWith('[SCRIPT]: ')) {
      // Ignore script stamping lines
    } else {
      currentText += line + '\n';
    }
  }
  if (currentText.trim()) parsedMessages.push({ id: Math.random().toString(), role: currentRole, text: currentText.trim(), timestamp: Date.now() });

  if (reentryStatement) {
    parsedMessages.push({
      id: 'reentry',
      role: 'ai',
      text: reentryStatement,
      timestamp: Date.now(),
      decision: { intent_classification: 're_entry', internal_reasoning: 'Resumed session.', action: 'continue' }
    });
  }
  return parsedMessages;
};
// ─── 2D pointer position returned by advanceTeleprompter ─────────────────────
interface Pointer {
  blockIdx: number;
  qIdx: number;
}

const InterviewPage: React.FC = () => {
  const navigate = useNavigate();
  const { session } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing] = useState(false);
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [nextSessionId, setNextSessionId] = useState<string | null>(null);
  const [isChapterComplete, setIsChapterComplete] = useState(false);
  const [hasPendingHomework, setHasPendingHomework] = useState(false);
  const [showDecision, setShowDecision] = useState<string | null>(null);
  const [sessionMeta, setSessionMeta] = useState({ iteration: 1, id: 'SESS-DAY-1' });
  const scrollRef = useRef<HTMLDivElement>(null);

  const [showScriptSidebar, setShowScriptSidebar] = useState(true);
  const [scriptThemes, setScriptThemes] = useState<any[]>([]);
  const [tangentCount, setTangentCount] = useState(0);

  // ─── 2D Pointer State Machine ─────────────────────────────────────────────
  const [activeBlockIdx, setActiveBlockIdx] = useState(0);
  const [activeQuestionIdx, setActiveQuestionIdx] = useState(0);

  // Derived values — always in sync with pointer, no extra state to desync
  const activeBlock = scriptThemes[activeBlockIdx]?.theme_title ?? 'Block 1: Personal Origin & Persona';
  const currentActiveQuestion = scriptThemes[activeBlockIdx]?.questions?.[activeQuestionIdx]?.question_text ?? '';

  const sessionId = localStorage.getItem('session_id');
  const icebreakerData = JSON.parse(localStorage.getItem('icebreaker') || '{}');
  const hasSeededRef = useRef(false);

  useEffect(() => {
    if (!sessionId) {
      navigate('/');
      return;
    }

    if (hasSeededRef.current) return;

    const restoredTranscript = localStorage.getItem('restored_transcript');
    const reentryStatement = localStorage.getItem('reentry_statement');

    if (restoredTranscript && reentryStatement) {
      setMessages(parseTranscriptToMessages(restoredTranscript, reentryStatement));
      localStorage.removeItem('restored_transcript');
      localStorage.removeItem('reentry_statement');
    } else {
      // Seed the conversation with a generic opening temporarily, it will be overwritten if DB has history
      setMessages([
        {
          id: '1',
          role: 'ai',
          text: icebreakerData.opening_icebreaker || "Welcome to the studio. We're excited to dive into your background and extract the unwritten rules of your domain.",
          timestamp: Date.now() - 600000,
          decision: {
            intent_classification: 'opening_question',
            internal_reasoning: 'Day 1 opening icebreaker from the generated script.',
            action: 'script_question'
          }
        }
      ]);
    }

    hasSeededRef.current = true;

    // Fetch the script data for the sidebar
    fetch(`http://localhost:9120/session/${sessionId}`, { headers: { 'Authorization': `Bearer ${session?.access_token}` } })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success' && data.session) {
          setSessionMeta({
            iteration: data.session.iteration_number || 1,
            id: data.session.id || 'SESS-DAY-1'
          });
        }
        if (data.status === 'success' && data.session?.script) {
          const arc = data.session.script.interview_arc || data.session.script;
          // Sort entries by block number to guarantee correct display order (block_1 → block_2 → … → block_5)
          // Object.entries() does NOT guarantee insertion order on plain objects, so we sort explicitly.
          const extractedThemes = Object.entries(arc || {})
            .sort(([keyA], [keyB]) => {
              // Extract the leading number from keys like "block_1_origin", "block_2_learning_journey", etc.
              const numA = parseInt(keyA.match(/\d+/)?.[0] ?? '0', 10);
              const numB = parseInt(keyB.match(/\d+/)?.[0] ?? '0', 10);
              return numA - numB;
            })
            .map(([key, phase]: [string, any], idx) => ({
              theme_id: idx,
              theme_title: key.replace('block_', 'Block ').replace(/_/g, ' '),
              editorial_rationale: phase.goal || "Phase goal",
              tentative_duration: phase.tentative_duration_minutes || 20,
              questions: phase.questions || []
            }));
          setScriptThemes(extractedThemes);

          const dbTranscript = data.session.raw_transcript;
          const dbSnapshot = data.session.snapshot;

          // If we didn't just resume (restoredTranscript is null) but the DB actually has a chat history, load it!
          if (!restoredTranscript && dbTranscript && dbTranscript.includes('[EXPERT]:')) {
            setMessages(parseTranscriptToMessages(dbTranscript));
          }

          const restoredSnapshotStr = localStorage.getItem('restored_snapshot');
          let finalSnapshot = dbSnapshot;

          if (restoredSnapshotStr) {
            try {
              finalSnapshot = JSON.parse(restoredSnapshotStr);
            } catch (e) { console.error("Error parsing snapshot", e); }
            localStorage.removeItem('restored_snapshot');
          }

          if (finalSnapshot && finalSnapshot.active_block) {
            const bIdx = extractedThemes.findIndex(t => t.theme_title === finalSnapshot.active_block);
            if (bIdx >= 0) {
              setActiveBlockIdx(bIdx);
              const qIdx = extractedThemes[bIdx].questions.findIndex((q: any) => q.question_text === finalSnapshot.current_script_question);
              if (qIdx >= 0) setActiveQuestionIdx(qIdx);
            }
            setTangentCount(finalSnapshot.tangent_count || 0);
          } else if (data.session.current_block) {
            const targetStr = data.session.current_block.toLowerCase();
            const bIdx = extractedThemes.findIndex(t => t.theme_title.toLowerCase().includes(targetStr) || targetStr.includes(t.theme_title.toLowerCase()));
            if (bIdx >= 0) {
              setActiveBlockIdx(bIdx);
            } else if (data.session.iteration_number > 1 && extractedThemes.length > 1) {
              setActiveBlockIdx(1);
            } else {
              setActiveBlockIdx(0);
            }
            setActiveQuestionIdx(0);
          } else if (data.session.iteration_number > 1 && extractedThemes.length > 1) {
            setActiveBlockIdx(1);
            setActiveQuestionIdx(0);
          } else {
            setActiveBlockIdx(0);
            setActiveQuestionIdx(0);
          }
        }
      })
      .catch(err => console.error("Failed to fetch session script", err));

    hasSeededRef.current = true;
  }, [sessionId, navigate]);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages]);

  // ─── advanceTeleprompter ──────────────────────────────────────────────────
  // Returns the NEW pointer position synchronously so the caller can use it
  // for display BEFORE React re-renders with the new state.
  // Returns null if all blocks are exhausted (triggers end-session).
  const advanceTeleprompter = useCallback((): Pointer | null => {
    const questionsInBlock = scriptThemes[activeBlockIdx]?.questions?.length ?? 0;
    const nextQIdx = activeQuestionIdx + 1;

    if (nextQIdx < questionsInBlock) {
      // More questions remain in the current block
      setActiveQuestionIdx(nextQIdx);
      return { blockIdx: activeBlockIdx, qIdx: nextQIdx };
    }

    // Current block exhausted — pause session and show homework transition screen!
    handleEndInterview(true);
    return null;
  }, [activeBlockIdx, activeQuestionIdx, scriptThemes]);

  // ─── handleSend ──────────────────────────────────────────────────────────
  const handleSend = async (text: string) => {
    if (!text.trim() || !sessionId) return;
    setMessages(prev => [...prev, { id: Date.now().toString(), role: 'expert', text, timestamp: Date.now() }]);
    setInputText('');
    setIsLoading(true);

    try {
      // Always read from the pointer — never hardcoded
      const currentQuestionText = currentActiveQuestion || 'General domain exploration.';

      const res = await fetch('http://localhost:9120/live-turn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${session?.access_token}` },
        body: JSON.stringify({
          session_id: sessionId,
          expert_answer: text,
          current_script_question: currentQuestionText,   // ✅ real active question
          active_block: activeBlock,                        // ✅ derived from pointer
          tangent_count: tangentCount
        })
      });
      const data = await res.json();

      const action = data.decision?.action ?? '';
      const intent = data.decision?.intent ?? 'unknown';
      const reasoning = data.decision?.reasoning ?? 'Backend copilot decision';

      let displayText = '';

      // ─── Explicit action switch (no fall-through ambiguity) ──────────────
      switch (action) {

        case 'next_script_question': {
          // 1. Reset tangent depth for the new question
          setTangentCount(0);
          // 2. Advance pointer and get the new position synchronously
          const next = advanceTeleprompter();
          // 3. Derive display text from the returned pointer (not stale state)
          if (next) {
            displayText =
              scriptThemes[next.blockIdx]?.questions?.[next.qIdx]?.question_text
              ?? "Great — let's keep going.";
          } else {
            displayText = "That is a brilliant insight to conclude this chapter on. Let me pause here to synthesize our notes and prepare the next part!";
            setTimeout(() => {
              setIsSynthesizing(true);
              fetch(`http://localhost:9120/end-session/${sessionId}`, { method: 'POST', headers: { 'Authorization': `Bearer ${session?.access_token}` } })
                .then(r => r.json())
                .then(resData => {
                  setIsSynthesizing(false);
                  if (resData.next_session_id) {
                    setNextSessionId(resData.next_session_id);
                    localStorage.setItem('session_id', resData.next_session_id);
                  }
                  setHasPendingHomework(Boolean(resData.has_pending_homework));
                  setIsChapterComplete(true);
                })
                .catch(e => {
                  console.error(e);
                  setIsSynthesizing(false);
                });
            }, 3000);
          }
          break;
        }

        case 'follow_tangent': {
          // Increment tangent depth and display the AI-generated follow-up
          setTangentCount(prev => prev + 1);
          displayText = data.question ?? '';
          break;
        }

        case 'redirect_to_script': {
          // Display the redirect question without changing the pointer
          displayText = data.question ?? "Let's steer back to the topic at hand.";
          break;
        }

        case 'system_auto_pause': {
          displayText = data.question ?? "That is a brilliant insight to conclude this chapter on. Let me pause here to synthesize our notes and prepare the next part!";
          setTimeout(() => {
            setIsSynthesizing(true);
            fetch(`http://localhost:9120/end-session/${sessionId}`, { method: 'POST', headers: { 'Authorization': `Bearer ${session?.access_token}` } })
              .then(r => r.json())
              .then(resData => {
                setIsSynthesizing(false);
                if (resData.next_session_id) {
                  setNextSessionId(resData.next_session_id);
                  localStorage.setItem('session_id', resData.next_session_id);
                }
                setHasPendingHomework(Boolean(resData.has_pending_homework));
                setIsChapterComplete(true);
              })
              .catch(e => {
                console.error(e);
                setIsSynthesizing(false);
              });
          }, 3000);
          break;
        }

        default: {
          // Fallback: display whatever the backend returned
          displayText = data.question ?? "Let's continue.";
          break;
        }
      }

      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'ai',
        text: displayText,
        timestamp: Date.now(),
        decision: {
          intent_classification: intent,
          internal_reasoning: reasoning,
          action: action
        }
      }]);

    } catch (err) {
      console.error(err);
      alert("Failed to get AI response.");
    } finally {
      setIsLoading(false);
    }
  };

  // ─── handleEndInterview ───────────────────────────────────────────────────
  // skipConfirm: pass true when auto-triggered by the teleprompter completing all blocks
  const handleEndInterview = async (skipConfirm = false) => {
    if (!skipConfirm && !confirm('Pause the interview and run the Homework Engine?')) return;
    if (!sessionId) return;

    setIsSynthesizing(true);
    try {
      // Wait for synthesis + homework generation to fully complete before navigating
      const res = await fetch(`http://localhost:9120/end-session/${sessionId}`, { method: 'POST', headers: { 'Authorization': `Bearer ${session?.access_token}` } });
      const resData = await res.json();
      if (resData.next_session_id) {
        setNextSessionId(resData.next_session_id);
      }
      setHasPendingHomework(Boolean(resData.has_pending_homework));
      setIsSynthesizing(false);
      setIsChapterComplete(true);
    } catch (err) {
      console.error(err);
      alert("Failed to synthesize session.");
      setIsSynthesizing(false);
    }
  };

  // ─── handlePauseSession ───────────────────────────────────────────────────
  const handlePauseSession = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`http://localhost:9120/pause-session/${sessionId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session?.access_token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          current_script_question: currentActiveQuestion,
          active_block: activeBlock,
          tangent_count: tangentCount
        })
      });

      if (res.ok) {
        await supabase.auth.signOut();
        navigate('/login');
      } else {
        alert("Failed to pause session.");
      }
    } catch (err) {
      console.error(err);
      alert("Network error.");
    } finally {
      setIsLoading(false);
    }
  };

  // ─── handleNextBlock (manual override button) ─────────────────────────────
  const handleNextBlock = () => {
    handleEndInterview(false);
  };

  // ─── Chapter Complete screen (Part 2 transition) ──────────────────────────
  if (isChapterComplete) {
    const isLocked = localStorage.getItem('hw_reviewed_' + (sessionId || '')) !== 'true' && localStorage.getItem('hw_reviewed_' + (nextSessionId || '')) !== 'true' && localStorage.getItem('hw_reviewed_global') !== 'true';
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', background: 'var(--bg)', color: 'var(--text)' }}>
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--accent)', borderRadius: '16px', padding: '40px', maxWidth: '520px', textAlign: 'center', boxShadow: '0 20px 25px -5px rgba(124,106,255,0.15)' }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>✨</div>
          <h2 style={{ fontSize: '24px', marginBottom: '12px' }}>Block Complete & Synthesized</h2>
          <p style={{ color: 'var(--text-dim)', lineHeight: '1.6', marginBottom: '20px' }}>
            The AI Journalist has processed this block's tacit insights, generated block-isolated homework verification loops, and prepared the clean handoff into the next block.
          </p>

          {isLocked && (
            <div style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid #f59e0b', borderRadius: '10px', padding: '14px', marginBottom: '20px', fontSize: '13px', color: '#f59e0b', textAlign: 'left' }}>
              <strong>🔒 Progression Locked:</strong> You must click <strong>Review Homework Ledger First</strong> below to review the homework and provide supporting resources before continuing to Block 2.
            </div>
          )}

          <button
            className="send-btn"
            disabled={isLocked}
            style={{ width: '100%', padding: '14px', fontSize: '15px', fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', opacity: isLocked ? 0.45 : 1, cursor: isLocked ? 'not-allowed' : 'pointer' }}
            onClick={() => {
              if (isLocked) return;
              if (nextSessionId) {
                localStorage.setItem('session_id', nextSessionId);
              }
              setIsChapterComplete(false);
              window.location.reload();
            }}
          >
            {isLocked ? '🔒 Review Homework First to Continue' : 'Continue to Next Block / Session'} {!isLocked && <ArrowRight size={18} />}
          </button>
          <button
            style={{ width: '100%', marginTop: '12px', padding: '14px', fontSize: '14px', fontWeight: 700, background: isLocked ? 'var(--accent)' : 'transparent', border: `1px solid ${isLocked ? 'var(--accent)' : 'var(--border)'}`, color: isLocked ? '#fff' : 'var(--text-dim)', borderRadius: '8px', cursor: 'pointer', boxShadow: isLocked ? '0 4px 14px rgba(124, 106, 255, 0.35)' : 'none' }}
            onClick={() => {
              if (nextSessionId) {
                localStorage.setItem('session_id', nextSessionId);
              }
              navigate('/homework');
            }}
          >
            📎 Review Homework Ledger First {isLocked && ' (Action Required)'}
          </button>
        </div>
      </div>
    );
  }

  // ─── Synthesizing screen ──────────────────────────────────────────────────
  if (isSynthesizing) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', background: 'var(--bg)', color: 'var(--text)' }}>
        <Loader2 size={48} className="spin" style={{ color: 'var(--accent)', marginBottom: '20px' }} />
        <h2>Synthesizing Knowledge...</h2>
        <p style={{ color: 'var(--text-dim)' }}>Extracting tacit knowledge and building vector memory for Chapter Part 2.</p>
      </div>
    );
  }

  // ─── Main render ──────────────────────────────────────────────────────────
  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden', background: 'var(--bg)' }}>
      <div className="chat-page" style={{ flex: 1, position: 'relative', display: 'flex', flexDirection: 'column', height: '100%' }}>
        <header className="chat-header">
          <div className="chat-header-left">
            <button className="chat-logo-btn" onClick={() => setShowScriptSidebar(!showScriptSidebar)}>
              <BrainCircuit size={20} />
            </button>
            <div className="chat-header-info">
              <h1>Live Interview — {session?.user?.user_metadata?.name || session?.user?.email?.split('@')[0] || 'Expert'}</h1>
              <div className="chat-header-status">
                <div className="pulse-dot" style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--green)' }}></div>
                Session Iteration {sessionMeta.iteration} ({sessionMeta.id.slice(0, 8)}) · Recording Active
              </div>
            </div>
          </div>

          <div className="chat-header-right" style={{ gap: '12px', display: 'flex', alignItems: 'center' }}>
            <div className="progress-section" style={{ marginRight: '16px', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', maxWidth: '360px' }}>
              <label style={{ fontSize: '11px', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Active Block: {activeBlock}</label>
              <div style={{ fontSize: '12px', fontWeight: 500, color: 'var(--text)', textAlign: 'right', marginTop: '2px', opacity: 0.8, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                Q{activeQuestionIdx + 1}: {currentActiveQuestion.slice(0, 60)}{currentActiveQuestion.length > 60 ? '…' : ''}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>Tangent Depth: {tangentCount}</div>
            </div>

            <button className="btn-ghost" style={{ borderColor: 'var(--accent)', color: 'var(--accent)' }} onClick={handleNextBlock}>
              Next Block <ArrowRight size={14} style={{ marginLeft: '6px', verticalAlign: '-2px' }} />
            </button>
            <button className="btn-ghost" style={{ borderColor: 'var(--yellow)', color: 'var(--yellow)' }} onClick={handlePauseSession} disabled={isLoading}>
              <PauseCircle size={14} style={{ marginRight: '6px', verticalAlign: '-2px' }} /> PAUSE SESSION
            </button>
            <button className="btn-ghost" style={{ borderColor: 'var(--red)', color: 'var(--red)' }} onClick={() => handleEndInterview()} disabled={isSynthesizing}>
              <Target size={14} style={{ marginRight: '6px', verticalAlign: '-2px' }} /> FINISH INTERVIEW
            </button>
          </div>
        </header>

        <div className="chat-feed" ref={scrollRef}>
          {messages.map(m => (
            <div key={m.id} className={`msg msg-${m.role}`}>
              <div className="msg-label">
                {m.role === 'expert' ? 'Demo Expert' : 'AI Journalist'}
                {m.role === 'ai' && m.decision && (
                  <button className="decision-toggle" onClick={() => setShowDecision(showDecision === m.id ? null : m.id)}>
                    <Zap size={10} /> AI Decision Log
                  </button>
                )}
              </div>
              <div className="msg-bubble">
                <div className="msg-text">{m.text}</div>
              </div>
              {m.role === 'ai' && m.decision && showDecision === m.id && (
                <div className="decision-section">
                  <div className="decision-panel">
                    <div className="decision-grid">
                      <div className="decision-item">
                        <div className="decision-item-label"><Target size={10} /> Intent Classification</div>
                        <div className="decision-item-value">
                          <span className={`depth-tag depth-deep`}>{m.decision.intent_classification}</span>
                        </div>
                      </div>
                      <div className="decision-item">
                        <div className="decision-item-label"><Zap size={10} /> Action</div>
                        <div className="decision-item-value">{m.decision.action}</div>
                      </div>
                    </div>
                    <div className="decision-monologue">
                      <div className="decision-item-label"><Eye size={10} /> Internal Reasoning</div>
                      <p style={{ fontSize: '13px', color: 'var(--text-dim)', lineHeight: '1.6', marginTop: '6px' }}>{m.decision.internal_reasoning}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
          {isLoading && (
            <div className="msg msg-ai">
              <div className="typing-indicator">
                <div className="typing-dots">
                  <div className="typing-dot" /><div className="typing-dot" /><div className="typing-dot" />
                </div>
                <span className="typing-text">Synthesizing follow-up...</span>
              </div>
            </div>
          )}
        </div>

        <div className="chat-input-bar">
          <div className="chat-input-wrapper">
            <button
              className={`mic-btn ${isRecording ? 'recording' : ''}`}
              onClick={() => setIsRecording(!isRecording)}
              disabled={isTranscribing}
            >
              {isTranscribing ? <Loader2 size={20} className="spin" /> : (isRecording ? <MicOff size={20} /> : <Mic size={20} />)}
            </button>
            <textarea
              value={inputText}
              onChange={e => setInputText(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(inputText); }
              }}
              placeholder="Type expert's response..."
              className="chat-textarea"
              rows={1}
            />
            <button className="send-btn" onClick={() => handleSend(inputText)} disabled={isLoading || !inputText.trim()}>
              <Send size={20} />
            </button>
          </div>
        </div>
      </div>

      {showScriptSidebar && (
        <div className="script-sidebar" style={{ width: '400px', height: '100%', background: 'var(--bg-card)', borderLeft: '1px solid var(--border)', display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
          <div style={{ padding: '20px', borderBottom: '1px solid var(--border)', background: '#fff' }}>
            <h3 style={{ margin: 0, fontSize: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FileText size={16} style={{ color: 'var(--accent)' }} /> Live Teleprompter
            </h3>
            <p style={{ margin: '4px 0 0', fontSize: '12px', color: 'var(--text-dim)' }}>Read these questions to guide the interview.</p>
          </div>
          <div style={{ flex: 1, overflowY: 'auto', padding: '20px' }}>
            {scriptThemes.map((theme, blockIdx) => (
              <div key={theme.theme_id} style={{ marginBottom: '24px' }}>
                <h4 style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-dim)', marginBottom: '12px', display: 'flex', justifyContent: 'space-between' }}>
                  <span>{theme.theme_title}</span>
                  <span style={{ color: 'var(--accent)', fontWeight: 'bold' }}>{theme.tentative_duration}m</span>
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {theme.questions.map((q: any, qIdx: number) => {
                    const isActive = blockIdx === activeBlockIdx && qIdx === activeQuestionIdx;
                    return (
                      <div
                        key={q.id}
                        style={{
                          background: isActive ? 'rgba(124,106,255,0.08)' : '#f8fafc',
                          border: `1px solid ${isActive ? 'var(--accent)' : 'var(--border)'}`,
                          borderRadius: '8px',
                          padding: '12px',
                          transition: 'border-color 0.2s, background 0.2s'
                        }}
                      >
                        <p style={{ margin: 0, fontSize: '13px', lineHeight: '1.5', fontWeight: isActive ? 700 : 500 }}>"{q.question_text}"</p>
                        <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '8px', fontStyle: 'italic' }}>
                          Rationale: {q.rationale}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
            {scriptThemes.length === 0 && <p style={{ fontSize: '13px', color: 'var(--text-dim)' }}>Loading script...</p>}
          </div>
        </div>
      )}
    </div>
  );
};

export default InterviewPage;
