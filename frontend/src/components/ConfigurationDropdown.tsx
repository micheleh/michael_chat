import React, { useState, useRef, useEffect } from 'react';
import { Configuration } from '../types/types';

interface ConfigurationDropdownProps {
  configurations: Configuration[];
  activeConfiguration: Configuration | null;
  onConfigurationChange: (configId: string) => void;
  disabled?: boolean;
}

const ConfigurationDropdown: React.FC<ConfigurationDropdownProps> = ({
  configurations,
  activeConfiguration,
  onConfigurationChange,
  disabled = false
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleToggle = () => {
    if (!disabled) {
      setIsOpen(!isOpen);
    }
  };

  const handleSelect = (configId: string) => {
    onConfigurationChange(configId);
    setIsOpen(false);
  };

  const sortedConfigurations = configurations
    .slice()
    .sort((a, b) => a.name.localeCompare(b.name));

  return (
    <div className="custom-dropdown" ref={dropdownRef}>
      <button
        type="button"
        className={`custom-dropdown-button ${isOpen ? 'open' : ''} ${disabled ? 'disabled' : ''}`}
        onClick={handleToggle}
        disabled={disabled}
      >
        <span className="custom-dropdown-selected">
          {activeConfiguration?.name || 'Select Configuration'}
        </span>
        <span className="custom-dropdown-arrow">
          <svg width="12" height="8" viewBox="0 0 12 8" fill="none">
            <path 
              d={isOpen ? "M11 6.5L6 1.5L1 6.5" : "M1 1.5L6 6.5L11 1.5"} 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            />
          </svg>
        </span>
      </button>
      
      {isOpen && !disabled && (
        <div className="custom-dropdown-list">
          {sortedConfigurations.map((config) => (
            <button
              key={config.id}
              type="button"
              className={`custom-dropdown-option ${config.id === activeConfiguration?.id ? 'active' : ''}`}
              onClick={() => handleSelect(config.id)}
            >
              <span className="config-name">{config.name}</span>
              {config.id === activeConfiguration?.id && (
                <span className="config-check">✓</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default ConfigurationDropdown;
