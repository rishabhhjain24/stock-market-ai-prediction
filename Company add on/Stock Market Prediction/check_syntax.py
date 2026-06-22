import ast
try:
    with open('enhanced_dashboard.py', 'r') as f:
        code = f.read()
    ast.parse(code)
    print("✓ Syntax valid - no errors")
except SyntaxError as e:
    print(f"✗ Syntax error at line {e.lineno}: {e.msg}")
    print(f"   {e.text}")
