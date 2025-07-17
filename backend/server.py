"""
Server utilities and route handlers for serving the React frontend
"""
import os
from flask import Flask, send_from_directory
from flask_cors import CORS


def create_app():
    """Create and configure the Flask application"""
    # Path to the React build directory
    BUILD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'build')
    
    # Configure Flask to serve static files from the build directory
    app = Flask(__name__, static_folder=BUILD_DIR, static_url_path='')
    CORS(app)
    
    # Register blueprints
    from api import api_blueprint
    app.register_blueprint(api_blueprint)
    
    # Frontend routes
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
    
    # Check if build directory exists
    if not os.path.exists(BUILD_DIR):
        print(f"Warning: Build directory not found at {BUILD_DIR}")
        print("Please run 'npm run build' in the frontend directory first.")
    
    return app
