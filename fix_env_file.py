#!/usr/bin/env python3
"""
Automatic .env Fixer for Jira Connection
This script fixes common issues in .env file
"""
import os
import re
from pathlib import Path

def fix_env_file():
    """Fix common issues in .env file"""
    env_path = Path('.env')
    
    if not env_path.exists():
        print("❌ .env file not found")
        return False
    
    print("🔧 Analyzing .env file...")
    print("="*70)
    
    # Read current .env
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    changes_made = []
    
    for line in lines:
        original_line = line
        
        # Fix JIRA_URL - remove /jira/ or /wiki/ from end
        if line.startswith('JIRA_URL='):
            url = line.split('=', 1)[1].strip()
            if url:
                # Remove trailing slashes
                url = url.rstrip('/')
                # Remove /jira or /wiki
                url = re.sub(r'/(jira|wiki)$', '', url)
                new_line = f'JIRA_URL={url}\n'
                if new_line != original_line:
                    changes_made.append(f"Fixed JIRA_URL: removed trailing /jira/ or /wiki/")
                    line = new_line
        
        # Fix CONFLUENCE_URL - should have /wiki
        elif line.startswith('CONFLUENCE_URL='):
            url = line.split('=', 1)[1].strip()
            if url and '/wiki' not in url:
                url = url.rstrip('/') + '/wiki'
                new_line = f'CONFLUENCE_URL={url}\n'
                if new_line != original_line:
                    changes_made.append(f"Fixed CONFLUENCE_URL: added /wiki")
                    line = new_line
        
        # Fix JIRA_PROJECTS - warn if has spaces (likely project name not key)
        elif line.startswith('JIRA_PROJECTS='):
            projects = line.split('=', 1)[1].strip()
            if ' ' in projects:
                changes_made.append(f"⚠️  JIRA_PROJECTS has spaces: '{projects}'")
                changes_made.append("   This should be PROJECT KEYS (e.g., PROJ,DEV,SUPPORT)")
                changes_made.append("   Not project names. You need to find the correct keys.")
                changes_made.append("   Commenting out for now - you'll need to fix this manually")
                line = f'# {line}'
                fixed_lines.append(f'JIRA_PROJECTS=\n')
        
        fixed_lines.append(line)
    
    # Write fixes
    if changes_made:
        print("\n✅ Found issues to fix:\n")
        for change in changes_made:
            print(f"  • {change}")
        
        # Backup original
        backup_path = env_path.with_suffix('.env.backup')
        with open(backup_path, 'w') as f:
            f.writelines(lines)
        print(f"\n📦 Backed up original to: {backup_path}")
        
        # Write fixed version
        with open(env_path, 'w') as f:
            f.writelines(fixed_lines)
        print(f"✅ Fixed .env file saved")
        
        return True
    else:
        print("✅ No issues found in .env file")
        return False

def main():
    print("\n" + "="*70)
    print("🔧 .ENV FILE FIXER")
    print("="*70 + "\n")
    
    fixed = fix_env_file()
    
    if fixed:
        print("\n" + "="*70)
        print("⚠️  IMPORTANT: JIRA_PROJECTS needs manual fixing")
        print("="*70)
        print("\nYour .env has JIRA_PROJECTS with a project NAME, not a KEY.")
        print("\nProject KEYS are short codes like:")
        print("  ✅ PROJ")
        print("  ✅ DEV")
        print("  ✅ SUPPORT")
        print("\nProject NAMES are full names like:")
        print("  ❌ 'A2Z Sync App'")
        print("  ❌ 'My Project Name'")
        print("\nTo find your project KEY:")
        print("  1. Remove the JIRA_PROJECTS line (or leave it empty)")
        print("  2. Run: python test_jira_connection.py")
        print("  3. Look at the project list - the KEY is the short code")
        print("  4. Update .env with: JIRA_PROJECTS=KEY1,KEY2,KEY3")
        print()
    
    print("\n" + "="*70)
    print("📋 NEXT STEPS")
    print("="*70)
    print("\n1️⃣  Test connection:")
    print("   python test_jira_connection.py")
    print("\n2️⃣  This will show you all available project KEYS")
    print("\n3️⃣  Update .env with correct project keys:")
    print("   nano .env")
    print("\n4️⃣  Test again to verify")
    print()

if __name__ == "__main__":
    main()

