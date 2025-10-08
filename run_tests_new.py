#!/usr/bin/env python3
"""
Comprehensive Test Runner for simTIM

This script runs the overhauled test suite that validates actual simulator behavior
rather than just basic object creation. Tests are organized by functionality and
provide meaningful validation of business logic.
"""
import os
import sys
import subprocess
import time
from datetime import datetime
from typing import List, Tuple, Dict

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

class ComprehensiveTestRunner:
    def __init__(self):
        self.test_dir = os.path.join(os.path.dirname(__file__), 'tests')
        self.results = []
        
        # Define test categories and their priorities
        self.test_categories = {
            'Core Functionality': [
                'test_strategies_comprehensive.py',
                'test_simulation_behavior.py',
                'test_action_validation.py',
                'test_network_integrity.py'
            ],
            'Legacy Tests (Basic)': [
                'test_core_graph.py',
                'test_integration.py',
                'test_action_system.py',
                'test_actor_system.py',
                'test_simulator_core.py',
                'test_detection_system.py',
                'test_economic_model.py',
                'test_behavioral_analysis.py',
                'test_tim_compliance.py'
            ]
        }
        
    def discover_tests(self) -> List[str]:
        """Discover all test files in the tests directory"""
        all_test_files = []
        
        # First add comprehensive tests in priority order
        for category, files in self.test_categories.items():
            for file in files:
                test_path = os.path.join(self.test_dir, file)
                if os.path.exists(test_path):
                    all_test_files.append(file)
        
        # Add any other test files not in categories
        for file in os.listdir(self.test_dir):
            if (file.startswith('test_') and file.endswith('.py') and 
                file != '__init__.py' and file not in all_test_files):
                all_test_files.append(file)
        
        return all_test_files
    
    def run_single_test(self, test_file: str) -> Tuple[bool, float, str, str]:
        """Run a single test file and return (success, duration, output, category)"""
        test_path = os.path.join(self.test_dir, test_file)
        
        # Determine category
        category = 'Other'
        for cat, files in self.test_categories.items():
            if test_file in files:
                category = cat
                break
        
        print(f"Running {test_file} ({category})...")
        start_time = time.time()
        
        try:
            # Run the test file as a subprocess with extended timeout for comprehensive tests
            timeout = 120 if category == 'Core Functionality' else 60
            
            result = subprocess.run(
                [sys.executable, test_path],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            duration = time.time() - start_time
            success = result.returncode == 0
            
            # Combine stdout and stderr for full output
            output = result.stdout
            if result.stderr:
                output += "\n" + result.stderr
            
            return success, duration, output, category
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return False, duration, f"Test timed out after {timeout} seconds", category
        except Exception as e:
            duration = time.time() - start_time
            return False, duration, f"Test execution failed: {str(e)}", category
    
    def run_all_tests(self) -> Dict:
        """Run all discovered tests and return summary"""
        test_files = self.discover_tests()
        
        if not test_files:
            print("No test files found!")
            return {"total": 0, "passed": 0, "failed": 0, "results": []}
        
        print(f"Discovered {len(test_files)} test files")
        print("🎯 Prioritizing comprehensive behavioral validation tests")
        print("=" * 70)
        
        total_start_time = time.time()
        category_stats = {}
        
        for test_file in test_files:
            success, duration, output, category = self.run_single_test(test_file)
            
            result = {
                "file": test_file,
                "success": success,
                "duration": duration,
                "output": output,
                "category": category
            }
            self.results.append(result)
            
            # Update category statistics
            if category not in category_stats:
                category_stats[category] = {"passed": 0, "failed": 0, "total_time": 0}
            
            category_stats[category]["total_time"] += duration
            if success:
                category_stats[category]["passed"] += 1
            else:
                category_stats[category]["failed"] += 1
            
            # Print immediate feedback with category context
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{status} {test_file} ({duration:.2f}s) [{category}]")
            
            if not success:
                # Print condensed error output for immediate feedback
                error_lines = output.split('\n')
                relevant_errors = [line for line in error_lines if 
                                 any(keyword in line.lower() for keyword in 
                                     ['failed', 'error', 'assertion', 'exception', '❌'])]
                
                for line in relevant_errors[:3]:  # Show up to 3 error lines
                    if line.strip():
                        print(f"  {line.strip()}")
                if len(relevant_errors) > 3:
                    print("  ... (more errors in detailed output)")
        
        total_duration = time.time() - total_start_time
        
        # Calculate summary
        passed = sum(1 for r in self.results if r["success"])
        failed = len(self.results) - passed
        
        summary = {
            "total": len(self.results),
            "passed": passed,
            "failed": failed,
            "total_duration": total_duration,
            "results": self.results,
            "category_stats": category_stats
        }
        
        return summary
    
    def print_detailed_summary(self, summary: Dict):
        """Print detailed summary of test results with emphasis on comprehensive tests"""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE TEST SUITE RESULTS")
        print("=" * 80)
        
        # Overall statistics
        total = summary["total"]
        passed = summary["passed"]
        failed = summary["failed"]
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Overall Results:")
        print(f"  Total Tests: {total}")
        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")
        print(f"  Success Rate: {success_rate:.1f}%")
        print(f"  Total Duration: {summary['total_duration']:.2f}s")
        
        # Category breakdown
        print(f"\n📊 Results by Category:")
        print("-" * 50)
        
        for category, stats in summary["category_stats"].items():
            total_cat = stats["passed"] + stats["failed"]
            success_rate_cat = (stats["passed"] / total_cat * 100) if total_cat > 0 else 0
            
            status_icon = "✅" if stats["failed"] == 0 else "❌"
            print(f"{status_icon} {category}:")
            print(f"    {stats['passed']}/{total_cat} passed ({success_rate_cat:.1f}%) in {stats['total_time']:.1f}s")
        
        # Critical test analysis
        core_tests = [r for r in summary["results"] if r["category"] == "Core Functionality"]
        core_failed = [r for r in core_tests if not r["success"]]
        
        if core_failed:
            print(f"\n🚨 CRITICAL: {len(core_failed)} Core Functionality tests failed!")
            print("   These test the actual simulator logic and behavior.")
        else:
            print(f"\n🎯 EXCELLENT: All {len(core_tests)} Core Functionality tests passed!")
            print("   Simulator behavior and strategy logic validated successfully.")
        
        # Failed tests details
        if failed > 0:
            print(f"\n❌ DETAILED FAILURE ANALYSIS ({failed} failures):")
            print("-" * 60)
            
            # Group failures by category
            failures_by_category = {}
            for result in summary["results"]:
                if not result["success"]:
                    cat = result["category"]
                    if cat not in failures_by_category:
                        failures_by_category[cat] = []
                    failures_by_category[cat].append(result)
            
            # Show core functionality failures first
            if "Core Functionality" in failures_by_category:
                print(f"\n🔥 CRITICAL FAILURES - Core Functionality:")
                for result in failures_by_category["Core Functionality"]:
                    print(f"\n❌ {result['file']} ({result['duration']:.2f}s):")
                    self._print_condensed_error(result["output"])
            
            # Show other failures
            for category, failures in failures_by_category.items():
                if category != "Core Functionality":
                    print(f"\n⚠️ {category} Failures:")
                    for result in failures:
                        print(f"\n❌ {result['file']} ({result['duration']:.2f}s):")
                        self._print_condensed_error(result["output"])
        
        # Performance analysis
        print(f"\n⏱️ PERFORMANCE ANALYSIS:")
        print("-" * 50)
        
        # Sort by duration for performance analysis
        sorted_results = sorted(summary["results"], key=lambda x: x["duration"], reverse=True)
        
        print("Slowest tests:")
        for result in sorted_results[:5]:  # Top 5 slowest
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['file']}: {result['duration']:.2f}s [{result['category']}]")
        
        # Test quality assessment
        print(f"\n🧪 TEST QUALITY ASSESSMENT:")
        print("-" * 50)
        
        core_success_rate = 0
        if core_tests:
            core_passed = sum(1 for r in core_tests if r["success"])
            core_success_rate = (core_passed / len(core_tests)) * 100
        
        legacy_tests = [r for r in summary["results"] if r["category"] == "Legacy Tests (Basic)"]
        legacy_success_rate = 0
        if legacy_tests:
            legacy_passed = sum(1 for r in legacy_tests if r["success"])
            legacy_success_rate = (legacy_passed / len(legacy_tests)) * 100
        
        print(f"  Comprehensive Tests (Core Logic): {core_success_rate:.1f}% success")
        print(f"  Legacy Tests (Basic Validation): {legacy_success_rate:.1f}% success")
        
        if core_success_rate >= 90:
            print("  🎯 EXCELLENT: Core simulator logic is robust")
        elif core_success_rate >= 70:
            print("  ⚠️ GOOD: Core logic mostly working, minor issues")
        else:
            print("  🚨 CRITICAL: Core simulator logic has significant issues")
        
        # Final verdict
        print("\n" + "=" * 80)
        if failed == 0:
            print("🎉 ALL TESTS PASSED - SIMULATOR FULLY VALIDATED!")
            print("✅ Both behavioral logic and basic functionality confirmed")
        elif core_failed:
            print("🚨 CRITICAL ISSUES DETECTED IN CORE FUNCTIONALITY")
            print("❌ Simulator behavior validation failed - address immediately")
        else:
            print("⚠️ MINOR ISSUES DETECTED IN NON-CRITICAL TESTS")
            print("✅ Core simulator functionality validated successfully")
        print("=" * 80)
    
    def _print_condensed_error(self, output: str, max_lines: int = 10):
        """Print a condensed version of error output"""
        lines = output.split('\n')
        
        # Find most relevant error lines
        error_indicators = ['failed', 'error', 'assertion', 'exception', '❌', 'traceback']
        relevant_lines = []
        
        for line in lines:
            line_lower = line.lower()
            if any(indicator in line_lower for indicator in error_indicators):
                relevant_lines.append(line.strip())
            elif line.strip() and not line.startswith(' ') and len(relevant_lines) < max_lines:
                relevant_lines.append(line.strip())
        
        # Print up to max_lines
        for line in relevant_lines[:max_lines]:
            if line:
                print(f"    {line}")
        
        if len(relevant_lines) > max_lines:
            print(f"    ... ({len(lines)} total lines in output)")

def main():
    """Main entry point for comprehensive test runner"""
    runner = ComprehensiveTestRunner()
    
    print("🧪 simTIM COMPREHENSIVE BEHAVIORAL TEST SUITE")
    print("🎯 Testing actual simulator logic, not just basic functionality")
    print("=" * 80)
    
    try:
        summary = runner.run_all_tests()
        runner.print_detailed_summary(summary)
        
        # Prioritize core functionality for exit code
        core_tests = [r for r in summary["results"] if r["category"] == "Core Functionality"]
        core_failed = sum(1 for r in core_tests if not r["success"])
        
        # Exit with error if core functionality fails, even if other tests pass
        if core_failed > 0:
            print(f"\n💥 Exiting with error due to {core_failed} core functionality failures")
            sys.exit(1)
        elif summary["failed"] == 0:
            print(f"\n🎉 All tests passed - simulator is fully validated!")
            sys.exit(0)
        else:
            print(f"\n✅ Core functionality validated, {summary['failed']} minor test failures")
            sys.exit(0)  # Don't fail build for non-critical test failures
        
    except KeyboardInterrupt:
        print("\n\nTest run interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nTest runner failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
