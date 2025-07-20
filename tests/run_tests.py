#!/usr/bin/env python3
"""
Test runner script for Michael's Chat backend API tests.
"""
import subprocess
import sys
import os

def install_test_dependencies():
    """Install test dependencies."""
    print("Installing test dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements-test.txt"])
        print("✅ Test dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install test dependencies: {e}")
        return False
    return True

def run_tests(test_type="all"):
    """Run the tests."""
    print(f"Running {test_type} tests...")
    
    cmd = [sys.executable, "-m", "pytest", ".", "-v"]
    
    if test_type == "unit":
        cmd.extend(["-m", "not integration"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    elif test_type == "all":
        pass  # Run all tests
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run tests: {e}")
        return False

def main():
    """Main function."""
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
        if test_type not in ["unit", "integration", "all"]:
            print("Usage: python run_tests.py [unit|integration|all]")
            sys.exit(1)
    else:
        test_type = "all"
    
    print("🧪 Michael's Chat Backend API Tests")
    print("=" * 50)
    
    # Install dependencies
    if not install_test_dependencies():
        sys.exit(1)
    
    # Run tests
    if run_tests(test_type):
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
