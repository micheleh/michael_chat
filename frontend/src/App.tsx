import React, { useState, useEffect } from 'react';
import Chat from './components/Chat';
import Configuration from './components/Configuration';
import { Configuration as ConfigType } from './types/types';
import './App.css';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<'chat' | 'config'>('chat');
  const [configuration, setConfiguration] = useState<ConfigType>({
    apiUrl: 'https://api.openai.com/v1/chat/completions',
    apiKey: ''
  });

  // Load configuration from localStorage on component mount
  useEffect(() => {
    const savedConfig = localStorage.getItem('michael-chat-config');
    if (savedConfig) {
      try {
        const parsed = JSON.parse(savedConfig);
        setConfiguration(parsed);
      } catch (error) {
        console.error('Error parsing saved configuration:', error);
      }
    }
  }, []);

  // Save configuration to localStorage and switch to chat view
  const handleConfigSave = (apiUrl: string, apiKey: string) => {
    const newConfig = { apiUrl, apiKey };
    setConfiguration(newConfig);
    localStorage.setItem('michael-chat-config', JSON.stringify(newConfig));
    setCurrentView('chat');
    alert('Configuration saved successfully!');
  };

  // Check if configuration is complete
  const isConfigComplete = configuration.apiUrl && configuration.apiKey;

  return (
    <div className="app">
      <nav className="navbar">
        <div className="nav-brand">
          <h1>Michael's Chat</h1>
        </div>
        <div className="nav-links">
          <button 
            className={currentView === 'chat' ? 'nav-button active' : 'nav-button'}
            onClick={() => setCurrentView('chat')}
            disabled={!isConfigComplete}
          >
            Chat
          </button>
          <button 
            className={currentView === 'config' ? 'nav-button active' : 'nav-button'}
            onClick={() => setCurrentView('config')}
          >
            Configuration
          </button>
        </div>
      </nav>

      <main className="main-content">
        {!isConfigComplete && currentView === 'chat' && (
          <div className="config-warning">
            <h2>Configuration Required</h2>
            <p>Please configure your API settings before starting a chat.</p>
            <button 
              onClick={() => setCurrentView('config')}
              className="config-button"
            >
              Go to Configuration
            </button>
          </div>
        )}

        {currentView === 'chat' && isConfigComplete && (
          <Chat 
            apiUrl={configuration.apiUrl}
            apiKey={configuration.apiKey}
          />
        )}

        {currentView === 'config' && (
          <Configuration
            onConfigSave={handleConfigSave}
            currentApiUrl={configuration.apiUrl}
            currentApiKey={configuration.apiKey}
          />
        )}
      </main>
    </div>
  );
};

export default App;
