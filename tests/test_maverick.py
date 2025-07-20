"""
Test suite for Maverick model integration.

⚠️  WARNING: This file contains API keys and should NOT be committed to git.
It's specifically excluded in .gitignore to prevent accidental exposure.
"""

import pytest


def validate_streaming_response(response_text):
    """Helper function to validate streaming response content."""
    assert response_text is not None, "Streaming response should not be empty"
    assert len(response_text.strip()) > 0, "Streaming response should contain content"
    
    # Verify we got some actual content (not just whitespace)
    assert any(char.isalnum() for char in response_text), "Streaming response should contain alphanumeric characters"
    
    return True


def validate_chat_response(response, message_context=""):
    """Helper function to validate chat response structure."""
    context = f" for message: '{message_context}'" if message_context else ""
    assert 'choices' in response.json, f"Response missing 'choices' field{context}"
    assert len(response.json['choices']) > 0, f"Response has no choices{context}"
    assert 'message' in response.json['choices'][0], f"Response missing 'message' field{context}"
    assert 'content' in response.json['choices'][0]['message'], f"Response missing 'content' field{context}"
    assert response.json['choices'][0]['message']['content'].strip() != '', f"Response content is empty{context}"


class TestMaverickModel:
    """Test suite for Maverick model integration."""
    
    @pytest.mark.integration
    def test_maverick_model_chat(self, client):
        """Integration test: Test chat API with Maverick model."""
        # Maverick model configuration
        maverick_config = {
            'name': 'Llama-4-Maverick-17B-128E',
            'apiUrl': 'https://model-service.athena-preprod.otxlab.net/v1/chat/completions',
            'apiKey': '93548b53-64c6-41a7-a04e-82c4b43982b4',
            'model': 'meta-llama/Llama-4-Maverick-17B-128E'
        }
        
        # Create the configuration
        create_response = client.post('/api/configurations', json=maverick_config)
        assert create_response.status_code == 201, "Failed to create Maverick configuration"
        
        # Test chat with the configuration
        chat_data = {
            'api_url': maverick_config['apiUrl'],
            'api_key': maverick_config['apiKey'],
            'message': 'Hello! Please respond with just "Hi there!"',
            'model': maverick_config['model']
        }
        
        response = client.post('/api/chat', json=chat_data)
        
        # Verify the API response
        assert response.status_code == 200, f"Maverick API request failed with status {response.status_code}"
        
        # Check if response is streaming or JSON
        content_type = response.headers.get('content-type', '')
        
        if 'text/event-stream' in content_type:
            # Handle streaming response
            response_text = response.get_data(as_text=True)
            validate_streaming_response(response_text)
            print(f"✅ Maverick streaming response: {response_text[:100]}...")
        else:
            # Handle JSON response (fallback)
            validate_chat_response(response)
            print(f"✅ Maverick response: {response.json['choices'][0]['message']['content']}")
    
    @pytest.mark.integration
    def test_maverick_model_configuration_crud(self, client):
        """Test CRUD operations specifically for Maverick configuration."""
        # Maverick model configuration
        maverick_config = {
            'name': 'Llama-4-Maverick-17B-128E',
            'apiUrl': 'https://model-service.athena-preprod.otxlab.net/v1/chat/completions',
            'apiKey': '93548b53-64c6-41a7-a04e-82c4b43982b4',
            'model': 'meta-llama/Llama-4-Maverick-17B-128E'
        }
        
        # Create configuration
        create_response = client.post('/api/configurations', json=maverick_config)
        assert create_response.status_code == 201
        
        config_id = create_response.json['id']
        
        # Verify configuration was created correctly
        assert create_response.json['name'] == maverick_config['name']
        assert create_response.json['apiUrl'] == maverick_config['apiUrl']
        assert create_response.json['apiKey'] == maverick_config['apiKey']
        assert create_response.json['model'] == maverick_config['model']
        assert create_response.json['isActive'] is True
        
        # Get all configurations
        get_response = client.get('/api/configurations')
        assert get_response.status_code == 200
        assert len(get_response.json) == 1
        assert get_response.json[0]['name'] == maverick_config['name']
        
        # Update configuration
        updated_config = {
            'name': 'Updated Maverick',
            'apiUrl': maverick_config['apiUrl'],
            'apiKey': maverick_config['apiKey'],
            'model': maverick_config['model']
        }
        
        update_response = client.put(f'/api/configurations/{config_id}', json=updated_config)
        assert update_response.status_code == 200
        assert update_response.json['name'] == 'Updated Maverick'
        
        # Delete configuration
        delete_response = client.delete(f'/api/configurations/{config_id}')
        assert delete_response.status_code == 200
        assert 'deleted successfully' in delete_response.json['message']
        
        # Verify it's gone
        get_response = client.get('/api/configurations')
        assert len(get_response.json) == 0
    
    @pytest.mark.integration
    def test_maverick_model_different_messages(self, client):
        """Test Maverick model with different types of messages."""
        # Maverick model configuration
        maverick_config = {
            'name': 'Llama-4-Maverick-17B-128E',
            'apiUrl': 'https://model-service.athena-preprod.otxlab.net/v1/chat/completions',
            'apiKey': '93548b53-64c6-41a7-a04e-82c4b43982b4',
            'model': 'meta-llama/Llama-4-Maverick-17B-128E'
        }
        
        # Create the configuration
        create_response = client.post('/api/configurations', json=maverick_config)
        assert create_response.status_code == 201
        
        test_messages = [
            "What is 2+2?",
            "Write a short haiku about programming",
            "Explain quantum computing in one sentence",
            "What's the capital of France?"
        ]
        
        for message in test_messages:
            chat_data = {
                'api_url': maverick_config['apiUrl'],
                'api_key': maverick_config['apiKey'],
                'message': message,
                'model': maverick_config['model']
            }
            
            response = client.post('/api/chat', json=chat_data)
            
            # Verify the API response
            assert response.status_code == 200, f"Maverick API request failed for message: '{message}' with status {response.status_code}"
            
            # Check if response is streaming or JSON
            content_type = response.headers.get('content-type', '')
            
            if 'text/event-stream' in content_type:
                # Handle streaming response
                response_text = response.get_data(as_text=True)
                validate_streaming_response(response_text)
                print(f"✅ Message: '{message}' -> Streaming response: {response_text[:100]}...")
            else:
                # Handle JSON response (fallback)
                validate_chat_response(response, message)
                print(f"✅ Message: '{message}' -> Response: {response.json['choices'][0]['message']['content'][:100]}...")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
