import { useState } from 'react';
import { api } from '../services/api';
import { useInterviewContext } from '../context/InterviewContext';
import { useNavigate } from 'react-router-dom';

export const useInterview = () => {
  const { sessionId, addMessage, setScriptProgress, setBlueprint } = useInterviewContext();
  const [isLoading, setIsLoading] = useState(false);
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const navigate = useNavigate();

  const handleSend = async (text: string) => {
    if (!text.trim() || !sessionId || isLoading) return;

    addMessage({ id: Date.now().toString(), role: 'expert', text });
    setIsLoading(true);

    try {
      const res = await api.post('/generate-question', {
        expert_answer: text,
        user_session_id: sessionId,
      });

      addMessage({
        id: (Date.now() + 1).toString(),
        role: 'ai',
        text: res.data.question,
        decision: res.data.decision,
        chunks: res.data.chunks_used,
      });

      setScriptProgress(res.data.script_progress);

      if (res.data.decision?.next_action === 'interview_complete') {
        // Automatically synthesize if complete
        handleSynthesizeKnowledge();
      }
    } catch (err) {
      console.error(err);
      addMessage({
        id: Date.now().toString(),
        role: 'system',
        text: 'Error connecting to Knowledge Hub. Please try again.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSynthesizeKnowledge = async () => {
    if (!sessionId) return;
    setIsSynthesizing(true);
    try {
      const res = await api.post(`/synthesize-knowledge/${sessionId}`);
      setBlueprint(res.data.report);
      navigate('/report');
    } catch (err: any) {
      alert(`Synthesis error: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsSynthesizing(false);
    }
  };

  const handleEndInterview = async () => {
    if (!sessionId) return;
    setIsSynthesizing(true);
    try {
      const res = await api.post(`/end-interview/${sessionId}`);
      if (res.data.report) {
        setBlueprint(res.data.report);
        navigate('/report');
      } else {
        alert(res.data.message);
        navigate('/');
      }
    } catch (err: any) {
      alert(`End interview error: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsSynthesizing(false);
    }
  };

  return {
    isLoading,
    isSynthesizing,
    handleSend,
    handleSynthesizeKnowledge,
    handleEndInterview
  };
};
