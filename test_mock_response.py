import sys

sys.path.append(".")
from tests.utils import create_mock_response

# Test with status code 200
mock_ok = create_mock_response("https://example.com", "test content", 200)
print(f"URL: {mock_ok.url}, Status: {mock_ok.status_code}")
try:
    mock_ok.raise_for_status()
    print("Status 200: No error raised (correct)")
except Exception as e:
    print(f"Status 200: Error raised (incorrect): {e}")

# Test with status code 404
mock_not_found = create_mock_response("https://example.com", "not found", 404)
print(f"URL: {mock_not_found.url}, Status: {mock_not_found.status_code}")
try:
    mock_not_found.raise_for_status()
    print("Status 404: No error raised (incorrect)")
except Exception as e:
    print(f"Status 404: Error raised (correct): {e}")

# Test with status code 500
mock_server_error = create_mock_response("https://example.com", "server error", 500)
print(f"URL: {mock_server_error.url}, Status: {mock_server_error.status_code}")
try:
    mock_server_error.raise_for_status()
    print("Status 500: No error raised (incorrect)")
except Exception as e:
    print(f"Status 500: Error raised (correct): {e}")

print("All tests completed")
