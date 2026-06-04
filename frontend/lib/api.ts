// Update frontend API URL
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://PYAE1994-manus-backend.hf.space';
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'wss://PYAE1994-manus-backend.hf.space';

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
  console.log('[API] createTask called with:', description);
  console.log('[API] Using URL:', API_URL);
  
  const response = await fetch(`${API_URL}/api/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      description,
      priority,
      timeout: 3600,
    }),
  });
  
  console.log('[API] Response status:', response.status);
  
  if (!response.ok) {
    const errorText = await response.text();
    console.error('[API] Error response:', errorText);
    throw new Error('Failed to create task');
  }
  
  const data = await response.json();
  console.log('[API] Task created:', data);
  return data;
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
  return new WebSocket(`${WS_URL}/api/tasks/${taskId}/stream`);
}

