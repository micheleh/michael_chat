"""
API proxy and health check endpoints for Michael's Chat server
"""
import json
import requests
from flask import Blueprint, request, jsonify
from config_manager import ConfigurationManager

api_blueprint = Blueprint('api_blueprint', __name__)
config_manager = ConfigurationManager()

@api_blueprint.route('/api/chat', methods=['POST'])
def chat_proxy():
    """Proxy endpoint for chat API requests"""
    try:
        data = request.get_json()
        
        # Extract configuration from request
        api_url = data.get('api_url')
        api_key = data.get('api_key')
        model = data.get('model')
        message = data.get('message')
        conversation_history = data.get('conversation_history', [])
        
        # Debug prints
        print(f"\n=== Chat Request Debug ===")
        print(f"API URL: {api_url}")
        print(f"API Key: {'*' * (len(api_key) - 8) + api_key[-8:] if api_key and len(api_key) > 8 else 'None'}")
        print(f"Message: {message}")

        if not api_url or not message:
            print(f"❌ Missing required fields - URL: {bool(api_url)}, Message: {bool(message)}")
            return jsonify({'error': 'Missing required fields: api_url, message'}), 400
        
        # Prepare the request to the external API
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Only add Authorization header if API key is provided
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        # Build messages array with conversation history
        messages = [
            {'role': 'system', 'content': 'You are a helpful assistant. Provide clear, accurate, and well-structured responses.'}
        ]
        
        # Add conversation history
        for hist_msg in conversation_history:
            if hist_msg.get('sender') == 'user':
                messages.append({'role': 'user', 'content': hist_msg.get('content', '')})
            elif hist_msg.get('sender') == 'ai':
                messages.append({'role': 'assistant', 'content': hist_msg.get('content', '')})
        
        # Add current message
        messages.append({'role': 'user', 'content': message})
        
        # API format for this specific endpoint
        payload = {
            'messages': messages,
            'max_tokens': 1000,
            'stream': False  # Disable streaming for more reliable responses
        }
        
        # Only include model in payload if it's specified in the configuration
        if model:
            payload['model'] = model
        
        print(f"📤 Sending request to: {api_url}")
        print(f"📦 Payload: {payload}")
        
        # Make request to external API
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        
        print(f"📥 Response status: {response.status_code}")

        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            print(f"Content-Type: {content_type}")
            
            if 'text/event-stream' in content_type:
                # Handle streaming response
                return handle_streaming_response(response)
            else:
                # Handle regular JSON response
                return handle_json_response(response)
        else:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"Error response: {response.text[:500]}...")
            return jsonify({
                'error': f'API request failed with status {response.status_code}',
                'details': response.text
            }), response.status_code
            
    except requests.RequestException as e:
        print(f"🚨 Request Exception: {str(e)}")
        return jsonify({'error': f'Request failed: {str(e)}'}), 500
    except Exception as e:
        print(f"🚨 Internal Server Error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@api_blueprint.route('/api/test-external', methods=['POST'])
def test_external_api():
    """Test external API health and connectivity"""
    try:
        data = request.get_json()
        api_url = data['api_url']
        
        print(f"\n=== External API Test ===")
        print(f"Testing API URL: {api_url}")

        # Extract base URL from API URL
        from urllib.parse import urlparse
        parsed_url = urlparse(api_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        print(f"Checking health at: {base_url}")
        
        health_response = requests.head(base_url, timeout=10)

        # Interpret health check results
        health_status = 'server_running_but_no_root_endpoint' if health_response.status_code == 404 else 'healthy'
        print(f"Health status interpretation: {health_status}")

        return jsonify({
            'health_status': health_response.status_code,
            'health_interpretation': health_status
        })
        
    except Exception as e:
        print(f"🚨 External API test error: {str(e)}")
        return jsonify({'error': str(e)}), 500


def handle_streaming_response(response):
    """Handle streaming response"""
    print(f"🔄 Handling streaming response...")
    
    full_content = ""
    error_content = ""
    line_count = 0
    
    for line in response.iter_lines(decode_unicode=True):
        line_count += 1
        print(f"📄 Line {line_count}: {line[:200]}..." if line and len(line) > 200 else f"📄 Line {line_count}: {line or 'None'}")
        
        if line and line.startswith('data: '):
            data_part = line[6:]  # Remove 'data: ' prefix
            if data_part.strip() == '[DONE]':
                break
            try:
                chunk_data = json.loads(data_part)
                print(f"📊 Parsed chunk: {chunk_data}")
                
                # Check for errors in the chunk
                if 'error' in chunk_data and chunk_data['error'] is not None:
                    error_content += str(chunk_data['error'])
                    print(f"❌ Error in chunk: {chunk_data['error']}")
                
                # Check for choices and content
                if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                    delta = chunk_data['choices'][0].get('delta', {})
                    if 'content' in delta and delta['content'] is not None:
                        full_content += delta['content']
                        print(f"✅ Added content: {delta['content']}")
                        
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"❌ Raw data: {data_part}")
                # If it's not JSON, treat as plain text error
                if data_part is not None:
                    error_content += data_part
                continue
    
    print(f"✅ Streaming complete! Full response length: {len(full_content)}")
    print(f"✅ Full response: {full_content}")
    
    # If we have error content and no regular content, return error
    if error_content and not full_content:
        print(f"❌ Returning error response: {error_content}")
        return jsonify({
            'error': 'API returned error in streaming response',
            'details': error_content
        }), 500
    
    # Return in OpenAI format for frontend compatibility
    return jsonify({
        'choices': [{
            'message': {
                'content': full_content if full_content else "No content received from API",
                'role': 'assistant'
            }
        }]
    })


def handle_json_response(response):
    """Handle JSON response"""
    try:
        response_data = response.json()
        return jsonify(response_data)
    except json.JSONDecodeError:
        return jsonify({
            'error': 'Failed to parse API response',
            'details': response.text[:500]
        }), 500


# Simplified configurations routes using ConfigurationManager
@api_blueprint.route('/api/configurations', methods=['GET'])
def get_configurations():
    configs = config_manager.get_all_configurations()
    return jsonify(configs)

@api_blueprint.route('/api/configurations', methods=['POST'])
def create_configuration():
    data = request.get_json()
    
    # Validate required fields
    if not data.get('name'):
        return jsonify({'error': 'Missing required field: name'}), 400
    if not data.get('apiUrl'):
        return jsonify({'error': 'Missing required field: apiUrl'}), 400
    
    name = data['name']
    api_url = data['apiUrl']
    api_key = data.get('apiKey', '')
    model = data.get('model', '')
    
    try:
        new_config = config_manager.create_configuration(name, api_url, api_key, model)
        return jsonify(new_config), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_blueprint.route('/api/configurations/<config_id>', methods=['PUT'])
def update_configuration(config_id):
    data = request.get_json()
    name = data['name']
    api_url = data['apiUrl']
    api_key = data.get('apiKey', '')
    model = data.get('model', '')
    try:
        updated_config = config_manager.update_configuration(config_id, name, api_url, api_key, model)
        return jsonify(updated_config)
    except ValueError as e:
        return jsonify({'error': str(e)}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_blueprint.route('/api/configurations/<config_id>', methods=['DELETE'])
def delete_configuration(config_id):
    try:
        deleted_config = config_manager.delete_configuration(config_id)
        return jsonify({'message': 'Configuration deleted successfully'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_blueprint.route('/api/configurations/<config_id>/activate', methods=['POST'])
def activate_configuration(config_id):
    try:
        activated_config = config_manager.activate_configuration(config_id)
        return jsonify(activated_config)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_blueprint.route('/api/configurations/active', methods=['GET'])
def get_active_configuration():
    active_config = config_manager.get_active_configuration()
    if active_config:
        return jsonify(active_config)
    return jsonify({'error': 'No active configuration found'}), 404

@api_blueprint.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Backend is running'})

