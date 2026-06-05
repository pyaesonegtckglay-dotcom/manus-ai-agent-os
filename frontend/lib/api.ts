const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'

export interface ChatRequest {
  message: string
  session_id?: string
  user_id?: string
}

export interface ChatResponse {
  response: string
  session_id: string
  execution_trace?: any[]
}

export interface AgentStats {
  name: string
  status: string
  executions: number
  avg_execution_time_ms: number
  capabilities: string[]
  tools: string[]
}

export interface LLMHealth {
  [provider: string]: {
    status: string
    latency_ms: number
    consecutive_failures: number
  }
}

export async function sendChat(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${API_URL}/api/v1/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  })
  
  if (!response.ok) {
    throw new Error(`Chat request failed: ${response.statusText}`)
  }
  
  return response.json()
}

export async function getAgentStats(): Promise<{ agents: AgentStats[] }> {
  const response = await fetch(`${API_URL}/api/v1/agents/stats`)
  
  if (!response.ok) {
    throw new Error(`Failed to get agent stats: ${response.statusText}`)
  }
  
  return response.json()
}

export async function getLLMHealth(): Promise<{ providers: LLMHealth }> {
  const response = await fetch(`${API_URL}/api/v1/llm/health`)
  
  if (!response.ok) {
    throw new Error(`Failed to get LLM health: ${response.statusText}`)
  }
  
  return response.json()
}

export async function getExecutionTrace(taskId?: string): Promise<{ events: any[] }> {
  const url = taskId 
    ? `${API_URL}/api/v1/execution/trace?task_id=${taskId}`
    : `${API_URL}/api/v1/execution/trace`
  
  const response = await fetch(url)
  
  if (!response.ok) {
    throw new Error(`Failed to get execution trace: ${response.statusText}`)
  }
  
  return response.json()
}

export class WebSocketClient {
  private ws: WebSocket | null = null
  private sessionId: string
  private messageHandlers: ((data: any) => void)[] = []
  private errorHandlers: ((error: any) => void)[] = []

  constructor(sessionId: string) {
    this.sessionId = sessionId
  }

  connect() {
    this.ws = new WebSocket(`${WS_URL}/api/v1/ws/${this.sessionId}`)
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      this.messageHandlers.forEach(handler => handler(data))
    }
    
    this.ws.onerror = (error) => {
      this.errorHandlers.forEach(handler => handler(error))
    }
  }

  send(message: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    }
  }

  onMessage(handler: (data: any) => void) {
    this.messageHandlers.push(handler)
  }

  onError(handler: (error: any) => void) {
    this.errorHandlers.push(handler)
  }

  disconnect() {
    this.ws?.close()
  }
}