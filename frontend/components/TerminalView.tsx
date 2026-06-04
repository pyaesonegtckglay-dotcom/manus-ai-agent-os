'use client';

import { useEffect, useRef } from 'react';
import clsx from 'clsx';

interface Message {
  type: string;
  content: string;
  timestamp: string;
}

interface TerminalViewProps {
  messages: Message[];
  className?: string;
}

export default function TerminalView({ messages, className }: TerminalViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages]);

  const getTypeStyles = (type: string) => {
    switch (type) {
      case 'thought': return 'text-purple-400';
      case 'action': return 'text-yellow-400';
      case 'terminal': return 'text-green-400';
      case 'status': return 'text-blue-400';
      case 'result': return 'text-green-400';
      case 'error': return 'text-red-400';
      default: return 'text-slate-300';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'thought': return '💭';
      case 'action': return '⚡';
      case 'terminal': return '▸';
      case 'status': return '📋';
      case 'result': return '✅';
      case 'error': return '❌';
      default: return '▸';
    }
  };

  return (
    <div className={className}>
      <div
        ref={containerRef}
        className="h-full bg-dark-200 rounded-lg p-4 overflow-auto font-mono text-sm"
      >
        <div className="text-cyan-400 mb-4">
          ┌─────────────────────────────────────────────────────────────┐
          │  <span className="text-yellow-400 font-bold">Manus AI Agent OS</span> Terminal              │
          │  Connected and ready to execute tasks                  │
          └─────────────────────────────────────────────────────────────┘
        </div>
        
        {messages.length === 0 ? (
          <div className="text-slate-500">Waiting for messages...</div>
        ) : (
          <div className="space-y-2">
            {messages.map((msg, i) => (
              <div key={i} className="flex items-start gap-2">
                <span className="text-slate-500 shrink-0">
                  [{new Date(msg.timestamp).toLocaleTimeString()}]
                </span>
                <span className={clsx('shrink-0', getTypeStyles(msg.type))}>
                  {getTypeIcon(msg.type)}
                </span>
                <span className={getTypeStyles(msg.type)}>
                  {msg.content}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
