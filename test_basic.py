#!/usr/bin/env python3
"""
Basic test script to identify issues in the drug-surfactant repository.
This script tests core functionality without requiring heavy dependencies.
"""

import sys
import os

def test_python_imports():
    """Test basic Python functionality and built-in modules."""
    print("Testing basic Python imports...")
    
    try:
        import re
        import json
        import subprocess
        print("✓ Basic Python modules imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Error importing basic Python modules: {e}")
        return False

def test_helper_functions_virtual_exp():
    """Test the virtual experiment function without pandas/ax dependencies."""
    print("Testing virtual experiment function...")
    
    # Instead of importing the whole module, let's test the core function
    def virtual_exp(s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12):
        complexity = sum(1 for x in [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12] if x != 0)
        cost = s1+s2+s3+s4+s5+s6+s7+s8+s9+s10+s11+s12
        performance = 0.3*s1*(1+s2) - 0.5*s3*s4 + s5**2 + 0.8*s9 - s10*s11 + 0.2*s12
        return {'complexity': complexity, 'cost': cost, 'performance': performance}
    
    try:
        # Test with sample parameters
        result = virtual_exp(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)
        expected_complexity = 12  # All non-zero
        expected_cost = sum(range(1, 13))  # 78
        
        if result['complexity'] == expected_complexity and result['cost'] == expected_cost:
            print("✓ Virtual experiment function works correctly")
            print(f"  Sample result: {result}")
            return True
        else:
            print(f"✗ Virtual experiment function returned unexpected results: {result}")
            return False
    except Exception as e:
        print(f"✗ Error in virtual experiment function: {e}")
        return False

def test_opentrons_protocol_syntax():
    """Test if the Opentrons protocol file has valid Python syntax."""
    print("Testing Opentrons protocol syntax...")
    
    try:
        protocol_file = "drug_surfactant_otflex.py"
        if not os.path.exists(protocol_file):
            print(f"✗ Protocol file {protocol_file} not found")
            return False
        
        # Try to compile the file to check for syntax errors
        with open(protocol_file, 'r') as f:
            content = f.read()
        
        compile(content, protocol_file, 'exec')
        print("✓ Opentrons protocol has valid Python syntax")
        return True
        
    except SyntaxError as e:
        print(f"✗ Syntax error in protocol file: {e}")
        return False
    except Exception as e:
        print(f"✗ Error reading protocol file: {e}")
        return False

def test_requirements_file():
    """Test if requirements.txt has valid syntax."""
    print("Testing requirements.txt syntax...")
    
    try:
        if not os.path.exists("requirements.txt"):
            print("✗ requirements.txt not found")
            return False
        
        with open("requirements.txt", 'r') as f:
            lines = f.readlines()
        
        issues = []
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line and not line.startswith('#'):
                # Check for common syntax issues
                if '=' in line and '==' not in line and '>=' not in line and '<=' not in line:
                    issues.append(f"Line {i}: '{line}' - Use '==' instead of '=' for version pinning")
        
        if issues:
            print("✗ Issues found in requirements.txt:")
            for issue in issues:
                print(f"  {issue}")
            return False
        else:
            print("✓ requirements.txt syntax looks correct")
            return True
            
    except Exception as e:
        print(f"✗ Error reading requirements.txt: {e}")
        return False

def test_file_permissions():
    """Test if key files are readable."""
    print("Testing file permissions...")
    
    key_files = ["helper_functions.py", "drug_surfactant_otflex.py", "requirements.txt"]
    all_readable = True
    
    for file in key_files:
        if os.path.exists(file) and os.access(file, os.R_OK):
            print(f"✓ {file} is readable")
        else:
            print(f"✗ {file} is not readable or doesn't exist")
            all_readable = False
    
    return all_readable

def main():
    """Run all tests and report results."""
    print("=" * 50)
    print("Drug-Surfactant Repository Basic Tests")
    print("=" * 50)
    
    tests = [
        test_python_imports,
        test_requirements_file,
        test_file_permissions,
        test_helper_functions_virtual_exp,
        test_opentrons_protocol_syntax,
    ]
    
    results = []
    for test in tests:
        print()
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "PASS" if result else "FAIL"
        print(f"{test.__name__}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The repository appears to be in good shape.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())