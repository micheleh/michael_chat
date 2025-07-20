import React, { useState, useEffect, useCallback, FormEvent, useRef } from 'react';
import { Configuration, ConfigurationInput } from '../types/types';
import { FaPlus, FaCheckCircle, FaTimesCircle, FaQuestionCircle, FaInfoCircle, FaTrash, FaEdit, FaPlay, FaPowerOff } from 'react-icons/fa';

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

  const [formData, setFormData] = useState<ConfigurationInput>({
    name: '',
    apiUrl: '',
    apiKey: '',
    model: ''
  });
  const [showApiKey, setShowApiKey] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);
  const [showTestResult, setShowTestResult] = useState(false);
  const [testingConfigId, setTestingConfigId] = useState<string | null>(null);

  const onConfigurationChangeRef = useRef(onConfigurationChange);

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
        const active = data.find((config: Configuration) => config.isActive);
        setActiveConfig(active);
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
  }, []);

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
      setTestingConfigId(config.id);
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
      setTestResult({
        config,
        response: data,
        success: response.ok,
        statusCode: response.status
      });
      setShowTestResult(true);
      if (response.ok) {
        await loadConfigurations();
      }
    } catch (error) {
      setTestResult({
        config,
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        statusCode: null
      });
      setShowTestResult(true);
    } finally {
      setTestingConfigId(null);
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
    return <div className="config-loading">Loading configurations...</div>;
  }

  return (
    <div className="configuration-page">
      <div className="config-main-content">
        <div className="config-header">
          <h2>API Configurations</h2>
          <button
            onClick={() => setShowForm(true)}
            className="btn btn-primary"
            disabled={loading}
          >
            <FaPlus /> Add Configuration
          </button>
        </div>

        {error && (
          <div className="error-message">
            {error}
            <button onClick={() => setError(null)} className="dismiss-error">×</button>
          </div>
        )}

        <div className="config-list">
          {configurations.length === 0 ? (
            <div className="no-configs">
              <p>No configurations found. Create your first one to get started.</p>
            </div>
          ) : (
            configurations.map((config) => (
              <div key={config.id} className={`config-card ${config.isActive ? 'active' : ''}`}>
                <div className="config-card-header">
                  <h3>{config.name}</h3>
                  {config.isActive && <span className="active-badge"><FaCheckCircle /> Active</span>}
                </div>
                <div className="config-card-body">
                  <p className="config-url"><span>URL:</span> {config.apiUrl}</p>
                  <p className="config-model"><span>Model:</span> {config.model || 'Not specified'}</p>
                  <div className="config-meta">
                    <span>Created: {new Date(config.createdAt).toLocaleDateString()}</span>
                    {config.updatedAt !== config.createdAt && (
                      <span>Updated: {new Date(config.updatedAt).toLocaleDateString()}</span>
                    )}
                  </div>
                  <div className="image-support-info">
                    <span>Image Support:</span>
                    {config.supportsImages === true && <span className="image-support-yes"><FaCheckCircle /> Yes</span>}
                    {config.supportsImages === false && <span className="image-support-no"><FaTimesCircle /> No</span>}
                    {config.supportsImages === null && <span className="image-support-unknown"><FaQuestionCircle /> Unknown</span>}
                  </div>
                </div>
                <div className="config-card-actions">
                  {!config.isActive && (
                    <button onClick={() => handleActivate(config.id)} className="btn btn-warning" disabled={loading}>
                      <FaPowerOff /> Activate
                    </button>
                  )}
                  <button 
                    onClick={() => handleTestExternalAPI(config)} 
                    className="btn btn-secondary" 
                    disabled={loading || testingConfigId === config.id}
                  >
                    {testingConfigId === config.id ? (
                      <>🔄 Testing...</>
                    ) : (
                      <><FaPlay /> Test</>
                    )}
                  </button>
                  <button onClick={() => handleEdit(config)} className="btn btn-secondary" disabled={loading}>
                    <FaEdit /> Edit
                  </button>
                  <button onClick={() => handleDelete(config.id)} className="btn btn-danger" disabled={loading || configurations.length === 1}>
                    <FaTrash /> Delete
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="config-sidebar">
        <div className="info-card">
          <h4><FaInfoCircle /> Information</h4>
          <ul>
            <li>Configurations are stored on the server.</li>
            <li>API calls are proxied through the backend.</li>
            <li>Only one configuration can be active at a time.</li>
            <li>Image support is tested on save/test.</li>
          </ul>
        </div>
        <button onClick={handleTestConnection} className="btn btn-secondary btn-full-width">
          Test Backend Connection
        </button>
      </div>

      {showForm && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3>{isEditing ? 'Edit Configuration' : 'Add New Configuration'}</h3>
            <form onSubmit={handleSubmit} className="config-form">
              <div className="form-group">
                <label htmlFor="name">Configuration Name:</label>
                <input
                  type="text"
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., OpenAI GPT-4"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="apiUrl">API Endpoint URL:</label>
                <input
                  type="url"
                  id="apiUrl"
                  value={formData.apiUrl}
                  onChange={(e) => setFormData({ ...formData, apiUrl: e.target.value })}
                  placeholder="https://api.openai.com/v1/chat/completions"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="model">Model:</label>
                <input
                  type="text"
                  id="model"
                  value={formData.model}
                  onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                  placeholder="e.g., gpt-4 (optional)"
                />
              </div>
              <div className="form-group">
                <label htmlFor="apiKey">API Key:</label>
                <div className="api-key-container">
                  <input
                    type={showApiKey ? 'text' : 'password'}
                    id="apiKey"
                    value={formData.apiKey}
                    onChange={(e) => setFormData({ ...formData, apiKey: e.target.value })}
                    placeholder="Enter your API key (optional)"
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
                <button type="button" onClick={handleCancel} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? 'Saving...' : (isEditing ? 'Update' : 'Save')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showTestResult && testResult && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3>API Test Results</h3>
            <div className="test-result-content">
              <h4>{testResult.config.name}</h4>
              <div className={`test-status ${testResult.success ? 'success' : 'failure'}`}>
                {testResult.success ? '✅ Test Passed' : '❌ Test Failed'}
              </div>
              {/* ... additional test result details ... */}
            </div>
            <div className="form-actions">
              <button onClick={() => setShowTestResult(false)} className="btn btn-secondary">
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ConfigurationComponent;
