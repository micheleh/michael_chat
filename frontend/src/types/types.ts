export interface ChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'ai' | 'system';
  timestamp: Date;
}

export interface Configuration {
  id: string;
  name: string;
  apiUrl: string;
  apiKey: string;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface ConfigurationInput {
  name: string;
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
