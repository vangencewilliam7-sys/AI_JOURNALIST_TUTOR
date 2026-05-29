import React, { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';
import type { Message, InterviewScript, CourseBlueprint } from '../types';

interface InterviewContextType {
  sessionId: string;
  setSessionId: (id: string) => void;
  
  courseMetadata: any;
  setCourseMetadata: (data: any) => void;
  
  script: InterviewScript | null;
  setScript: (script: InterviewScript | null) => void;
  
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  addMessage: (msg: Message) => void;
  
  scriptProgress: string;
  setScriptProgress: (progress: string) => void;
  
  blueprint: CourseBlueprint | null;
  setBlueprint: (blueprint: CourseBlueprint | null) => void;

  resetInterviewState: () => void;
}

const InterviewContext = createContext<InterviewContextType | undefined>(undefined);

export const InterviewProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [sessionId, setSessionId] = useState<string>('');
  const [courseMetadata, setCourseMetadata] = useState<any>({});
  const [script, setScript] = useState<InterviewScript | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [scriptProgress, setScriptProgress] = useState<string>('0/0');
  const [blueprint, setBlueprint] = useState<CourseBlueprint | null>(null);

  const addMessage = (msg: Message) => {
    setMessages((prev) => [...prev, msg]);
  };

  const resetInterviewState = () => {
    setSessionId('');
    setCourseMetadata({});
    setScript(null);
    setMessages([]);
    setScriptProgress('0/0');
    setBlueprint(null);
  };

  return (
    <InterviewContext.Provider
      value={{
        sessionId,
        setSessionId,
        courseMetadata,
        setCourseMetadata,
        script,
        setScript,
        messages,
        setMessages,
        addMessage,
        scriptProgress,
        setScriptProgress,
        blueprint,
        setBlueprint,
        resetInterviewState
      }}
    >
      {children}
    </InterviewContext.Provider>
  );
};

export const useInterviewContext = () => {
  const context = useContext(InterviewContext);
  if (context === undefined) {
    throw new Error('useInterviewContext must be used within an InterviewProvider');
  }
  return context;
};
