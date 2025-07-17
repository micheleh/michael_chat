import React, { useState, useEffect } from 'react';
import Chat from './components/Chat';
import Configuration from './components/Configuration';
import { Configuration as ConfigType } from './types/types';
import './App.css';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<'chat' | 'config'>('config');
  const [activeConfiguration, setActiveConfiguration] = useState<ConfigType | null>(null);

  // Handle configuration changes from the Configuration component
  const handleConfigurationChange = (config: ConfigType | null) => {
    setActiveConfiguration(config);
    if (config && currentView === 'config') {
      // Don't auto-switch to chat, let user decide
    }
  };

  // Check if configuration is complete
  const isConfigComplete = activeConfiguration && activeConfiguration.apiUrl;

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
            apiUrl={activeConfiguration.apiUrl}
            apiKey={activeConfiguration.apiKey}
            model={activeConfiguration.model}
          />
        )}

        {currentView === 'config' && (
          <Configuration
            onConfigurationChange={handleConfigurationChange}
          />
        )}
      </main>
    </div>
  );
};

export default App;
