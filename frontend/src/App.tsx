import React, { useState, useEffect, useRef } from 'react';
import Chat, { ChatRef } from './components/Chat';
import Configuration from './components/Configuration';
import { Configuration as ConfigType } from './types/types';
import './App.css';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<'chat' | 'config'>('chat');
  const [activeConfiguration, setActiveConfiguration] = useState<ConfigType | null>(null);
  const chatRef = useRef<ChatRef>(null);

  // Handle configuration changes from the Configuration component
  const handleConfigurationChange = (config: ConfigType | null) => {
    console.log('Configuration changed:', config);
    setActiveConfiguration(config);
    
    // If we just set up the first configuration and we're on config view, switch to chat
    if (config && currentView === 'config' && !activeConfiguration) {
      setCurrentView('chat');
    }
  };

  // Check if configuration is complete
  const isConfigComplete = activeConfiguration && activeConfiguration.apiUrl;


  // Focus chat input when switching to chat view
  useEffect(() => {
    if (currentView === 'chat' && isConfigComplete) {
      // Focus the chat input after the component has rendered
      chatRef.current?.focus();
    }
  }, [currentView, isConfigComplete]);

  return (
    <div className="app">
      <nav className="navbar">
        <div className="nav-brand">
          <h1>Michael's Chat</h1>
          {activeConfiguration && (
            <span className="active-config-indicator">
              Active: {activeConfiguration.name}
            </span>
          )}
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
            ref={chatRef}
            apiUrl={activeConfiguration.apiUrl}
            apiKey={activeConfiguration.apiKey}
            model={activeConfiguration.model}
            supportsImages={activeConfiguration.supportsImages || false}
          />
        )}

        <div style={{ display: currentView === 'config' ? 'block' : 'none' }}>
          <Configuration
            onConfigurationChange={handleConfigurationChange}
          />
        </div>
      </main>
    </div>
  );
};

export default App;
