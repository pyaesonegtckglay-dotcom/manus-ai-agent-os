'use client';

import { useEffect, useRef } from 'react';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import { WebLinksAddon } from '@xterm/addon-web-links';
import '@xterm/xterm/css/xterm.css';

interface TerminalViewProps {
  messages: Array<{
    type: string;
    content: string;
    timestamp: string;
  }>;
  className?: string;
}

export default function TerminalView({ messages, className }: TerminalViewProps) {
  const terminalRef = useRef<HTMLDivElement>(null);
  const terminalInstance = useRef<Terminal | null>(null);
  const fitAddon = useRef<FitAddon | null>(null);

  useEffect(() => {
    if (!terminalRef.current || terminalInstance.current) return;

    // Initialize terminal
    const term = new Terminal({
      cursorBlink: true,
      fontSize: 14,
      fontFamily: '"JetBrains Mono", "Fira Code", monospace',
      theme: {
        background: '#0f172a',
        foreground: '#e2e8f0',
        cursor: '#38bdf8',
        cursorAccent: '#0f172a',
        selectionBackground: '#334155',
        black: '#1e293b',
        red: '#ef4444',
        green: '#22c55e',
        yellow: '#eab308',
        blue: '#3b82f6',
        magenta: '#a855f7',
        cyan: '#06b6d4',
        white: '#e2e8f0',
        brightBlack: '#475569',
        brightRed: '#f87171',
        brightGreen: '#4ade80',
        brightYellow: '#facc15',
        brightBlue: '#60a5fa',
        brightMagenta: '#c084fc',
        brightCyan: '#22d3ee',
        brightWhite: '#f8fafc',
      },
      convertEol: true,
    });

    // Add fit addon
    const fit = new FitAddon();
    fitAddon.current = fit;
    term.loadAddon(fit);

    // Add web links
    term.loadAddon(new WebLinksAddon());

    // Open terminal
    term.open(terminalRef.current);
    fit.fit();

    terminalInstance.current = term;

    // Welcome message
    term.writeln('\x1b[36m┌─────────────────────────────────────────────────────────────┐\x1b[0m');
    term.writeln('\x1b[36m│\x1b[0m  \x1b[1m\x1b[33mManus AI Agent OS\x1b[0m Terminal                    \x1b[36m│\x1b[0m');
    term.writeln('\x1b[36m│\x1b[0m  Connected and ready to execute tasks                  \x1b[36m│\x1b[0m');
    term.writeln('\x1b[36m└─────────────────────────────────────────────────────────────┘\x1b[0m');
    term.writeln('');

    // Handle resize
    const handleResize = () => {
      fit.fit();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      term.dispose();
      terminalInstance.current = null;
    };
  }, []);

  // Handle new messages
  useEffect(() => {
    const term = terminalInstance.current;
    if (!term) return;

    messages.forEach((msg) => {
      const timestamp = new Date(msg.timestamp).toLocaleTimeString();
      
      switch (msg.type) {
        case 'thought':
          term.writeln(`\x1b[90m[${timestamp}]\x1b[0m \x1b[35m💭 ${msg.content}\x1b[0m`);
          break;
        case 'action':
          term.writeln(`\x1b[90m[${timestamp}]\x1b[0m \x1b[33m⚡ ${msg.content}\x1b[0m`);
          break;
        case 'terminal':
          term.writeln(`\x1b[90m[${timestamp}]\x1b[0m \x1b[32m${msg.content}\x1b[0m`);
          break;
        case 'status':
          term.writeln(`\x1b[90m[${timestamp}]\x1b[0m \x1b[34m📋 ${msg.content}\x1b[0m`);
          break;
        case 'result':
          term.writeln(`\x1b[90m[${timestamp}]\x1b[0m \x1b[32m✅ ${msg.content}\x1b[0m`);
          break;
        case 'error':
          term.writeln(`\x1b[90m[${timestamp}]\x1b[0m \x1b[31m❌ ${msg.content}\x1b[0m`);
          break;
        default:
          term.writeln(`\x1b[90m[${timestamp}]\x1b[0m ${msg.content}`);
      }
      
      term.writeln('');
    });

    // Scroll to bottom
    term.scrollToBottom();
  }, [messages]);

  return (
    <div className={className}>
      <div
        ref={terminalRef}
        className="h-full bg-dark-200 rounded-lg overflow-hidden"
        style={{ padding: '8px' }}
      />
    </div>
  );
}