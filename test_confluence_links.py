import os
import requests
import json
from dotenv import dotenv_values

# Load env vars
config = dotenv_values('.env')
CONFLUENCE_URL = config.get('CONFLUENCE_URL')
USERNAME = config.get('CONFLUENCE_USERNAME')
API_TOKEN = config.get('CONFLUENCE_API_TOKEN')

print(f"Confluence URL: {CONFLUENCE_URL}\n")

url = f"{CONFLUENCE_URL}/rest/api/content"
params = {
    'spaceKey': 'AT',
    'type': 'page',
    'limit': 1,
    'expand': '_links'
}

response = requests.get(
    url,
    params=params,
    auth=(USERNAME, API_TOKEN),
    headers={'Accept': 'application/json'}
)

if response.status_code == 200:
    data = response.json()
    if data['results']:
        page = data['results'][0]
        print(f"📄 Page: {page.get('title')}")
        print(f"   Page ID: {page.get('id')}")
        print(f"\n🔗 Available _links:")
        links = page.get('_links', {})
        print(json.dumps(links, indent=2))
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text[:500])

