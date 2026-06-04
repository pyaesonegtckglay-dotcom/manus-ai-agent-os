'use client';

import { useState, useEffect, useRef } from 'react';
import TaskInput from '@/components/TaskInput';
import ActivityPanel from '@/components/ActivityPanel';
import { createTask, getTask, type Task } from '@/lib/api';
import clsx from 'clsx';

// Note: Using HTTP polling instead of WebSocket for task updates
// This works better with Vercel/Edge deployments and HF Spaces
// Version: 1.0.2 - Added debug logging

export default function HomePage() {
  const [currentTask, setCurrentTask] = useState<Task | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<{type: string; content: string; timestamp: string}[]>([]);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const taskCreatedRef = useRef(false);

  // Poll for task updates when task is created
  useEffect(() => {
    if (currentTask && currentTask.status !== 'completed' && currentTask.status !== 'failed') {
      // Add initial status message
      setMessages([{
        type: 'status',
        content: 'Task queued, processing with AI...',
        timestamp: new Date().toISOString()
      }]);

      // Poll for updates every 2 seconds
      pollIntervalRef.current = setInterval(async () => {
        try {
          console.log('Polling for task updates:', currentTask.id);
          const updatedTask = await getTask(currentTask.id);
          console.log('Task updated:', updatedTask.status);
          setCurrentTask(updatedTask);

          if (updatedTask.status === 'running') {
            setMessages(prev => [...prev, {
              type: 'thought',
              content: 'AI is processing your request...',
              timestamp: new Date().toISOString()
            }]);
          }

          if (updatedTask.status === 'completed' && updatedTask.result) {
            const response = String(updatedTask.result.response || updatedTask.result.output || '');
            setMessages(prev => [...prev, {
              type: 'result',
              content: response,
              timestamp: new Date().toISOString()
            }]);
            if (pollIntervalRef.current) {
              clearInterval(pollIntervalRef.current);
            }
          }

          if (updatedTask.status === 'failed') {
            setMessages(prev => [...prev, {
              type: 'error',
              content: updatedTask.error || 'Task failed',
              timestamp: new Date().toISOString()
            }]);
            if (pollIntervalRef.current) {
              clearInterval(pollIntervalRef.current);
            }
          }
        } catch (err) {
          console.error('Poll error:', err);
        }
      }, 2000);

      return () => {
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
        }
      };
    }
  }, [currentTask?.id]);

  const handleSubmitTask = async (description: string, priority: string) => {
    setIsLoading(true);
    setError(null);
    setMessages([]);
    console.log('[DEBUG] handleSubmitTask called:', description);
    console.log('[DEBUG] API URL:', process.env.NEXT_PUBLIC_API_URL || 'default');

    try {
      console.log('Creating task:', description);
      const task = await createTask(description, priority);
      console.log('[DEBUG] Task created response:', task);
      setCurrentTask(task);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to create task';
      console.error('[DEBUG] Task creation error:', err);
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusBadge = () => {
    if (!currentTask) return null;

    const statusConfig = {
      pending: { bg: 'bg-gray-600', text: 'Pending' },
      queued: { bg: 'bg-blue-600', text: 'Queued' },
      running: { bg: 'bg-yellow-600', text: 'Running' },
      completed: { bg: 'bg-green-600', text: 'Completed' },
      failed: { bg: 'bg-red-600', text: 'Failed' },
      cancelled: { bg: 'bg-gray-600', text: 'Cancelled' },
    };

    const config = statusConfig[currentTask.status] || statusConfig.pending;

    return (
      <span className={clsx('px-3 py-1 rounded-full text-sm font-medium text-white', config.bg)}>
        {config.text}
      </span>
    );
  };

  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="border-b border-slate-800 bg-dark-200/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Manus AI Agent OS</h1>
              <p className="text-sm text-slate-400">Autonomous task execution</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {currentTask && getStatusBadge()}
            <div className="flex items-center gap-2">
              <span className={clsx(
                'w-2 h-2 rounded-full',
                currentTask ? 'bg-green-500' : 'bg-gray-500'
              )} />
              <span className="text-sm text-slate-400">
                {currentTask ? 'AI Connected' : 'Ready'}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Task Input */}
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-dark-100 rounded-lg border border-slate-700 p-6">
              <h2 className="text-lg font-semibold text-white mb-4">New Task</h2>
              <TaskInput onSubmit={handleSubmitTask} isLoading={isLoading} />
              {error && (
                <div className="mt-4 p-4 bg-red-500/10 border border-red-500/50 rounded-lg">
                  <p className="text-sm text-red-400">{error}</p>
                </div>
              )}
            </div>

            {/* Quick Examples */}
            <div className="bg-dark-100 rounded-lg border border-slate-700 p-6">
              <h3 className="text-sm font-medium text-slate-400 mb-3">Try these examples</h3>
              <div className="space-y-2">
                {[
                  'Research the latest AI agent frameworks',
                  'Write a Python script to analyze CSV data',
                  'Find and summarize top tech news from this week',
                ].map((example, i) => (
                  <button
                    key={i}
                    onClick={() => handleSubmitTask(example, 'normal')}
                    disabled={isLoading}
                    className="w-full text-left px-4 py-3 bg-dark-200 rounded-lg text-sm text-slate-300 hover:bg-dark-300 hover:text-white transition-colors disabled:opacity-50"
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column - Activity Panel */}
          <div className="lg:col-span-2">
            <ActivityPanel messages={messages} status={currentTask ? 'connected' : 'disconnected'} />
          </div>
        </div>

        {/* Results Section */}
        {currentTask && currentTask.status === 'completed' && currentTask.result && (
          <div className="mt-8 bg-dark-100 rounded-lg border border-slate-700 p-6">
            <h2 className="text-lg font-semibold text-white mb-4">AI Response</h2>
            <div className="bg-dark-200 rounded-lg p-4 text-sm text-slate-300 whitespace-pre-wrap">
              {String(currentTask.result.response || currentTask.result.output || JSON.stringify(currentTask.result, null, 2))}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}