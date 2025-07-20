# API Tests for Michael's Chat Backend

This directory contains comprehensive API tests for the Michael's Chat backend server. The tests are designed to be run without affecting your existing configuration files.

## Test Overview

### 🧪 Test Categories

1. **Configuration API Tests** (`TestConfigurationAPI`)
   - Create, read, update, delete configurations
   - Configuration activation/deactivation
   - Validation and error handling
   - Uses temporary configuration files (won't affect your real configs)

2. **Chat API Tests** (`TestChatAPI`)
   - Chat endpoint functionality
   - Request/response validation
   - Integration tests with real API endpoints
   - Error handling for missing fields

3. **Health API Tests** (`TestHealthAPI`)
   - Backend health check endpoint
   - External API health check functionality

## 🚀 Quick Start

### Install Test Dependencies
```bash
cd tests
pip install -r requirements-test.txt
```

### Run All Tests
```bash
cd tests
python3 -m pytest test_api.py -v
```

### Or Use the Test Runner Script
```bash
cd tests
python3 run_tests.py
```

### Run Specific Test Categories
```bash
cd tests
# Run only configuration tests
python3 -m pytest test_api.py::TestConfigurationAPI -v

# Run only chat tests
python3 -m pytest test_api.py::TestChatAPI -v

# Run only health tests
python3 -m pytest test_api.py::TestHealthAPI -v
```

### Run Unit Tests Only (skip integration tests)
```bash
cd tests
python3 -m pytest test_api.py -v -m "not integration"
```

### Run Integration Tests Only
```bash
cd tests
python3 -m pytest test_api.py -v -m "integration"
```

## 📋 Test Details

### Configuration API Tests

These tests create and use temporary configuration files, so they won't interfere with your existing configurations:

- ✅ **Create Configuration**: Tests creating new configurations with validation
- ✅ **Update Configuration**: Tests updating existing configurations
- ✅ **Delete Configuration**: Tests deleting configurations
- ✅ **Activate Configuration**: Tests switching between configurations
- ✅ **Get Active Configuration**: Tests retrieving the currently active config
- ✅ **Error Handling**: Tests validation, duplicate names, missing fields

### Chat API Tests

- ✅ **Basic Chat**: Tests chat endpoint with required fields
- ✅ **Missing Fields**: Tests error handling for missing parameters
- ✅ **Mock Endpoint**: Tests with httpbin.org for basic functionality
- ✅ **Integration**: Tests with real API endpoints (marked as integration tests)

### Health API Tests

- ✅ **Backend Health**: Tests the `/api/health` endpoint
- ✅ **External API Health**: Tests the `/api/test-external` endpoint

## 🔧 Configuration Testing

The tests use a sophisticated approach to avoid affecting your real configuration files:

1. **Temporary Files**: Each test creates a temporary configuration file
2. **Isolated Config Manager**: Uses a separate ConfigurationManager instance
3. **Automatic Cleanup**: Temporary files are automatically deleted after tests
4. **No Side Effects**: Your real `configurations.json` remains untouched

## 📊 Test Results

### Expected Output
```
================ test session starts ================
platform darwin -- Python 3.11.5, pytest-8.4.1
collected 15 items

test_api.py::TestConfigurationAPI::test_get_empty_configurations PASSED
test_api.py::TestConfigurationAPI::test_create_configuration PASSED
test_api.py::TestConfigurationAPI::test_create_configuration_missing_fields PASSED
test_api.py::TestConfigurationAPI::test_create_duplicate_configuration PASSED
test_api.py::TestConfigurationAPI::test_get_configurations PASSED
test_api.py::TestConfigurationAPI::test_update_configuration PASSED
test_api.py::TestConfigurationAPI::test_delete_configuration PASSED
test_api.py::TestConfigurationAPI::test_activate_configuration PASSED
test_api.py::TestConfigurationAPI::test_get_active_configuration PASSED
test_api.py::TestChatAPI::test_chat_missing_fields PASSED
test_api.py::TestChatAPI::test_chat_with_mock_endpoint PASSED
test_api.py::TestHealthAPI::test_health_check PASSED
test_api.py::TestHealthAPI::test_external_api_health PASSED

================ 13 passed in 2.34s ================
```

## 🧑‍💻 Integration Tests

Integration tests are marked with `@pytest.mark.integration` and test against real API endpoints:

- **Local API**: Tests against `http://localhost:10001` (if available)
- **External APIs**: Tests against configured external APIs
- **Automatic Skipping**: If endpoints are not available, tests are automatically skipped

### Running Integration Tests

```bash
# Run integration tests (requires real API endpoints)
python3 -m pytest test_api.py -v -m "integration"

# Run all tests including integration
python3 -m pytest test_api.py -v
```

## 🔍 Debugging

To see detailed output during tests:

```bash
# Run with extra verbose output
python3 -m pytest test_api.py -vv

# Run with stdout capture disabled (see print statements)
python3 -m pytest test_api.py -v -s

# Run a specific test with detailed output
python3 -m pytest test_api.py::TestConfigurationAPI::test_create_configuration -vv -s
```

## 📁 Test File Structure

```
backend/
├── test_api.py              # Main test file
├── requirements-test.txt    # Test dependencies
├── pytest.ini              # Pytest configuration
├── run_tests.py            # Test runner script
└── README-TESTS.md         # This file
```

## ⚠️ Important Notes

1. **Safe Testing**: All tests use temporary files - your real configurations are never modified
2. **Network Tests**: Some tests make real HTTP requests to test endpoints
3. **Local Dependencies**: Integration tests may require local API servers to be running
4. **Cleanup**: Temporary files are automatically cleaned up after each test

## 🎯 Adding New Tests

To add new tests:

1. Add test methods to the appropriate test class
2. Use the existing fixtures for app, client, and temporary configs
3. Follow the naming convention: `test_<functionality>`
4. Mark integration tests with `@pytest.mark.integration`

Example:
```python
def test_new_feature(self, client):
    \"\"\"Test description.\"\"\"
    response = client.get('/api/new-endpoint')
    assert response.status_code == 200
    assert 'expected_field' in response.json
```

## 🤝 Contributing

When adding new API endpoints or modifying existing ones:

1. Add corresponding tests to `test_api.py`
2. Update this README if needed
3. Run the full test suite to ensure nothing breaks
4. Consider both unit and integration test scenarios
