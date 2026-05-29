import React from 'react';
import { ShieldCheck } from 'lucide-react';
import type { Message } from '../../types';
import { DecisionLog } from './DecisionLog';

interface Props {
  msg: Message;
}

export const ChatBubble: React.FC<Props> = ({ msg }) => {
  const isAi = msg.role === 'ai';

  return (
    <div className={`msg ${isAi ? 'msg-ai' : 'msg-expert'}`}>
      <div className="msg-bubble">
        {isAi && (
          <div className="msg-label">
            <span><ShieldCheck size={10} /> Grounded Follow-up</span>
          </div>
        )}
        <div className="msg-text">{msg.text}</div>
      </div>
      
      {isAi && msg.decision && (
        <DecisionLog decision={msg.decision} chunks={msg.chunks} />
      )}
    </div>
  );
};
