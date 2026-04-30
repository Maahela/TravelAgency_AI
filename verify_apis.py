
import requests
import time
import sys
import json

BASE_URL = "http://localhost:4003"
ENDPOINTS = [
    ("GET", "/"),
    ("GET", "/health"),
    ("GET", "/system-status"),
    ("GET", "/stats"),
    ("GET", "/rates"),
    ("GET", "/price-items"),
    ("GET", "/contacts"),
    ("GET", "/analytics"),
    ("GET", "/audit-log"),
    ("GET", "/debug-db"),
    ("POST", "/chat", {"message": "Hello, are you working?"})
]

def wait_for_server(url, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            requests.get(url, timeout=1)
            return True
        except requests.exceptions.ConnectionError:
            time.sleep(1)
            print(".", end="", flush=True)
    return False

def test_endpoints():
    print(f"Waiting for server at {BASE_URL}...")
    if not wait_for_server(BASE_URL + "/health"):
        print("\nServer not available.")
        sys.exit(1)
    
    print("\nServer is up! Testing endpoints:\n")
    
    results = []
    
    for endpoint in ENDPOINTS:
        method = endpoint[0]
        path = endpoint[1]
        data = endpoint[2] if len(endpoint) > 2 else None
        
        url = f"{BASE_URL}{path}"
        try:
            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                response = requests.post(url, json=data)
            
            status = response.status_code
            try:
                content = response.json()
                content_str = json.dumps(content, indent=2)
                if len(content_str) > 200:
                    content_str = content_str[:200] + "... (truncated)"
            except:
                content_str = response.text[:200]
            
            print(f"[{method}] {path}: {status}")
            if status != 200:
                print(f"  Error: {content_str}")
            
            results.append({
                "endpoint": path,
                "status": status,
                "success": status == 200
            })
            
        except Exception as e:
            print(f"[{method}] {path}: FAILED - {e}")
            results.append({
                "endpoint": path,
                "status": "EXCEPTION",
                "success": False
            })

    print("\nSummary:")
    success_count = sum(1 for r in results if r['success'])
    print(f"Passed: {success_count}/{len(results)}")

if __name__ == "__main__":
    test_endpoints()
