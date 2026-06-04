const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Task {
  id: string;
  status: 'pending' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  description: string;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  created_at: string;
  updated_at: string;
  started_at?: string;
  completed_at?: string;
  result?: Record<string, unknown>;
  error?: string;
}

export interface Session {
  id: string;
  user_id: string;
  name?: string;
  status: string;
  sandbox_id?: string;
  created_at: string;
  updated_at: string;
}

export async function createTask(description: string, priority: string = 'normal'): Promise<Task> {
  const response = await fetch(`${API_URL}/api/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      description,
      priority,
      timeout: 3600,
    }),
  });
  
  if (!response.ok) {
    throw new Error('Failed to create task');
  }
  
  return response.json();
}

export async function getTask(taskId: string): Promise<Task> {
  const response = await fetch(`${API_URL}/api/tasks/${taskId}`);
  
  if (!response.ok) {
    throw new Error('Failed to get task');
  }
  
  return response.json();
}

export async function cancelTask(taskId: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/tasks/${taskId}`, {
    method: 'DELETE',
  });
  
  if (!response.ok) {
    throw new Error('Failed to cancel task');
  }
}

export async function createSession(userId: string, name?: string): Promise<Session> {
  const response = await fetch(`${API_URL}/api/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, name }),
  });
  
  if (!response.ok) {
    throw new Error('Failed to create session');
  }
  
  return response.json();
}

export async function getHealth(): Promise<{ status: string; services: Record<string, boolean> }> {
  const response = await fetch(`${API_URL}/health`);
  return response.json();
}

export function createWebSocket(taskId: string): WebSocket {
  const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
  return new WebSocket(`${WS_URL}/api/tasks/${taskId}/stream`);
}

