#!/usr/bin/env python3
"""
Quick script to list Confluence spaces and their keys
"""
import os
import sys

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv('.env')
except ImportError:
    pass

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from confluence_loader import ConfluenceLoader

def main():
    confluence_url = os.getenv('CONFLUENCE_URL')
    username = os.getenv('CONFLUENCE_USERNAME')
    api_token = os.getenv('CONFLUENCE_API_TOKEN')
    
    if not all([confluence_url, username, api_token]):
        print("❌ Missing Confluence credentials in .env file")
        return 1
    
    print(f"\n🔍 Connecting to: {confluence_url}")
    print(f"   Username: {username}\n")
    
    loader = ConfluenceLoader(confluence_url, username, api_token)
    
    print("📚 Fetching your Confluence spaces...\n")
    spaces = loader.get_spaces()
    
    if not spaces:
        print("❌ No spaces found or connection failed")
        return 1
    
    print(f"✅ Found {len(spaces)} spaces:\n")
    print("="*70)
    print(f"{'KEY':<20} {'NAME':<40} {'TYPE':<10}")
    print("="*70)
    
    for space in spaces:
        key = space.get('key', 'N/A')
        name = space.get('name', 'N/A')
        space_type = space.get('type', 'N/A')
        print(f"{key:<20} {name[:38]:<40} {space_type:<10}")
    
    print("="*70)
    print("\n💡 Use the 'KEY' column in your CONFLUENCE_SPACES setting")
    print(f"   Example: CONFLUENCE_SPACES={spaces[0].get('key', 'KEY1')},{spaces[1].get('key', 'KEY2') if len(spaces) > 1 else 'KEY2'}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

