# -*- coding: utf-8 -*-
"""
Configure GitHub Pages via API
"""
import os
import requests
import json
import time

REPO_OWNER = "victorcandido1"
REPO_NAME = "cityexpansions_corporate"

# Check for GitHub token
token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')

if not token:
    print("="*80)
    print("GITHUB TOKEN NOT FOUND")
    print("="*80)
    print("\nTo configure GitHub Pages automatically, you need a GitHub Personal Access Token.")
    print("\n1. Create a token at: https://github.com/settings/tokens")
    print("   - Click 'Generate new token (classic)'")
    print("   - Select scope: 'repo' (full control)")
    print("   - Copy the token")
    print("\n2. Set the token:")
    print("   $env:GITHUB_TOKEN = 'your_token_here'")
    print("   python configure_github_pages.py")
    print("\nOR configure manually:")
    print("   https://github.com/victorcandido1/cityexpansions_corporate/settings/pages")
    exit(1)

# Configure GitHub Pages
url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pages'
headers = {
    'Authorization': f'token {token}',
    'Accept': 'application/vnd.github.v3+json'
}
data = {
    'source': {
        'branch': 'main',
        'path': '/'
    }
}

print("="*80)
print("CONFIGURING GITHUB PAGES")
print("="*80)
print(f"\nRepository: {REPO_OWNER}/{REPO_NAME}")
print(f"Branch: main")
print(f"Path: / (root)")

try:
    # First, try to get current settings
    response = requests.get(url, headers=headers, timeout=10)
    
    if response.status_code == 200:
        current = response.json()
        print(f"\n[INFO] GitHub Pages already configured!")
        print(f"Status: {current.get('status', 'unknown')}")
        print(f"URL: {current.get('html_url', 'N/A')}")
        
        # Update if needed
        if current.get('source', {}).get('branch') != 'main':
            print("\n[INFO] Updating configuration...")
            response = requests.put(url, headers=headers, json=data, timeout=10)
            if response.status_code == 200:
                print("[OK] Configuration updated!")
            else:
                print(f"[WARNING] Update failed: {response.status_code}")
    elif response.status_code == 404:
        # Not configured yet, create it
        print("\n[INFO] Configuring GitHub Pages...")
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 201:
            print("[OK] GitHub Pages configured successfully!")
            result = response.json()
            print(f"Status: {result.get('status', 'unknown')}")
            print(f"URL: {result.get('html_url', 'N/A')}")
        else:
            print(f"[ERROR] Status code: {response.status_code}")
            print(response.text)
    else:
        print(f"[ERROR] Status code: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"[ERROR] {e}")
    print("\nPlease configure manually at:")
    print(f"https://github.com/{REPO_OWNER}/{REPO_NAME}/settings/pages")

print("\n" + "="*80)
print("NEXT STEPS")
print("="*80)
print("\n1. Wait 1-2 minutes for GitHub to process")
print("\n2. Access your dashboard at:")
print(f"   https://{REPO_OWNER}.github.io/{REPO_NAME}/")
print(f"   https://{REPO_OWNER}.github.io/{REPO_NAME}/10percent/dashboard_integrated.html")
print("\n3. Check status at:")
print(f"   https://github.com/{REPO_OWNER}/{REPO_NAME}/settings/pages")

