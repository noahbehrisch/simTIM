import sys
import os
import subprocess
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_test(test_file, description, category=""):
    print(f"\n{'='*70}")
    print(f"Running: {description}")
    print(f"File: {test_file}")
    if category:
        print(f"Category: {category}")
    print(f"{'='*70}")
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
                # Show condensed output for passed tests
                lines = result.stdout.strip().split('\n')
                summary_lines = [line for line in lines if '✅' in line or 'PASSED' in line or line.startswith('  ✅')]
                if summary_lines:
                    print("Summary:")
                    for line in summary_lines[-5:]:  # Show last 5 summary lines
                        print(line)
                else:
                    print("Output:")
                    print(result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
            return True, duration
        else:
            print(f"❌ FAILED ({duration:.2f}s)")
            if result.stderr:
                print("Error:")
                print(result.stderr)
            if result.stdout:
                print("Output:")
                print(result.stdout)
            return False, duration
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ ERROR ({duration:.2f}s): {e}")
        return False, duration

def main():
    import argparse
    parser = argparse.ArgumentParser(description='simTIM Comprehensive Test Suite')
    parser.add_argument('--category', choices=['core', 'advanced', 'integration', 'behavioral', 'all'], 
                       default='all', help='Test category to run')
    parser.add_argument('--analysis-only', action='store_true', 
                       help='Run only behavioral analysis tests')
    args = parser.parse_args()
    
    print("🚀 simTIM Comprehensive Test Suite")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if args.category != 'all':
        print(f"Running category: {args.category}")
    if args.analysis_only:
        print("Mode: Analysis only (no pass/fail validation)")
    print()
    
    # Organized test categories
    test_categories = [
        ("Core Components", [
            ("tests/test_core_graph.py", "Graph Structure (Nodes, Links, Networks)"),
            ("tests/test_actor_system.py", "Actor System (Attackers, Defenders, Capacity)"),
            ("tests/test_action_system.py", "Action System (Preconditions, Postconditions, JSON)"),
        ]),
        ("Advanced Systems", [
            ("tests/test_detection_system.py", "Detection Engine (Probability, Timing)"),
            ("tests/test_simulator_core.py", "Simulator Core (Events, Temporal Logic)"),
            ("tests/test_economic_model.py", "Economic Model (Costs, Damage, Objectives)"),
        ]),
        ("Integration", [
            ("tests/test_integration.py", "Full System Integration"),
        ]),
        ("Behavioral Analysis", [
            ("tests/test_behavioral_analysis.py", "Component Behavior and Interaction Analysis"),
            ("tests/test_tim_compliance.py", "TIM Model Compliance Analysis"),
        ])
    ]
    
    # Filter test categories based on arguments
    if args.analysis_only:
        test_categories = [("Behavioral Analysis", test_categories[-1][1])]
    elif args.category != 'all':
        category_map = {
            'core': [test_categories[0]],
            'advanced': [test_categories[1]], 
            'integration': [test_categories[2]],
            'behavioral': [test_categories[3]]
        }
        test_categories = category_map.get(args.category, test_categories)
    
    results = []
    total_start = time.time()
    
    # Run tests by category
    for category_name, tests in test_categories:
        print(f"\n🔧 {category_name} Tests")
        print("-" * 50)
        
        for test_file, description in tests:
            if os.path.exists(test_file):
                success, duration = run_test(test_file, description, category_name)
                results.append((test_file, description, success, duration, category_name))
            else:
                print(f"\n⚠️  SKIPPED: {test_file} (file not found)")
                results.append((test_file, description, None, 0, category_name))
    
    total_duration = time.time() - total_start
    
    # Generate comprehensive summary
    print(f"\n{'='*70}")
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print(f"{'='*70}")
    
    passed = sum(1 for _, _, result, _, _ in results if result is True)
    failed = sum(1 for _, _, result, _, _ in results if result is False)
    skipped = sum(1 for _, _, result, _, _ in results if result is None)
    total = len(results)
    
    print(f"🕒 Total Time: {total_duration:.2f}s")
    print(f"📈 Total Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Skipped: {skipped}")
    print(f"📊 Success Rate: {(passed/total*100):.1f}%" if total > 0 else "No tests run")
    
    # Category breakdown
    print(f"\n📋 Results by Category:")
    for category_name, tests in test_categories:
        category_results = [r for r in results if r[4] == category_name]
        cat_passed = sum(1 for r in category_results if r[2] is True)
        cat_total = len(category_results)
        cat_rate = (cat_passed/cat_total*100) if cat_total > 0 else 0
        print(f"  {category_name}: {cat_passed}/{cat_total} passed ({cat_rate:.1f}%)")
    
    # Detailed results
    print(f"\n📝 Detailed Results:")
    for test_file, description, result, duration, category in results:
        if result is True:
            status = f"✅ PASS ({duration:.2f}s)"
        elif result is False:
            status = f"❌ FAIL ({duration:.2f}s)"
        else:
            status = "⚠️ SKIP"
        print(f"  {status} - {description}")
    
    # Performance insights
    if any(r[2] is True for r in results):
        slowest_test = max((r for r in results if r[2] is True), key=lambda x: x[3])
        fastest_test = min((r for r in results if r[2] is True), key=lambda x: x[3])
        avg_duration = sum(r[3] for r in results if r[2] is True) / passed
        
        print(f"\n⚡ Performance Insights:")
        print(f"  Slowest: {slowest_test[1]} ({slowest_test[3]:.2f}s)")
        print(f"  Fastest: {fastest_test[1]} ({fastest_test[3]:.2f}s)")
        print(f"  Average: {avg_duration:.2f}s per test")
    
    # Final status
    print(f"\n{'='*70}")
    if failed > 0:
        print(f"❌ Test suite FAILED ({failed} failures)")
        print("🔍 Review failed tests above for details")
        sys.exit(1)
    elif skipped > 0:
        print(f"⚠️  Test suite completed with {skipped} skipped tests")
        print("✨ All available tests passed!")
        sys.exit(0)
    else:
        print("🎉 ALL TESTS PASSED!")
        print("🚀 simTIM is ready for action!")
        sys.exit(0)

if __name__ == "__main__":
    main()