from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import requests
import os
import json
import uuid
from datetime import datetime

# Path to the React build directory
BUILD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'build')

# Configure Flask to serve static files from the build directory
app = Flask(__name__, static_folder=BUILD_DIR, static_url_path='')
CORS(app)

@app.route('/')
def serve_index():
    """Serve the React app's index.html"""
    return send_from_directory(BUILD_DIR, 'index.html')

@app.route('/static/<path:path>')
def serve_static_files(path):
    """Serve static files from the React build directory"""
    static_dir = os.path.join(BUILD_DIR, 'static')
    return send_from_directory(static_dir, path)

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files from the React build directory"""
    try:
        return send_from_directory(BUILD_DIR, path)
    except:
        # If file not found, serve index.html for React Router
        return send_from_directory(BUILD_DIR, 'index.html')

@app.route('/api/chat', methods=['POST'])
def chat_proxy():
    """Proxy endpoint for chat API requests"""
    try:
        data = request.get_json()
        
        # Extract configuration from request
        api_url = data.get('api_url')
        api_key = data.get('api_key')
        message = data.get('message')
        conversation_history = data.get('conversation_history', [])
        
        # Debug prints
        print(f"\n=== Chat Request Debug ===")
        print(f"API URL: {api_url}")
        print(f"API Key: {'*' * (len(api_key) - 8) + api_key[-8:] if api_key and len(api_key) > 8 else 'None'}")
        print(f"Message: {message}")
        print(f"Conversation history length: {len(conversation_history)}")
        print(f"Request data keys: {list(data.keys()) if data else 'None'}")
        
        if not api_url or not api_key or not message:
            print(f"❌ Missing required fields - URL: {bool(api_url)}, Key: {bool(api_key)}, Message: {bool(message)}")
            return jsonify({'error': 'Missing required fields: api_url, api_key, message'}), 400
        
        # Prepare the request to the external API
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
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
            'model': 'meta-llama/Llama-4-Maverick-17B-128E',
            'messages': messages,
            'max_tokens': 1000
        }
        
        print(f"📤 Sending request to: {api_url}")
        print(f"📦 Payload: {payload}")
        print(f"🔐 Headers: {{'Authorization': 'Bearer ***', 'Content-Type': 'application/json'}}")
        
        # Make request to external API
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        
        print(f"📥 Response status: {response.status_code}")
        print(f"📄 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            print(f"Content-Type: {content_type}")
            
            if 'text/event-stream' in content_type:
                # Handle streaming response
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
            else:
                # Handle regular JSON response
                try:
                    response_data = response.json()
                    print(f"✅ Success! Response preview: {str(response_data)[:200]}...")
                    return jsonify(response_data)
                except json.JSONDecodeError:
                    print(f"❌ Failed to parse JSON response")
                    return jsonify({
                        'error': 'Failed to parse API response',
                        'details': response.text[:500]
                    }), 500
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
        print(f"Exception type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

# Configuration storage (in-memory for now - in production, use a database)
configurations = {}

@app.route('/api/configurations', methods=['GET'])
def get_configurations():
    """Get all configurations"""
    print(f"\n=== Get Configurations Request ===")
    config_list = list(configurations.values())
    # Sort by creation date, most recent first
    config_list.sort(key=lambda x: x['createdAt'], reverse=True)
    print(f"Found {len(config_list)} configurations")
    return jsonify(config_list)

@app.route('/api/configurations', methods=['POST'])
def create_configuration():
    """Create a new configuration"""
    try:
        data = request.get_json()
        
        print(f"\n=== Create Configuration Request ===")
        print(f"Data received: {data}")
        
        # Validate required fields
        required_fields = ['name', 'apiUrl', 'apiKey']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if name already exists
        for config in configurations.values():
            if config['name'].lower() == data['name'].lower():
                return jsonify({'error': 'Configuration with this name already exists'}), 409
        
        # Create new configuration
        config_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # If this is the first configuration, make it active
        is_first_config = len(configurations) == 0
        
        new_config = {
            'id': config_id,
            'name': data['name'],
            'apiUrl': data['apiUrl'],
            'apiKey': data['apiKey'],
            'isActive': is_first_config,
            'createdAt': now,
            'updatedAt': now
        }
        
        configurations[config_id] = new_config
        print(f"Created configuration: {new_config['name']} (ID: {config_id})")
        
        return jsonify(new_config), 201
        
    except Exception as e:
        print(f"🚨 Error creating configuration: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/configurations/<config_id>', methods=['PUT'])
def update_configuration(config_id):
    """Update an existing configuration"""
    try:
        data = request.get_json()
        
        print(f"\n=== Update Configuration Request ===")
        print(f"Config ID: {config_id}")
        print(f"Data received: {data}")
        
        if config_id not in configurations:
            return jsonify({'error': 'Configuration not found'}), 404
        
        # Validate required fields
        required_fields = ['name', 'apiUrl', 'apiKey']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if name already exists (excluding current config)
        for cid, config in configurations.items():
            if cid != config_id and config['name'].lower() == data['name'].lower():
                return jsonify({'error': 'Configuration with this name already exists'}), 409
        
        # Update configuration
        config = configurations[config_id]
        config['name'] = data['name']
        config['apiUrl'] = data['apiUrl']
        config['apiKey'] = data['apiKey']
        config['updatedAt'] = datetime.now().isoformat()
        
        print(f"Updated configuration: {config['name']} (ID: {config_id})")
        
        return jsonify(config)
        
    except Exception as e:
        print(f"🚨 Error updating configuration: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/configurations/<config_id>', methods=['DELETE'])
def delete_configuration(config_id):
    """Delete a configuration"""
    try:
        print(f"\n=== Delete Configuration Request ===")
        print(f"Config ID: {config_id}")
        
        if config_id not in configurations:
            return jsonify({'error': 'Configuration not found'}), 404
        
        config = configurations[config_id]
        was_active = config['isActive']
        
        # Delete the configuration
        del configurations[config_id]
        print(f"Deleted configuration: {config['name']} (ID: {config_id})")
        
        # If the deleted config was active, make another one active
        if was_active and configurations:
            # Make the first remaining configuration active
            next_config = next(iter(configurations.values()))
            next_config['isActive'] = True
            next_config['updatedAt'] = datetime.now().isoformat()
            print(f"Made {next_config['name']} the new active configuration")
        
        return jsonify({'message': 'Configuration deleted successfully'})
        
    except Exception as e:
        print(f"🚨 Error deleting configuration: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/configurations/<config_id>/activate', methods=['POST'])
def activate_configuration(config_id):
    """Set a configuration as active"""
    try:
        print(f"\n=== Activate Configuration Request ===")
        print(f"Config ID: {config_id}")
        
        if config_id not in configurations:
            return jsonify({'error': 'Configuration not found'}), 404
        
        # Deactivate all configurations
        for config in configurations.values():
            config['isActive'] = False
        
        # Activate the selected configuration
        config = configurations[config_id]
        config['isActive'] = True
        config['updatedAt'] = datetime.now().isoformat()
        
        print(f"Activated configuration: {config['name']} (ID: {config_id})")
        
        return jsonify(config)
        
    except Exception as e:
        print(f"🚨 Error activating configuration: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/configurations/active', methods=['GET'])
def get_active_configuration():
    """Get the currently active configuration"""
    print(f"\n=== Get Active Configuration Request ===")
    
    for config in configurations.values():
        if config['isActive']:
            print(f"Active configuration: {config['name']} (ID: {config['id']})")
            return jsonify(config)
    
    print("No active configuration found")
    return jsonify({'error': 'No active configuration found'}), 404

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    print(f"\n=== Health Check Request ===")
    print(f"✅ Backend is healthy and running")
    return jsonify({'status': 'healthy', 'message': 'Backend is running'})

@app.route('/api/test-external', methods=['POST'])
def test_external_api():
    """Test external API health and connectivity"""
    try:
        data = request.get_json()
        api_url = data.get('api_url')
        api_key = data.get('api_key')
        
        print(f"\n=== External API Test ===")
        print(f"Testing API URL: {api_url}")
        
        if not api_url:
            return jsonify({'error': 'API URL required'}), 400
            
        # Test health endpoint first
        health_url = api_url.replace('/chat/completions', '/chat/health')
        print(f"Checking health at: {health_url}")
        
        health_response = requests.get(health_url, timeout=10)
        print(f"Health check status: {health_response.status_code}")
        print(f"Health response: {health_response.text}")
        
        # Test a simple chat request
        if api_key:
            print(f"Testing chat endpoint with API key...")
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            test_payload = {
                'model': 'meta-llama/Llama-4-Maverick-17B-128E',
                'messages': [{'role': 'user', 'content': 'Hello'}],
                'max_tokens': 10
            }
            
            chat_response = requests.post(api_url, headers=headers, json=test_payload, timeout=10)
            print(f"Chat test status: {chat_response.status_code}")
            print(f"Chat response: {chat_response.text[:200]}...")
            
            return jsonify({
                'health_status': health_response.status_code,
                'health_response': health_response.text,
                'chat_test_status': chat_response.status_code,
                'chat_test_response': chat_response.text[:200]
            })
        else:
            return jsonify({
                'health_status': health_response.status_code,
                'health_response': health_response.text,
                'note': 'API key not provided, skipping chat test'
            })
            
    except Exception as e:
        print(f"🚨 External API test error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Check if build directory exists
    if not os.path.exists(BUILD_DIR):
        print(f"Warning: Build directory not found at {BUILD_DIR}")
        print("Please run 'npm run build' in the frontend directory first.")
    
    print("Starting Michael's Chat server on http://localhost:8000")
    app.run(host='0.0.0.0', port=8000, debug=True)
