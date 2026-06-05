// PSP AI Configuration
export const CONFIG = {
  // Backend API - HuggingFace Space
  API_BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'https://pyae1994-psp-ai-backend.hf.space',
  
  // WebSocket for real-time updates
  WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'wss://pyae1994-psp-ai-backend.hf.space',
  
  // Feature flags
  ENABLE_WEBSOCKET: true,
  ENABLE_METRICS: true,
};