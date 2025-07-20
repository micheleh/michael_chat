"""
Shared test fixtures for the backend test suite.

This file contains common fixtures used across multiple test files to avoid
code duplication and ensure consistent test setup.
"""

import pytest
import os
import tempfile
import sys
from pathlib import Path
from unittest.mock import patch

# Add backend directory to path to import modules
backend_path = str(Path(__file__).parent.parent / 'backend')
sys.path.insert(0, backend_path)

# Import modules from backend
try:
    from server import create_app
    from config_manager import ConfigurationManager
    import api
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Backend path: {backend_path}")
    print(f"Current sys.path: {sys.path}")
    raise


@pytest.fixture
def temp_config_file():
    """Create a temporary configurations file for testing."""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
    temp_file.write('{}')  # Start with empty JSON
    temp_file.close()
    
    yield temp_file.name
    
    # Clean up
    if os.path.exists(temp_file.name):
        os.remove(temp_file.name)


@pytest.fixture
def app_with_temp_config(temp_config_file):
    """Create Flask app with temporary config file."""
    # Patch the config manager to use temporary file
    with patch('api.config_manager') as mock_config_manager:
        mock_config_manager.config_file = temp_config_file
        mock_config_manager.configurations = {}
        mock_config_manager.load_configurations()
        
        app = create_app()
        app.config['TESTING'] = True
        
        # Override the config manager in the API module
        original_config_manager = api.config_manager
        api.config_manager = ConfigurationManager(config_file=temp_config_file)
        
        yield app
        
        # Restore original config manager
        api.config_manager = original_config_manager


@pytest.fixture
def client(app_with_temp_config):
    """A test client for the app."""
    return app_with_temp_config.test_client()


def validate_chat_response(response, message_context=""):
    """Helper function to validate chat response structure."""
    context = f" for message: '{message_context}'" if message_context else ""
    assert 'choices' in response.json, f"Response missing 'choices' field{context}"
    assert len(response.json['choices']) > 0, f"Response has no choices{context}"
    assert 'message' in response.json['choices'][0], f"Response missing 'message' field{context}"
    assert 'content' in response.json['choices'][0]['message'], f"Response missing 'content' field{context}"
    assert response.json['choices'][0]['message']['content'].strip() != '', f"Response content is empty{context}"
