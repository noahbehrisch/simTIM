import sys
import os
import subprocess
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_test(test_file, description):

    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"File: {test_file}")
    print(f"{'='*60}")
    start_time = time.time()
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, 
                              text=True, 
                              cwd=os.path.dirname(os.path.abspath(__file__)))
        duration = time.time() - start_time
        if result.returncode == 0:
            print(f"✅ PASSED ({duration:.2f}s)")
            if result.stdout:
                print("Output:")
                print(result.stdout)
            return True
        else:
            print(f"❌ FAILED ({duration:.2f}s)")
            if result.stderr:
                print("Error:")
                print(result.stderr)
            if result.stdout:
                print("Output:")
                print(result.stdout)
            return False
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ ERROR ({duration:.2f}s): {e}")
        return False
def main():

    print("🚀 simTIM Test Suite Runner")
    print("=" * 60)
    tests = [
        ("tests/test_integration.py", "Core system integration"),
        ("tests/test_focused_interruption.py", "TIM temporal monitoring compliance"),
        ("tests/test_smt_conditions.py", "Enhanced SMT-like condition system"),
        ("tests/test_network_library.py", "Network library functionality"),
        ("tests/demo_action_system.py", "Action system demonstration"),
        ("tests/test_tim_economic_model.py", "TIM economic model implementation"),
    ]
    results = []
    total_start = time.time()
    for test_file, description in tests:
        if os.path.exists(test_file):
            success = run_test(test_file, description)
            results.append((test_file, description, success))
        else:
            print(f"\n⚠️  SKIPPED: {test_file} (file not found)")
            results.append((test_file, description, None))
    total_duration = time.time() - total_start
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    passed = sum(1 for _, _, result in results if result is True)
    failed = sum(1 for _, _, result in results if result is False)
    skipped = sum(1 for _, _, result in results if result is None)
    total = len(results)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Skipped: {skipped} ⚠️")
    print(f"Total Time: {total_duration:.2f}s")
    print(f"\nDetailed Results:")
    for test_file, description, result in results:
        status = "✅ PASS" if result is True else "❌ FAIL" if result is False else "⚠️ SKIP"
        print(f"  {status} - {description}")
    if failed > 0:
        print(f"\n❌ Test suite failed ({failed} failures)")
        sys.exit(1)
    else:
        print(f"\n🎉 All tests passed!")
        sys.exit(0)
if __name__ == "__main__":
    main()