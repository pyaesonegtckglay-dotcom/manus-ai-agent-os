import '@testing-library/jest-dom';

// Mock environment variables
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
process.env.NEXT_PUBLIC_WS_URL = 'ws://localhost:8000';

// Mock fetch
global.fetch = jest.fn();

// Mock WebSocket
class MockWebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = 1; // OPEN
    this.onopen = null;
    this.onmessage = null;
    this.onclose = null;
    this.onerror = null;
  }

  send(data) {
    // Mock send
  }

  close() {
    this.readyState = 3; // CLOSED
    if (this.onclose) this.onclose();
  }
}

global.WebSocket = MockWebSocket;