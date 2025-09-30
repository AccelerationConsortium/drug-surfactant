#!/usr/bin/env python3
"""
Simple dependency installer for drug-surfactant repository.
This script installs dependencies in a safe and controlled manner.
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a single package using pip."""
    try:
        print(f"Installing {package}...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", package, "--timeout", "30"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ {package} installed successfully")
            return True
        else:
            print(f"✗ Failed to install {package}: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Error installing {package}: {e}")
        return False

def main():
    """Install core dependencies."""
    print("=" * 50)
    print("Installing Drug-Surfactant Dependencies")
    print("=" * 50)
    
    # Basic dependencies needed for core functionality
    packages = [
        "numpy",
        "pandas", 
        "matplotlib",
    ]
    
    # Try to install each package
    successful = []
    failed = []
    
    for package in packages:
        if install_package(package):
            successful.append(package)
        else:
            failed.append(package)
    
    print("\n" + "=" * 50)
    print("Installation Summary:")
    print("=" * 50)
    
    if successful:
        print(f"✓ Successfully installed: {', '.join(successful)}")
    
    if failed:
        print(f"✗ Failed to install: {', '.join(failed)}")
        print("\nNote: Some packages may require internet connectivity")
        print("You can try installing them manually when online:")
        print(f"pip install {' '.join(failed)}")
    
    # Test imports after installation
    print("\nTesting imports after installation...")
    try:
        import numpy as np
        print("✓ numpy works")
        
        import pandas as pd
        print("✓ pandas works")
        
        import matplotlib.pyplot as plt
        print("✓ matplotlib works")
        
        print("\n🎉 Basic dependencies are now working!")
        print("Note: ax-platform and opentrons still need to be installed separately")
        
        return 0
        
    except ImportError as e:
        print(f"✗ Import test failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())