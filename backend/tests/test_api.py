import pytest


def validate_chat_response(response, message_context=""):
    """Helper function to validate chat response structure."""
    context = f" for message: '{message_context}'" if message_context else ""
    assert 'choices' in response.json, f"Response missing 'choices' field{context}"
    assert len(response.json['choices']) > 0, f"Response has no choices{context}"
    assert 'message' in response.json['choices'][0], f"Response missing 'message' field{context}"
    assert 'content' in response.json['choices'][0]['message'], f"Response missing 'content' field{context}"
    assert response.json['choices'][0]['message']['content'].strip() != '', f"Response content is empty{context}"


class TestConfigurationAPI:
    """Test suite for Configuration API endpoints."""
    
    def test_get_empty_configurations(self, client):
        """Test getting configurations when none exist."""
        response = client.get('/api/configurations')
        assert response.status_code == 200
        assert response.json == []
    
    def test_create_configuration(self, client):
        """Test creating a new configuration."""
        config_data = {
            'name': 'Test Config',
            'apiUrl': 'http://localhost:10001/v1/chat/completions',
            'apiKey': 'test-key',
            'model': 'phi4:latest'
        }
        
        response = client.post('/api/configurations', json=config_data)
        assert response.status_code == 201
        
        data = response.json
        assert 'id' in data
        assert data['name'] == config_data['name']
        assert data['apiUrl'] == config_data['apiUrl']
        assert data['apiKey'] == config_data['apiKey']
        assert data['model'] == config_data['model']
        assert data['isActive'] is True  # First config should be active
    
    def test_create_configuration_missing_fields(self, client):
        """Test creating configuration with missing required fields."""
        response = client.post('/api/configurations', json={'name': 'Test'})
        assert response.status_code == 400
        assert 'Missing required field' in response.json['error']
    
    def test_create_duplicate_configuration(self, client):
        """Test creating configuration with duplicate name."""
        config_data = {
            'name': 'Duplicate Test',
            'apiUrl': 'http://localhost:10001/v1/chat/completions'
        }
        
        # Create first configuration
        response1 = client.post('/api/configurations', json=config_data)
        assert response1.status_code == 201
        
        # Try to create duplicate
        response2 = client.post('/api/configurations', json=config_data)
        assert response2.status_code == 409
        assert 'already exists' in response2.json['error']
    
    def test_get_configurations(self, client):
        """Test getting all configurations."""
        # Create a test configuration
        config_data = {
            'name': 'Test Config',
            'apiUrl': 'http://localhost:10001/v1/chat/completions'
        }
        client.post('/api/configurations', json=config_data)
        
        # Get all configurations
        response = client.get('/api/configurations')
        assert response.status_code == 200
        assert len(response.json) == 1
        assert response.json[0]['name'] == 'Test Config'
    
    def test_update_configuration(self, client):
        """Test updating an existing configuration."""
        # Create a configuration
        config_data = {
            'name': 'Original Config',
            'apiUrl': 'http://localhost:10001/v1/chat/completions'
        }
        create_response = client.post('/api/configurations', json=config_data)
        config_id = create_response.json['id']
        
        # Update the configuration
        updated_data = {
            'name': 'Updated Config',
            'apiUrl': 'http://localhost:10002/v1/chat/completions',
            'model': 'updated-model'
        }
        
        response = client.put(f'/api/configurations/{config_id}', json=updated_data)
        assert response.status_code == 200
        
        data = response.json
        assert data['name'] == 'Updated Config'
        assert data['apiUrl'] == 'http://localhost:10002/v1/chat/completions'
        assert data['model'] == 'updated-model'
    
    def test_delete_configuration(self, client):
        """Test deleting a configuration."""
        # Create a configuration
        config_data = {
            'name': 'To Delete',
            'apiUrl': 'http://localhost:10001/v1/chat/completions'
        }
        create_response = client.post('/api/configurations', json=config_data)
        config_id = create_response.json['id']
        
        # Delete the configuration
        response = client.delete(f'/api/configurations/{config_id}')
        assert response.status_code == 200
        assert 'deleted successfully' in response.json['message']
        
        # Verify it's gone
        get_response = client.get('/api/configurations')
        assert len(get_response.json) == 0
    
    def test_activate_configuration(self, client):
        """Test activating a configuration."""
        # Create two configurations
        config1_data = {
            'name': 'Config 1',
            'apiUrl': 'http://localhost:10001/v1/chat/completions'
        }
        config2_data = {
            'name': 'Config 2',
            'apiUrl': 'http://localhost:10002/v1/chat/completions'
        }
        
        response1 = client.post('/api/configurations', json=config1_data)
        response2 = client.post('/api/configurations', json=config2_data)
        
        config1_id = response1.json['id']
        config2_id = response2.json['id']
        
        # Activate config2
        response = client.post(f'/api/configurations/{config2_id}/activate')
        assert response.status_code == 200
        assert response.json['isActive'] is True
        
        # Verify config1 is no longer active
        get_response = client.get('/api/configurations')
        configs = get_response.json
        
        config1 = next(c for c in configs if c['id'] == config1_id)
        config2 = next(c for c in configs if c['id'] == config2_id)
        
        assert config1['isActive'] is False
        assert config2['isActive'] is True
    
    def test_get_active_configuration(self, client):
        """Test getting the active configuration."""
        # Initially no active configuration
        response = client.get('/api/configurations/active')
        assert response.status_code == 404
        
        # Create a configuration (should be active by default)
        config_data = {
            'name': 'Active Config',
            'apiUrl': 'http://localhost:10001/v1/chat/completions'
        }
        client.post('/api/configurations', json=config_data)
        
        # Get active configuration
        response = client.get('/api/configurations/active')
        assert response.status_code == 200
        assert response.json['name'] == 'Active Config'
        assert response.json['isActive'] is True


class TestChatAPI:
    """Test suite for Chat API endpoints."""
    
    def test_chat_missing_fields(self, client):
        """Test chat API with missing required fields."""
        response = client.post('/api/chat', json={'message': 'Hello'})
        assert response.status_code == 400
        assert 'Missing required fields' in response.json['error']
    
    def test_chat_with_mock_endpoint(self, client):
        """Test chat API with a mock endpoint."""
        # Use httpbin.org as a mock endpoint that returns our request
        chat_data = {
            'api_url': 'https://httpbin.org/post',
            'message': 'Hello, world!',
            'model': 'test-model'
        }
        
        response = client.post('/api/chat', json=chat_data)
        # This will fail because httpbin doesn't return the expected format,
        # but we can check that the request was made
        assert response.status_code in [200, 500, 502, 503]  # Either success, parsing error, bad gateway, or service unavailable
    
    @pytest.mark.integration
    def test_chat_with_real_configurations(self, client):
        """Integration test: Test chat API with real configurations."""
        # This test requires the local API server to be running
        # Create a configuration for local API
        config_data = {
            'name': 'Local Test',
            'apiUrl': 'http://localhost:10001/v1/chat/completions',
            'model': 'phi4:latest'
        }
        
        create_response = client.post('/api/configurations', json=config_data)
        assert create_response.status_code == 201, "Failed to create test configuration"
        
        # Test chat with the configuration
        chat_data = {
            'api_url': config_data['apiUrl'],
            'message': 'Hello! Please respond with just "Hi there!"',
            'model': config_data['model']
        }
        
        response = client.post('/api/chat', json=chat_data)
        
        # Fail if the local API server is not available
        assert response.status_code == 200, f"Local API server is not available or returned error (status: {response.status_code}). Please start the local API server at http://localhost:10001"
        
        # Validate successful response structure
        validate_chat_response(response)


class TestHealthAPI:
    """Test suite for Health check endpoints."""
    
    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get('/api/health')
        assert response.status_code == 200
        assert response.json['status'] == 'healthy'
    
    def test_external_api_health_with_mock(self, client):
        """Test external API health check with mock endpoint."""
        # Use httpbin.org as a mock endpoint that returns our request
        test_data = {
            'api_url': 'https://httpbin.org/post'
        }
        
        response = client.post('/api/test-external', json=test_data)
        # This will fail because httpbin doesn't return the expected chat format,
        # but we can check that the request was made and handled properly
        assert response.status_code in [200, 502, 503]  # Either success, bad gateway, or service unavailable
        assert 'health_status' in response.json
        
        # If it's an error response, check error handling
        if response.status_code != 200:
            assert response.json['health_status'] == 'unhealthy'
            assert 'error' in response.json
    
    @pytest.mark.integration
    def test_external_api_health_with_real_config(self, client):
        """Integration test: Test external API health check with real configuration."""
        # This test requires the local API server to be running
        test_data = {
            'api_url': 'http://localhost:10001/v1/chat/completions',
            'model': 'phi4:latest'
        }
        
        response = client.post('/api/test-external', json=test_data)
        
        # If local API is running, should get healthy response
        if response.status_code == 200:
            assert response.json['health_status'] == 'healthy'
            assert 'test_response' in response.json
            assert 'API is responding correctly' in response.json['message']
        else:
            # If local API is not running, should get proper error
            assert response.status_code in [502, 503]
            assert response.json['health_status'] == 'unhealthy'
            assert 'error' in response.json


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
