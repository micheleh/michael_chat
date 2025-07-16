from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import requests
import os
import json

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
