export interface ChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'ai' | 'system';
  timestamp: Date;
}

export interface Configuration {
  apiUrl: string;
  apiKey: string;
}

export interface ApiResponse {
  choices: Array<{
    message: {
      content: string;
      role: string;
    };
  }>;
}

export interface ApiError {
  error: string;
  details?: string;
}
