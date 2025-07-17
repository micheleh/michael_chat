import React, { useState, ChangeEvent, FormEvent, useRef, useEffect, useImperativeHandle, forwardRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { ChatMessage } from '../types/types';

interface ChatProps {
  apiUrl: string;
  apiKey: string;
  model?: string;
}

export interface ChatRef {
  focus: () => void;
}

const Chat = forwardRef<ChatRef, ChatProps>(({ apiUrl, apiKey, model }, ref) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Expose focus method to parent component
  useImperativeHandle(ref, () => ({
    focus: () => {
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    }
  }));

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

      if (response.ok) {
        const contentType = response.headers.get('content-type');
        
        if (contentType && contentType.includes('text/event-stream')) {
          // Handle streaming response
          const reader = response.body?.getReader();
          const decoder = new TextDecoder("utf-8");

          if (reader) {
            let isDone = false;
            let aiMessageId = (Date.now() + 1).toString();
            let isFirstChunk = true;
            
            // Add initial AI message
            setMessages(prev => [...prev, {
              id: aiMessageId,
              content: '',
              sender: 'ai',
              timestamp: new Date()
            }]);

            while (!isDone) {
              const { done, value } = await reader.read();
              isDone = done;
              if (value) {
                const chunk = decoder.decode(value, { stream: !done });
                
                // Hide "Thinking..." indicator when first chunk arrives
                if (isFirstChunk) {
                  setIsLoading(false);
                  isFirstChunk = false;
                }
                
                // Update the AI message with new content
                setMessages(prevMessages => {
                  return prevMessages.map(msg => 
                    msg.id === aiMessageId 
                      ? { ...msg, content: msg.content + chunk }
                      : msg
                  );
                });
              }
            }
          }
        } else {
          // Handle regular JSON response
          const data = await response.json();
          const aiContent = data.choices?.[0]?.message?.content || 'No response received';
          
          const aiMessage: ChatMessage = {
            id: (Date.now() + 1).toString(),
            content: aiContent,
            sender: 'ai',
            timestamp: new Date()
          };
          
          setMessages(prev => [...prev, aiMessage]);
        }
        
        // Focus input after completion
        setTimeout(() => {
          inputRef.current?.focus();
        }, 100);
      } else {
        // Error handling
        const errorMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          content: `Error: ${response.statusText || 'Unknown error occurred'}`,
          sender: 'system',
          timestamp: new Date()
        };

        setMessages(prev => [...prev, errorMessage]);
        setTimeout(() => {
          inputRef.current?.focus();
        }, 100);
      }
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        content: `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        sender: 'system',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
      // Focus input after network error
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
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
    // Focus input after clearing chat
    setTimeout(() => {
      inputRef.current?.focus();
    }, 100);
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
          ref={inputRef}
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
});

export default Chat;
