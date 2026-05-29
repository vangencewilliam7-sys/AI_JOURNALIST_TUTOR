import React, { useState, useRef } from 'react';
import { Mic, MicOff, Send, Loader2 } from 'lucide-react';
import { apiService } from '../../services/api';

interface Props {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export const ChatInput: React.FC<Props> = ({ onSend, disabled }) => {
  const [inputText, setInputText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);

  const handleSend = () => {
    if (!inputText.trim() || disabled) return;
    onSend(inputText.trim());
    setInputText('');
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder.current = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      audioChunks.current = [];

      mediaRecorder.current.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunks.current.push(event.data);
      };

      mediaRecorder.current.onstop = async () => {
        setIsTranscribing(true);
        const audioBlob = new Blob(audioChunks.current, { type: 'audio/webm' });
        
        // Prevent sending empty audio which causes Deepgram SLOW_UPLOAD timeout
        if (audioBlob.size < 100) {
          setIsTranscribing(false);
          stream.getTracks().forEach(track => track.stop());
          return;
        }

        try {
          const res = await apiService.transcribeAudio(audioBlob);
          if (res.transcript) {
            const finalMessage = inputText + (inputText ? ' ' : '') + res.transcript;
            onSend(finalMessage);
            setInputText('');
          }
        } catch (error) {
          console.error("Transcription failed", error);
          const errMsg = (error as any)?.response?.data?.detail || "Transcription failed. Check backend logs for details.";
          alert(errMsg);
        } finally {
          setIsTranscribing(false);
          stream.getTracks().forEach(track => track.stop());
        }
      };

      // Pass timeslice to ensure chunks are pushed periodically
      mediaRecorder.current.start(250); 
      setIsRecording(true);
    } catch (err) {
      console.error("Microphone access denied", err);
      alert("Microphone access denied. Please allow microphone permissions.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorder.current && isRecording) {
      mediaRecorder.current.stop();
      setIsRecording(false);
    }
  };

  const toggleRecording = () => {
    if (isRecording) stopRecording();
    else startRecording();
  };

  return (
    <footer className="chat-input-bar">
      <div className="chat-input-wrapper">
        <button 
          className={`mic-btn ${isRecording ? 'recording' : ''}`} 
          onClick={toggleRecording}
          disabled={disabled || isTranscribing}
        >
          {isTranscribing ? <Loader2 size={20} className="spin" /> : isRecording ? <MicOff size={20} /> : <Mic size={20} />}
        </button>
        <input 
          className="chat-textarea" 
          placeholder={isRecording ? "Listening..." : isTranscribing ? "Transcribing..." : "Speak or type your insight..."} 
          value={inputText} 
          onChange={e => setInputText(e.target.value)} 
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          disabled={disabled || isRecording || isTranscribing}
        />
        <button className="send-btn" onClick={handleSend} disabled={disabled || !inputText.trim() || isRecording || isTranscribing}>
          <Send size={20} />
        </button>
      </div>
    </footer>
  );
};
