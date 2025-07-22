import React, { useState, ChangeEvent, FormEvent, useRef, useEffect, useImperativeHandle, forwardRef, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { ChatMessage, Configuration } from '../types/types';
import ImageThumbnail from './ImageThumbnail';

interface ChatProps {
  apiUrl: string;
  apiKey: string;
  model?: string;
  supportsImages?: boolean;
  configurations?: Configuration[];
  activeConfiguration: Configuration | null;
  onConfigurationChange?: (configId: string) => void;
}

export interface ChatRef {
  focus: () => void;
  clearChat: () => void;
}

const Chat = forwardRef<ChatRef, ChatProps>(({ apiUrl, apiKey, model, supportsImages, configurations = [], activeConfiguration, onConfigurationChange }, ref) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [images, setImages] = useState<Array<{ id: string; file: File; url: string; name: string; size: number }>>([]);
  const [currentStreamId, setCurrentStreamId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Expose focus and clearChat methods to parent component
  useImperativeHandle(ref, () => ({
    focus: () => {
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    },
    clearChat: clearChat
  }));

  const handlePaste = useCallback((event: ClipboardEvent) => {
    if (!supportsImages) return;
    
    const items = event.clipboardData?.items;
    if (items) {
      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        if (item.kind === 'file' && item.type.startsWith('image/')) {
          const file = item.getAsFile();
          if (file) {
            const fileName = file.name || 'pasted-image.png';
            const fileSize = file.size;
            
            // Check for duplicate images in current message (by name and size)
            setImages((prev) => {
              const isDuplicate = prev.some(img => 
                img.name === fileName && img.size === fileSize
              );
              
              if (isDuplicate) {
                console.log('Duplicate image detected, skipping:', fileName);
                return prev; // Don't add duplicate
              }
              
              const id = Date.now().toString() + Math.random().toString(36).substring(2, 11);
              return [
                ...prev,
                { id, file, url: URL.createObjectURL(file), name: fileName, size: fileSize },
              ];
            });
          }
        }
      }
    }
  }, [supportsImages]);

  const removeImage = (id: string) => {
    setImages((prev) => {
      const imageToRemove = prev.find(img => img.id === id);
      if (imageToRemove) {
        URL.revokeObjectURL(imageToRemove.url);
      }
      return prev.filter((image) => image.id !== id);
    });
  };

  useEffect(() => {
    if (supportsImages) {
      document.addEventListener('paste', handlePaste);
      return () => {
        document.removeEventListener('paste', handlePaste);
      };
    }
  }, [supportsImages, handlePaste]);

  // Convert File to base64 data URL
  const convertFileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  const sendMessage = async (content: string, messageImages?: Array<{ id: string; file: File; url: string; name: string; size: number }>) => {
    if (!content.trim() && (!messageImages || messageImages.length === 0)) return;

    // Convert image files to base64 data URLs
    const processedImages = messageImages ? await Promise.all(
      messageImages.map(async (img) => {
        const base64Url = await convertFileToBase64(img.file);
        return {
          id: img.id,
          url: base64Url,
          name: img.name,
          size: img.size
        };
      })
    ) : [];

    // Add user message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content,
      sender: 'user',
      timestamp: new Date(),
      images: messageImages
    };
    
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInput('');
    setImages([]);
    setIsLoading(true);

    try {
      // Send to Python backend with conversation history
      const sanitizedHistory = messages.map(msg => {
        const { images, ...rest } = msg;
        if (!images) return rest;
        return {
          ...rest,
          images: images.map(img => ({
            id: img.id,
            name: img.name,
            size: img.size,
            url: 'about:blank' // Don't send user's local object URLs to the backend
          }))
        };
      });

      const requestBody = {
        message: content,
        images: processedImages,
        api_url: apiUrl,
        api_key: apiKey,
        model: model,
        conversation_history: sanitizedHistory  // Send sanitized history
      };
      
      console.log('Sending chat request:', requestBody);
      
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
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
            let isFirstStreamChunk = true;
            let buffer = '';
            
            // Set a temporary stream ID immediately to show stop button
            const tempStreamId = 'temp-' + Date.now();
            setCurrentStreamId(tempStreamId);
            
            // Add initial AI message with placeholder content
            setMessages(prev => [...prev, {
              id: aiMessageId,
              content: '...',
              sender: 'ai',
              timestamp: new Date()
            }]);
            while (!isDone) {
              const { done, value } = await reader.read();
              isDone = done;
              if (value) {
                const rawChunk = decoder.decode(value, { stream: !done });
                buffer += rawChunk;
                
                // Process complete SSE events from buffer
                const lines = buffer.split('\n');
                buffer = lines.pop() || ''; // Keep incomplete line in buffer
                
                for (const line of lines) {
                  if (line.trim() === '') continue; // Skip empty lines
                  
                  // Check for stream ID in the first chunk
                  if (isFirstStreamChunk && line.includes('stream_id')) {
                    const streamIdMatch = line.match(/"stream_id":\s*"([^"]+)"/);
                    if (streamIdMatch) {
                      setCurrentStreamId(streamIdMatch[1]);
                      console.log('Stream ID received:', streamIdMatch[1]);
                      continue;
                    }
                  }
                  isFirstStreamChunk = false;
                  
                  // Parse SSE data lines
                  if (line.startsWith('data: ')) {
                    let content = line.substring(6); // Remove 'data: ' prefix
                    
                    // Skip only control data, not empty content (which may contain newlines)
                    if (content.includes('stream_id')) {
                      continue;
                    }
                    
                    // Handle newlines explicitly - convert empty strings to actual newlines
                    if(content === "") {
                      content = "\n";
                    }
                    
                    // Update the AI message with new content
                    setMessages(prevMessages => {
                      return prevMessages.map(msg => {
                        if (msg.id === aiMessageId) {
                          // Replace placeholder dots with first real content
                          const currentContent = msg.content === '...' ? '' : msg.content;
                          return { ...msg, content: currentContent + content };
                        }
                        return msg;
                      });
                    });
                  }
                }
              }
            }
            
            // Reset stream ID and loading state when done
            setCurrentStreamId(null);
            setIsLoading(false);
          }
        } else {
          // Handle regular JSON response
          const data = await response.json();
          if (typeof data !== 'object' || data === null) {
            throw new Error('Received invalid response from server');
          }
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

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if ((input.trim() || images.length > 0) && !isLoading) {
      await sendMessage(input, images);
    }
  };

  const handleKeyDown = async (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      if ((input.trim() || images.length > 0) && !isLoading) {
        await sendMessage(input, images);
      }
    }
  };

  const stopStream = async () => {
    if (currentStreamId) {
      try {
        await fetch('/api/chat/stop', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ stream_id: currentStreamId }),
        });
        setCurrentStreamId(null);
        setIsLoading(false);
        console.log('Stream stopped successfully');
      } catch (error) {
        console.error('Error stopping stream:', error);
        setCurrentStreamId(null);
        setIsLoading(false);
      }
    }
  };

  const clearChat = () => {
    setMessages([]);
    // Clear images and revoke object URLs
    images.forEach(img => URL.revokeObjectURL(img.url));
    setImages([]);
    // Reset streaming state
    setCurrentStreamId(null);
    setIsLoading(false);
    // Focus input after clearing chat
    setTimeout(() => {
      inputRef.current?.focus();
    }, 100);
  };

  // Copy to clipboard functionality
  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      // You can add a toast notification here if desired
      console.log('Code copied to clipboard!');
    } catch (err) {
      console.error('Failed to copy code: ', err);
    }
  };

  // Custom code block component
  const CodeBlock = ({ language, children }: { language: string; children: string }) => {
    const [copied, setCopied] = useState(false);
    
    const handleCopy = async () => {
      await copyToClipboard(children);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    };

    return (
      <div className="code-block-container">
        <div className="code-block-header">
          <span className="code-language">{language}</span>
          <button 
            onClick={handleCopy}
            className="copy-button"
            title={copied ? "Copied!" : "Copy code"}
          >
            {copied ? (
              <span className="copy-feedback">✓ Copied!</span>
            ) : (
              <span className="copy-icon">📋</span>
            )}
          </button>
        </div>
        <SyntaxHighlighter
          language={language}
          style={oneDark}
          customStyle={{
            margin: 0,
            borderRadius: '0 0 8px 8px',
            fontSize: '14px',
            lineHeight: '1.5'
          }}
          showLineNumbers={true}
          wrapLines={true}
        >
          {children}
        </SyntaxHighlighter>
      </div>
    );
  };

  return (
    <div className="chat-page">
      <div className="chat-container">
        
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
                <ReactMarkdown
                  components={{
                    code(props: any) {
                      const { node, inline, className, children, ...rest } = props;
                      const match = /language-(\w+)/.exec(className || "");
                      const language = match ? match[1] : "text";

                      if (inline) {
                        return <code {...rest}>{children}</code>;
                      } else {
                        return (
                          <CodeBlock language={language}>
                            {String(children).replace(/\n$/, "")}
                          </CodeBlock>
                        );
                      }
                    }
                  }}
                >
                  {msg.content}
                </ReactMarkdown>
              ) : (
                <p>{msg.content}</p>
              )}
              {msg.images && msg.images.length > 0 && (
                <div className="message-images">
                  {msg.images.map((image) => (
                    <ImageThumbnail
                      key={image.id}
                      image={image}
                      onRemove={() => {}}
                      showRemoveButton={false}
                    />
                  ))}
                </div>
              )}
            </div>
            <div className="message-time">
              {msg.timestamp.toLocaleTimeString()}
            </div>
          </div>
        ))}
        
        {isLoading && !currentStreamId && (
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
        {supportsImages && images.length > 0 && (
          <div className="image-thumbnails">
            {images.map((image) => (
              <ImageThumbnail
                key={image.id}
                image={image}
                onRemove={removeImage}
              />
            ))}
          </div>
        )}
        <div className="input-row">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={supportsImages ? "Type your message or paste images..." : "Type your message..."}
            disabled={isLoading}
            className="message-input"
          />
          {isLoading && currentStreamId ? (
            <button type="button" onClick={stopStream} className="stop-button">
              ⏹ Stop
            </button>
          ) : (
            <button type="submit" disabled={isLoading || (!input.trim() && images.length === 0)} className="send-button">
              {isLoading ? 'Sending...' : 'Send'}
            </button>
          )}
        </div>
        </form>
      </div>
    </div>
  );
});

export default Chat;
