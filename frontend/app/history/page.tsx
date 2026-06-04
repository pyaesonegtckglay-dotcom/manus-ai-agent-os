'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import clsx from 'clsx';

interface Task {
  id: string;
  status: string;
  description: string;
  created_at: string;
  completed_at?: string;
}

export default function HistoryPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    // In a real app, fetch from API
    // For demo, using sample data
    setTasks([
      {
        id: '1',
        status: 'completed',
        description: 'Research the latest AI agent frameworks',
        created_at: new Date(Date.now() - 3600000).toISOString(),
        completed_at: new Date(Date.now() - 3000000).toISOString(),
      },
      {
        id: '2',
        status: 'failed',
        description: 'Analyze CSV data from uploaded file',
        created_at: new Date(Date.now() - 7200000).toISOString(),
      },
      {
        id: '3',
        status: 'completed',
        description: 'Write Python automation script',
        created_at: new Date(Date.now() - 86400000).toISOString(),
        completed_at: new Date(Date.now() - 85000000).toISOString(),
      },
    ]);
    setIsLoading(false);
  }, []);

  const statusConfig = {
    pending: { bg: 'bg-gray-600', text: 'Pending', icon: '⏳' },
    queued: { bg: 'bg-blue-600', text: 'Queued', icon: '📋' },
    running: { bg: 'bg-yellow-600', text: 'Running', icon: '⚡' },
    completed: { bg: 'bg-green-600', text: 'Completed', icon: '✅' },
    failed: { bg: 'bg-red-600', text: 'Failed', icon: '❌' },
    cancelled: { bg: 'bg-gray-600', text: 'Cancelled', icon: '🚫' },
  };

  const filteredTasks = filter === 'all' 
    ? tasks 
    : tasks.filter(t => t.status === filter);

  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="border-b border-slate-800 bg-dark-200/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
              <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">Manus AI Agent OS</h1>
                <p className="text-sm text-slate-400">Task History</p>
              </div>
            </Link>
          </div>
          <Link 
            href="/"
            className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg text-sm font-medium transition-colors"
          >
            New Task
          </Link>
        </div>
      </header>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-6 py-8">
        {/* Filters */}
        <div className="flex items-center gap-4 mb-6">
          <span className="text-sm text-slate-400">Filter:</span>
          <div className="flex gap-2">
            {['all', 'completed', 'failed', 'running'].map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={clsx(
                  'px-3 py-1 rounded text-sm capitalize transition-colors',
                  filter === f
                    ? 'bg-primary-600 text-white'
                    : 'bg-dark-100 text-slate-400 hover:bg-dark-200'
                )}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* Task List */}
        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-dark-100 rounded-lg p-6 border border-slate-700">
                <div className="skeleton h-4 w-3/4 mb-3 rounded" />
                <div className="skeleton h-3 w-1/4 rounded" />
              </div>
            ))}
          </div>
        ) : filteredTasks.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📭</div>
            <h3 className="text-xl font-semibold text-white mb-2">No tasks found</h3>
            <p className="text-slate-400 mb-6">You haven&apos;t completed any tasks yet.</p>
            <Link 
              href="/"
              className="px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition-colors"
            >
              Create your first task
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredTasks.map((task) => {
              const config = statusConfig[task.status as keyof typeof statusConfig] || statusConfig.pending;
              return (
                <div 
                  key={task.id}
                  className="bg-dark-100 rounded-lg p-6 border border-slate-700 hover:border-slate-600 transition-colors"
                >
                  <div className="flex items-start justify-between mb-3">
                    <span className={clsx('px-2 py-1 rounded text-xs font-medium text-white', config.bg)}>
                      {config.text}
                    </span>
                    <span className="text-sm text-slate-500">
                      {new Date(task.created_at).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-white mb-3">{task.description}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-500">
                      ID: {task.id}
                    </span>
                    <div className="flex gap-2">
                      {task.status === 'completed' && (
                        <button className="px-3 py-1 bg-dark-200 hover:bg-dark-300 text-slate-400 rounded text-sm transition-colors">
                          View Results
                        </button>
                      )}
                      <button className="px-3 py-1 bg-primary-600/20 hover:bg-primary-600/30 text-primary-400 rounded text-sm transition-colors">
                        Re-run
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </main>
  );
}