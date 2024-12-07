import requests
import json
import sys
from datetime import datetime

# Use localhost since we're running in Codespaces
BASE_URL = "http://localhost:8000/api"

def test_endpoint(method, endpoint, data=None):
    """Test an API endpoint with better error handling"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\nTesting {method.upper()} {url}")
    
    try:
        if method.lower() == 'get':
            response = requests.get(url)
        else:
            response = requests.post(url, json=data)
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to {url}")
        print("Make sure the Flask server is running and accessible")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        try:
            print("Response:", response.json())
        except:
            print("Response:", response.text)
        return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def format_json(data):
    """Format JSON data for display"""
    return json.dumps(data, indent=2)

def main():
    # First test the health endpoint
    print("\nTesting health endpoint...")
    if not test_endpoint('get', '/health'):
        print("Health check failed. Exiting.")
        sys.exit(1)

    # Load the source JSON file
    try:
        with open('source.json', 'r') as f:
            test_data = json.load(f)
    except Exception as e:
        print(f"Error loading source.json: {str(e)}")
        sys.exit(1)

    # Test validation endpoint
    print("\nTesting validation endpoint...")
    result = test_endpoint('post', '/validate', test_data)
    if result:
        print("Validation Response:")
        print(format_json(result))

    # Test batch processing endpoint
    print("\nTesting batch processing endpoint...")
    batch_data = [test_data]
    result = test_endpoint('post', '/batch/process', batch_data)
    if result:
        print("Batch Processing Response:")
        print(format_json(result))

    # Test statistics endpoint
    print("\nTesting statistics endpoint...")
    result = test_endpoint('get', '/stats')
    if result:
        print("Statistics Response:")
        print(format_json(result))

    # Test errors endpoint
    print("\nTesting errors endpoint...")
    result = test_endpoint('get', '/errors')
    if result:
        print("Recent Errors:")
        print(format_json(result))

if __name__ == "__main__":
    main()
