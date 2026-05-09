#!/usr/bin/env python3
"""
Interactive Setup Script for Jira Connection
This script helps you configure Jira credentials step-by-step
"""
import os
import sys
import requests
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def print_step(number, text):
    """Print formatted step"""
    print(f"\n{number}️⃣  {text}")
    print("-" * 70)

def test_jira_connection(url, username, token):
    """Test Jira connection with provided credentials"""
    try:
        test_url = f"{url.rstrip('/')}/rest/api/3/myself"
        response = requests.get(
            test_url,
            auth=(username, token),
            headers={'Accept': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            user_data = response.json()
            return True, user_data
        elif response.status_code == 401:
            return False, "Authentication failed. Check your username/token."
        elif response.status_code == 404:
            return False, "Jira URL not found. Check the URL format."
        else:
            return False, f"Unexpected error: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to Jira. Check your URL and network."
    except Exception as e:
        return False, str(e)

def get_jira_projects(url, username, token):
    """Get list of accessible Jira projects"""
    try:
        projects_url = f"{url.rstrip('/')}/rest/api/3/project"
        response = requests.get(
            projects_url,
            auth=(username, token),
            headers={'Accept': 'application/json'},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"⚠️  Error fetching projects: {e}")
        return []

def main():
    print_header("🔧 JIRA CONNECTION SETUP WIZARD")
    
    print("This wizard will help you configure Jira integration.")
    print("You'll need:")
    print("  • Your Jira site URL")
    print("  • Your Jira email/username")
    print("  • A Jira API token")
    
    input("\nPress Enter to continue...")
    
    # Step 1: Get Jira URL
    print_step(1, "Configure Jira URL")
    print("Enter your Jira URL (e.g., https://yourcompany.atlassian.net)")
    print("⚠️  Important: Do NOT include /wiki at the end")
    
    while True:
        jira_url = input("\nJira URL: ").strip()
        
        if not jira_url:
            print("❌ URL cannot be empty")
            continue
        
        # Clean up URL
        jira_url = jira_url.rstrip('/')
        if '/wiki' in jira_url:
            jira_url = jira_url.replace('/wiki', '')
            print(f"ℹ️  Removed /wiki from URL: {jira_url}")
        
        if not jira_url.startswith('http'):
            jira_url = f"https://{jira_url}"
            print(f"ℹ️  Added https://: {jira_url}")
        
        print(f"✅ Using URL: {jira_url}")
        break
    
    # Step 2: Get Username
    print_step(2, "Configure Username/Email")
    print("Enter your Jira email address")
    
    while True:
        username = input("\nJira Username/Email: ").strip()
        
        if not username:
            print("❌ Username cannot be empty")
            continue
        
        if '@' not in username:
            print("⚠️  Username should be your email address")
            confirm = input("Continue anyway? (y/n): ").lower()
            if confirm != 'y':
                continue
        
        print(f"✅ Using username: {username}")
        break
    
    # Step 3: Get API Token
    print_step(3, "Configure API Token")
    print("You need to create a Jira API token.")
    print("\n📋 Instructions:")
    print("  1. Go to: https://id.atlassian.com/manage-profile/security/api-tokens")
    print("  2. Click 'Create API token'")
    print("  3. Give it a name (e.g., 'Mini LLM Assistant')")
    print("  4. Copy the token")
    print("  5. Paste it below")
    print("\n⚠️  Token will be hidden when you paste it")
    
    while True:
        try:
            import getpass
            api_token = getpass.getpass("\nJira API Token: ").strip()
        except:
            api_token = input("\nJira API Token: ").strip()
        
        if not api_token:
            print("❌ API token cannot be empty")
            continue
        
        if len(api_token) < 10:
            print("❌ API token seems too short. Please check.")
            continue
        
        print(f"✅ Token received (length: {len(api_token)} characters)")
        break
    
    # Step 4: Test Connection
    print_step(4, "Testing Connection")
    print("Verifying your credentials...")
    
    success, result = test_jira_connection(jira_url, username, api_token)
    
    if success:
        print("✅ Connection successful!")
        print(f"   Logged in as: {result.get('displayName', 'Unknown')}")
        print(f"   Email: {result.get('emailAddress', 'Unknown')}")
    else:
        print(f"❌ Connection failed: {result}")
        print("\n⚠️  Please check your credentials and try again.")
        print("   Run this script again: python setup_jira_connection.py")
        sys.exit(1)
    
    # Step 5: Get Projects
    print_step(5, "Discover Projects")
    print("Fetching your accessible Jira projects...")
    
    projects = get_jira_projects(jira_url, username, api_token)
    
    if not projects:
        print("⚠️  No projects found or you don't have access to any.")
        print("   You can still save credentials and configure projects later.")
        project_keys = ""
    else:
        print(f"✅ Found {len(projects)} accessible projects:\n")
        
        for i, project in enumerate(projects[:20], 1):  # Show max 20
            key = project.get('key', 'N/A')
            name = project.get('name', 'N/A')
            ptype = project.get('projectTypeKey', 'N/A')
            print(f"   {i:2d}. {key:10s} - {name[:40]:40s} ({ptype})")
        
        if len(projects) > 20:
            print(f"   ... and {len(projects) - 20} more projects")
        
        print("\n📋 Which projects would you like to index?")
        print("   Enter project keys separated by commas (e.g., PROJ,DEV,SUPPORT)")
        print("   Or press Enter to skip for now")
        
        project_keys = input("\nProject Keys: ").strip().upper()
    
    # Step 6: Save to .env
    print_step(6, "Save Configuration")
    
    env_path = Path(__file__).parent / '.env'
    
    # Read existing .env if it exists
    existing_env = {}
    if env_path.exists():
        print(f"ℹ️  Found existing .env file at {env_path}")
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    existing_env[key.strip()] = value.strip()
    
    # Update with new values
    existing_env['JIRA_URL'] = jira_url
    existing_env['JIRA_USERNAME'] = username
    existing_env['JIRA_API_TOKEN'] = api_token
    if project_keys:
        existing_env['JIRA_PROJECTS'] = project_keys
    
    # Write to .env
    with open(env_path, 'w') as f:
        f.write("# ============================================\n")
        f.write("# MINI LLM ASSISTANT - ENVIRONMENT VARIABLES\n")
        f.write("# ============================================\n\n")
        
        f.write("# ============================================\n")
        f.write("# OpenAI Configuration\n")
        f.write("# ============================================\n")
        f.write(f"OPENAI_API_KEY={existing_env.get('OPENAI_API_KEY', 'your-openai-api-key-here')}\n")
        f.write(f"OPENAI_MODEL={existing_env.get('OPENAI_MODEL', 'gpt-4o-mini')}\n\n")
        
        f.write("# ============================================\n")
        f.write("# Jira Configuration\n")
        f.write("# ============================================\n")
        f.write(f"JIRA_URL={jira_url}\n")
        f.write(f"JIRA_USERNAME={username}\n")
        f.write(f"JIRA_API_TOKEN={api_token}\n")
        if project_keys:
            f.write(f"JIRA_PROJECTS={project_keys}\n")
        else:
            f.write("JIRA_PROJECTS=\n")
        f.write("JIRA_JQL=\n\n")
        
        f.write("# ============================================\n")
        f.write("# Confluence Configuration\n")
        f.write("# ============================================\n")
        f.write(f"CONFLUENCE_URL={existing_env.get('CONFLUENCE_URL', jira_url + '/wiki')}\n")
        f.write(f"CONFLUENCE_USERNAME={username}\n")
        f.write(f"CONFLUENCE_API_TOKEN={api_token}\n")
        f.write(f"CONFLUENCE_SPACES={existing_env.get('CONFLUENCE_SPACES', '')}\n\n")
        
        f.write("# ============================================\n")
        f.write("# Database Configuration\n")
        f.write("# ============================================\n")
        f.write(f"DB_TYPE={existing_env.get('DB_TYPE', 'sqlite')}\n")
        f.write(f"DB_PATH={existing_env.get('DB_PATH', 'data/assistant.db')}\n")
    
    print(f"✅ Configuration saved to: {env_path}")
    
    # Step 7: Next Steps
    print_header("🎉 SETUP COMPLETE!")
    
    print("✅ Jira credentials configured successfully!\n")
    print("📋 Next Steps:\n")
    print("  1️⃣  Test your connection:")
    print("     python test_jira_connection.py\n")
    
    if project_keys:
        print("  2️⃣  Load Jira issues into knowledge base:")
        print("     python load_jira.py\n")
    else:
        print("  2️⃣  Update .env with project keys:")
        print("     nano .env")
        print("     (Add: JIRA_PROJECTS=YOUR,PROJECT,KEYS)\n")
    
    print("  3️⃣  Start the application:")
    print("     ./run_all.sh\n")
    
    print("💡 Tips:")
    print("  • You can edit .env file anytime to change settings")
    print("  • Use same API token for Confluence")
    print("  • Run this script again to reconfigure\n")
    
    print("="*70)
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        print(f"\nFull error:\n{traceback.format_exc()}")
        sys.exit(1)

