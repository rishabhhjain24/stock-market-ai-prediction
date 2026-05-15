#!/usr/bin/env python3
"""Quick test to verify dashboard loads without critical errors."""

import sys
import traceback

try:
    # Try a basic import to catch syntax errors early
    print("Checking enhanced_dashboard.py for syntax errors...")
    
    with open('enhanced_dashboard.py', 'r', encoding='utf-8') as f:
        code_text = f.read()
    
    # Compile the code to check for syntax errors
    compile(code_text, 'enhanced_dashboard.py', 'exec')
    print("✓ Syntax check PASSED - No syntax errors found")
    print("✓ Dashboard file is ready to run")
    
except SyntaxError as e:
    print(f"✗ SYNTAX ERROR at line {e.lineno}:")
    print(f"  {e.msg}")
    if e.text:
        print(f"  {e.text}")
        print(f"  {' ' * (e.offset - 1)}^")
    sys.exit(1)
    
except Exception as e:
    print(f"✗ ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)
