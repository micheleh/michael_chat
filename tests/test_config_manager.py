import os
import pytest
from unittest.mock import MagicMock, patch, mock_open
from config_manager import ConfigurationManager

CONFIG_FILE = 'test_configurations.json'

def setup_function(function):
    """Setup function to clear the test configuration file."""
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)


def test_load_legacy_format():
    """Test loading configurations from a legacy list format."""
    legacy_data = [
        {
            'name': 'Legacy Config',
            'api_url': 'http://localhost',
            'api_key': 'legacy-key',
            'model': 'legacy-model',
            'active': True,
            'image_support': True
        }
    ]
    
    # Use proper JSON format
    import json
    with patch('builtins.open', mock_open(read_data=json.dumps(legacy_data))):
        with patch('os.path.exists', return_value=True):
            manager = ConfigurationManager(config_file=CONFIG_FILE)
            configs = manager.get_all_configurations()
            assert len(configs) == 1
            assert configs[0]['name'] == 'Legacy Config'
            assert configs[0]['apiUrl'] == 'http://localhost'


def test_file_io_errors():
    """Test error handling when reading from and writing to files."""
    with patch('builtins.open', mock_open()) as mocked_open:
        # Simulate file read error
        mocked_open.side_effect = IOError("Unable to read file")
        manager = ConfigurationManager(config_file=CONFIG_FILE)
        assert manager.configurations == {}

        # Simulate file write error
        mocked_open.reset_mock()
        mocked_open.side_effect = IOError("Unable to write file")
        manager.configurations = {
            'test_id': {'name': 'Test Config', 'apiUrl': 'http://test-url'}
        }
        manager.save_configurations()  # Should handle IOError gracefully


def test_update_exceptions():
    """Test exception handling for updating configurations."""
    with patch('os.path.exists', return_value=False):  # No existing config file
        manager = ConfigurationManager(config_file=CONFIG_FILE)
        
        # Add two configs to test duplicate name scenario
        config1 = manager.create_configuration('First Config', 'http://first')
        config2 = manager.create_configuration('Second Config', 'http://second')

        # Test updating non-existent configuration
        with pytest.raises(ValueError, match='Configuration not found'):
            manager.update_configuration('nonexistent_id', 'Updated Name', 'http://new-url')

        # Test updating with duplicate name (try to rename config2 to config1's name)
        with pytest.raises(ValueError, match='Configuration with this name already exists'):
            manager.update_configuration(config2['id'], 'First Config', 'http://new-url')


def test_delete_exceptions():
    """Test exception handling for deleting configurations."""
    manager = ConfigurationManager(config_file=CONFIG_FILE)

    # Test deleting non-existent configuration
    with pytest.raises(ValueError, match='Configuration not found'):
        manager.delete_configuration('nonexistent_id')


def test_activate_exceptions():
    """Test exception handling for activating configurations."""
    manager = ConfigurationManager(config_file=CONFIG_FILE)

    # Test activating non-existent configuration
    with pytest.raises(ValueError, match='Configuration not found'):
        manager.activate_configuration('nonexistent_id')


def test_update_image_support_exceptions():
    """Test exception handling for updating image support."""
    manager = ConfigurationManager(config_file=CONFIG_FILE)

    # Test updating image support for non-existent configuration
    with pytest.raises(ValueError, match='Configuration not found'):
        manager.update_image_support('nonexistent_id', True)


def test_load_invalid_data_format():
    """Test loading configurations with invalid data format (neither list nor dict)."""
    import json
    # Test with string data (invalid format)
    with patch('builtins.open', mock_open(read_data=json.dumps("invalid string"))):
        with patch('os.path.exists', return_value=True):
            manager = ConfigurationManager(config_file=CONFIG_FILE)
            assert manager.configurations == {}


def test_load_dict_format():
    """Test loading configurations from dictionary format (modern format)."""
    import json
    from datetime import datetime
    now = datetime.now().isoformat()
    
    dict_data = {
        'config_id_123': {
            'id': 'config_id_123',
            'name': 'Dict Config',
            'apiUrl': 'http://dict-url',
            'apiKey': 'dict-key',
            'model': 'dict-model',
            'isActive': True,
            'supportsImages': None,
            'imageTestAt': None,
            'createdAt': now,
            'updatedAt': now
        }
    }
    
    with patch('builtins.open', mock_open(read_data=json.dumps(dict_data))):
        with patch('os.path.exists', return_value=True):
            manager = ConfigurationManager(config_file=CONFIG_FILE)
            configs = manager.get_all_configurations()
            assert len(configs) == 1
            assert configs[0]['name'] == 'Dict Config'
            assert configs[0]['apiUrl'] == 'http://dict-url'


def test_load_corrupted_json():
    """Test loading configurations with corrupted JSON."""
    with patch('builtins.open', mock_open(read_data="{invalid json")):
        with patch('os.path.exists', return_value=True):
            manager = ConfigurationManager(config_file=CONFIG_FILE)
            assert manager.configurations == {}


def test_get_configuration():
    """Test getting a specific configuration by ID."""
    with patch('os.path.exists', return_value=False):
        manager = ConfigurationManager(config_file=CONFIG_FILE)
        config = manager.create_configuration('Test Config', 'http://test')
        
        # Test getting existing configuration
        retrieved = manager.get_configuration(config['id'])
        assert retrieved['name'] == 'Test Config'
        
        # Test getting non-existent configuration
        assert manager.get_configuration('nonexistent_id') is None


def test_delete_active_configuration():
    """Test deleting the active configuration and auto-activating another."""
    with patch('os.path.exists', return_value=False):
        manager = ConfigurationManager(config_file=CONFIG_FILE)
        
        # Create two configurations
        config1 = manager.create_configuration('First Config', 'http://first')
        config2 = manager.create_configuration('Second Config', 'http://second')
        
        # First config should be active (created first)
        assert config1['isActive'] is True
        assert config2['isActive'] is False
        
        # Delete the active configuration
        manager.delete_configuration(config1['id'])
        
        # Check that the remaining config is now active
        remaining_configs = manager.get_all_configurations()
        assert len(remaining_configs) == 1
        assert remaining_configs[0]['isActive'] is True
        assert remaining_configs[0]['name'] == 'Second Config'


def test_get_active_configuration():
    """Test getting the active configuration."""
    with patch('os.path.exists', return_value=False):
        manager = ConfigurationManager(config_file=CONFIG_FILE)
        
        # No active configuration initially
        assert manager.get_active_configuration() is None
        
        # Create a configuration (should be active by default)
        config = manager.create_configuration('Active Config', 'http://active')
        active = manager.get_active_configuration()
        assert active is not None
        assert active['name'] == 'Active Config'


def test_create_configuration_duplicate_name():
    """Test creating configuration with duplicate name (case insensitive)."""
    with patch('os.path.exists', return_value=False):
        manager = ConfigurationManager(config_file=CONFIG_FILE)
        
        # Create first configuration
        manager.create_configuration('Test Config', 'http://first')
        
        # Try to create with same name (different case)
        with pytest.raises(ValueError, match='Configuration with this name already exists'):
            manager.create_configuration('TEST CONFIG', 'http://second')


def test_update_configuration_success():
    """Test successful configuration update."""
    with patch('os.path.exists', return_value=False):
        manager = ConfigurationManager(config_file=CONFIG_FILE)
        
        # Create and update configuration
        config = manager.create_configuration('Original Config', 'http://original')
        updated = manager.update_configuration(
            config['id'], 'Updated Config', 'http://updated', 'new-key', 'new-model'
        )
        
        assert updated['name'] == 'Updated Config'
        assert updated['apiUrl'] == 'http://updated'
        assert updated['apiKey'] == 'new-key'
        assert updated['model'] == 'new-model'


def test_activate_configuration_success():
    """Test successful configuration activation."""
    with patch('os.path.exists', return_value=False):
        manager = ConfigurationManager(config_file=CONFIG_FILE)
        
        # Create two configurations
        config1 = manager.create_configuration('Config 1', 'http://first')
        config2 = manager.create_configuration('Config 2', 'http://second')
        
        # Activate second configuration
        activated = manager.activate_configuration(config2['id'])
        
        assert activated['isActive'] is True
        assert activated['name'] == 'Config 2'
        
        # Verify first config is deactivated
        configs = manager.get_all_configurations()
        config1_updated = next(c for c in configs if c['id'] == config1['id'])
        assert config1_updated['isActive'] is False


def test_update_image_support_success():
    """Test successful image support update."""
    with patch('os.path.exists', return_value=False):
        manager = ConfigurationManager(config_file=CONFIG_FILE)
        
        # Create configuration and update image support
        config = manager.create_configuration('Image Config', 'http://image')
        updated = manager.update_image_support(config['id'], True)
        
        assert updated['supportsImages'] is True
        assert updated['imageTestAt'] is not None

