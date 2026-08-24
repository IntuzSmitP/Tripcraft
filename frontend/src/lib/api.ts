/**
 * TripCraft API Client
 */

const API_BASE = "http://localhost:8000/api"
const BEARER_TOKEN = "tripcraft-dev-token"

export interface StartPlanResponse {
  session_id: string
  status: string
  message: string
}

export async function startPlanningSession(goal: string): Promise<StartPlanResponse> {
  const response = await fetch(`${API_BASE}/plan`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${BEARER_TOKEN}`
    },
    body: JSON.stringify({ goal })
  })

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`Failed to start planning: ${error}`)
  }

  return response.json()
}

export async function provideUserInput(sessionId: string, input: string): Promise<any> {
  const response = await fetch(`${API_BASE}/plan/${sessionId}/input`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${BEARER_TOKEN}`
    },
    body: JSON.stringify({ input })
  })
  
  if (!response.ok) {
    const error = await response.text()
    throw new Error(`Failed to submit input: ${error}`)
  }
  
  return response.json()
}

export function subscribeToExecutionLog(
  sessionId: string, 
  onLog: (entry: any) => void,
  onResult: (result: any) => void,
  onDone: (status: string) => void,
  onError: (err: any) => void
): () => void {
  const url = `${API_BASE}/plan/${sessionId}/stream`
  
  // Create an EventSource with auth headers if possible, or use alternative
  // Since standard EventSource doesn't support headers well, we might need a custom fetch stream
  // But for this demo where CORS allows everything, we'll try standard EventSource and pass token in query if backend supported it
  // Actually, standard EventSource doesn't support auth headers. 
  // For this demo we'll use a fetch-based polyfill or just fetch directly.
  
  const controller = new AbortController();
  
  async function streamData() {
    try {
      const response = await fetch(url, {
        headers: {
          "Authorization": `Bearer ${BEARER_TOKEN}`
        },
        signal: controller.signal
      });
      
      if (!response.ok) throw new Error(`Stream error: ${response.status}`);
      if (!response.body) throw new Error("No response body");
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        
        // Process complete SSE events
        while (true) {
          const match = buffer.match(/\r?\n\r?\n/);
          if (!match) break;
          
          const eventEndIndex = match.index!;
          const matchLength = match[0].length;
          const eventString = buffer.substring(0, eventEndIndex);
          buffer = buffer.substring(eventEndIndex + matchLength);
          
          let eventName = "message";
          let data = "";
          
          const lines = eventString.split(/\r?\n/);
          for (const line of lines) {
            if (line.startsWith('event:')) {
              eventName = line.substring(6).trim();
            } else if (line.startsWith('data:')) {
              data = line.substring(5).trim();
            }
          }
          
          if (data) {
            try {
              const parsed = JSON.parse(data);
              
              if (eventName === 'log') {
                onLog(parsed);
              } else if (eventName === 'result') {
                onResult(parsed);
              } else if (eventName === 'done') {
                onDone(parsed.status);
              }
            } catch (e) {
              console.error("Failed to parse SSE data", e, data);
            }
          }
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        onError(err);
      }
    }
  }
  
  streamData();
  
  // Return cleanup function
  return () => {
    controller.abort();
  };
}

export async function fetchAgentState(sessionId: string): Promise<any> {
  const response = await fetch(`${API_BASE}/plan/${sessionId}/state`, {
    headers: {
      "Authorization": `Bearer ${BEARER_TOKEN}`
    }
  })
  
  if (!response.ok) {
    throw new Error("Failed to fetch state")
  }
  
  return response.json()
}
