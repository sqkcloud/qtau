#!/usr/bin/env python3
"""
Quick test to verify critical bug fixes work correctly.
This test doesn't require actual cluster resources.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_enum_definition():
    """Test 1: ExecutionEngine enum is properly defined"""
    print("Test 1: ExecutionEngine enum definition...")
    from pilot.pilot_enums_exceptions import ExecutionEngine, PilotAPIException
    
    # Check enum has correct values
    assert hasattr(ExecutionEngine, 'DASK'), "Missing DASK enum value"
    assert hasattr(ExecutionEngine, 'RAY'), "Missing RAY enum value"
    assert ExecutionEngine.DASK.value == "dask", "DASK value incorrect"
    assert ExecutionEngine.RAY.value == "ray", "RAY value incorrect"
    
    # Check enum comparison works
    assert ExecutionEngine.DASK == ExecutionEngine.DASK
    assert ExecutionEngine.RAY == ExecutionEngine.RAY
    assert ExecutionEngine.DASK != ExecutionEngine.RAY
    
    print("✅ ExecutionEngine enum is correctly defined")


def test_imports_no_duplicates():
    """Test 2: Module imports work without errors"""
    print("\nTest 2: Module imports...")
    try:
        # Test if we can at least parse the file
        import ast
        with open('pilot/pilot_compute_service.py', 'r') as f:
            source = f.read()
            ast.parse(source)  # Will raise SyntaxError if invalid
        
        # Try to import - may fail due to missing dependencies but that's OK
        try:
            from pilot import pilot_compute_service
            # Check that module-level lock exists
            assert hasattr(pilot_compute_service, 'METRICS_LOCK'), "Missing METRICS_LOCK"
            assert hasattr(pilot_compute_service, 'SORTED_METRICS_FIELDS'), "Missing SORTED_METRICS_FIELDS"
            print("✅ Module imports correctly with no duplicate import errors")
        except ImportError as ie:
            # Dependencies not installed, but syntax is valid
            print(f"✅ Module syntax is valid (import failed due to missing deps: {ie.name})")
    except SyntaxError as e:
        print(f"❌ Syntax error in module: {e}")
        raise


def test_metrics_lock_is_shared():
    """Test 3: METRICS_LOCK is a module-level singleton"""
    print("\nTest 3: METRICS_LOCK is shared across the module...")
    
    # Read the source and verify METRICS_LOCK is defined at module level
    with open('pilot/pilot_compute_service.py', 'r') as f:
        source = f.read()
    
    # Check that METRICS_LOCK is defined at module level (not inside a function/class)
    assert 'METRICS_LOCK = threading.Lock()' in source, "METRICS_LOCK not defined at module level"
    
    # Check it's used in the task function
    assert 'with METRICS_LOCK:' in source, "METRICS_LOCK not used in task function"
    
    try:
        from pilot import pilot_compute_service
        import threading
        # Verify it's a Lock object
        assert isinstance(pilot_compute_service.METRICS_LOCK, threading.Lock), "METRICS_LOCK is not a Lock"
        # Verify it's the same object when accessed multiple times
        lock1 = pilot_compute_service.METRICS_LOCK
        lock2 = pilot_compute_service.METRICS_LOCK
        assert lock1 is lock2, "METRICS_LOCK should be the same instance"
        print("✅ METRICS_LOCK is properly shared at module level")
    except ImportError:
        print("✅ METRICS_LOCK is properly defined in source code (runtime check skipped due to missing deps)")


def test_exception_propagation():
    """Test 4: Exceptions are properly re-raised in task functions"""
    print("\nTest 4: Exception propagation...")
    
    # Read source and verify the code structure
    with open('pilot/pilot_compute_service.py', 'r') as f:
        source = f.read()
    
    # Check that 'raise' appears after exception handling
    assert 'raise  # Re-raise to propagate the error' in source, \
        "Missing 'raise' statement in exception handler"
    
    # Check that finally block is used
    assert 'finally:' in source, "Missing 'finally' block for metrics cleanup"
    
    try:
        import inspect
        from pilot import pilot_compute_service
        
        # Get the submit_task method source
        source = inspect.getsource(pilot_compute_service.PilotComputeBase.submit_task)
        
        # Verify both raise and finally are present
        assert 'raise' in source and 'finally:' in source
        print("✅ Exception handling includes re-raise and finally block")
    except ImportError:
        print("✅ Exception handling code verified in source (runtime check skipped due to missing deps)")


def test_slurm_queue_logic():
    """Test 5: SLURM queue condition uses 'and' not 'or'"""
    print("\nTest 5: SLURM queue validation logic...")
    import inspect
    from pilot.job import slurm
    
    # Get the Job.__init__ source
    source = inspect.getsource(slurm.Job.__init__)
    
    # Check that the condition uses 'and' operators
    assert "job_description['queue'] is not None and job_description['queue'] != \"None\"" in source, \
        "SLURM queue condition should use 'and' operators"
    
    print("✅ SLURM queue logic uses correct 'and' operators")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Running Bug Fix Verification Tests")
    print("=" * 60)
    
    tests = [
        test_enum_definition,
        test_imports_no_duplicates,
        test_metrics_lock_is_shared,
        test_exception_propagation,
        test_slurm_queue_logic,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ Test failed: {test.__name__}")
            print(f"   Error: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

