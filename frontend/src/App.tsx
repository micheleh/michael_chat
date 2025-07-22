import React, { useState, useEffect, useRef, useCallback } from 'react';
import Chat, { ChatRef } from './components/Chat';
import Configuration from './components/Configuration';
import ConfigurationDropdown from './components/ConfigurationDropdown';
import { Configuration as ConfigType } from './types/types';
import './App.css';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<'chat' | 'config'>('chat');
  const [activeConfiguration, setActiveConfiguration] = useState<ConfigType | null>(null);
  const [configurations, setConfigurations] = useState<ConfigType[]>([]);
  const chatRef = useRef<ChatRef>(null);

  // Load all configurations from the server
  const loadConfigurations = useCallback(async () => {
    try {
      const response = await fetch('/api/configurations');
      const data = await response.json();
      
      if (response.ok) {
        setConfigurations(data);
        const active = data.find((config: ConfigType) => config.isActive);
        setActiveConfiguration(active || null);
      } else {
        console.error('Failed to load configurations:', data.error);
      }
    } catch (err) {
      console.error('Error loading configurations:', err);
    }
  }, []);

  // Load configurations on app startup
  useEffect(() => {
    loadConfigurations();
  }, [loadConfigurations]);

  // Handle configuration changes from the Configuration component
  const handleConfigurationChange = (config: ConfigType | null) => {
    console.log('Configuration changed:', config);
    setActiveConfiguration(config);
    
    // If we just set up the first configuration and we're on config view, switch to chat
    if (config && currentView === 'config' && !activeConfiguration) {
      setCurrentView('chat');
    }
    
    // Reload configurations to get the updated list
    loadConfigurations();
  };

  // Handle configuration changes from the Chat component dropdown
  const handleChatConfigurationChange = async (configId: string) => {
    try {
      const response = await fetch(`/api/configurations/${configId}/activate`, {
        method: 'POST'
      });
      
      if (response.ok) {
        const data = await response.json();
        setActiveConfiguration(data);
        // Reload all configurations to update their active status
        loadConfigurations();
      } else {
        const error = await response.json();
        console.error('Failed to activate configuration:', error);
      }
    } catch (err) {
      console.error('Error activating configuration:', err);
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
        </div>
        <div className="nav-center">
          {/* Empty center section for future use */}
        </div>
        
        <div className="nav-right">
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
          <div className="three-panel-layout">
            {/* Left Panel - Controls */}
            <div className="left-panel">
              <div className="panel-content">
                {/* Configuration selector */}
                {configurations.length > 1 && (
                  <div className="panel-config-selector">
                    <ConfigurationDropdown
                      configurations={configurations}
                      activeConfiguration={activeConfiguration}
                      onConfigurationChange={handleChatConfigurationChange}
                      disabled={false}
                    />
                  </div>
                )}
                
                {/* Clear chat button */}
                <button 
                  className="panel-clear-button" 
                  onClick={() => chatRef.current?.clearChat?.()}
                >
                  🗑️ Clear Chat
                </button>
              </div>
            </div>

            {/* Center Panel - Chat */}
            <div className="center-panel">
              <Chat 
                ref={chatRef}
                apiUrl={activeConfiguration.apiUrl}
                apiKey={activeConfiguration.apiKey}
                model={activeConfiguration.model}
                supportsImages={activeConfiguration.supportsImages || false}
                configurations={configurations}
                activeConfiguration={activeConfiguration}
                onConfigurationChange={handleChatConfigurationChange}
              />
            </div>

            {/* Right Panel - Empty for now */}
            <div className="right-panel">
              {/* Empty for future use */}
            </div>
          </div>
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
