import React, { useState, FormEvent } from 'react';

interface ConfigurationProps {
  onConfigSave: (apiUrl: string, apiKey: string) => void;
  currentApiUrl: string;
  currentApiKey: string;
}

const Configuration: React.FC<ConfigurationProps> = ({ onConfigSave, currentApiUrl, currentApiKey }) => {
  const [apiUrl, setApiUrl] = useState(currentApiUrl);
  const [apiKey, setApiKey] = useState(currentApiKey);
  const [showApiKey, setShowApiKey] = useState(false);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (apiUrl.trim() && apiKey.trim()) {
      onConfigSave(apiUrl.trim(), apiKey.trim());
    }
  };

  const handleTestConnection = async () => {
    try {
      const response = await fetch('/api/health');
      const data = await response.json();
      
      if (response.ok) {
        alert('Backend connection successful!');
      } else {
        alert('Backend connection failed!');
      }
    } catch (error) {
      alert('Backend connection failed: ' + (error instanceof Error ? error.message : 'Unknown error'));
    }
  };

  const handleTestExternalAPI = async () => {
    if (!apiUrl.trim()) {
      alert('Please enter an API URL first');
      return;
    }

    try {
      const response = await fetch('/api/test-external', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          api_url: apiUrl.trim(),
          api_key: apiKey.trim()
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        let message = `External API Test Results:\n\n`;
        message += `Health Check: ${data.health_status === 200 ? '✅ Success' : '❌ Failed'} (${data.health_status})\n`;
        message += `Health Response: ${data.health_response}\n\n`;
        
        if (data.chat_test_status) {
          message += `Chat Test: ${data.chat_test_status === 200 ? '✅ Success' : '❌ Failed'} (${data.chat_test_status})\n`;
          message += `Chat Response: ${data.chat_test_response}\n`;
        } else {
          message += data.note || 'Chat test not performed';
        }
        
        alert(message);
      } else {
        alert('External API test failed: ' + (data.error || 'Unknown error'));
      }
    } catch (error) {
      alert('External API test failed: ' + (error instanceof Error ? error.message : 'Unknown error'));
    }
  };

  const resetToDefaults = () => {
    setApiUrl('https://api.openai.com/v1/chat/completions');
    setApiKey('');
  };

  return (
    <div className="configuration-container">
      <h2>Configuration</h2>
      
      <form onSubmit={handleSubmit} className="config-form">
        <div className="form-group">
          <label htmlFor="apiUrl">API Endpoint URL:</label>
          <input
            type="url"
            id="apiUrl"
            value={apiUrl}
            onChange={(e) => setApiUrl(e.target.value)}
            placeholder="https://api.openai.com/v1/chat/completions"
            required
            className="config-input"
          />
          <small className="form-help">
            Enter the complete API endpoint URL for your chat service
          </small>
        </div>

        <div className="form-group">
          <label htmlFor="apiKey">API Key:</label>
          <div className="api-key-container">
            <input
              type={showApiKey ? 'text' : 'password'}
              id="apiKey"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Enter your API key"
              required
              className="config-input"
            />
            <button
              type="button"
              onClick={() => setShowApiKey(!showApiKey)}
              className="toggle-visibility"
            >
              {showApiKey ? 'Hide' : 'Show'}
            </button>
          </div>
          <small className="form-help">
            Your API key will be stored locally in your browser
          </small>
        </div>

        <div className="form-actions">
          <button type="submit" className="save-button">
            Save Configuration
          </button>
          <button type="button" onClick={resetToDefaults} className="reset-button">
            Reset to Defaults
          </button>
          <button type="button" onClick={handleTestConnection} className="test-button">
            Test Backend Connection
          </button>
          <button type="button" onClick={handleTestExternalAPI} className="test-button">
            Test External API
          </button>
        </div>
      </form>

      <div className="config-info">
        <h3>Information</h3>
        <ul>
          <li>Configuration is saved locally in your browser</li>
          <li>API calls are proxied through the Python backend</li>
          <li>Your API key is never stored on the server</li>
          <li>Default endpoint works with OpenAI API</li>
        </ul>
      </div>
    </div>
  );
};

export default Configuration;
