#!/usr/bin/env python3
"""
Test script to verify VizOS setup
"""

import sys
import os

def test_imports():
    """Test if all modules can be imported"""
    print("Testing module imports...")
    
    try:
        # Add backend modules to path
        sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'modules'))
        
        from fcfs_module import FCFSModule
        from sjf_module import SJFModule
        from priority_module import PriorityModule
        from roundrobin_module import RoundRobinModule
        from bankers_module import BankersModule
        from deadlock_module import DeadlockModule
        
        print("✅ All backend modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_fcfs():
    """Test FCFS algorithm"""
    print("\nTesting FCFS algorithm...")
    
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'modules'))
        from fcfs_module import FCFSModule
        
        fcfs = FCFSModule()
        processes = [
            {"id": "P1", "arrival": 0, "burst": 8, "priority": 3},
            {"id": "P2", "arrival": 1, "burst": 4, "priority": 1}
        ]
        
        result = fcfs.simulate(processes)
        
        if result['algorithm'] == 'FCFS' and 'metrics' in result:
            print("✅ FCFS algorithm working correctly")
            return True
        else:
            print("❌ FCFS algorithm returned unexpected result")
            return False
    except Exception as e:
        print(f"❌ FCFS test failed: {e}")
        return False

def test_bankers():
    """Test Banker's algorithm"""
    print("\nTesting Banker's algorithm...")
    
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'modules'))
        from bankers_module import BankersModule
        
        bankers = BankersModule()
        result = bankers.simulate(3, 3)
        
        if result['algorithm'] == "Banker's Algorithm" and 'safeSequence' in result:
            print("✅ Banker's algorithm working correctly")
            return True
        else:
            print("❌ Banker's algorithm returned unexpected result")
            return False
    except Exception as e:
        print(f"❌ Banker's test failed: {e}")
        return False

def test_file_structure():
    """Test if all required files exist"""
    print("\nTesting file structure...")
    
    required_files = [
        'frontend/index.html',
        'frontend/styles.css',
        'frontend/js/main.js',
        'frontend/js/fcfs.js',
        'frontend/js/sjf.js',
        'frontend/js/priority.js',
        'frontend/js/roundrobin.js',
        'frontend/js/bankers.js',
        'frontend/js/deadlock.js',
        'backend/app.py',
        'backend/requirements.txt',
        'backend/modules/fcfs_module.py',
        'backend/modules/sjf_module.py',
        'backend/modules/priority_module.py',
        'backend/modules/roundrobin_module.py',
        'backend/modules/bankers_module.py',
        'backend/modules/deadlock_module.py',
        'docs/README.md'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if not missing_files:
        print("✅ All required files present")
        return True
    else:
        print(f"❌ Missing files: {missing_files}")
        return False

def main():
    """Run all tests"""
    print("🧪 VizOS Setup Test")
    print("===================")
    
    tests = [
        test_file_structure,
        test_imports,
        test_fcfs,
        test_bankers
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! VizOS is ready to use.")
        print("\nTo start the application:")
        print("1. Run: python backend/app.py")
        print("2. Open: frontend/index.html in your browser")
        print("3. Or use: ./start.sh (Linux/Mac) or start.bat (Windows)")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
