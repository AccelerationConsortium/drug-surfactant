#!/usr/bin/env python3
"""
Advanced test script to identify import and dependency issues.
"""

import sys
import os
import importlib

def test_import_availability():
    """Test which imports are available without installing anything."""
    print("Testing import availability...")
    
    # Required modules from helper_functions.py
    modules_to_test = [
        ("pandas", "pd"),
        ("numpy", "np"), 
        ("matplotlib.pyplot", "plt"),
        ("subprocess", None),
        ("re", None),
        ("json", None),
    ]
    
    # Ax platform modules
    ax_modules = [
        ("ax.service.ax_client", "AxClient, ObjectiveProperties"),
        ("ax.modelbridge.factory", "Models"),
        ("ax.modelbridge.generation_strategy", "GenerationStep, GenerationStrategy"),
    ]
    
    available_modules = []
    missing_modules = []
    
    for module_path, alias in modules_to_test + ax_modules:
        try:
            if alias:
                exec(f"import {module_path} as {alias}")
            else:
                exec(f"import {module_path}")
            available_modules.append(module_path)
            print(f"✓ {module_path} - Available")
        except ImportError as e:
            missing_modules.append((module_path, str(e)))
            print(f"✗ {module_path} - Missing: {e}")
        except Exception as e:
            missing_modules.append((module_path, str(e)))
            print(f"✗ {module_path} - Error: {e}")
    
    return available_modules, missing_modules

def test_helper_functions_imports():
    """Test importing helper_functions.py and identify specific issues."""
    print("\nTesting helper_functions.py imports...")
    
    try:
        import helper_functions
        print("✓ helper_functions.py imported successfully")
        
        # Test specific functions
        if hasattr(helper_functions, 'virtual_exp'):
            result = helper_functions.virtual_exp(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)
            print(f"✓ virtual_exp function works: {result}")
        
        if hasattr(helper_functions, 'optimizer_init'):
            print("✓ optimizer_init function found")
            try:
                # Don't actually call it since it might fail, just check it exists
                print("  Note: Not calling optimizer_init due to potential dependency issues")
            except Exception as e:
                print(f"  Warning: optimizer_init might have issues: {e}")
        
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import helper_functions.py: {e}")
        return False
    except Exception as e:
        print(f"✗ Error with helper_functions.py: {e}")
        return False

def test_opentrons_imports():
    """Test Opentrons protocol imports."""
    print("\nTesting Opentrons protocol imports...")
    
    try:
        # Test if opentrons module is available
        import opentrons
        print("✓ opentrons module is available")
        
        # Test specific imports from the protocol
        from opentrons import protocol_api
        print("✓ protocol_api imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Opentrons not available: {e}")
        print("  This is expected in environments without Opentrons installed")
        return False
    except Exception as e:
        print(f"✗ Error with Opentrons imports: {e}")
        return False

def create_compatibility_helper():
    """Create a simplified version of helper functions that work without heavy dependencies."""
    print("\nCreating compatibility helper...")
    
    try:
        compatibility_code = '''
import json
import subprocess

def virtual_exp(s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12):
    """Virtual experiment function that works without dependencies."""
    complexity = sum(1 for x in [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12] if x != 0)
    cost = s1+s2+s3+s4+s5+s6+s7+s8+s9+s10+s11+s12
    performance = 0.3*s1*(1+s2) - 0.5*s3*s4 + s5**2 + 0.8*s9 - s10*s11 + 0.2*s12
    return {'complexity': complexity, 'cost': cost, 'performance': performance}

def optimizer_init_dummy():
    """Dummy optimizer function for testing."""
    print("Dummy optimizer init - would normally create AxClient")
    return None

def design_to_conc_dummy(data):
    """Dummy design to concentration conversion."""
    print("Dummy design_to_conc - would normally use pandas")
    return data

def upload_file_to_robot(local_file_path, remote_file_name):
    """Upload file to robot - same as original."""
    remote_user = 'root'
    remote_host = '192.168.10.143'
    remote_folder = '/var/lib/jupyter/notebooks/Zeqing_Bao/drug_surfactant/'
    remote_file_path = remote_folder + remote_file_name

    mkdir_command = [
        'ssh',
        f'{remote_user}@{remote_host}',
        f'mkdir -p {remote_folder}'
    ]

    try:
        mkdir_result = subprocess.run(mkdir_command, capture_output=True, text=True)
        if mkdir_result.returncode == 0:
            print("Remote notebooks directory ready.")
        else:
            print("Failed to verify/create notebooks directory.")
            print("Error:", mkdir_result.stderr)

        scp_command = [
            'scp',
            local_file_path,
            f'{remote_user}@{remote_host}:{remote_file_path}'
        ]

        scp_result = subprocess.run(scp_command, capture_output=True, text=True)
        if scp_result.returncode == 0:
            print("File transfer successful!")
        else:
            print("File transfer failed.")
            print("Error:", scp_result.stderr)
    except Exception as e:
        print(f"Error in file transfer: {e}")
'''
        
        with open('helper_functions_minimal.py', 'w') as f:
            f.write(compatibility_code)
        
        print("✓ Created helper_functions_minimal.py for basic functionality")
        
        # Test the minimal version
        import helper_functions_minimal
        result = helper_functions_minimal.virtual_exp(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)
        print(f"✓ Minimal virtual_exp works: {result}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error creating compatibility helper: {e}")
        return False

def main():
    """Run all advanced tests."""
    print("=" * 60)
    print("Drug-Surfactant Repository Advanced Dependency Tests")
    print("=" * 60)
    
    available_modules, missing_modules = test_import_availability()
    
    helper_works = test_helper_functions_imports()
    opentrons_works = test_opentrons_imports()
    compatibility_created = create_compatibility_helper()
    
    print("\n" + "=" * 60)
    print("Summary and Recommendations:")
    print("=" * 60)
    
    print(f"\nAvailable modules: {len(available_modules)}")
    for module in available_modules:
        print(f"  ✓ {module}")
    
    print(f"\nMissing modules: {len(missing_modules)}")
    for module, error in missing_modules:
        print(f"  ✗ {module}: {error}")
    
    print("\nRecommendations:")
    
    if missing_modules:
        print("1. Install missing dependencies:")
        unique_modules = set()
        for module, _ in missing_modules:
            if module.startswith('ax.'):
                unique_modules.add('ax-platform')
            elif module == 'pandas':
                unique_modules.add('pandas')
            elif module == 'numpy':
                unique_modules.add('numpy') 
            elif module == 'matplotlib.pyplot':
                unique_modules.add('matplotlib')
        
        print(f"   pip install {' '.join(unique_modules)}")
    
    if not helper_works:
        print("2. Use helper_functions_minimal.py for basic functionality")
    
    if not opentrons_works:
        print("3. Install Opentrons for protocol execution: pip install opentrons")
    
    print("\n4. Current repository status:")
    if len(missing_modules) == 0:
        print("   🎉 All dependencies available - ready to run!")
    elif len(missing_modules) <= 3:
        print("   ⚠️  Minor dependency issues - easily fixable")
    else:
        print("   🔧 Major dependency issues - need to install requirements")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())