import React, { useState, useEffect, useCallback, FormEvent, useRef } from 'react';
import { Configuration, ConfigurationInput } from '../types/types';

interface ConfigurationProps {
  onConfigurationChange: (config: Configuration | null) => void;
}

const ConfigurationComponent: React.FC<ConfigurationProps> = ({ onConfigurationChange }) => {
  const [configurations, setConfigurations] = useState<Configuration[]>([]);
  const [activeConfig, setActiveConfig] = useState<Configuration | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editingConfig, setEditingConfig] = useState<Configuration | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Form state
  const [formData, setFormData] = useState<ConfigurationInput>({
    name: '',
    apiUrl: '',
    apiKey: '',
    model: ''
  });
  const [showApiKey, setShowApiKey] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);
  const [showTestResult, setShowTestResult] = useState(false);

  // Use ref to store the callback to prevent infinite loops
  const onConfigurationChangeRef = useRef(onConfigurationChange);
  
  // Update the ref when the callback changes
  useEffect(() => {
    onConfigurationChangeRef.current = onConfigurationChange;
  }, [onConfigurationChange]);

  const loadConfigurations = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/configurations');
      const data = await response.json();
      
      if (response.ok) {
        setConfigurations(data);
        
        // Find and set active configuration
        const active = data.find((config: Configuration) => config.isActive);
        setActiveConfig(active);
        // Use the ref to call the callback
        if (active) {
          onConfigurationChangeRef.current(active);
        }
      } else {
        throw new Error(data.error || 'Failed to load configurations');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load configurations');
    } finally {
      setLoading(false);
    }
  }, []); // No dependencies needed now

  // Load configurations on component mount
  useEffect(() => {
    loadConfigurations();
  }, [loadConfigurations]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    if (!formData.name.trim() || !formData.apiUrl.trim()) {
      setError('Name and API URL are required');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const url = isEditing ? `/api/configurations/${editingConfig?.id}` : '/api/configurations';
      const method = isEditing ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });
      
      const data = await response.json();
      
      if (response.ok) {
        await loadConfigurations();
        resetForm();
        setShowForm(false);
        setIsEditing(false);
        setEditingConfig(null);
        
        // If this is the first configuration, it becomes active automatically
        if (!isEditing && configurations.length === 0) {
          setActiveConfig(data);
          onConfigurationChangeRef.current(data);
        }
      } else {
        throw new Error(data.error || 'Failed to save configuration');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (config: Configuration) => {
    setIsEditing(true);
    setEditingConfig(config);
    setFormData({
      name: config.name,
      apiUrl: config.apiUrl,
      apiKey: config.apiKey,
      model: config.model
    });
    setShowForm(true);
  };

  const handleDelete = async (configId: string) => {
    if (!window.confirm('Are you sure you want to delete this configuration?')) {
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`/api/configurations/${configId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        await loadConfigurations();
      } else {
        const data = await response.json();
        throw new Error(data.error || 'Failed to delete configuration');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleActivate = async (configId: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`/api/configurations/${configId}/activate`, {
        method: 'POST'
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setActiveConfig(data);
        onConfigurationChangeRef.current(data);
        await loadConfigurations();
      } else {
        throw new Error(data.error || 'Failed to activate configuration');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to activate configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async () => {
    try {
      const response = await fetch('/api/health');
      
      if (response.ok) {
        alert('Backend connection successful!');
      } else {
        alert('Backend connection failed!');
      }
    } catch (error) {
      alert('Backend connection failed: ' + (error instanceof Error ? error.message : 'Unknown error'));
    }
  };

  const handleTestExternalAPI = async (config: Configuration) => {
    try {
      const response = await fetch('/api/test-external', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          api_url: config.apiUrl,
          api_key: config.apiKey,
          model: config.model
        })
      });

      const data = await response.json();
      
      // Set the test result data and show modal
      setTestResult({
        config,
        response: data,
        success: response.ok,
        statusCode: response.status
      });
      setShowTestResult(true);
      
    } catch (error) {
      // Set error result and show modal
      setTestResult({
        config,
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        statusCode: null
      });
      setShowTestResult(true);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      apiUrl: '',
      apiKey: '',
      model: ''
    });
    setShowApiKey(false);
  };

  const handleCancel = () => {
    resetForm();
    setShowForm(false);
    setIsEditing(false);
    setEditingConfig(null);
    setError(null);
  };

  if (loading && configurations.length === 0) {
    return <div className="configuration-container">Loading configurations...</div>;
  }

  return (
    <div className="configuration-container">
      <div className="config-header">
        <h2>API Configurations</h2>
        <button 
          onClick={() => setShowForm(true)} 
          className="add-config-button"
          disabled={loading}
        >
          + Add Configuration
        </button>
      </div>

      {error && (
        <div className="error-message">
          {error}
          <button onClick={() => setError(null)} className="dismiss-error">×</button>
        </div>
      )}

      {/* Configuration List */}
      <div className="config-list">
        {configurations.length === 0 ? (
          <div className="no-configs">
            <p>No configurations found. Create your first configuration to get started.</p>
          </div>
        ) : (
          configurations.map((config) => (
            <div key={config.id} className={`config-item ${config.isActive ? 'active' : ''}`}>
              <div className="config-info">
                <h3>{config.name}</h3>
                <p className="config-url">{config.apiUrl}</p>
                <p className="config-url">Model: {config.model}</p>
                <p className="config-meta">
                  Created: {new Date(config.createdAt).toLocaleDateString()}
                  {config.updatedAt !== config.createdAt && (
                    <span> • Updated: {new Date(config.updatedAt).toLocaleDateString()}</span>
                  )}
                </p>
                <div className="image-support-info">
                  <span className="image-support-label">Image Support:</span>
                  {config.supportsImages === true && (
                    <span className="image-support-yes">✅ Yes</span>
                  )}
                  {config.supportsImages === false && (
                    <span className="image-support-no">❌ No</span>
                  )}
                  {config.supportsImages === null && (
                    <span className="image-support-unknown">❓ Unknown</span>
                  )}
                  {config.imageTestAt && (
                    <span className="image-test-date">
                      • Tested: {new Date(config.imageTestAt).toLocaleDateString()}
                    </span>
                  )}
                </div>
              </div>
              <div className="config-actions">
                {config.isActive ? (
                  <span className="active-badge">Active</span>
                ) : (
                  <button 
                    onClick={() => handleActivate(config.id)}
                    className="activate-button"
                    disabled={loading}
                  >
                    Activate
                  </button>
                )}
                <button 
                  onClick={() => handleEdit(config)}
                  className="edit-button"
                  disabled={loading}
                >
                  Edit
                </button>
                <button 
                  onClick={() => handleTestExternalAPI(config)}
                  className="test-button"
                  disabled={loading}
                >
                  Test
                </button>
                <button 
                  onClick={() => handleDelete(config.id)}
                  className="delete-button"
                  disabled={loading || configurations.length === 1}
                >
                  Delete
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Add/Edit Form */}
      {showForm && (
        <div className="config-form-overlay">
          <div className="config-form-modal">
            <h3>{isEditing ? 'Edit Configuration' : 'Add New Configuration'}</h3>
            
            <form onSubmit={handleSubmit} className="config-form">
              <div className="form-group">
                <label htmlFor="name">Configuration Name:</label>
                <input
                  type="text"
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  placeholder="e.g., OpenAI GPT-4, Local LLM, etc."
                  required
                  className="config-input"
                />
              </div>

              <div className="form-group">
                <label htmlFor="apiUrl">API Endpoint URL:</label>
                <input
                  type="url"
                  id="apiUrl"
                  value={formData.apiUrl}
                  onChange={(e) => setFormData({...formData, apiUrl: e.target.value})}
                  placeholder="https://api.openai.com/v1/chat/completions"
                  required
                  className="config-input"
                />
              </div>

              <div className="form-group">
                <label htmlFor="model">Model:</label>
                <input
                  type="text"
                  id="model"
                  value={formData.model}
                  onChange={(e) => setFormData({...formData, model: e.target.value})}
                  placeholder="e.g., gpt-4, phi4:latest, claude-3-opus (optional)"
                  className="config-input"
                />
              </div>

              <div className="form-group">
                <label htmlFor="apiKey">API Key:</label>
                <div className="api-key-container">
                  <input
                    type={showApiKey ? 'text' : 'password'}
                    id="apiKey"
                    value={formData.apiKey}
                    onChange={(e) => setFormData({...formData, apiKey: e.target.value})}
                    placeholder="Enter your API key (optional)"
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
              </div>

              <div className="form-actions">
                <button type="submit" className="save-button" disabled={loading}>
                  {loading ? 'Saving...' : (isEditing ? 'Update Configuration' : 'Save Configuration')}
                </button>
                <button type="button" onClick={handleCancel} className="cancel-button">
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Test Result Modal */}
      {showTestResult && testResult && (
        <div className="config-form-overlay">
          <div className="config-form-modal">
            <h3>External API Test Results</h3>
            
            <div className="test-result-content">
              <div className="test-result-header">
                <h4>Configuration: {testResult.config.name}</h4>
                <div className={`test-status ${testResult.success ? 'success' : 'failure'}`}>
                  {testResult.success ? '✅ Test Passed' : '❌ Test Failed'}
                </div>
              </div>
              
              {testResult.response && (
                <div className="test-result-details">
                  <p><strong>Status:</strong> {testResult.response.health_status || 'Unknown'}</p>
                  <p><strong>Status Code:</strong> {testResult.response.status_code || testResult.statusCode || 'N/A'}</p>
                  <p><strong>Message:</strong> {testResult.response.message || 'No message'}</p>
                  
                  {/* Image Support Information */}
                  <div className="image-support-test-result">
                    <p><strong>Image Support:</strong>
                      {testResult.response.supports_images === true && (
                        <span className="image-support-yes"> ✅ Yes</span>
                      )}
                      {testResult.response.supports_images === false && (
                        <span className="image-support-no"> ❌ No</span>
                      )}
                      {testResult.response.supports_images === null && (
                        <span className="image-support-unknown"> ❓ Unknown</span>
                      )}
                    </p>
                    {testResult.response.image_test_error && (
                      <p><strong>Image Test Error:</strong> {testResult.response.image_test_error}</p>
                    )}
                  </div>
                  
                  {testResult.response.test_response && (
                    <div className="api-response">
                      <p><strong>API Response:</strong></p>
                      <pre>{testResult.response.test_response}</pre>
                    </div>
                  )}
                  
                  {testResult.response.error && (
                    <div className="error-details">
                      <p><strong>Error:</strong> {testResult.response.error}</p>
                      {testResult.response.error_type && (
                        <p><strong>Error Type:</strong> {testResult.response.error_type}</p>
                      )}
                    </div>
                  )}
                </div>
              )}
              
              {testResult.error && (
                <div className="error-details">
                  <p><strong>Connection Error:</strong> {testResult.error}</p>
                </div>
              )}
            </div>
            
            <div className="form-actions">
              <button 
                type="button" 
                onClick={() => setShowTestResult(false)} 
                className="cancel-button"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Utility Actions */}
      <div className="config-utilities">
        <button onClick={handleTestConnection} className="test-button">
          Test Backend Connection
        </button>
      </div>

      <div className="config-info">
        <h3>Information</h3>
        <ul>
          <li>Configurations are stored on the server (in-memory for now)</li>
          <li>API calls are proxied through the Python backend</li>
          <li>Only one configuration can be active at a time</li>
          <li>The active configuration is used for all chat requests</li>
          <li>Image support is automatically tested when saving or testing configurations</li>
          <li>Image support testing helps identify models that can process images</li>
        </ul>
      </div>
    </div>
  );
};

export default ConfigurationComponent;
