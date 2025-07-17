import React, { useState, ChangeEvent, FormEvent, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { ChatMessage } from '../types/types';

interface ChatProps {
  apiUrl: string;
  apiKey: string;
  model?: string;
}

const Chat: React.FC<ChatProps> = ({ apiUrl, apiKey, model }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (content: string) => {
    if (!content.trim()) return;

    // Add user message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content,
      sender: 'user',
      timestamp: new Date()
    };
    
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInput('');
    setIsLoading(true);

    try {
      // Send to Python backend with conversation history
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: content,
          api_url: apiUrl,
          api_key: apiKey,
          model: model,
          conversation_history: messages  // Send previous messages as context
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        // Extract AI response from OpenAI format
        const aiContent = data.choices?.[0]?.message?.content || 'No response received';
        
        const aiMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          content: aiContent,
          sender: 'ai',
          timestamp: new Date()
        };
        
        setMessages(prev => [...prev, aiMessage]);
      } else {
        // Error handling
        const errorMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          content: `Error: ${data.error || 'Unknown error occurred'}`,
          sender: 'system',
          timestamp: new Date()
        };
        
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        content: `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        sender: 'system',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (input.trim() && !isLoading) {
      sendMessage(input);
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>Michael's Chat</h2>
        <button onClick={clearChat} className="clear-button">
          Clear Chat
        </button>
      </div>
      
      <div className="messages-container">
        {messages.length === 0 && (
          <div className="welcome-message">
            <p>Welcome to Michael's Chat! Start a conversation.</p>
          </div>
        )}
        
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.sender}`}>
            <div className="message-content">
              <strong>{msg.sender === 'user' ? 'You' : msg.sender === 'ai' ? 'AI' : 'System'}:</strong>
              {msg.sender === 'ai' ? (
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              ) : (
                <p>{msg.content}</p>
              )}
            </div>
            <div className="message-time">
              {msg.timestamp.toLocaleTimeString()}
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="message ai">
            <div className="message-content">
              <strong>AI:</strong>
              <p>Thinking...</p>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <form onSubmit={onSubmit} className="input-form">
        <input
          type="text"
          value={input}
          onChange={(e: ChangeEvent<HTMLInputElement>) => setInput(e.target.value)}
          placeholder="Type your message..."
          disabled={isLoading}
          className="message-input"
        />
        <button type="submit" disabled={isLoading || !input.trim()} className="send-button">
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  );
};

export default Chat;
