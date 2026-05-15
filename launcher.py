#!/usr/bin/env python3
# launcher.py - Simple launcher for the AI Trading System

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Launch the enhanced dashboard"""
    
    print("\n" + "="*60)
    print("🤖 AI Stock Trading System - Enhanced Dashboard")
    print("="*60)
    print("\n📊 Multi-Stock Support + Intraday Scalping Signals\n")
    
    # Check .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env file not found!")
        print("   Please create .env with:")
        print("   GEMINI_API_KEY=your_key")
        print("   NEWS_API_KEY=your_key")
        print("   DEFAULT_STOCK=RELIANCE.NS\n")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    else:
        print("✅ .env file found")
    
    print("\n🚀 Launching dashboard...\n")
    print("   Opening: http://localhost:8501")
    print("   Press Ctrl+C to stop\n")
    
    print("-"*60)
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "enhanced_dashboard.py"
        ])
    except KeyboardInterrupt:
        print("\n\n✅ Dashboard stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
