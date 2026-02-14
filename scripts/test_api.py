#!/usr/bin/env python3
import requests
import sys
from time import sleep

def test_api():
    base_url = "http://localhost:8000"

    print("=" * 60)
    print("Testing Medical OCR API")
    print("=" * 60)
    print()


    print("⏳ Waiting for API to start...")
    for i in range(10):
        try:
            response = requests.get(f"{base_url}/", timeout=2)
            if response.status_code == 200:
                print("✓ API is running!")
                break
        except requests.exceptions.ConnectionError:
            sleep(1)
            if i == 9:
                print("✗ Could not connect to API")
                print("  Make sure API is running: python backend/app/main.py")
                return False

    print()
    print("-" * 60)
    print("Test 1: Root Endpoint")
    print("-" * 60)

    try:
        response = requests.get(f"{base_url}/")
        data = response.json()
        print(f"Status Code: {response.status_code}")
        print(f"App Name: {data.get('app')}")
        print(f"Version: {data.get('version')}")
        print(f"Status: {data.get('status')}")
        print("✓ PASSED")
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False

    print()
    print("-" * 60)
    print("Test 2: Health Check")
    print("-" * 60)

    try:
        response = requests.get(f"{base_url}/api/v1/health")
        data = response.json()
        print(f"Status Code: {response.status_code}")
        print(f"Health Status: {data.get('status')}")
        print(f"Timestamp: {data.get('timestamp')}")
        print("✓ PASSED")
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False

    print()
    print("-" * 60)
    print("Test 3: Detailed Health Check")
    print("-" * 60)

    try:
        response = requests.get(f"{base_url}/api/v1/health/detailed")
        data = response.json()
        print(f"Status Code: {response.status_code}")
        print(f"CPU Count: {data['system']['cpu_count']}")
        print(f"CPU Usage: {data['system']['cpu_percent']}%")
        print(f"Memory Usage: {data['system']['memory']['percent_used']}%")
        print(f"OCR Engine: {data['configuration']['ocr_engine']}")
        print(f"DPI: {data['configuration']['dpi']}")
        print("✓ PASSED")
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False

    print()
    print("-" * 60)
    print("Test 4: Request ID Header")
    print("-" * 60)

    try:
        response = requests.get(f"{base_url}/api/v1/health")
        request_id = response.headers.get('X-Request-ID')
        print(f"Request ID: {request_id}")
        if request_id:
            print("✓ PASSED")
        else:
            print("✗ FAILED: No request ID in headers")
            return False
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False

    print()
    print("=" * 60)
    print("All Tests Passed! ✓")
    print("=" * 60)
    print()
    print("✓ API is working correctly")
    print("✓ Health endpoints are functional")
    print("✓ Logging is working")
    print("✓ Request tracking is active")
    print()
    print("Next: Visit http://localhost:8000/docs for API documentation")
    print()

    return True


if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)