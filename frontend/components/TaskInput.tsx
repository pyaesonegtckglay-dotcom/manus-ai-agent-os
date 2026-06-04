import { useState, useRef } from 'react';
import clsx from 'clsx';

interface TaskInputProps {
  onSubmit: (description: string, priority: string) => void;
  isLoading?: boolean;
}

export default function TaskInput({ onSubmit, isLoading }: TaskInputProps) {
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<'low' | 'normal' | 'high' | 'urgent'>('normal');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (description.trim() && !isLoading) {
      onSubmit(description.trim(), priority);
      setDescription('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleSubmit(e);
    }
  };

  const priorityOptions = [
    { value: 'low', label: 'Low', color: 'text-gray-400' },
    { value: 'normal', label: 'Normal', color: 'text-blue-400' },
    { value: 'high', label: 'High', color: 'text-orange-400' },
    { value: 'urgent', label: 'Urgent', color: 'text-red-400' },
  ];

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="relative">
        <textarea
          ref={textareaRef}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="What would you like Manus to do? (e.g., 'Research the latest AI developments and create a summary report')"
          className="w-full h-32 px-4 py-3 bg-dark-100 border border-slate-700 rounded-lg 
                     text-white placeholder-slate-500 resize-none focus:outline-none focus:border-primary-500
                     transition-colors"
          disabled={isLoading}
        />
        <div className="absolute bottom-3 right-3 text-xs text-slate-500">
          ⌘ + Enter to submit
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-400">Priority:</span>
          <div className="flex gap-1">
            {priorityOptions.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => setPriority(option.value as typeof priority)}
                className={clsx(
                  'px-3 py-1 rounded text-sm transition-colors',
                  priority === option.value
                    ? 'bg-primary-600 text-white'
                    : 'bg-dark-100 text-slate-400 hover:bg-dark-200'
                )}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        <button
          type="submit"
          disabled={!description.trim() || isLoading}
          className={clsx(
            'px-6 py-2 rounded-lg font-medium transition-all',
            'bg-primary-600 hover:bg-primary-700 text-white',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            'flex items-center gap-2'
          )}
        >
          {isLoading ? (
            <>
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Executing...
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Execute Task
            </>
          )}
        </button>
      </div>
    </form>
  );
}