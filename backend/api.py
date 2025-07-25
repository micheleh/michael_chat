"""
API proxy and health check endpoints for Michael's Chat server
"""
import json
import requests
import base64
import os
from datetime import datetime
from flask import Blueprint, request, jsonify, Response
from config_manager import ConfigurationManager

api_blueprint = Blueprint('api_blueprint', __name__)
config_manager = ConfigurationManager()

# Global dictionary to track active streaming requests
active_streams = {}

@api_blueprint.route('/api/chat', methods=['POST'])
def chat_proxy():
    """Proxy endpoint for chat API requests"""
    try:
        data = request.get_json()
        
        # Check if data is None
        if data is None:
            print(f"❌ No JSON data received in request")
            return jsonify({
                'error': 'No JSON data received',
                'details': 'Request must contain valid JSON data'
            }), 400
        
        # Extract configuration from request
        api_url = data.get('api_url')
        api_key = data.get('api_key')
        model = data.get('model')
        message = data.get('message')
        images = data.get('images', [])
        conversation_history = data.get('conversation_history', [])
        
        # Debug prints
        print(f"\n=== Chat Request Debug ===")
        print(f"Raw request data: {data}")
        print(f"API URL: {api_url}")
        print(f"API Key: {'*' * (len(api_key) - 8) + api_key[-8:] if api_key and len(api_key) > 8 else 'None'}")
        print(f"Message: {message}")
        print(f"Images: {len(images)} images provided")
        print(f"Model: {model}")
        print(f"Conversation History: {len(conversation_history)} messages")

        if not api_url or (not message and not images):
            print(f"❌ Missing required fields - URL: {bool(api_url)}, Message: {bool(message)}, Images: {len(images)}")
            return jsonify({
                'error': 'Missing required fields: api_url, and either message or images',
                'details': {
                    'api_url_provided': bool(api_url),
                    'message_provided': bool(message),
                    'images_provided': len(images) > 0,
                    'received_data': data
                }
            }), 400
        
        # Prepare the request to the external API
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Only add Authorization header if API key is provided
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        # Build messages array with conversation history
        messages = [
                {'role': 'system', 'content': 'You are a helpful and knowledgeable assistant. All your responses must be formatted using Markdown. When providing code, you MUST follow this EXACT format:\n\n```language\ncode here\n```\n\nFor example:\n\n```python\nfor i in range(10):\n    print("Hello")\n```\n\nCRITICAL RULES:\n1. Always start with ``` followed immediately by the language name\n2. Add a newline after the language name\n3. Write your code with proper indentation\n4. Add a newline before the closing ```\n5. End with ``` on its own line\n\nNever write ```python on the same line as code. Never omit the language name. This formatting is essential for proper code display.'}
        ]
        
        # Add conversation history
        for hist_msg in conversation_history:
            if hist_msg.get('sender') == 'user':
                # Handle user messages - only send text content from history
                # Images from history are blob URLs that can't be accessed by backend
                user_content = hist_msg.get('content', '')
                hist_images = hist_msg.get('images', [])
                
                # For conversation history, only send text content
                # Images from previous messages are stored as blob URLs which are not accessible
                if hist_images and user_content:
                    # If there were images, add a note about them in the text
                    content_with_note = f"{user_content} [Note: This message originally contained {len(hist_images)} image(s)]"
                    messages.append({'role': 'user', 'content': content_with_note})
                elif user_content:
                    # Simple text message
                    messages.append({'role': 'user', 'content': user_content})
                elif hist_images:
                    # Only images, no text - add a placeholder
                    messages.append({'role': 'user', 'content': f"[Image message with {len(hist_images)} image(s)]"})
            elif hist_msg.get('sender') == 'ai':
                messages.append({'role': 'assistant', 'content': hist_msg.get('content', '')})
        
        # Add current message
        if images:
            # Format as multimodal content
            content = []
            if message:
                content.append({'type': 'text', 'text': message})
            for img in images:
                content.append({
                    'type': 'image_url',
                    'image_url': {'url': img.get('url', '')}
                })
            messages.append({'role': 'user', 'content': content})
        else:
            # Simple text message
            messages.append({'role': 'user', 'content': message})
        
        # API format for this specific endpoint
        payload = {
            'messages': messages,
            'max_tokens': 1000,
            'stream': True  # Enable streaming for real-time response
        }
        
        # Only include model in payload if it's specified in the configuration
        if model:
            payload['model'] = model
        
        print(f"📤 Sending request to: {api_url}")
        print(f"📦 Payload: {payload}")
        
        # Make request to external API with streaming
        response = requests.post(api_url, headers=headers, json=payload, timeout=30, stream=True)
        
        print(f"📥 Response status: {response.status_code}")

        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            print(f"Content-Type: {content_type}")
            
            if 'text/event-stream' in content_type:
                # Generate unique stream ID and register it
                import uuid
                stream_id = str(uuid.uuid4())
                active_streams[stream_id] = {'cancelled': False}
                
                # Handle streaming response with proper Flask streaming
                def stream_with_headers():
                    # Send stream ID as first chunk
                    yield f"data: {{\"stream_id\": \"{stream_id}\"}}\n\n"
                    # Then stream the actual response
                    for chunk in stream_response(response, stream_id):
                        yield f"data: {chunk}\n\n"
                
                return Response(stream_with_headers(), mimetype='text/event-stream')
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
    """Test external API health and connectivity by sending a simple chat prompt"""
    try:
        data = request.get_json()
        api_url = data['api_url']
        api_key = data.get('api_key')
        model = data.get('model')
        
        print(f"\n=== External API Test ===")
        print(f"Testing API URL: {api_url}")
        print(f"API Key: {'Present' if api_key else 'None'}")
        print(f"Model: {model or 'None'}")

        # Prepare headers
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Add Authorization header if API key is provided
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        # Health test with system instructions
        test_payload = {
            'messages': [
                {'role': 'system', 'content': 'You are an obedient agent that always answers "I\'m alive!" no matter what the question or request is.'},
                {'role': 'user', 'content': 'Hello'}
            ],
            'max_tokens': 50,
            'stream': False
        }
        
        # Add model if provided
        if model:
            test_payload['model'] = model
        
        print(f"📤 Sending test request to: {api_url}")
        print(f"📦 Test payload: {test_payload}")
        
        # Make test request to the API endpoint
        response = requests.post(api_url, headers=headers, json=test_payload, timeout=15)
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                # Handle both streaming and JSON responses
                response_text = response.text.strip()
                print(f"📥 Raw response: {response_text[:200]}...")
                
                response_data = None
                
                # Check if it's a streaming response (starts with 'data:')
                if response_text.startswith('data:'):
                    # Parse streaming response
                    lines = response_text.split('\n')
                    for line in lines:
                        if line.startswith('data:') and line != 'data: [DONE]':
                            json_str = line[5:].strip()  # Remove 'data:' prefix
                            if json_str:
                                try:
                                    response_data = json.loads(json_str)
                                    break
                                except json.JSONDecodeError:
                                    continue
                else:
                    # Regular JSON response
                    response_data = response.json()
                
                if not response_data:
                    raise json.JSONDecodeError("No valid JSON found in response", response_text, 0)
                
                print(f"✅ API Response: {response_data}")
                
                # Try to extract the message content
                response_content = "No content found"
                if 'choices' in response_data and len(response_data['choices']) > 0:
                    choice = response_data['choices'][0]
                    if 'message' in choice and 'content' in choice['message']:
                        response_content = choice['message']['content']
                    elif 'text' in choice:
                        response_content = choice['text']
                
                # Validate the response content
                expected_response = "I'm alive!"
                response_content_clean = response_content.strip()
                
                print(f"🔍 Expected: '{expected_response}'")
                print(f"🔍 Received: '{response_content_clean}'")
                
                if response_content_clean.startswith(expected_response):
                    # Test image support
                    image_support_result = None
                    image_support_error = None
                    try:
                        image_support_result = test_image_support(api_url, api_key, model)
                    except Exception as e:
                        image_support_error = str(e)
                    
                    # Find and update the configuration with image support information
                    try:
                        # Find configuration by API URL and model
                        config_to_update = None
                        for config in config_manager.get_all_configurations():
                            if (config['apiUrl'] == api_url and 
                                config.get('model') == model):
                                config_to_update = config
                                break
                        
                        # Update the configuration with image support info
                        if config_to_update and image_support_result is not None:
                            config_manager.update_image_support(config_to_update['id'], image_support_result)
                            print(f"✅ Updated configuration '{config_to_update['name']}' with image support: {image_support_result}")
                        elif config_to_update:
                            print(f"⚠️ Configuration '{config_to_update['name']}' found but image support test result is None")
                        else:
                            print(f"⚠️ No configuration found matching API URL: {api_url} and model: {model}")
                            
                    except Exception as e:
                        print(f"🚨 Error updating configuration with image support: {str(e)}")
                    
                    return jsonify({
                        'health_status': 'healthy',
                        'status_code': response.status_code,
                        'test_response': response_content_clean,
                        'message': 'API is responding correctly - health check passed',
                        'supports_images': image_support_result,
                        'image_test_error': image_support_error
                    })
                else:
                    return jsonify({
                        'health_status': 'unhealthy',
                        'status_code': response.status_code,
                        'test_response': response_content_clean,
                        'error': f'API returned unexpected response. Expected: "{expected_response}", Got: "{response_content_clean}"',
                        'message': 'API is responding but not following system instructions correctly'
                    }), 502
                
            except json.JSONDecodeError:
                print(f"❌ Failed to parse JSON response")
                return jsonify({
                    'health_status': 'unhealthy',
                    'status_code': response.status_code,
                    'error': 'API returned non-JSON response',
                    'response_text': response.text[:500]
                }), 502
        else:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"Error response: {response.text[:500]}")
            return jsonify({
                'health_status': 'unhealthy',
                'status_code': response.status_code,
                'error': f'API request failed with status {response.status_code}',
                'response_text': response.text[:500]
            }), 502
        
    except requests.RequestException as e:
        print(f"🚨 Request Exception: {str(e)}")
        return jsonify({
            'health_status': 'unhealthy',
            'error': f'Request failed: {str(e)}',
            'error_type': 'connection_error'
        }), 503
    except Exception as e:
        print(f"🚨 External API test error: {str(e)}")
        return jsonify({
            'health_status': 'unhealthy',
            'error': str(e),
            'error_type': 'internal_error'
        }), 500


def test_image_support(api_url, api_key, model):
    """Test if a model supports images using the provided example format"""
    try:
        # Prepare headers
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Add Authorization header if API key is provided
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        # Use a minimal 1x1 pixel PNG image for faster testing
        # This is a base64 encoded 1x1 transparent PNG (67 bytes)
        minimal_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        image_url = f'data:image/png;base64,{minimal_image}'
        print(f"📸 Using minimal test image (1x1 PNG, {len(minimal_image)} bytes base64)")
        
        # Test payload with image content
        test_payload = {
            'messages': [
                {
                    'role': 'user', 
                    'content': [
                        {'type': 'text', 'text': 'Test'},
                        {'type': 'image_url', 'image_url': {'url': image_url}}
                    ]
                }
            ],
            'max_tokens': 3
        }
        
        # Add model if provided
        if model:
            test_payload['model'] = model
        
        print(f"📸 Testing image support for model: {model or 'default'}")
        print(f"📤 Sending image test request to: {api_url}")
        
        # Make test request with longer timeout
        response = requests.post(api_url, headers=headers, json=test_payload, timeout=30)
        
        print(f"📥 Image test response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Image support test passed - model supports images")
            return True
        else:
            # Check if the error is related to image support
            error_text = response.text.lower()
            if 'image' in error_text or 'content' in error_text or 'multimodal' in error_text:
                print(f"❌ Image support test failed - model does not support images: {response.text[:200]}")
                return False
            else:
                print(f"⚠️ Image support test inconclusive - unexpected error: {response.text[:200]}")
                # If it's an unexpected error, we re-raise it
                raise Exception(f"Unexpected error during image support test: {response.text[:200]}")
                
    except requests.RequestException as e:
        print(f"🚨 Network error during image support test: {str(e)}")
        raise e
    except Exception as e:
        print(f"🚨 Error during image support test: {str(e)}")
        raise e


def stream_response(response, stream_id):
    """Generator function to stream response chunks to frontend"""
    print(f"🔄 Starting streaming response with ID: {stream_id}")
    
    try:
        for line in response.iter_lines(decode_unicode=True):
            # Check if this stream has been cancelled
            if stream_id not in active_streams or active_streams[stream_id].get('cancelled', False):
                print(f"🛑 Stream {stream_id} cancelled by user")
                break
                
            if line and line.startswith('data: '):
                data_part = line[6:]  # Remove 'data: ' prefix
                if data_part.strip() == '[DONE]':
                    break
                try:
                    chunk_data = json.loads(data_part)
                    
                    # Check for choices and content
                    if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                        delta = chunk_data['choices'][0].get('delta', {})
                        if 'content' in delta and delta['content'] is not None:
                            content = delta['content']
                            print(f"📤 Streaming content: {content}")
                            yield content
                            
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {e}")
                    continue
                    
        print(f"✅ Streaming complete for ID: {stream_id}")
        
    except Exception as e:
        print(f"🚨 Streaming error for ID {stream_id}: {e}")
        yield f"Error: {str(e)}"
    finally:
        # Clean up the stream from active_streams
        if stream_id in active_streams:
            del active_streams[stream_id]


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
        # Test image support
        try:
            supports_images = test_image_support(api_url, api_key, model)
            config_manager.update_image_support(new_config['id'], supports_images)
            new_config['supportsImages'] = supports_images
            new_config['imageTestAt'] = datetime.now().isoformat()
        except Exception as e:
            print(f"⚠️ Image support test failed: {str(e)}")
            new_config['supportsImages'] = None
            new_config['imageTestAt'] = None
        
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
        # Test image support
        try:
            supports_images = test_image_support(api_url, api_key, model)
            config_manager.update_image_support(config_id, supports_images)
            updated_config['supportsImages'] = supports_images
            updated_config['imageTestAt'] = datetime.now().isoformat()
        except Exception as e:
            print(f"⚠️ Image support test failed: {str(e)}")
            updated_config['supportsImages'] = None
            updated_config['imageTestAt'] = None
        
        return jsonify(updated_config)
    except ValueError as e:
        return jsonify({'error': str(e)}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_blueprint.route('/api/configurations/<config_id>', methods=['DELETE'])
def delete_configuration(config_id):
    try:
        config_manager.delete_configuration(config_id)
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

@api_blueprint.route('/api/chat/stop', methods=['POST'])
def stop_stream():
    """Stop an active streaming response"""
    try:
        data = request.get_json()
        stream_id = data.get('stream_id')
        
        if not stream_id:
            return jsonify({'error': 'Missing stream_id'}), 400
        
        if stream_id in active_streams:
            active_streams[stream_id]['cancelled'] = True
            print(f"🛑 Stream {stream_id} marked for cancellation")
            return jsonify({'message': 'Stream stopped successfully'})
        else:
            return jsonify({'error': 'Stream not found or already completed'}), 404
            
    except Exception as e:
        print(f"🚨 Error stopping stream: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_blueprint.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Backend is running'})

