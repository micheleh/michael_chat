"""
Configuration management module with file persistence
"""
import json
import os
import uuid
from datetime import datetime


class ConfigurationManager:
    def __init__(self, config_file='configurations.json'):
        self.config_file = config_file
        self.configurations = {}
        self.load_configurations()
    
    def load_configurations(self):
        """Load configurations from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.configurations = json.load(f)
                print(f"✅ Loaded {len(self.configurations)} configurations from {self.config_file}")
            else:
                print(f"📄 No configuration file found at {self.config_file}, starting with empty configurations")
        except Exception as e:
            print(f"⚠️ Error loading configurations: {e}")
            self.configurations = {}
    
    def save_configurations(self):
        """Save configurations to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.configurations, f, indent=2)
            print(f"💾 Saved {len(self.configurations)} configurations to {self.config_file}")
        except Exception as e:
            print(f"❌ Error saving configurations: {e}")
    
    def get_all_configurations(self):
        """Get all configurations sorted by creation date"""
        config_list = list(self.configurations.values())
        config_list.sort(key=lambda x: x['createdAt'], reverse=True)
        return config_list
    
    def get_configuration(self, config_id):
        """Get a specific configuration by ID"""
        return self.configurations.get(config_id)
    
    def create_configuration(self, name, api_url, api_key='', model=''):
        """Create a new configuration"""
        # Check if name already exists
        for config in self.configurations.values():
            if config['name'].lower() == name.lower():
                raise ValueError('Configuration with this name already exists')
        
        # Create new configuration
        config_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # If this is the first configuration, make it active
        is_first_config = len(self.configurations) == 0
        
        new_config = {
            'id': config_id,
            'name': name,
            'apiUrl': api_url,
            'apiKey': api_key,
            'model': model,
            'isActive': is_first_config,
            'createdAt': now,
            'updatedAt': now
        }
        
        self.configurations[config_id] = new_config
        self.save_configurations()
        
        return new_config
    
    def update_configuration(self, config_id, name, api_url, api_key='', model=''):
        """Update an existing configuration"""
        if config_id not in self.configurations:
            raise ValueError('Configuration not found')
        
        # Check if name already exists (excluding current config)
        for cid, config in self.configurations.items():
            if cid != config_id and config['name'].lower() == name.lower():
                raise ValueError('Configuration with this name already exists')
        
        # Update configuration
        config = self.configurations[config_id]
        config['name'] = name
        config['apiUrl'] = api_url
        config['apiKey'] = api_key
        config['model'] = model
        config['updatedAt'] = datetime.now().isoformat()
        
        self.save_configurations()
        return config
    
    def delete_configuration(self, config_id):
        """Delete a configuration"""
        if config_id not in self.configurations:
            raise ValueError('Configuration not found')
        
        config = self.configurations[config_id]
        was_active = config['isActive']
        
        # Delete the configuration
        del self.configurations[config_id]
        
        # If the deleted config was active, make another one active
        if was_active and self.configurations:
            # Make the first remaining configuration active
            next_config = next(iter(self.configurations.values()))
            next_config['isActive'] = True
            next_config['updatedAt'] = datetime.now().isoformat()
        
        self.save_configurations()
        return config
    
    def activate_configuration(self, config_id):
        """Set a configuration as active"""
        if config_id not in self.configurations:
            raise ValueError('Configuration not found')
        
        # Deactivate all configurations
        for config in self.configurations.values():
            config['isActive'] = False
        
        # Activate the selected configuration
        config = self.configurations[config_id]
        config['isActive'] = True
        config['updatedAt'] = datetime.now().isoformat()
        
        self.save_configurations()
        return config
    
    def get_active_configuration(self):
        """Get the currently active configuration"""
        for config in self.configurations.values():
            if config['isActive']:
                return config
        return None
