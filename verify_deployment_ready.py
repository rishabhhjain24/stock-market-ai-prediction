#!/usr/bin/env python3
"""
Pre-Deployment Verification Script
Checks if everything is ready for deployment to Streamlit Cloud/Railway/Heroku
"""

import os
import sys
import subprocess
from pathlib import Path

def check_file_exists(filepath):
    """Check if file exists"""
    exists = os.path.exists(filepath)
    status = "✅" if exists else "❌"
    print(f"{status} {filepath}")
    return exists

def check_git_status():
    """Check if git repo is initialized and files are committed"""
    print("\n" + "="*60)
    print("🔍 GIT STATUS CHECK")
    print("="*60)
    
    try:
        result = subprocess.run(['git', 'status'], capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            print("✅ Git repository initialized")
            print("\n📊 Current status:")
            print(result.stdout)
            return True
        else:
            print("❌ Git repository not initialized")
            print("   Run: git init && git add . && git commit -m 'Initial commit'")
            return False
    except Exception as e:
        print(f"❌ Git check failed: {e}")
        return False

def check_github_remote():
    """Check if GitHub remote is configured"""
    print("\n" + "="*60)
    print("🌐 GITHUB REMOTE CHECK")
    print("="*60)
    
    try:
        result = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True)
        if result.stdout:
            print("✅ GitHub remote configured:")
            print(result.stdout)
            return True
        else:
            print("❌ GitHub remote not configured")
            print("   Run: git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git")
            return False
    except Exception as e:
        print(f"❌ Remote check failed: {e}")
        return False

def check_requirements():
    """Check if requirements.txt exists and has core dependencies"""
    print("\n" + "="*60)
    print("📦 REQUIREMENTS CHECK")
    print("="*60)
    
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt not found!")
        print("   Run: pip freeze > requirements.txt")
        return False
    
    print("✅ requirements.txt exists")
    
    required = ['streamlit', 'pandas', 'numpy', 'yfinance']
    with open('requirements.txt', 'r') as f:
        content = f.read().lower()
    
    missing = [pkg for pkg in required if pkg.lower() not in content]
    
    if missing:
        print(f"⚠️  Missing packages: {missing}")
        print("   Add them to requirements.txt")
        return False
    
    print("✅ All core packages found")
    return True

def check_streamlit_app():
    """Check if trading_dashboard.py exists"""
    print("\n" + "="*60)
    print("📱 STREAMLIT APP CHECK")
    print("="*60)
    
    if not os.path.exists('trading_dashboard.py'):
        print("❌ trading_dashboard.py not found!")
        return False
    
    print("✅ trading_dashboard.py exists")
    
    # Check if it has streamlit imports
    with open('trading_dashboard.py', 'r') as f:
        content = f.read()
    
    if 'import streamlit' in content:
        print("✅ Streamlit import found")
        return True
    else:
        print("⚠️  Streamlit import not found - make sure it's a Streamlit app")
        return False

def check_gitignore():
    """Check if .gitignore properly excludes secrets"""
    print("\n" + "="*60)
    print("🔐 SECURITY CHECK (.gitignore)")
    print("="*60)
    
    if not os.path.exists('.gitignore'):
        print("⚠️  .gitignore not found - creating one")
        create_gitignore()
        return False
    
    with open('.gitignore', 'r') as f:
        gitignore_content = f.read()
    
    security_patterns = ['.env', '__pycache__', '*.pyc', '.vscode', 'venv']
    missing = [p for p in security_patterns if p not in gitignore_content]
    
    if missing:
        print(f"⚠️  Missing security patterns: {missing}")
        print("   Add these to .gitignore")
        return False
    
    print("✅ .gitignore properly configured")
    return True

def create_gitignore():
    """Create a standard .gitignore"""
    content = """.env
.env.local
.DS_Store
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/
.vscode/
.idea/
venv/
env/
node_modules/
.streamlit/secrets.toml
"""
    with open('.gitignore', 'w') as f:
        f.write(content)
    print("✅ Created .gitignore")

def check_api_keys():
    """Check if API keys are in code (they shouldn't be)"""
    print("\n" + "="*60)
    print("🔑 API KEY CHECK (Hardcoded keys?)")
    print("="*60)
    
    suspicious_files = []
    
    for root, dirs, files in os.walk('.'):
        # Skip hidden dirs and common non-code dirs
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', 'env']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Check for common API key patterns
                    if any(keyword in content for keyword in ['api_key = "', "api_key = '", 'apikey="', "apikey='"]):
                        suspicious_files.append(filepath)
                except:
                    pass
    
    if suspicious_files:
        print("⚠️  Found potential hardcoded API keys in:")
        for f in suspicious_files:
            print(f"   - {f}")
        print("\n   ❌ SECURITY RISK! Move them to environment variables or .env")
        return False
    
    print("✅ No hardcoded API keys found")
    return True

def main():
    """Run all checks"""
    print("\n" + "="*70)
    print("🚀 PRE-DEPLOYMENT VERIFICATION")
    print("="*70)
    print("\nThis script checks if your app is ready for deployment.\n")
    
    checks = [
        ("Git initialization", check_git_status),
        ("GitHub remote", check_github_remote),
        ("Requirements", check_requirements),
        ("Streamlit app", check_streamlit_app),
        (".gitignore security", check_gitignore),
        ("API key hardcoding", check_api_keys),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error checking {name}: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*70)
    print("📋 SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")
    
    print(f"\n✅ {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 YOUR APP IS READY TO DEPLOY!")
        print("\n📱 Next steps:")
        print("1. Go to https://share.streamlit.io")
        print("2. Click 'Create new app'")
        print("3. Connect to your GitHub repo")
        print("4. Deploy trading_dashboard.py")
        print("\nYou'll have a live URL in 2-3 minutes!")
        return 0
    else:
        print("\n⚠️  Please fix the failing checks before deploying.")
        print("   See messages above for what to do.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
