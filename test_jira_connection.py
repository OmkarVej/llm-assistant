#!/usr/bin/env python3
"""
Test Jira Connection and Configuration
This script helps debug Jira connection issues
"""
import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
JIRA_URL = os.getenv('JIRA_URL')
JIRA_USERNAME = os.getenv('JIRA_USERNAME')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
JIRA_PROJECTS = os.getenv('JIRA_PROJECTS', '').split(',')

print("\n" + "="*70)
print("🔍 JIRA CONNECTION TESTER")
print("="*70)

# Step 1: Check environment variables
print("\n1️⃣ Checking Environment Variables...")
print("-" * 70)

if not JIRA_URL:
    print("❌ JIRA_URL is not set")
else:
    print(f"✅ JIRA_URL: {JIRA_URL}")

if not JIRA_USERNAME:
    print("❌ JIRA_USERNAME is not set")
else:
    print(f"✅ JIRA_USERNAME: {JIRA_USERNAME}")

if not JIRA_API_TOKEN:
    print("❌ JIRA_API_TOKEN is not set")
else:
    print(f"✅ JIRA_API_TOKEN: {'*' * 10}{JIRA_API_TOKEN[-4:]} (last 4 chars)")

if not JIRA_PROJECTS or JIRA_PROJECTS == ['']:
    print("⚠️  JIRA_PROJECTS is not set (this is optional if using JQL)")
else:
    print(f"✅ JIRA_PROJECTS: {', '.join(JIRA_PROJECTS)}")

# Stop if credentials are missing
if not all([JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN]):
    print("\n❌ Missing required credentials. Please check your .env file.")
    print("\nAdd these to your .env file:")
    print("  JIRA_URL=https://yourcompany.atlassian.net")
    print("  JIRA_USERNAME=your-email@company.com")
    print("  JIRA_API_TOKEN=your-api-token")
    print("  JIRA_PROJECTS=PROJ,DEV")
    sys.exit(1)

# Step 2: Test basic authentication
print("\n2️⃣ Testing Authentication...")
print("-" * 70)

try:
    # Test with myself endpoint (always works if auth is correct)
    url = f"{JIRA_URL.rstrip('/')}/rest/api/3/myself"
    response = requests.get(
        url,
        auth=(JIRA_USERNAME, JIRA_API_TOKEN),
        headers={'Accept': 'application/json'}
    )
    
    if response.status_code == 200:
        user_data = response.json()
        print(f"✅ Authentication successful!")
        print(f"   Logged in as: {user_data.get('displayName', 'Unknown')}")
        print(f"   Email: {user_data.get('emailAddress', 'Unknown')}")
        print(f"   Account ID: {user_data.get('accountId', 'Unknown')}")
    elif response.status_code == 401:
        print("❌ Authentication failed!")
        print("   Possible reasons:")
        print("   - API token is incorrect or expired")
        print("   - Username (email) is incorrect")
        print("   - Token doesn't have required permissions")
        print("\n   Create a new token at:")
        print("   https://id.atlassian.com/manage-profile/security/api-tokens")
        sys.exit(1)
    elif response.status_code == 404:
        print("❌ Jira URL is incorrect!")
        print(f"   Your URL: {JIRA_URL}")
        print("   Make sure it's in the format: https://yourcompany.atlassian.net")
        print("   (NO /wiki at the end for Jira)")
        sys.exit(1)
    else:
        print(f"⚠️  Unexpected response: {response.status_code}")
        print(f"   Response: {response.text}")
        sys.exit(1)
        
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to Jira!")
    print(f"   URL: {JIRA_URL}")
    print("   Check:")
    print("   - Is the URL correct?")
    print("   - Do you have internet connection?")
    print("   - Is Jira accessible from your network?")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Step 3: Test project access
print("\n3️⃣ Testing Project Access...")
print("-" * 70)

try:
    url = f"{JIRA_URL.rstrip('/')}/rest/api/3/project"
    response = requests.get(
        url,
        auth=(JIRA_USERNAME, JIRA_API_TOKEN),
        headers={'Accept': 'application/json'}
    )
    response.raise_for_status()
    
    projects = response.json()
    
    if not projects:
        print("⚠️  No projects found!")
        print("   You may not have access to any Jira projects.")
        print("   Ask your Jira admin to grant you access.")
    else:
        print(f"✅ Found {len(projects)} accessible projects:")
        print()
        for project in projects[:10]:  # Show first 10
            key = project.get('key', 'N/A')
            name = project.get('name', 'N/A')
            project_type = project.get('projectTypeKey', 'N/A')
            print(f"   📋 {key} - {name} ({project_type})")
        
        if len(projects) > 10:
            print(f"   ... and {len(projects) - 10} more")
        
        # Check if user's specified projects exist
        if JIRA_PROJECTS and JIRA_PROJECTS != ['']:
            print("\n   Checking your specified projects:")
            project_keys = [p.get('key') for p in projects]
            for proj in JIRA_PROJECTS:
                proj = proj.strip()
                if proj in project_keys:
                    print(f"   ✅ {proj} - Found!")
                else:
                    print(f"   ❌ {proj} - NOT FOUND (check spelling/access)")
        
except Exception as e:
    print(f"❌ Error fetching projects: {e}")
    sys.exit(1)

# Step 4: Test fetching issues from first available project
print("\n4️⃣ Testing Issue Fetch...")
print("-" * 70)

if projects:
    # Try the first project or user's specified project
    if JIRA_PROJECTS and JIRA_PROJECTS != ['']:
        test_project = JIRA_PROJECTS[0].strip()
    else:
        test_project = projects[0].get('key')
    
    print(f"Testing with project: {test_project}")
    
    try:
        url = f"{JIRA_URL.rstrip('/')}/rest/api/3/search"
        params = {
            'jql': f'project={test_project} ORDER BY updated DESC',
            'maxResults': 5,
            'fields': 'summary,status,priority,issuetype'
        }
        
        response = requests.get(
            url,
            auth=(JIRA_USERNAME, JIRA_API_TOKEN),
            headers={'Accept': 'application/json'},
            params=params
        )
        response.raise_for_status()
        
        data = response.json()
        total = data.get('total', 0)
        issues = data.get('issues', [])
        
        print(f"✅ Found {total} total issues in {test_project}")
        
        if issues:
            print(f"\n   Sample issues (showing {len(issues)}):")
            for issue in issues:
                key = issue.get('key', 'N/A')
                fields = issue.get('fields', {})
                summary = fields.get('summary', 'No summary')
                status = fields.get('status', {}).get('name', 'Unknown')
                print(f"   🎫 {key}: {summary[:50]}... [{status}]")
        else:
            print(f"   ⚠️  No issues found in {test_project}")
            print("   This project might be empty.")
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            print(f"❌ Invalid JQL query or project key: {test_project}")
            print("   Make sure the project key is correct (case-sensitive)")
        else:
            print(f"❌ Error fetching issues: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

# Summary
print("\n" + "="*70)
print("📊 SUMMARY")
print("="*70)

print("\n✅ Tests Completed!")
print("\nIf all tests passed:")
print("  1. Your Jira connection is working")
print("  2. Your credentials are correct")
print("  3. You can now run: python load_jira.py")

print("\nIf you see errors:")
print("  - Fix any issues mentioned above")
print("  - Update your .env file with correct values")
print("  - Make sure project keys are spelled correctly (case-sensitive)")

print("\n💡 Tips:")
print("  - Use the project keys shown above in your .env file")
print("  - JIRA_PROJECTS should be comma-separated: PROJ1,PROJ2,PROJ3")
print("  - No spaces between project keys")

print("\n" + "="*70)

