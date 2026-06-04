'use client';

import { useState } from 'react';
import TerminalView from './TerminalView';
import clsx from 'clsx';

interface ActivityPanelProps {
  messages: Array<{
    type: string;
    content: string;
    timestamp: string;
  }>;
  status: 'connecting' | 'connected' | 'disconnected' | 'error';
}

export default function ActivityPanel({ messages, status }: ActivityPanelProps) {
  const [activeTab, setActiveTab] = useState<'terminal' | 'thoughts' | 'timeline'>('terminal');

  const statusColors = {
    connecting: 'bg-yellow-500',
    connected: 'bg-green-500',
    disconnected: 'bg-gray-500',
    error: 'bg-red-500',
  };

  const statusLabels = {
    connecting: 'Connecting...',
    connected: 'Connected',
    disconnected: 'Disconnected',
    error: 'Error',
  };

  return (
    <div className="bg-dark-100 rounded-lg border border-slate-700 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-dark-200 border-b border-slate-700">
        <div className="flex items-center gap-3">
          <h3 className="font-semibold text-white">Manus&apos;s Computer</h3>
          <div className="flex items-center gap-2">
            <span className={clsx('w-2 h-2 rounded-full', statusColors[status])} />
            <span className="text-sm text-slate-400">{statusLabels[status]}</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-700">
        <button
          onClick={() => setActiveTab('terminal')}
          className={clsx(
            'px-4 py-2 text-sm font-medium transition-colors',
            activeTab === 'terminal'
              ? 'text-primary-400 border-b-2 border-primary-400 bg-dark-100'
              : 'text-slate-400 hover:text-white hover:bg-dark-200'
          )}
        >
          Terminal
        </button>
        <button
          onClick={() => setActiveTab('thoughts')}
          className={clsx(
            'px-4 py-2 text-sm font-medium transition-colors',
            activeTab === 'thoughts'
              ? 'text-primary-400 border-b-2 border-primary-400 bg-dark-100'
              : 'text-slate-400 hover:text-white hover:bg-dark-200'
          )}
        >
          Thoughts
        </button>
        <button
          onClick={() => setActiveTab('timeline')}
          className={clsx(
            'px-4 py-2 text-sm font-medium transition-colors',
            activeTab === 'timeline'
              ? 'text-primary-400 border-b-2 border-primary-400 bg-dark-100'
              : 'text-slate-400 hover:text-white hover:bg-dark-200'
          )}
        >
          Timeline
        </button>
      </div>

      {/* Content */}
      <div className="h-96">
        {activeTab === 'terminal' && (
          <TerminalView messages={messages} className="h-full" />
        )}
        {activeTab === 'thoughts' && (
          <div className="h-full overflow-y-auto p-4 space-y-3">
            {messages.filter((m) => m.type === 'thought').length === 0 ? (
              <p className="text-slate-500 text-center py-8">No thoughts yet</p>
            ) : (
              messages
                .filter((m) => m.type === 'thought')
                .map((thought, i) => (
                  <div key={i} className="bg-dark-200 rounded-lg p-3 border-l-2 border-purple-500">
                    <p className="text-sm text-slate-300">{thought.content}</p>
                    <span className="text-xs text-slate-500 mt-1 block">
                      {new Date(thought.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                ))
            )}
          </div>
        )}
        {activeTab === 'timeline' && (
          <div className="h-full overflow-y-auto p-4">
            <div className="relative">
              <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-slate-700" />
              <div className="space-y-4">
                {messages.length === 0 ? (
                  <p className="text-slate-500 text-center py-8">No activity yet</p>
                ) : (
                  messages.map((msg, i) => (
                    <div key={i} className="relative flex items-start gap-4 pl-10">
                      <div
                        className={clsx(
                          'absolute left-2 w-4 h-4 rounded-full border-2',
                          msg.type === 'error' ? 'bg-red-500 border-red-500' :
                          msg.type === 'result' ? 'bg-green-500 border-green-500' :
                          msg.type === 'action' ? 'bg-yellow-500 border-yellow-500' :
                          'bg-blue-500 border-blue-500'
                        )}
                      />
                      <div className="flex-1 bg-dark-200 rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs text-slate-500">
                            {new Date(msg.timestamp).toLocaleTimeString()}
                          </span>
                          <span className="text-xs font-medium text-slate-400 uppercase">
                            {msg.type}
                          </span>
                        </div>
                        <p className="text-sm text-slate-300">{msg.content}</p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}