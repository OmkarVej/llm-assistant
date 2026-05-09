#!/usr/bin/env python3
"""
Test the backend with better error logging
"""
import requests
import json

def test_chat():
    """Test the chat endpoint"""
    url = 'http://localhost:8000/chat'
    
    data = {
        'prompt': 'Summarize Jira issue AZ-53118',
        'use_local': False,
        'use_rag': True,
        'save_to_db': True,
        'max_new_tokens': 2000
    }
    
    print("Testing chat endpoint...")
    print(f"URL: {url}")
    print(f"Request: {json.dumps(data, indent=2)}")
    print("\n" + "="*70)
    
    try:
        response = requests.post(url, json=data, timeout=30)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print("\nResponse Body:")
        
        if response.status_code == 200:
            result = response.json()
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_chat()

